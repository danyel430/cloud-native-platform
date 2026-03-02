import os
import pymongo


# dotenv.load_dotenv()
# strconectDB = os.getenv("strconectDB")
#en vez de hacer eso creo una función para que no se intente cinectar nada más carguen los imports, ya que en docker se van a alevantar ambos contenedores a la vez 
# y si el contenedor de la app intenta conectarse a la DB antes de que esta esté lista, va a dar error. Con esta función, solo se conecta cuando se llama a init_db() desde app.py, que es después de que se haya levantado la DB.

# función para inicializar la conexión a la DB, que se llama desde app.py
_client = None
_db = None
collection_crimes = None

def init_db():
    global _client, _db, collection_crimes
    if _client is None:
        uri = os.getenv("MONGO_URI") # la conexión con la clave que están en el dotenv, que en docker se pasan como variables de entorno a través del docker-compose
        if not uri:
            raise RuntimeError("MONGO_URI environment variable not set")
        _client = pymongo.MongoClient(uri)
        _db = _client.proyecto_final
        collection_crimes = _db["Crimes"]

# Diccionario de estados traducidos
status_description = {
    "IC": "Investigación en curso",
    "AA": "Arresto de adulto",
    "AO": "Adulto – otro estado",
    "JA": "Arresto de menor",
    "JO": "Menor – otro estado",
    "CC": "Caso cerrado",
    "TH": "Transferido / otro estado",
}
# diccionario de sexos traducidos
sex_description= {
    "M": "Masculino",
    "F": "Femenino",
    "X": "Otro / No especificado",
}

# eliminar espacios, nne, etc


def limpiar_valores(lista):
 
    valores_limpios = []
    for v in lista:
        if isinstance(v, str):
            v = v.strip()
            if v != "":
                valores_limpios.append(v)
        elif isinstance(v, (int, float)):
            valores_limpios.append(v)

    return valores_limpios


#obetener los valores distintos, limpios y ordenados


def get_crime_types():
    valores = collection_crimes.distinct("Crm Cd Desc")
    valores = limpiar_valores(valores)
    return sorted(valores)

def get_areas():
    valores = collection_crimes.distinct("AREA NAME")
    valores = limpiar_valores(valores)
    return sorted(valores)

def get_victim_sexes():
    valores = collection_crimes.distinct("Vict Sex")
    valores = limpiar_valores(valores)
    resultado = []
    for valor in valores:
        desc = sex_description.get(valor, "Descripción no disponible") 
        resultado.append({"codigo": valor, "descripcion": desc})
    resultado.sort(key=lambda x: x["descripcion"])

    return resultado
def hora_militar_a_html():
    time_list = collection_crimes.distinct("TIME OCC")
    resultado = set()        # pares (hh, mm)
    horas_solas = set()      # solo hh

    for time_occurred in time_list:
        try:
            hora = str(int(time_occurred)).zfill(4)
            hh = hora[:2]
            mm = hora[2:]

            resultado.add((hh, mm))
            horas_solas.add(hh)
        except:
            continue

    resultado = sorted(list(resultado))
    horas_solas = sorted(list(horas_solas))

    return resultado, horas_solas


def vict_age():
    valores = collection_crimes.distinct("Vict Age")
    valores = [v for v in valores if isinstance(v, int)]
    return sorted(valores)

def crime_place():
    valores = collection_crimes.distinct("Premis Desc")
    valores = limpiar_valores(valores)
    return sorted(valores)

def modus_oprendi():
    valores = collection_crimes.distinct("Mocodes")
    valores = limpiar_valores(valores)
    return sorted(valores)

def crime_status():
    # Devuelve [{codigo: 'IC', descripcion: 'Investigación en curso'}, ...]
    codigos = limpiar_valores(collection_crimes.distinct("Status"))
    resultado = []
    for code in codigos:
        desc = status_description.get(code, "Descripción no disponible")
        resultado.append({"codigo": code, "descripcion": desc})

    resultado.sort(key=lambda x: x["descripcion"])
    return resultado


#   Consultas generales


def buscar_crimenes(filtros: dict, limite: int = 200):
    # Búsqueda general con límite.
    return list(collection_crimes.find(filtros).limit(limite))


#   Agregaciones de estadísticas

#crímenes por área
def agg_crimenes_por_area():
    pipeline = [
        {"$group": {"_id": "$AREA NAME", "total": {"$sum": 1}}},
        {"$sort": {"total": -1}},
    ]
    return list(collection_crimes.aggregate(pipeline))
# top tipos de crímenes
def agg_top_tipos_crimen(limit=10):
    pipeline = [
        {"$group": {"_id": "$Crm Cd Desc", "total": {"$sum": 1}}},
        {"$sort": {"total": -1}},
        {"$limit": limit},
    ]
    return list(collection_crimes.aggregate(pipeline))
