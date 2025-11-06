import csv
import time
import requests

file_path = 'data_geocoded.csv'

def geocode_address(address):
    """Géocode une adresse via l'API Adresse du gouvernement français."""
    if not address:
        return '', ''
    
    url = 'https://api-adresse.data.gouv.fr/search/'
    params = {
        'q': address,
        'limit': 1
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code != 200:
            print(f"  ⚠ Erreur HTTP {response.status_code}")
            return '', ''
        
        data = response.json()
        
        if data.get('features'):
            coords = data['features'][0]['geometry']['coordinates']
            score = data['features'][0]['properties']['score']
            
            # Afficher le score de confiance
            if score > 0.7:
                print(f"  ✓ Trouvé (score: {score:.2f})")
            elif score > 0.5:
                print(f"  ⚠ Score moyen ({score:.2f})")
            else:
                print(f"  ⚠ Score faible ({score:.2f})")
            
            return coords[1], coords[0]  # lat, lon
        else:
            print(f"  ✗ Aucun résultat")
            
    except Exception as e:
        print(f"  ✗ Erreur: {e}")
    
    return '', ''

# Lire le CSV existant
with open(file_path, newline='', encoding='utf-8-sig') as csvfile:
    reader = csv.DictReader(csvfile, delimiter=',')
    # Nettoyer noms de colonnes
    fieldnames = [name.strip() for name in reader.fieldnames]
    rows = [{k.strip(): v.strip() for k, v in row.items()} for row in reader]

print("Colonnes détectées :", fieldnames)

# Détecter automatiquement la colonne adresse
address_col = None
for col in fieldnames:
    if 'adress' in col.lower():
        address_col = col
        break
if not address_col:
    raise ValueError("Impossible de trouver la colonne d'adresse dans le CSV")

print(f"Colonne d'adresse utilisée : '{address_col}'")

# Vérifier si les colonnes lat/lon existent, sinon les ajouter
if 'lat' not in fieldnames:
    fieldnames.append('lat')
if 'lon' not in fieldnames:
    fieldnames.append('lon')

# Statistiques
total = len(rows)
deja_geocodees = 0
a_geocoder = 0
succes = 0
echecs = 0

# Géocoder uniquement les lignes sans lat/lon
print(f"\n=== Début du géocodage ===\n")

for i, row in enumerate(rows, start=1):
    address = row.get(address_col, '').strip()
    lat = row.get('lat', '').strip()
    lon = row.get('lon', '').strip()

    if lat and lon:
        print(f"[{i}/{total}] Déjà géocodée : {address}")
        deja_geocodees += 1
        continue

    if not address:
        print(f"[{i}/{total}] Adresse vide, passage...")
        row['lat'] = ''
        row['lon'] = ''
        continue

    print(f"[{i}/{total}] Géocodage : {address}")
    a_geocoder += 1
    
    new_lat, new_lon = geocode_address(address)
    row['lat'] = new_lat
    row['lon'] = new_lon
    
    if new_lat and new_lon:
        succes += 1
    else:
        echecs += 1
    
    # Pause courte (l'API gouv est plus tolérante)
    time.sleep(0.3)

# Réécrire le CSV avec les lat/lon mises à jour
with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

# Afficher les statistiques finales
print(f"\n=== Résultats ===")
print(f"Total d'adresses : {total}")
print(f"Déjà géocodées : {deja_geocodees}")
print(f"À géocoder : {a_geocoder}")
print(f"Succès : {succes} ({succes/a_geocoder*100:.1f}%)" if a_geocoder > 0 else "Succès : 0")
print(f"Échecs : {echecs} ({echecs/a_geocoder*100:.1f}%)" if a_geocoder > 0 else "Échecs : 0")

# Afficher les adresses non géocodées
adresses_echec = [row.get(address_col, '') for row in rows if not row.get('lat') and row.get(address_col, '').strip()]
if adresses_echec:
    print(f"\nAdresses non géocodées ({len(adresses_echec)}):")
    for addr in adresses_echec:
        print(f"  - {addr}")

print(f"\n✅ Fichier mis à jour : {file_path}")