import pandas as pd
import folium
from folium.plugins import HeatMap, MarkerCluster
import time
import requests

# 1. Charger le fichier CSV
df = pd.read_csv("data_geocoded.csv")

def geocode_adresse_api_gouv(adresse):
    """
    Géocode une adresse avec l'API Adresse du gouvernement français
    """
    url = "https://api-adresse.data.gouv.fr/search/"
    params = {
        'q': adresse,
        'limit': 1
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data['features']:
            coords = data['features'][0]['geometry']['coordinates']
            score = data['features'][0]['properties']['score']
            
            if score > 0.5:
                print(f"✓ Trouvé (score: {score:.2f}): {adresse}")
                return coords[1], coords[0]  # lat, lon
            else:
                print(f"⚠ Score faible ({score:.2f}): {adresse}")
                return coords[1], coords[0]
        
        print(f"✗ Non trouvé: {adresse}")
        
    except Exception as e:
        print(f"✗ Erreur pour {adresse}: {e}")
    
    return None, None

# 2. Géocoder toutes les adresses
print("Début du géocodage avec l'API Adresse (gouv.fr)...")
df['latitude'] = None
df['longitude'] = None

for idx, row in df.iterrows():
    if pd.notna(row['Adresse précise']):
        adresse = row['Adresse précise']
        lat, lon = geocode_adresse_api_gouv(adresse)
        df.at[idx, 'latitude'] = lat
        df.at[idx, 'longitude'] = lon
        time.sleep(0.2)

# 3. Statistiques sur le géocodage
print("\n=== Analyse géographique ===")
print(f"Lignes totales : {len(df)}")

# Identifier les lignes en Dordogne et hors Dordogne
df_geocodees = df[(df['latitude'].notna()) & (df['longitude'].notna())].copy()

df_en_dordogne = df_geocodees[
    (df_geocodees['latitude'] >= 44.8) & 
    (df_geocodees['latitude'] <= 45.6) &
    (df_geocodees['longitude'] >= 0.0) & 
    (df_geocodees['longitude'] <= 1.3)
]

df_hors_dordogne = df_geocodees[
    ~df_geocodees.index.isin(df_en_dordogne.index)
]

print(f"Géocodées en Dordogne : {len(df_en_dordogne)}")
print(f"Géocodées hors Dordogne : {len(df_hors_dordogne)}")
print(f"Non géocodées : {len(df) - len(df_geocodees)}")

# Afficher les adresses hors Dordogne (qui seront quand même affichées)
if len(df_hors_dordogne) > 0:
    print("\n⚠️  Entreprises hors Dordogne (affichées en violet sur la carte):")
    for idx, row in df_hors_dordogne.iterrows():
        print(f"  - {row['Adresse précise']} (lat: {row['latitude']:.4f}, lon: {row['longitude']:.4f})")

# 4. Afficher les statistiques
total = len(df)
trouvees = df['latitude'].notna().sum()
non_trouvees = total - trouvees
en_dordogne = len(df_en_dordogne)
hors_dordogne = len(df_hors_dordogne)

print(f"\n=== Résultats ===")
print(f"Total initial: {total}")
print(f"Géocodées: {trouvees} ({trouvees/total*100:.1f}%)")
print(f"Non trouvées: {non_trouvees} ({non_trouvees/total*100:.1f}%)")
print(f"En Dordogne: {en_dordogne} ({en_dordogne/total*100:.1f}%)")
print(f"Hors Dordogne (affichées quand même): {hors_dordogne} ({hors_dordogne/total*100:.1f}%)")

# 5. Sauvegarder le fichier complet (avec toutes les entreprises)
df.to_csv("map_complet_avec_localisation.csv", index=False)
print("\n✓ Fichier complet sauvegardé : map_complet_avec_localisation.csv")

# 6. Créer la carte interactive avec HEATMAP (centrée sur la Dordogne)
if len(df_en_dordogne) > 0:
    center_lat = df_en_dordogne['latitude'].mean()
    center_lon = df_en_dordogne['longitude'].mean()
else:
    center_lat, center_lon = 45.2, 0.7

# Carte de base
m = folium.Map(
    location=[center_lat, center_lon], 
    zoom_start=10,
    tiles='OpenStreetMap'
)

# HEATMAP avec rouge prononcé pour les zones chaudes (uniquement Dordogne)
# Poids augmenté pour atteindre le rouge plus rapidement
heat_data = [
    [row['latitude'], row['longitude'], 800.5]  # Poids augmenté de 1 à 2.5
    for idx, row in df_en_dordogne.iterrows()
]

HeatMap(
    heat_data,
    min_opacity=0.4,
    max_opacity=0.95,
    radius=35,  # Rayon augmenté pour plus de chaleur
    blur=18,
    max_zoom=13,  # Limite pour garder l'intensité même zoomé
    gradient={
        0.0: 'navy',
        0.15: 'blue',      # Plus rapide vers les couleurs chaudes
        0.3: 'cyan',
        0.45: 'lime',
        0.6: 'yellow',
        0.75: 'orange',
        0.85: '#FF4500',   # Orange-rouge
        1.0: '#FF0000'     # Rouge vif pour les zones très denses
    }
).add_to(m)

# Ajouter un cluster de marqueurs pour TOUTES les entreprises (Dordogne + hors Dordogne)
marker_cluster = MarkerCluster(name="Tous les coiffeurs").add_to(m)

for idx, row in df_geocodees.iterrows():
    if pd.isna(row['latitude']) or pd.isna(row['longitude']):
        continue
    
    # Déterminer si en Dordogne ou pas
    en_dordogne = (
        44.8 <= row['latitude'] <= 45.6 and 
        0.0 <= row['longitude'] <= 1.3
    )
    
    # Couleur selon présence site web ET localisation
    if not en_dordogne:
        color = 'purple'  # Violet pour hors Dordogne
        localisation = "⚠️ HORS DORDOGNE"
    elif pd.isna(row['url_pappers']) or row['url_pappers'] == "Non renseigné":
        color = 'red'
        localisation = "✓ En Dordogne"
    else:
        color = 'green'
        localisation = "✓ En Dordogne"
    
    # Texte du popup
    if pd.isna(row['url_pappers']) or row['url_pappers'] == "Non renseigné":
        popup_text = f"<b>{localisation}</b><br><b>SIREN:</b> {row['siren']}<br><b>Adresse:</b> {row['Adresse précise']}<br>❌ Pas de site internet"
    else:
        popup_text = f"<b>{localisation}</b><br><b>SIREN:</b> {row['siren']}<br><b>Adresse:</b> {row['Adresse précise']}<br>🌐 <a href='{row['url_pappers']}' target='_blank'>{row['url_pappers']}</a>"

    folium.Marker(
        location=[row['latitude'], row['longitude']],
        popup=folium.Popup(popup_text, max_width=300),
        icon=folium.Icon(color=color, icon="scissors", prefix="fa")
    ).add_to(marker_cluster)

# Ajouter un contrôle de couches
folium.LayerControl().add_to(m)

# 7. Sauvegarder la carte
m.save("carte_coiffeurs_toutes_entreprises.html")
print("✓ Carte avec toutes les entreprises sauvegardée : carte_coiffeurs_toutes_entreprises.html")
print("\n🎨 Légende des couleurs:")
print("  🟢 Vert = En Dordogne + site web")
print("  🔴 Rouge = En Dordogne + pas de site web")
print("  🟣 Violet = Hors Dordogne")
print("\n🔥 La heatmap (zones chaudes en rouge) ne montre que les entreprises EN Dordogne")
