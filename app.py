from flask import Flask, render_template
import requests
import folium
from folium import TileLayer
from folium.plugins import MarkerCluster
import pandas as pd

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

    # Crear un nuevo mapa centrado en Querétaro, México
    queretaro_map = folium.Map(
        tiles="OpenStreetMap",
        location=[20.5888, -100.3899],  # Coordenadas de Querétaro, México
        zoom_start=10,  # Un valor de zoom más detallado para Querétaro
    )

    # Definir las coordenadas del polígono para rodear mejor la región de Querétaro
    polygon_coordinates = [
        [20.7951, -100.6842],
        [20.7639, -100.4329],
        [20.5369, -100.3039],
        [20.5262, -100.1807],
        [20.4116, -100.0932],
        [20.2037, -100.1453],
        [20.2194, -100.4797],
        [20.3367, -100.6140],
        [20.5550, -100.7291],
        [20.7117, -100.6834],
        [20.7951, -100.6842]  # Cierre del polígono (mismo que el primer punto)
    ]

    # Agregar el polígono al mapa
    folium.Polygon(locations=polygon_coordinates, color='red', fill=True, fill_color='red').add_to(queretaro_map)

    # Guardar el mapa de Querétaro en la carpeta 'static'
    queretaro_map.save('static/queretaro_map.html')

    # Crear un mapa centrado en México con los datos de CO2 por entidad
    df = pd.DataFrame({
        'Entidad': [
            'Aguascalientes', 'Baja California', 'Baja California Sur', 'Campeche',
            'Chiapas', 'Chihuahua', 'Coahuila de Zaragoza', 'Colima',
            'Distrito Federal', 'Durango', 'Guanajuato', 'Guerrero',
            'Hidalgo', 'Jalisco', 'México', 'Michoacán de Ocampo',
            'Morelos', 'Nayarit', 'Nuevo León', 'Oaxaca',
            'Puebla', 'Querétaro', 'Quintana Roo', 'San Luis Potosí',
            'Sinaloa', 'Sonora', 'Tabasco', 'Tamaulipas',
            'Tlaxcala', 'Veracruz', 'Yucatán', 'Zacatecas'
        ],
        'Toneladas CO2': [
            10835185.68, 66171711.16, 4583550.53, 11447025.53,
            23274510.79, 1488489.30, 21882731.37, 4112492.37,
            7041372.89, 444678.64, 21384778.21, 57287511.75,
            41785463.78, 6708170.61, 21687866.24, 681589.05,
            52294519.09, 5155958.28, 9482601.42, 59600602.43,
            131483.69, 16253401.32, 521325.83, 10576659.90,
            42089899.75, 67919608.54, 419748.72, 63610874.87,
            6284024.09, 1916509.18, 8286322.97, 1905775.41
        ],
        'Latitud': [
            21.88234, 32.6519, 24.14437, 19.8301, 16.75, 28.835, 27.0587, 19.1223,
            19.4326, 24.5593, 21.019, 17.4392, 20.0971, 20.6596, 19.325, 19.5665,
            18.9186, 21.7514, 25.6866, 17.0747, 19.0413, 20.5888, 19.1817, 22.1566,
            24.8081, 29.072967, 18.0111, 23.7417, 19.3181, 19.1738, 20.9671, 22.7709
        ],
        'Longitud': [
            -102.2916, -115.4683, -110.3005, -90.5349, -93.1167, -105.9903, -101.7068, -104.0072,
            -99.1332, -104.6576, -101.2331, -99.5451, -98.7624, -103.3496, -99.8442, -101.7068,
            -99.234, -105.2286, -100.3161, -96.7135, -98.2063, -100.3899, -88.3027, -100.9855,
            -107.3963, -110.9559, -92.9303, -98.0922, -98.239, -96.1429, -89.6252, -102.5832
        ]
    })

    co2_map = folium.Map(location=[23.6345, -102.5528], zoom_start=5)

    # Crear un cluster para agrupar los marcadores
    marker_cluster = MarkerCluster().add_to(co2_map)

    # Añadir los datos de CO2 al mapa como marcadores
    for i, row in df.iterrows():
        folium.CircleMarker(
            location=[row['Latitud'], row['Longitud']],
            radius=row['Toneladas CO2'] / 1e7,  # Escalar el radio del círculo según las toneladas de CO2
            popup=f"{row['Entidad']}: {row['Toneladas CO2']} toneladas de CO2",
            color='blue',
            fill=True,
            fill_color='blue'
        ).add_to(marker_cluster)

    # Guardar el mapa de CO2 por entidad en la carpeta 'static'



    co2_map.save('static/co2_entidades_map.html')

    cdmx_map = folium.Map(
        tiles="OpenStreetMap",
        location=[19.4326, -99.1332],  # Coordenadas de la Ciudad de México
        zoom_start=11  # Un valor de zoom detallado para la Ciudad de México
    )

    # Definir las coordenadas del polígono para rodear la Ciudad de México
    polygon_cdmx_coordinates = [
        [19.5928, -99.2951],
        [19.5312, -99.0271],
        [19.3573, -98.9863],
        [19.2707, -99.1378],
        [19.2781, -99.3176],
        [19.4256, -99.3636],
        [19.5928, -99.2951]  # Cierre del polígono (mismo que el primer punto)
    ]

    # Agregar el polígono al mapa de la Ciudad de México
    folium.Polygon(locations=polygon_cdmx_coordinates, color='blue', fill=True, fill_color='blue').add_to(cdmx_map)

    # Guardar el mapa de la Ciudad de México en la carpeta 'static'
    cdmx_map.save('static/cdmx_map.html')


    return render_template('index.html')
# Ejecutar la aplicación
if __name__ == '__main__':
    app.run(debug=True)
