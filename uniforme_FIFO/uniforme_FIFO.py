import random
import time
from pymongo import MongoClient
import redis
from collections import deque
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
cache_fifo = deque()
frecuencias = {}

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
        if frecuencias[_id] >= 3:
            agregar_a_cache(_id, doc)
        return doc
    return None

def agregar_a_cache(key, value):
    global miss
    if key in cache_fifo:
        return
    if len(cache_fifo) >= cache_size:
        delete = cache_fifo.popleft()
        cache.delete(delete)
        print(f"🧹 FIFO: eliminado {delete} del cache")
        miss += 1

    cache.set(key, str(value))
    cache_fifo.append(key)
    print(f"📝 Guardado en cache: {key}")

ids = obtener_ids()
print(f"🟢 Iniciando consultas gaussianas sobre {len(ids)} documentos...\n")
for i in range(5000):
    id_random = random.choice(ids)
    obtener_evento(id_random)
    time.sleep(0.2)

hit_rate = (hits / 5000) * 100
print()
print(f"Número de veces que se actualizo el caché: {miss}")
print(f"Hit rate: {hit_rate}%")