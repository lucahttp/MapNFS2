import pandas as pd
import json

def convert_csv_to_geojson(input_file, output_file):
    df = pd.read_csv(input_file)
    
    # Filter out rows with missing lat/lon
    df = df.dropna(subset=['lat', 'lon'])
    
    features = []
    for _, row in df.iterrows():
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [float(row['lon']), float(row['lat'])]
            },
            "properties": {
                "address": row['formatted_address'],
                "original_location": row['lugar_de_instalacion'],
                "type": row.get('tipo', 'Unknown')
            }
        }
        features.append(feature)
        
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    with open(output_file, 'w') as f:
        json.dump(geojson, f, indent=2)
        
    print(f"Converted {len(features)} records to {output_file}")

if __name__ == "__main__":
    convert_csv_to_geojson('cinemometros_geocoded.csv', 'speed_cameras.geojson')
