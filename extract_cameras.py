import re
import json

def extract_cameras(html_file, output_file):
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Regex to capture the object inside receivedArr.push({...})
    # We look for receivedArr.push({ ... }) and capture the content inside the braces
    pattern = re.compile(r'receivedArr\.push\(\{(.*?)\}\)', re.DOTALL)
    matches = pattern.findall(content)

    features = []

    for match in matches:
        # Extract fields using regex for each property
        # nroSerie: "NEO_0183",
        nro_serie = re.search(r'nroSerie:\s*"([^"]*)"', match)
        calle_ruta = re.search(r'calleRuta:\s*"([^"]*)"', match)
        velocidad_permitida = re.search(r'velocidadPermitida:\s*"([^"]*)"', match)
        sentido = re.search(r'sentido:\s*"([^"]*)"', match)
        latitud = re.search(r'latitud:\s*"([^"]*)"', match)
        longitud = re.search(r'longitud:\s*"([^"]*)"', match)
        
        # Clean up data
        props = {}
        if nro_serie: props['nroSerie'] = nro_serie.group(1)
        if calle_ruta: props['calleRuta'] = calle_ruta.group(1)
        if velocidad_permitida: props['velocidadPermitida'] = velocidad_permitida.group(1)
        if sentido: props['sentido'] = sentido.group(1)
        
        lat = 0.0
        lon = 0.0
        
        if latitud and longitud:
            try:
                lat = float(latitud.group(1))
                lon = float(longitud.group(1))
            except ValueError:
                continue # Skip invalid coordinates

        if lat == 0.0 and lon == 0.0:
            continue

        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [lon, lat]
            },
            "properties": props
        }
        features.append(feature)

    geojson = {
        "type": "FeatureCollection",
        "features": features
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(geojson, f, indent=2)

    print(f"Extracted {len(features)} cameras to {output_file}")

if __name__ == "__main__":
    extract_cameras('MEDIDORESPBA.HTML', 'speed_cameras.geojson')
