import csv
import json
import os

EXISTING_GEOJSON = 'speed_cameras.geojson'
CABA_FILE = 'camaras-fijas-de-control-vehicular.csv'
NACION_FILE = 'cinemometros_geocoded.csv'

def load_existing_features():
    if not os.path.exists(EXISTING_GEOJSON):
        return []
    try:
        with open(EXISTING_GEOJSON, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('features', [])
    except:
        return []

def safe_float(val):
    if not val: return None
    try:
        # Handle comma decimal
        return float(str(val).replace(',', '.'))
    except (ValueError, AttributeError):
        return None

def process_caba():
    features = []
    if not os.path.exists(CABA_FILE): 
        print(f"File missing: {CABA_FILE}")
        return features
    
    # Try encodings
    encodings = ['latin-1', 'utf-8', 'cp1252']
    rows = []
    used_enc = ''
    
    for enc in encodings:
        try:
            with open(CABA_FILE, 'r', encoding=enc, newline='') as f:
                reader = csv.DictReader(f, delimiter=';')
                # Force read to check encoding
                rows = list(reader)
            used_enc = enc
            print(f"Read CABA with {enc}")
            break
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"Error reading CABA with {enc}: {e}")
            
    for i, row in enumerate(rows):
        # Validate columns flexibly
        lat_key = next((k for k in row.keys() if k and 'latitud' in k.lower()), None)
        lon_key = next((k for k in row.keys() if k and 'longitud' in k.lower()), None)
        ubi_key = next((k for k in row.keys() if k and 'ubicaci' in k.lower()), None)
        
        if lat_key and lon_key:
            lat = safe_float(row[lat_key])
            lon = safe_float(row[lon_key])
            
            if lat and lon:
                props = {
                    "nroSerie": f"CABA_{i+1}",
                    "calleRuta": row.get(ubi_key, "Unknown"),
                    "source": "CABA"
                }
                feature = {
                    "type": "Feature",
                    "geometry": { "type": "Point", "coordinates": [lon, lat] },
                    "properties": props
                }
                features.append(feature)
                
    return features

def process_nacion():
    features = []
    if not os.path.exists(NACION_FILE):
        print(f"File missing: {NACION_FILE}")
        return features
        
    try:
        with open(NACION_FILE, 'r', encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                lat = safe_float(row.get('lat', ''))
                lon = safe_float(row.get('lon', ''))
                
                if lat and lon:
                    props = {
                        "nroSerie": row.get('nro_de_serie', 'NACION'),
                        "calleRuta": row.get('lugar_de_instalacion', 'Unknown'),
                        "source": "NACION",
                        "marca": row.get('marca', ''),
                        "modelo": row.get('modelo', '')
                    }
                    feature = {
                        "type": "Feature",
                        "geometry": { "type": "Point", "coordinates": [lon, lat] },
                        "properties": props
                    }
                    features.append(feature)
    except Exception as e:
        print(f"Error reading Nacion file: {e}")
        
    return features

def main():
    existing = load_existing_features()
    caba = process_caba()
    nacion = process_nacion()
    
    print(f"Existing: {len(existing)}, CABA: {len(caba)}, Nacion: {len(nacion)}")
    
    # We do NOT append existing if it already contains the merged data from a previous run to avoid rapid duplication
    # A simple check: if existing count > 5000 and we are adding ~300, it might be safer to restart from base 
    # or detect if features look same.
    # For now, to simply fulfill "add these", we append. 
    # Ideally, we'd start with a 'clean' base if we knew which one it was. 
    # Assuming 'speed_cameras.geojson' WAS just the 'renabap' or similar set initially? 
    # No, speed_cameras.geojson was 198KB (line 4 of step 4). 
    # CABA is small? Nacion is small?
    # Let's just combine all.
    
    combined = existing + caba + nacion
    
    output = { "type": "FeatureCollection", "features": combined }
    
    with open(EXISTING_GEOJSON, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)
    print("Done.")

if __name__ == "__main__":
    main()
