from flask import Flask, render_template, request, redirect, url_for, flash
import db
from bson import ObjectId


app = Flask(__name__)
#  Inicializo la DB antes de importar las funciones que la usan, para evitar errores de importación circular
db.init_db()

#importo las funciones que voy a usar
from db import (
    collection_crimes,
    get_crime_types,
    get_areas,
    get_victim_sexes,
    hora_militar_a_html,
    vict_age,
    crime_place,
    modus_oprendi,
    crime_status,
    buscar_crimenes,
    agg_crimenes_por_area,
    agg_top_tipos_crimen,
)



@app.route("/", methods=["GET", "POST"])
def home():
    # se ejecuta siempre que cargue la página
    filtros = {}
    resultados = []
    total_encontrados = 0
    hora_minutos, horas_solas = hora_militar_a_html()
    
    if request.method == "POST":
        # cuando pulsas buscar
        time_occ = request.form.get("time_occ")
        crime_type = request.form.get("crime_type")
        area = request.form.get("area")
        victim_age = request.form.get("victim_age")
        victim_gender = request.form.get("victim_gender")
        modus_operandi = request.form.get("modus_operandi")
        status = request.form.get("status")
        crime_place_f = request.form.get("crime_place")
        hour_only = request.form.get("hour_only")


     
    
        # Hora exacta
        if time_occ and time_occ != "All":
            filtros["TIME OCC"] = int(time_occ.replace(":", ""))

        # Sólo hora aproximada. Si relleno ambas, se ignora este filtro
        elif hour_only and hour_only != "All":
            try:
                hora_int = int(hour_only)
                filtros["TIME OCC"] = {
                    "$gte": hora_int * 100,
                    "$lte": hora_int * 100 + 59
                }
            except:
                pass
        
       

        if crime_type and crime_type != "All":
            filtros["Crm Cd Desc"] = crime_type

        if area and area != "All":
            filtros["AREA NAME"] = area

        if victim_age and victim_age != "All":
            try:
                filtros["Vict Age"] = int(victim_age)
            except ValueError:
                pass

        if victim_gender and victim_gender != "All":
            filtros["Vict Sex"] = victim_gender

        if modus_operandi and modus_operandi != "All":
            filtros["Mocodes"] = modus_operandi

   
        if status and status != "All":
            filtros["Status"] = status

        if crime_place_f and crime_place_f != "All":
            filtros["Premis Desc"] = crime_place_f

        resultados = buscar_crimenes(filtros, limite=200)
        total_encontrados = len(resultados)

        
    #cuando cargue la página se renderizan los filtros
    return render_template(
        "home.html",
        tipos_crimen=get_crime_types(),
        areas=get_areas(),
        victim_sexes=get_victim_sexes(),
        hora_minutos=hora_minutos,
        horas_solas=horas_solas,
        edades_victimas=vict_age(),
        lugares=crime_place(),
        modus_operandi=modus_oprendi(),
        estado_crimen=crime_status(),
        resultados=resultados,
        total_encontrados=total_encontrados,
    )



@app.route("/mapa")
def mapa():
    # Obtener los campos necesarios para el mapa
    cursor = collection_crimes.find(
        {
            "LAT": {"$ne": None},
            "LON": {"$ne": None}
        },
        {
            "LAT": 1,
            "LON": 1,
            "Crm Cd Desc": 1,
            "AREA NAME": 1,
            "Vict Age": 1,
            "Vict Sex": 1,
            "Premis Desc": 1,
            "DATE OCC": 1,
            "Status": 1
        }
    ).limit(1000)  # por rendimiento, 1000 puntos

    datos = []
    for d in cursor:
        d["_id"] = str(d["_id"])   # Convertir ObjectId a string
        datos.append(d)


    return render_template("mapa.html", datos=datos)


@app.route("/estadisticas")
def estadisticas():
    datos_area = agg_crimenes_por_area()
    top_tipos = agg_top_tipos_crimen()
    return render_template(
        "statistics.html",
        datos_area=datos_area,
        top_tipos=top_tipos,
    )


@app.route("/crimen/<id>/eliminar", methods=["POST"])
def eliminar_crimen(id):
    try:
        collection_crimes.delete_one({"_id": ObjectId(id)})
        flash("Crimen eliminado correctamente.", "success")
    except Exception as e:
        flash(f"Error al eliminar el crimen: {e}", "danger")
    return redirect(url_for("home"))


@app.route("/crimen/<id>/actualizar-estado", methods=["POST"])
def actualizar_estado_crimen(id):
    nuevo_estado = request.form.get("nuevo_estado")
    if not nuevo_estado:
        flash("No se ha proporcionado un nuevo estado.", "warning")
        return redirect(url_for("home"))

    try:
        collection_crimes.update_one(
            {"_id": ObjectId(id)},
            {"$set": {"Status": nuevo_estado}}, 
        )
        flash("Estado del crimen actualizado correctamente.", "success")
    except Exception as e:
        flash(f"Error al actualizar el estado: {e}", "danger")

    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000) # habilito acceso externo para que me conecte desde el navegador del host, no solo desde dentro del contenedor. 

