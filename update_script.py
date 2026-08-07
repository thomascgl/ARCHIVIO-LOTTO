import json
import re
from datetime import datetime
import requests
from bs4 import BeautifulSoup

# Mappatura delle ruote standard (in maiuscolo per sicurezza)
RUOTE_MAP = {
    "BARI": "Bari",
    "CAGLIARI": "Cagliari",
    "FIRENZE": "Firenze",
    "GENOVA": "Genova",
    "MILANO": "Milano",
    "NAPOLI": "Napoli",
    "PALERMO": "Palermo",
    "ROMA": "Roma",
    "TORINO": "Torino",
    "VENEZIA": "Venezia",
    "NAZIONALE": "Nazionale"
}

ADM_URL = "https://www.adm.gov.it/portale/monopoli/giochi/gioco-del-lotto/lotto_g"

def scarica_estrazione_adm():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(ADM_URL, headers=headers, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"Errore nella richiesta HTTP ad ADM: {e}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    
    # Cerca la stringa con la data (es: "Estrazione n° 124 del 04/08/2026")
    page_text = soup.get_text()
    match_data = re.search(r"Estrazione\s+n°?\s*\d+\s+del\s+(\d{2}/\d{2}/\d{4})", page_text, re.IGNORECASE)
    
    if not match_data:
        print("Impossibile trovare la data dell'estrazione nella pagina.")
        return None
        
    data_estrazione = match_data.group(1)

    ruote_list = []
    
    # Cerca le righe della tabella contenenti le ruote ed i numeri
    rows = soup.find_all("tr")
    for row in rows:
        cols = [td.get_text().strip() for td in row.find_all(["td", "th"])]
        if not cols:
            continue
            
        nome_ruota_raw = cols[0].upper()
        if nome_ruota_raw in RUOTE_MAP:
            # Assicuriamoci che ci siano i 5 estratti (colonne da 1 a 5)
            if len(cols) >= 6:
                ruote_list.append({
                    "Ruota": RUOTE_MAP[nome_ruota_raw],
                    "N1": cols[1],
                    "N2": cols[2],
                    "N3": cols[3],
                    "N4": cols[4],
                    "N5": cols[5]
                })

    if not ruote_list:
        print("Nessuna ruota trovata nella tabella.")
        return None

    return {
        "Data": data_estrazione,
        "Ruote": ruote_list
    }

def aggiorna_archivio_json():
    nuova_estrazione = scarica_estrazione_adm()
    if not nuova_estrazione:
        print("Operazione annullata: estrazione non recuperata.")
        return

    # Leggi il file JSON esistente
    try:
        with open("estrazioni.json", "r", encoding="utf-8") as f:
            archivio = json.load(f)
    except FileNotFoundError:
        archivio = []

    # Se l'archivio non è vuoto, controlla la data
    if archivio:
        ultima_data_salvata = archivio[-1]["Data"]
        if nuova_estrazione["Data"] == ultima_data_salvata:
            print(f"L'archivio è già aggiornato all'estrazione del {nuova_estrazione['Data']}.")
            return
    else:
        ultima_data_salvata = ""

    # Calcolo progressivo del Numero Estrazione per Anno
    anno_nuovo = datetime.strptime(nuova_estrazione["Data"], "%d/%m/%Y").year
    
    if ultima_data_salvata:
        anno_ultimo = datetime.strptime(ultima_data_salvata, "%d/%m/%Y").year
    else:
        anno_ultimo = None

    if anno_nuovo != anno_ultimo:
        numero_estrazione = 1
    else:
        numero_estrazione = archivio[-1]["Numero"] + 1

    # Aggiungi il campo Numero
    nuova_estrazione_completa = {
        "Data": nuova_estrazione["Data"],
        "Numero": numero_estrazione,
        "Ruote": nuova_estrazione["Ruote"]
    }

    # Accoda e salva sul file
    archivio.append(nuova_estrazione_completa)

    with open("estrazioni.json", "w", encoding="utf-8") as f:
        json.dump(archivio, f, indent=2, ensure_ascii=False)

    print(f"SUCCESS: Aggiunta estrazione del {nuova_estrazione['Data']} (N. {numero_estrazione})")

if __name__ == "__main__":
    aggiorna_archivio_json()
