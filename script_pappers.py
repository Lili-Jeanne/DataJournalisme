import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import os

# IDENTIFIANTS PAPPERS
EMAIL_PAPPERS = "lili0jeanne0flourez@gmail.com"
MOT_DE_PASSE_PAPPERS = "aZERTYUIOP24*"

# Fichiers
FICHIER_CSV = r"siren_coiffeurs.csv"
FICHIER_RESULTAT = "resultat_sites_web_final.csv"
FICHIER_PROGRESS = "resultat_sites_web_temp.csv"  # Utilise votre fichier existant

# 1. Lire le fichier CSV
def charger_donnees():
    print(f"Lecture du fichier CSV : {FICHIER_CSV}")
    df = pd.read_csv(FICHIER_CSV)
    print(f"Nombre d'entreprises dans le CSV : {len(df)}")
    return df

# 2. Fonction pour générer l'URL Pappers
def generer_url_pappers(siren):
    return f"https://www.pappers.fr/recherche?q={siren}"

# 3. Fonction pour se connecter à Pappers
def connexion_pappers(driver):
    try:
        print("Connexion à Pappers...")
        driver.get("https://www.pappers.fr/connexion")
        time.sleep(3)
        
        # Essayer plusieurs sélecteurs possibles pour l'email
        email_input = None
        selecteurs_email = [
            (By.NAME, "email"),
            (By.ID, "email"),
            (By.CSS_SELECTOR, "input[type='email']"),
            (By.XPATH, "//input[@type='email']"),
            (By.XPATH, "//input[contains(@placeholder, 'mail')]")
        ]
        
        for by, selector in selecteurs_email:
            try:
                email_input = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((by, selector))
                )
                print(f"Champ email trouvé.")
                break
            except:
                continue
        
        if not email_input:
            print("Impossible de trouver le champ email.")
            return False
        
        email_input.clear()
        email_input.send_keys(EMAIL_PAPPERS)
        
        # Essayer plusieurs sélecteurs pour le mot de passe
        password_input = None
        selecteurs_password = [
            (By.NAME, "password"),
            (By.ID, "password"),
            (By.CSS_SELECTOR, "input[type='password']"),
            (By.XPATH, "//input[@type='password']")
        ]
        
        for by, selector in selecteurs_password:
            try:
                password_input = driver.find_element(by, selector)
                print(f"Champ mot de passe trouvé.")
                break
            except:
                continue
        
        if not password_input:
            print("Impossible de trouver le champ mot de passe.")
            return False
        
        password_input.clear()
        password_input.send_keys(MOT_DE_PASSE_PAPPERS)
        
        # Soumettre le formulaire
        try:
            selecteurs_bouton = [
                (By.CSS_SELECTOR, "button[type='submit']"),
                (By.XPATH, "//button[@type='submit']"),
                (By.XPATH, "//button[contains(text(), 'Connexion')]"),
                (By.XPATH, "//button[contains(text(), 'connecter')]"),
                (By.CSS_SELECTOR, "input[type='submit']")
            ]
            
            for by, selector in selecteurs_bouton:
                try:
                    submit_button = driver.find_element(by, selector)
                    submit_button.click()
                    break
                except:
                    continue
            else:
                password_input.send_keys(Keys.RETURN)
        except:
            password_input.send_keys(Keys.RETURN)
        
        time.sleep(4)
        
        # Vérifier si la connexion a réussi
        if "connexion" not in driver.current_url.lower():
            print(f"Connexion réussie !\n")
            return True
        else:
            print("Échec de la connexion.")
            return False
        
    except Exception as e:
        print(f"Erreur lors de la connexion : {e}")
        return False

# 4. Fonction pour vérifier si le site web est renseigné
def verifier_site_web(driver, url, index, total):
    try:
        print(f"[{index+1}/{total}] Traitement : {url}")
        driver.get(url)
        time.sleep(2)

        # Chercher la ligne "Site internet"
        try:
            ligne_site_internet = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//th[contains(text(), 'Site internet')]/parent::tr"))
            )
            
            # Chercher le lien dans la cellule td
            try:
                lien_site = ligne_site_internet.find_element(By.CSS_SELECTOR, "td a")
                site_web = lien_site.get_attribute("href")
                texte_lien = lien_site.text.strip()
                
                if "Réservé" in texte_lien or "connectés" in texte_lien:
                    print(f"    → Non accessible (réservé)")
                    return "Non accessible"
                
                print(f"    → Site trouvé : {site_web}")
                return site_web
            except:
                cellule_td = ligne_site_internet.find_element(By.TAG_NAME, "td")
                texte = cellule_td.text.strip()
                
                if "Réservé" in texte or "connectés" in texte:
                    print(f"    → Non accessible (réservé)")
                    return "Non accessible"
                elif texte and texte != "-" and texte != "":
                    print(f"    → Site (texte) : {texte}")
                    return texte
                else:
                    print(f"    → Non renseigné")
                    return "Non renseigné"
                
        except Exception as e:
            print(f"    → Non renseigné (erreur)")
            return "Non renseigné"

    except Exception as e:
        print(f"    → Erreur : {str(e)[:50]}")
        return "Erreur"

