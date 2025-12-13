import struct

def read_dbf_header(filename):
    with open(filename, 'rb') as f:
        # Read file header
        # 0: version (1 byte)
        # 1-3: YYMMDD (3 bytes)
        # 4-7: Num records (4 bytes, little endian)
        # 8-9: Header length (2 bytes, little endian)
        # 10-11: Record length (2 bytes, little endian)
        data = f.read(32)
        if len(data) < 32:
            print("File too short")
            return

        num_records = struct.unpack('<I', data[4:8])[0]
        header_len = struct.unpack('<H', data[8:10])[0]
        record_len = struct.unpack('<H', data[10:12])[0]
        
        print(f"Records: {num_records}")
        print(f"Header Length: {header_len}")
        print(f"Record Length: {record_len}")
        
        # Read field descriptors
        # Each is 32 bytes
        # Terminated by 0x0D
        
        fields = []
        while f.tell() < header_len - 1:
            field_data = f.read(32)
            if len(field_data) < 32: break
            if field_data[0] == 0x0D: break # Terminator
            
            name = field_data[0:11].replace(b'\x00', b'').decode('latin-1').strip()
            field_type = chr(field_data[11])
            field_len = field_data[16]
            
            fields.append({'name': name, 'type': field_type, 'len': field_len})
            
        print("\nFields found:")
        for fd in fields:
            print(f"- {fd['name']} ({fd['type']}) len={fd['len']}")
            
        print("\nChecking for WGS84 fields...")
        has_lat = any(f['name'] == 'LAT_WGS84' for f in fields)
        has_lon = any(f['name'] == 'LONG_WGS84' for f in fields)
        print(f"LAT_WGS84 present: {has_lat}")
        print(f"LONG_WGS84 present: {has_lon}")
        
        # Read records
        f.seek(header_len)
        print("\n--- First 5 Records ---")
        
        for i in range(min(5, num_records)):
            # Read deletion flag
            flag = f.read(1)
            
            record_data = {}
            for fd in fields:
                raw = f.read(fd['len'])
                val = raw.decode('utf-8', errors='replace').strip()
                # Handle nulls
                val = val.replace('\x00', '')
                record_data[fd['name']] = val
                
            print(f"\nRecord {i}:")
            print(f"  Name: {record_data.get('Name')}")
            print(f"  Latitud: {record_data.get('Latitud')}")
            print(f"  Longitud: {record_data.get('Longitud')}")
            print(f"  Conducta: {record_data.get('Conducta_f')}")
            print(f"  Description: {record_data.get('descriptio')}")
            print(f"  Tipo: {record_data.get('Tipo_de_fi')}")

if __name__ == "__main__":
    read_dbf_header('caba/camaras-fijas-de-control-vehicular.dbf')
