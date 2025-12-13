import requests
import xml.etree.ElementTree as ET
import pandas as pd
import json
from typing import List, Dict, Tuple

def extract_wfs_data(typename: str) -> pd.DataFrame:
    """
    Extrae datos de un servicio WFS y los convierte a DataFrame
    
    Args:
        typename: Nombre de la capa WFS (res1104_mmino_eess o res1104_mmino_dist)
    
    Returns:
        DataFrame con los datos procesados
    """
    # Construir URL
    url = f"https://sig.energia.gob.ar/wmspubmap?VERSION=1.0.0&SERVICE=WFS&REQUEST=GetFeature&TYPENAME={typename}"
    
    # Realizar petición
    response = requests.get(url)
    response.encoding = 'utf-8'
    
    # Parsear XML
    root = ET.fromstring(response.content)
    
    # Definir namespaces
    namespaces = {
        'gml': 'http://www.opengis.net/gml',
        'ms': 'http://mapserver.gis.umn.edu/mapserver',
        'wfs': 'http://www.opengis.net/wfs'
    }
    
    # Extraer features
    features = root.findall(f'.//{{{namespaces["ms"]}}}{typename}', namespaces)
    
    data = []
    
    def _find_coord_element(f):
        # Buscar distintos nodos de GML que puedan contener coordenadas
        for tag in ("{http://www.opengis.net/gml}coordinates", "{http://www.opengis.net/gml}pos", "{http://www.opengis.net/gml}posList"):
            el = f.find('.//' + tag)
            if el is not None and (el.text and el.text.strip()):
                return el
        return None

    def _parse_coords_text(text: str) -> Tuple[float, float]:
        txt = text.strip()
        # Algunos GML usan coma, otros espacio. Normalizar a separador por espacios
        if ',' in txt and ' ' not in txt:
            parts = [p.strip() for p in txt.split(',') if p.strip()]
        else:
            # reemplazar comas por espacios y dividir por cualquier whitespace
            parts = [p for p in txt.replace(',', ' ').split() if p]
        if len(parts) >= 2:
            try:
                lon = float(parts[0])
                lat = float(parts[1])
                return lon, lat
            except Exception:
                try:
                    lon = float(parts[-2]); lat = float(parts[-1])
                    return lon, lat
                except Exception:
                    return None, None
        return None, None

    for feature in features:
        # Extraer coordenadas (robusto: coordinates, pos, posList)
        coord_elem = _find_coord_element(feature)
        if coord_elem is not None and coord_elem.text:
            longitude, latitude = _parse_coords_text(coord_elem.text)
        else:
            longitude = None
            latitude = None
        
        # Extraer otros campos
        record = {
            'tipooperador': feature.find(f'.//{{{namespaces["ms"]}}}tipooperador', namespaces),
            'empresabandera': feature.find(f'.//{{{namespaces["ms"]}}}empresabandera', namespaces),
            'razonsocial': feature.find(f'.//{{{namespaces["ms"]}}}razonsocial', namespaces),
            'cuit': feature.find(f'.//{{{namespaces["ms"]}}}cuit', namespaces),
            'direccion': feature.find(f'.//{{{namespaces["ms"]}}}direccion', namespaces),
            'localidad': feature.find(f'.//{{{namespaces["ms"]}}}localidad', namespaces),
            'provincia': feature.find(f'.//{{{namespaces["ms"]}}}provincia', namespaces),
            'Longitude': longitude,
            'Latitude': latitude
        }
        
        # Convertir elementos XML a texto
        for key, elem in record.items():
            if key not in ['Longitude', 'Latitude'] and elem is not None:
                record[key] = elem.text
        
        data.append(record)
    
    # Crear DataFrame
    df = pd.DataFrame(data)
    
    return df


def main():
    """
    Función principal que combina los datos de ambas capas WFS
    """
    print("Extrayendo datos de res1104_mmino_eess...")
    df_eess = extract_wfs_data('res1104_mmino_eess')
    print(f"✓ {len(df_eess)} registros extraídos")
    
    print("\nExtrayendo datos de res1104_mmino_dist...")
    df_dist = extract_wfs_data('res1104_mmino_dist')
    print(f"✓ {len(df_dist)} registros extraídos")
    
    # Combinar ambos DataFrames
    print("\nCombinando datos...")
    df_combined = pd.concat([df_eess, df_dist], ignore_index=True)
    
    # Conservar todos los atributos devueltos por el WFS
    # Si querés eliminar columnas específicas, descomenta y ajusta la siguiente
    # línea:
    # columns_to_remove = ['cuit', 'localidad', 'provincia', 'empresabandera']
    # df_combined = df_combined.drop(columns=columns_to_remove, errors='ignore')
    
    # Convertir coordenadas a numérico
    df_combined['Latitude'] = pd.to_numeric(df_combined['Latitude'], errors='coerce')
    df_combined['Longitude'] = pd.to_numeric(df_combined['Longitude'], errors='coerce')
    
    print(f"\n✓ Total de registros combinados: {len(df_combined)}")
    print(f"\nColumnas finales: {list(df_combined.columns)}")
    print(f"\nPrimeras filas:")
    print(df_combined.head())
    
    # Guardar resultados
    output_file = 'estaciones_servicio_argentina.csv'
    df_combined.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\n✓ Datos guardados en: {output_file}")
    
    # Opcional: Guardar en Excel
    output_excel = 'estaciones_servicio_argentina.xlsx'
    df_combined.to_excel(output_excel, index=False, engine='openpyxl')
    print(f"✓ Datos guardados en: {output_excel}")

    # Guardar como GeoJSON (sólo registros con coordenadas válidas)
    geojson_file = 'estaciones_servicio_argentina.geojson'
    features = []
    for _, row in df_combined.dropna(subset=['Longitude', 'Latitude']).iterrows():
        properties = row.drop(labels=['Longitude', 'Latitude']).to_dict()
        # Convertir NaN por None para JSON
        for k, v in list(properties.items()):
            if pd.isna(v):
                properties[k] = None
        feat = {
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [float(row['Longitude']), float(row['Latitude'])]
            },
            'properties': properties
        }
        features.append(feat)
    fc = {'type': 'FeatureCollection', 'features': features}
    with open(geojson_file, 'w', encoding='utf-8') as f:
        json.dump(fc, f, ensure_ascii=False, indent=2)
    print(f"✓ GeoJSON guardado en: {geojson_file}")

    # Guardar JSON (array de objetos con lat/lon y propiedades)
    json_file = 'estaciones_servicio_argentina.json'
    rows = []
    for _, row in df_combined.iterrows():
        obj = row.to_dict()
        # asegurar tipos serializables
        for k, v in list(obj.items()):
            if pd.isna(v):
                obj[k] = None
            elif isinstance(v, (pd.Timestamp,)):
                obj[k] = str(v)
        rows.append(obj)
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    print(f"✓ JSON guardado en: {json_file}")
    
    return df_combined


if __name__ == "__main__":
    df_result = main()
