import pandas as pd
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
import time
from tqdm import tqdm
import sys
import os
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- Configuration ---
INPUT_FILE = 'cinemometros.csv'
OUTPUT_FILE = 'cinemometros_geocoded.csv'
USER_AGENT = "speedcamera_geocoder_v1.1"
RATE_LIMIT_DELAY = 1.1  # Seconds between requests (Nominatim policy says absolute max 1/s)

def clean_address(raw_address):
    """
    Cleans and formats the raw address string for better geocoding results.
    """
    if not isinstance(raw_address, str):
        return ""
    
    # Remove "sentido de circulación" descriptions which confuse the geocoder
    clean = raw_address.split("sentido")[0]
    
    # Remove some common noise words seen in the file
    clean = clean.replace(" (carril sentido descendente)", "")
    clean = clean.replace(" (carril sentido ascendente)", "")
    
    # Ensure it ends with Argentina context if possible
    if "Argentina" not in clean:
        clean = f"{clean.strip()}, Argentina"
        
    return clean

def geocode_address(geolocator, raw_address):
    """
    Geocodes a single address string. Returns (lat, lon, formatted_address).
    """
    query_address = clean_address(raw_address)
    try:
        location = geolocator.geocode(query_address)
        if location:
            return location.latitude, location.longitude, location.address
        
        # Fallback: Try less granular search
        parts = query_address.split(',')
        if len(parts) >= 3:
            simple_address = f"{parts[-2]}, {parts[-1]}"
            location = geolocator.geocode(simple_address)
            if location:
                return location.latitude, location.longitude, location.address + " (approx)"
                
    except (GeocoderTimedOut, GeocoderUnavailable):
        # In a real threaded env, we might want to retry, but for simplicity we return None
        # and let the main loop handle (or just leave empty)
        pass
    except Exception as e:
        # print(f"Error: {e}")
        pass
        
    return None, None, None

def main():
    parser = argparse.ArgumentParser(description='Geocode speed cameras.')
    parser.add_argument('--test', action='store_true', help='Run in test mode (first 5 unique records)')
    parser.add_argument('--workers', type=int, default=1, help='Number of threads (Default 1 to respect Rate Limits)')
    args = parser.parse_args()

    print(f"Reading {INPUT_FILE}...")
    try:
        df = pd.read_csv(INPUT_FILE)
    except FileNotFoundError:
        print(f"Error: {INPUT_FILE} not found.")
        return

    # Identify Unique Addresses
    unique_addresses = df['lugar_de_instalacion'].unique()
    print(f"Total records: {len(df)}. Unique addresses: {len(unique_addresses)}")
    
    # Create a DataFrame for unique addresses
    unique_df = pd.DataFrame({'lugar_de_instalacion': unique_addresses})
    unique_df['lat'] = None
    unique_df['lon'] = None
    unique_df['formatted_address'] = None

    # Load existing progress if any
    if os.path.exists('unique_cache.csv'):
        print("Loading cached unique addresses...")
        cached_df = pd.read_csv('unique_cache.csv')
        # Update unique_df with known values
        # We merge to keep only current unique addresses but fill known ones
        unique_df = pd.merge(unique_df, cached_df[['lugar_de_instalacion', 'lat', 'lon', 'formatted_address']], 
                             on='lugar_de_instalacion', how='left', suffixes=('', '_y'))
        
        # Coalesce
        if 'lat_y' in unique_df.columns:
            unique_df['lat'] = unique_df['lat'].fillna(unique_df['lat_y'])
            unique_df['lon'] = unique_df['lon'].fillna(unique_df['lon_y'])
            unique_df['formatted_address'] = unique_df['formatted_address'].fillna(unique_df['formatted_address_y'])
            unique_df = unique_df.drop(columns=['lat_y', 'lon_y', 'formatted_address_y'])

    # Determine what to process
    if args.test:
        print("Running in TEST mode (processing first 5 unique records)...")
        to_process_indices = unique_df[unique_df['lat'].isnull()].head(5).index
    else:
        to_process_indices = unique_df[unique_df['lat'].isnull()].index
        print(f"Addresses remaining to geocode: {len(to_process_indices)}")

    geolocator = Nominatim(user_agent=USER_AGENT)

    # We use a lock or just robust logic. Since we are updating specific indices, it's thread-safe enough for pandas in this context?
    # Actually, pandas isn't strictly thread safe for writing. 
    # Better to collect results and update.

    results = []
    
    # To respect rate limits with threading, we need to be careful.
    # If workers=1, it is sequential.
    # If workers > 1, we share the pool.
    
    # NOTE: Nominatim requires 1 req/sec. We enforce this by sleeping.
    # If we have multiple workers, we can't easily enforce a global rate limit without a lock.
    # But filtering uniqueness IS the speedup.
    
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        future_to_index = {}
        for idx in to_process_indices:
            address = unique_df.at[idx, 'lugar_de_instalacion']
            future = executor.submit(geocode_address, geolocator, address)
            future_to_index[future] = idx
            
            # Simple rate limiting: Sleep in the main submission loop? 
            # No, that slows down submission but not execution if pool is large.
            # But with workers=1 it behaves sequentially.
            if args.workers == 1:
                time.sleep(RATE_LIMIT_DELAY)

        for future in tqdm(as_completed(future_to_index), total=len(to_process_indices), desc="Geocoding"):
            idx = future_to_index[future]
            try:
                lat, lon, addr = future.result()
                unique_df.at[idx, 'lat'] = lat
                unique_df.at[idx, 'lon'] = lon
                unique_df.at[idx, 'formatted_address'] = addr
            except Exception as e:
                pass
            
            # If threaded, we might be hitting rate limits.
            if args.workers > 1:
                # We can't really sleep here effectively for the API, 
                # but we rely on the user knowing what they are doing if they asked for threads.
                pass

    # Save cache
    unique_df.to_csv('unique_cache.csv', index=False)

    # Merge back to main DF
    print("Merging results back to main dataset...")
    final_df = pd.merge(df, unique_df, on='lugar_de_instalacion', how='left')
    
    final_output = 'cinemometros_geocoded_test.csv' if args.test else OUTPUT_FILE
    final_df.to_csv(final_output, index=False)
    print(f"Done! Results saved to {final_output}")

if __name__ == "__main__":
    main()
