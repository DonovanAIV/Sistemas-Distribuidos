import random
import time
from pymongo import MongoClient
import redis
from bson import ObjectId

hits = 0
miss = 0

# MongoDB
mongo_uri = "mongodb://admin:admin123@mongo:27017/"
client = MongoClient(mongo_uri)
db = client["info"]
coleccion = db["eventos"]

# Redis
cache = redis.Redis(host="redis", port=6379, decode_responses=True)
cache.flushdb()

# Caché
cache_size = 10
frecuencias = {}
cache_keys = set() # Eventos almacenados en caché

def obtener_ids():
    return [str(doc["_id"]) for doc in coleccion.find({}, {"_id": 1})]

def obtener_evento(_id):
    global hits
    evento = cache.get(_id)
    if evento:
        print(f"🔁 HIT en cache: {_id}")
        frecuencias[_id] = frecuencias.get(_id, 0) + 1
        hits += 1
        return evento

    doc = coleccion.find_one({"_id": ObjectId(_id)})
    if doc:
        print(f"🚫 MISS en cache → consultando MongoDB: {_id}")
        frecuencias[_id] = frecuencias.get(_id, 0) + 1
        if _id not in cache_keys:
            agregar_a_cache(_id, doc)
        return doc
    return None

def agregar_a_cache(key, value):
    global miss
    global cache_keys    
    if len(cache_keys) >= cache_size:
        delete = min(cache_keys, key=lambda k: frecuencias.get(k, 0))
        if frecuencias.get(key, 0) > frecuencias.get(delete, 0):
            cache.delete(delete)
            cache_keys.remove(delete)
            print(f"🧹 LFU: eliminado {delete} del cache (uso: {frecuencias[delete]})")
            miss += 1

            cache.set(key, str(value))
            cache_keys.add(key)
            print(f"📝 Guardado en cache: {key} (uso: {frecuencias[key]})")
    else:
        cache.set(key, str(value))
        cache_keys.add(key)
        print(f"📝 Guardado en cache: {key} (uso: {frecuencias[key]})")

ids = obtener_ids()
print(f"🟢 Iniciando consultas aleatorias sobre {len(ids)} documentos...\n")
for i in range(5000):
    index = int(random.gauss(mu=len(ids)//2, sigma=len(ids)//6))
    index = max(0, min(index, len(ids) - 1))
    id_random = ids[index]
    obtener_evento(id_random)
    time.sleep(0.2)

hit_rate = (hits / 5000) * 100
print()
print(f"Número de veces que se actualizo el caché: {miss}")
print(f"Hit rate: {hit_rate}%")