import struct
import json
import re
import os
import csv

DBF_FILE = 'caba/camaras-fijas-de-control-vehicular.dbf'
CSV_OUTPUT = 'caba_full_data.csv'
GEOJSON_FILE = 'speed_cameras.geojson'

def read_dbf_records(filename):
    records = []
    field_names = []
    try:
        with open(filename, 'rb') as f:
            # Header
            data = f.read(32)
            num_records = struct.unpack('<I', data[4:8])[0]
            header_len = struct.unpack('<H', data[8:10])[0]
            
            # Fields
            fields = []
            f.seek(32)
            while f.tell() < header_len - 1:
                field_data = f.read(32)
                if field_data[0] == 0x0D: break
                name = field_data[0:11].replace(b'\x00', b'').decode('latin-1').strip()
                length = field_data[16]
                fields.append({'name': name, 'len': length})
            
            field_names = [fd['name'] for fd in fields]
            f.seek(header_len)
            
            for _ in range(num_records):
                flag = f.read(1)
                record = {}
                for fd in fields:
                    if flag == b'*': # Deleted
                        f.read(fd['len'])
                        continue
                        
                    raw = f.read(fd['len'])
                    try:
                        val = raw.decode('utf-8').strip()
                    except:
                        val = raw.decode('latin-1').strip()
                    val = val.replace('\x00', '')
                    record[fd['name']] = val
                
                if flag != b'*':
                    records.append(record)
                    
    except Exception as e:
        print(f"Error reading DBF: {e}")
        
    return records, field_names

def parse_speed(text):
    # Look for "Velocidad permitida: 60 km/h"
    match = re.search(r'Velocidad permitida:\s*(\d+)', text, re.IGNORECASE)
    if match:
        return match.group(1)
    return ""

def main():
    print("Reading CABA DBF...")
    records, columns = read_dbf_records(DBF_FILE)
    print(f"Found {len(records)} records with {len(columns)} columns.")
    
    # Export to CSV
    print(f"Exporting to {CSV_OUTPUT}...")
    try:
        with open(CSV_OUTPUT, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            writer.writerows(records)
        print("CSV export successful.")
    except Exception as e:
        print(f"Error writing CSV: {e}")
    
    # Continue with GeoJSON update
    new_features = []
    for i, r in enumerate(records):
        try:
            lat = float(r.get('Latitud', 0))
            lon = float(r.get('Longitud', 0))
            if lat == 0 or lon == 0: continue
            
            desc = r.get('descriptio', '')
            speed = parse_speed(desc)
            
            props = {
                "nroSerie": f"CABA_SHP_{i+1}",
                "calleRuta": r.get('Name', 'Unknown'),
                "velocidadPermitida": speed,
                "sentido": "", 
                "source": "CABA_SHP",
                "tipo": r.get('Tipo_de_fi', ''),
                "conducta": r.get('Conducta_f', '')
            }
            
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [lon, lat]
                },
                "properties": props
            }
            new_features.append(feature)
        except ValueError:
            continue
            
    print(f"Parsed {len(new_features)} valid features for GeoJSON.")
    
    # Update GeoJSON
    if os.path.exists(GEOJSON_FILE):
        with open(GEOJSON_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        current_features = data.get('features', [])
        
        # Remove old CABA (csv based)
        filtered = [f for f in current_features if f['properties'].get('source') != 'CABA']
        
        # Add new
        final_features = filtered + new_features
        data['features'] = final_features
        
        with open(GEOJSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
            
        print(f"Updated {GEOJSON_FILE} with {len(final_features)} features.")
    else:
        print("GeoJSON file not found to update.")

if __name__ == "__main__":
    main()
