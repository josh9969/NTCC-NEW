import streamlit as st
import folium
from streamlit_folium import st_folium
import openrouteservice
from openrouteservice import convert
import os
import math

st.set_page_config(page_title="Isochrone & Drive Time Calculator", layout="centered")
st.markdown("""
    <style>
    .main {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }
    .stSlider > div {
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🗺️ Isochrone & Drive Time Calculator")
st.write("This app calculates isochrones and estimates travel time, distance, and fuel cost.")

# User input fields
api_key = st.text_input("Enter your OpenRouteService API Key", type="password")
location = st.text_input("Enter location coordinates (latitude,longitude)", value="25.276987,55.296249")
drive_time_minutes = st.slider("Select Drive Time (minutes)", 1, 60, 5)
fuel_efficiency = st.number_input("Fuel Efficiency (km per liter)", min_value=1.0, value=12.0)
fuel_price = st.number_input("Fuel Price (AED per liter)", min_value=0.0, value=2.95)

if st.button("Calculate Isochrone"):
    try:
        client = openrouteservice.Client(key=api_key)
        coords = tuple(map(float, location.split(",")))

        # Generate Isochrone
        isochrone = client.isochrones(
            locations=[coords],
            profile='driving-car',
            range=[drive_time_minutes * 60],
            attributes=['total_pop']
        )

        # Generate map
        m = folium.Map(location=coords, zoom_start=13)
        folium.Marker(coords, tooltip="Start Point").add_to(m)
        folium.GeoJson(isochrone, name="Isochrone").add_to(m)

        st.subheader("Isochrone Map")
        st_data = st_folium(m, width=700, height=500)

        # Estimate drive distance
        route = client.directions(coordinates=[coords, coords], profile='driving-car')
        dist_m = route['routes'][0]['summary']['distance']
        drive_time = drive_time_minutes
        dist_km = (drive_time_minutes / 60) * 40  # rough estimation with avg 40 km/h
        fuel_cost = (dist_km / fuel_efficiency) * fuel_price

        # Stylish results
        st.markdown("""
        <div style='display: flex; justify-content: center; gap: 20px; margin-top: 20px; flex-wrap: wrap;'>

            <div style='background-color: #e6f7ec; padding: 20px 30px; border-radius: 10px; min-width: 250px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.1);'>
                <div style='font-size: 20px;'>🕒</div>
                <div style='font-weight: bold;'>Drive Time</div>
                <div style='font-size: 18px; color: #17633d;'>{:.2f} minutes</div>
            </div>

            <div style='background-color: #e6f7ec; padding: 20px 30px; border-radius: 10px; min-width: 250px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.1);'>
                <div style='font-size: 20px;'>📍</div>
                <div style='font-weight: bold;'>Distance</div>
                <div style='font-size: 18px; color: #17633d;'>{:.2f} km</div>
            </div>

            <div style='background-color: #e6f7ec; padding: 20px 30px; border-radius: 10px; min-width: 250px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.1);'>
                <div style='font-size: 20px;'>⛽</div>
                <div style='font-weight: bold;'>Fuel Cost</div>
                <div style='font-size: 18px; color: #17633d;'>{:.2f} AED</div>
            </div>

        </div>
        """.format(drive_time, dist_km, fuel_cost), unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Error: {e}")

