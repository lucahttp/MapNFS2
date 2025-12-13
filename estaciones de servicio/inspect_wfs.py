import requests
import xml.etree.ElementTree as ET

NAMESPACES = {
    'gml': 'http://www.opengis.net/gml',
    'ms': 'http://mapserver.gis.umn.edu/mapserver',
    'wfs': 'http://www.opengis.net/wfs'
}

LAYERS = [
    'res1104_mmino_eess',
    'res1104_mmino_dist'
]

BASE_URL = 'https://sig.energia.gob.ar/wmspubmap?VERSION=1.0.0&SERVICE=WFS&REQUEST=GetFeature&TYPENAME='

for layer in LAYERS:
    url = BASE_URL + layer
    print('\n--- LAYER:', layer, '---')
    r = requests.get(url, timeout=30)
    r.encoding = 'utf-8'
    root = ET.fromstring(r.content)

    # Encontrar el primer elemento que corresponde al feature
    # Los features suelen tener el prefijo ms: o directamente el nombre
    found = root.findall('.//')
    # Buscaremos el primer elemento cuyo tag contenga el nombre de la capa
    feature_elem = None
    for el in root.iter():
        tag = el.tag
        if isinstance(tag, str) and layer in tag:
            feature_elem = el
            break
    if feature_elem is None:
        # fallback: buscar ms:FeatureTypeMember o similar
        for el in root.iter():
            if 'featureMember' in el.tag or 'member' in el.tag:
                # el primer child suele ser el feature
                if len(list(el))>0:
                    feature_elem = list(el)[0]
                    break
    if feature_elem is None:
        print('No se encontró un elemento feature para la capa', layer)
        continue

    # Listar nombres de atributos (nodos hijos) y mostrar algunos valores de ejemplo
    attrs = {}
    for child in feature_elem:
        # usar solo el localname (sin namespace)
        tag = child.tag
        if '}' in tag:
            local = tag.split('}', 1)[1]
        else:
            local = tag
        # recoger texto o, si tiene hijos, el tag de los hijos
        if len(list(child)) == 0:
            attrs[local] = child.text
        else:
            # mostrar nombres de subnodos
            subs = [c.tag.split('}',1)[1] if '}' in c.tag else c.tag for c in child]
            attrs[local] = f"[COMPLEX: subnodes={subs}]"

    print('Atributos encontrados (nombre : ejemplo/estructura):')
    for k, v in attrs.items():
        print('-', k, ':', v)

    print('\nTotal atributos_detectados:', len(attrs))

print('\n-- Fin análisis --')
