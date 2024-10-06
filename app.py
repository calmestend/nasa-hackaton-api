from flask import Flask, render_template
import requests
import folium
from folium import TileLayer

# Definir los endpoints de la API STAC y RASTER
STAC_API_URL = "https://earth.gov/ghgcenter/api/stac"
RASTER_API_URL = "https://earth.gov/ghgcenter/api/raster"

# Nombre de la colección
collection_name = "oco2-mip-co2budget-yeargrid-v1"

# Crear la aplicación Flask
app = Flask(__name__)

# Función para contar los elementos de la colección
def get_item_count(collection_id):
    count = 0
    items_url = f"{STAC_API_URL}/collections/{collection_id}/items"
    while True:
        response = requests.get(items_url)
        if not response.ok:
            print("Error obteniendo elementos")
            break
        stac = response.json()
        count += int(stac["context"].get("returned", 0))
        next = [link for link in stac["links"] if link["rel"] == "next"]
        if not next:
            break
        items_url = next[0]["href"]
    return count

# Ruta principal de la aplicación
@app.route('/')
def index():
    # Obtener el número de items de la colección
    number_of_items = get_item_count(collection_name)

    # Obtener todos los items de la colección
    items = requests.get(f"{STAC_API_URL}/collections/{collection_name}/items?limit={number_of_items}").json()["features"]

    # Obtener el primer item (2020)
    asset_name = "ff"
    co2_flux_1 = requests.get(
        f"{RASTER_API_URL}/collections/{items[0]['collection']}/items/{items[0]['id']}/tilejson.json?"
        f"&assets={asset_name}"
        f"&color_formula=gamma+r+1.05&colormap_name=purd"
        f"&rescale=0,450"
    ).json()

    # Crear el mapa con Folium
    map_ = folium.Map(location=(34, -118), zoom_start=6)

    # Agregar la capa de CO₂ de 2020
    map_layer_2020 = TileLayer(
        tiles=co2_flux_1["tiles"][0],
        attr="GHG",
        opacity=0.5
    )
    map_layer_2020.add_to(map_)

    # Guardar el mapa en la carpeta 'static'
    map_.save('static/co2_map.html')

    # Renderizar la plantilla HTML
    return render_template('index.html')

# Ejecutar la aplicación
if __name__ == '__main__':
    app.run(debug=True)
