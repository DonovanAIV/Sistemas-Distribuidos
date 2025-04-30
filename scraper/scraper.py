import requests
from pymongo import MongoClient

def coordenadas(top, bottom, left, right):
    url = f"https://www.waze.com/live-map/api/georss?top={top}&bottom={bottom}&left={left}&right={right}&env=row&types=alerts"
    return url

# Plaza de Armas (Punto central de Santiago)
start_lat = -33.437824585848496
start_lon = -70.65050275448678

# Tamaño de los bloques (2km aprox)
step_lat = 2 / 111.32   # ≈ 0.01796 grados
step_lon = 2 / 93.5     # ≈ 0.02139 grados
radio = 25
blocks = []

for i in range(-radio, radio+1):
    for j in range(-radio, radio+1):
        bottom = start_lat + i * step_lat
        top = bottom + step_lat
        left = start_lon + j * step_lon
        right = left + step_lon

        blocks.append({
            'top': top,
            'bottom': bottom,
            'left': left,
            'right': right,
        })

# Conexión mongdb
uri = "mongodb://admin:admin123@localhost:27017/"
client = MongoClient(uri)
db = client["info"]
coleccion = db["eventos"]

for i, block in enumerate(blocks):
    print()
    print(f"Bloque {i+1}/{len(blocks)}")
    url = coordenadas(block['top'], block['bottom'], block['left'], block['right'])

    for intento in range(3):
        try:
            response = requests.get(url)
            data = response.json()

            if 'alerts' in data and data['alerts']:
                coleccion.insert_many(data['alerts'])
                print(f"✔️  {len(data['alerts'])} alertas insertadas.")
            else:
                print("❌ No hay alertas en este bloque.")

            break

        except Exception as e:
            print(f"⚠️ Error en el bloque {i+1} (intento {intento + 1}/3): {e}")