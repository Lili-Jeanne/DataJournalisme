import csv
import time
import requests

file_path = 'data_geocoded.csv'

def geocode_address(address):
    """Géocode une adresse via Nominatim."""
    if not address:
        return '', ''
    url = 'https://nominatim.openstreetmap.org/search'
    params = {'q': f'{address}, France', 'format': 'json', 'limit': 1}
    try:
        response = requests.get(url, params=params, headers={'User-Agent': 'MyApp'})
        if response.status_code != 200 or not response.text.strip():
            return '', ''
        data = response.json()
        if data:
            return data[0]['lat'], data[0]['lon']
    except Exception as e:
        print(f"Erreur géocodage pour '{address}': {e}")
    return '', ''

# Lire le CSV existant
with open(file_path, newline='', encoding='utf-8-sig') as csvfile:
    reader = csv.DictReader(csvfile, delimiter=',')
    # Nettoyer noms de colonnes
    fieldnames = [name.strip() for name in reader.fieldnames]
    rows = [ {k.strip(): v.strip() for k, v in row.items()} for row in reader ]

print("Colonnes détectées :", fieldnames)

# Détecter automatiquement la colonne adresse
address_col = None
for col in fieldnames:
    if 'adress' in col.lower():
        address_col = col
        break
if not address_col:
    raise ValueError("Impossible de trouver la colonne d'adresse dans le CSV")

# Vérifier si les colonnes lat/lon existent, sinon les ajouter
if 'lat' not in fieldnames:
    fieldnames.append('lat')
if 'lon' not in fieldnames:
    fieldnames.append('lon')

# Géocoder uniquement les lignes sans lat/lon
for i, row in enumerate(rows, start=1):
    address = row.get(address_col, '').strip()
    lat = row.get('lat', '').strip()
    lon = row.get('lon', '').strip()

    if lat and lon:
        print(f"[{i}] Déjà géocodée : {address}")
        continue

    if not address:
        print(f"[{i}] Adresse vide, passage...")
        continue

    print(f"[{i}] Géocodage : {address}")
    row['lat'], row['lon'] = geocode_address(address)
    time.sleep(1)

# Réécrire le CSV avec les lat/lon mises à jour
with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"✅ Fichier mis à jour : {file_path}")
