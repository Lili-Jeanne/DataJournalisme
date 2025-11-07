import pandas as pd

# Liste des numéros SIREN à supprimer
siren_to_remove = [
    '942241373', '941174013', '979019908', '399093665', '492738133',
    '811984087', '852012475', '379466089', '992862888', '989998448',
    '812235810', '811559020', '831648134', '792123481', '838797223',
    '539582338', '894112804', '326907037', '848080883', '838165447',
    '839010246', '491196812', '424696276', '853753911', '991230673',
    '442671459', '928896844', '922189469', '989609482', '984476697',
    '528222995', '984009704', '849444179', '807735238'
]

# Charger le fichier CSV
df = pd.read_csv('data_geocoded.csv')

# Supprimer les lignes contenant les numéros SIREN
df = df[~df['siren'].astype(str).isin(siren_to_remove)]

# Enregistrer le fichier modifié
df.to_csv('data_geocoded_cleaned.csv', index=False)
