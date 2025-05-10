# --- Upgraded Drive Time + Isochrone App (Enhanced UI/UX) ---

import streamlit as st
import openrouteservice
from openrouteservice import convert
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, LineString, Polygon
import folium
from folium.plugins import MarkerCluster
from io import BytesIO
import base64
from streamlit_folium import folium_static

# --- Constants ---
ORS_API_KEY = '5b3ce3597851110001cf62483c9fa348736d4315a694410fd874e918'  # Replace with your real API Key
client = openrouteservice.Client(key=ORS_API_KEY)

# --- Page Config ---
st.set_page_config(page_title="Drive Time & Isochrone App", page_icon="🚗", layout="wide")

# --- Custom Styles ---
st.markdown("""
    <style>
        .main {background-color: #f8f9fa;}
        h1 {color: #2C3E50;}
        .stButton button {
            background-color: #3498DB;
            color: white;
            font-weight: bold;
            border-radius: 0.5rem;
        }
        .stSelectbox, .stTextInput, .stNumberInput {
            background-color: #F0F3F4;
        }
        .css-1cpxqw2 {padding-top: 2rem;}
    </style>
""", unsafe_allow_html=True)

# --- Helper Functions ---
def geocode_address(address):
    try:
        res = client.pelias_search(text=address)
        coords = res['features'][0]['geometry']['coordinates']
        return coords[1], coords[0]
    except:
        return None, None

def get_route(origin, destination, profile):
    try:
        route = client.directions(
            coordinates=[origin, destination],
            profile=profile,
            format='geojson'
        )
        duration = route['features'][0]['properties']['segments'][0]['duration']
        distance = route['features'][0]['properties']['segments'][0]['distance']
        geometry = route['features'][0]['geometry']
        return duration, distance, geometry
    except Exception as e:
        st.error(f"Routing error: {e}")
        return None, None, None

def get_isochrone(location, profile, minutes):
    try:
        params = {
            'locations': [location],
            'profile': profile,
            'range': [minutes * 60],
        }
        isochrones = client.isochrones(**params)
        return isochrones
    except Exception as e:
        st.error(f"Isochrone error: {e}")
        return None

def save_map(m, filename='map.html'):
    m.save(filename)
    with open(filename, "rb") as f:
        html_data = f.read()
    return html_data

# --- Core Processing Function ---
def process_drive_time_or_isochrone(origin, destination, mode, profile, fuel_price, mileage):
    m = folium.Map(location=[origin[1], origin[0]], zoom_start=12)
    mc = MarkerCluster().add_to(m)

    if mode == "Drive Time Calculator":
        duration, distance, geometry = get_route(origin, destination, profile)
        if duration:
            drive_time = duration / 60
            dist_km = distance / 1000
            fuel_cost = (dist_km / mileage) * fuel_price

            st.metric(label="Drive Time (min)", value=f"{drive_time:.1f}")
            st.metric(label="Distance (km)", value=f"{dist_km:.2f}")
            st.metric(label="Estimated Fuel Cost (AED)", value=f"{fuel_cost:.2f}")

            line = LineString(geometry['coordinates'])
            folium.GeoJson(line, tooltip="Route").add_to(m)
            folium.Marker(location=[origin[1], origin[0]], popup="Origin", icon=folium.Icon(color='green')).add_to(mc)
            folium.Marker(location=[destination[1], destination[0]], popup="Destination", icon=folium.Icon(color='red')).add_to(mc)

    elif mode == "Isochrone Generator":
        minutes = st.slider("Select minutes for Isochrone", min_value=5, max_value=60, step=5, value=15)
        isochrones = get_isochrone(origin, profile, minutes)
        if isochrones:
            polygon = isochrones['features'][0]['geometry']
            folium.GeoJson(polygon, tooltip=f"{minutes} min isochrone", style_function=lambda x: {
                'fillColor': '#1abc9c',
                'color': '#16a085',
                'fillOpacity': 0.4,
                'weight': 2,
            }).add_to(m)
            folium.Marker(location=[origin[1], origin[0]], popup="Center", icon=folium.Icon(color='blue')).add_to(mc)

    folium_static(m)

    html_data = save_map(m)
    b64 = base64.b64encode(html_data).decode()
    href = f'<a href="data:text/html;base64,{b64}" download="map.html">📥 Download Map HTML</a>'
    st.markdown(href, unsafe_allow_html=True)

# --- Main App ---
def main():
    st.title("🚗 Drive Time & Isochrone Calculator")
    st.subheader("Professional Project with Fuel Cost, Excel Input & Enhanced UI")

    mode = st.radio("Select Mode", ("Drive Time Calculator", "Isochrone Generator"))
    input_method = st.selectbox("Choose Input Method", ("Manual Address", "Manual Coordinates", "Upload Excel File"))
    transport_mode = st.selectbox("Select Transport Mode", ("driving-car", "cycling-regular", "foot-walking"))
    fuel_price = st.number_input("Fuel Price (per liter)", min_value=0.0, value=3.5)
    mileage = st.number_input("Car Mileage (km per liter)", min_value=1.0, value=12.0)

    if input_method == "Manual Address":
        origin_address = st.text_input("Origin Address", "Dubai Mall, Dubai")
        destination_address = st.text_input("Destination Address", "Burj Khalifa, Dubai")
        if st.button("🚀 Calculate"):
            origin_lat, origin_lon = geocode_address(origin_address)
            dest_lat, dest_lon = geocode_address(destination_address)
            if origin_lat is None or dest_lat is None:
                st.error("Address geocoding failed.")
                return
            process_drive_time_or_isochrone((origin_lon, origin_lat), (dest_lon, dest_lat), mode, transport_mode, fuel_price, mileage)

    elif input_method == "Manual Coordinates":
        origin_lat = st.number_input("Origin Latitude", value=25.1972)
        origin_lon = st.number_input("Origin Longitude", value=55.2744)
        dest_lat = st.number_input("Destination Latitude", value=25.1975)
        dest_lon = st.number_input("Destination Longitude", value=55.2757)
        if st.button("🚀 Calculate"):
            process_drive_time_or_isochrone((origin_lon, origin_lat), (dest_lon, dest_lat), mode, transport_mode, fuel_price, mileage)

    elif input_method == "Upload Excel File":
        uploaded_file = st.file_uploader("Upload Excel", type=["xlsx"])
        if uploaded_file:
            df = pd.read_excel(uploaded_file)
            st.write(df)
            if st.button("🚀 Calculate for File"):
                for idx, row in df.iterrows():
                    if 'Origin' in row and 'Destination' in row:
                        origin_lat, origin_lon = geocode_address(row['Origin'])
                        dest_lat, dest_lon = geocode_address(row['Destination'])
                    else:
                        origin_lat, origin_lon = row['Origin_Lat'], row['Origin_Lon']
                        dest_lat, dest_lon = row['Destination_Lat'], row['Destination_Lon']
                    process_drive_time_or_isochrone((origin_lon, origin_lat), (dest_lon, dest_lat), mode, transport_mode, fuel_price, mileage)

if __name__ == "__main__":
    main()