# 5. Fonction pour charger ou créer les résultats existants
def charger_progress(df):
    """Charge les résultats déjà traités s'ils existent"""
    if os.path.exists(FICHIER_PROGRESS):
        print(f"\n📂 Fichier de progression trouvé : {FICHIER_PROGRESS}")
        df_progress = pd.read_csv(FICHIER_PROGRESS)
        
        # Compter combien ont déjà été traités (lignes où site_web n'est pas vide)
        # On compte les lignes où site_web existe et n'est pas une chaîne vide
        if 'site_web' in df_progress.columns:
            # Compter toutes les lignes avec une valeur (même "Non renseigné", etc.)
            nb_traites = df_progress['site_web'].apply(
                lambda x: pd.notna(x) and str(x).strip() != ''
            ).sum()
        else:
            nb_traites = 0
            df_progress['site_web'] = None
        
        print(f"✅ {nb_traites} entreprises déjà traitées")
        print(f"⏭️  Reprise à partir de la ligne {nb_traites + 1}\n")
        
        # S'assurer que url_pappers est présente
        if 'url_pappers' not in df_progress.columns:
            df_progress['url_pappers'] = df_progress['siren'].apply(generer_url_pappers)
        
        return df_progress, nb_traites
    else:
        print("\n🆕 Nouveau scraping, démarrage depuis le début\n")
        df['url_pappers'] = df['siren'].apply(generer_url_pappers)
        df['site_web'] = None
        return df, 0

# 6. Programme principal
def main():
    driver = None
    try:
        print("="*70)
        print("DÉMARRAGE DU SCRAPING PAPPERS (avec reprise automatique)")
        print("="*70)
        
        # Charger les données
        df = charger_donnees()
        
        # Charger la progression existante
        df, index_debut = charger_progress(df)
        
        # Si tout est déjà traité, on arrête
        if index_debut >= len(df):
            print("✨ Tout le scraping est déjà terminé !")
            return
        
        # Initialiser le driver
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        
        # Se connecter à Pappers
        if not connexion_pappers(driver):
            print("\nImpossible de se connecter à Pappers. Arrêt du programme.")
            return
        
        # Traiter les entreprises restantes
        print("="*70)
        print(f"TRAITEMENT DE {len(df) - index_debut} ENTREPRISES RESTANTES")
        print(f"(de {index_debut + 1} à {len(df)})")
        print("="*70 + "\n")
        
        temps_debut = time.time()
        
        for index in range(index_debut, len(df)):
            row = df.iloc[index]
            url = row["url_pappers"]
            site_web = verifier_site_web(driver, url, index, len(df))
            df.at[index, "site_web"] = site_web
            
            # Petite pause pour ne pas surcharger le serveur
            time.sleep(1)
            
            # Sauvegarder progressivement tous les 10 résultats
            if (index + 1) % 10 == 0:
                df.to_csv(FICHIER_PROGRESS, index=False)
                print(f"\n    💾 Sauvegarde automatique ({index + 1}/{len(df)} traités)\n")
        
        # Sauvegarder le fichier final
        df.to_csv(FICHIER_RESULTAT, index=False)
        
        # Supprimer le fichier de progression une fois terminé
        if os.path.exists(FICHIER_PROGRESS):
            os.remove(FICHIER_PROGRESS)
            print("\n🗑️  Fichier de progression supprimé (scraping terminé)")
        
        temps_total = time.time() - temps_debut
        
        # Statistiques
        resultats = df["site_web"].tolist()
        print("\n" + "="*70)
        print("RÉSUMÉ")
        print("="*70)
        print(f"Temps de cette session : {temps_total/60:.1f} minutes")
        print(f"Sites trouvés : {sum(1 for r in resultats if r not in ['Non renseigné', 'Non accessible', 'Erreur', None])}")
        print(f"Non renseignés : {resultats.count('Non renseigné')}")
        print(f"Non accessibles : {resultats.count('Non accessible')}")
        print(f"Erreurs : {resultats.count('Erreur')}")
        print(f"\n✅ Fichier final sauvegardé : {FICHIER_RESULTAT}")
        print("="*70)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interruption détectée (Ctrl+C)")
        if 'df' in locals():
            df.to_csv(FICHIER_PROGRESS, index=False)
            print(f"💾 Progression sauvegardée dans : {FICHIER_PROGRESS}")
            print("💡 Relancez le script pour reprendre là où vous vous êtes arrêté")
    
    except Exception as e:
        print(f"\n❌ Erreur principale : {e}")
        if 'df' in locals():
            df.to_csv(FICHIER_PROGRESS, index=False)
            print(f"💾 Progression sauvegardée dans : {FICHIER_PROGRESS}")
            print("💡 Relancez le script pour reprendre là où vous vous êtes arrêté")
    
    finally:
        if driver:
            driver.quit()
            print("\nNavigateur fermé.")

# Exécuter le programme
if __name__ == "__main__":
    main()