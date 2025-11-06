import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import folium
import time

# 1. Charger le fichier CSV
df = pd.read_csv("map.csv")

# 2. Initialiser le géocodeur avec un User-Agent personnalisé
geolocator = Nominatim(user_agent="my_geocoder/1.0")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=2)  # Augmenter le délai

def geocode_adresse(adresse):
    try:
        location = geocode(adresse)
        if location:
            return location.latitude, location.longitude
    except Exception as e:
        print(f"Erreur pour l'adresse {adresse}: {e}")
    return None, None

# 3. Géocoder toutes les adresses
for idx, row in df.iterrows():
    if pd.notna(row['Adresse précise']):
        adresse = row['Adresse précise']
        lat, lon = geocode_adresse(adresse)
        df.at[idx, 'latitude'] = lat
        df.at[idx, 'longitude'] = lon
        time.sleep(2)  # Pause pour éviter les blocages

# 4. Sauvegarder le fichier avec les nouvelles coordonnées
df.to_csv("map_complet.csv", index=False)

# 5. Créer la carte interactive
m = folium.Map(location=[45.0, 0.7], zoom_start=9)

for idx, row in df.iterrows():
    if pd.isna(row['latitude']) or pd.isna(row['longitude']):
        continue  # Sauter les lignes sans coordonnées

    if pd.isna(row['url_pappers']) or row['url_pappers'] == "Non renseigné":
        color = 'red'
        popup_text = f"SIREN: {row['siren']}<br>Pas de site internet"
    else:
        color = 'green'
        popup_text = f"SIREN: {row['siren']}<br>Site: <a href='{row['url_pappers']}' target='_blank'>{row['url_pappers']}</a>"

    folium.Marker(
        location=[row['latitude'], row['longitude']],
        popup=popup_text,
        icon=folium.Icon(color=color, icon="scissors", prefix="fa")
    ).add_to(m)

# 6. Sauvegarder la carte dans un fichier HTML
m.save("carte_coiffeurs_dordogne.html")
