import json
import re
from datetime import datetime
import cloudscraper
from bs4 import BeautifulSoup

RUOTE_MAP = {
    "BARI": "Bari", "CAGLIARI": "Cagliari", "FIRENZE": "Firenze", 
    "GENOVA": "Genova", "MILANO": "Milano", "NAPOLI": "Napoli", 
    "PALERMO": "Palermo", "ROMA": "Roma", "TORINO": "Torino", 
    "VENEZIA": "Venezia", "NAZIONALE": "Nazionale"
}

def scarica_da_estrazionedellotto():
    url = "https://www.estrazionedellotto.it/"
    
    # Crea uno scraper capace di aggirare le protezioni anti-bot
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )
    
    try:
        response = scraper.get(url, timeout=15)
        if response.status_code != 200:
            print(f"Errore HTTP: {response.status_code}")
            return None
            
        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text()
        
        # Cerca la data nel formato gg/mm/aaaa (es. 07/08/2026)
        match = re.search(r"(\d{2}/\d{2}/\d{4})", text)
        if not match:
            print("Data dell'estrazione non trovata.")
            return None
            
        data_estrazione = match.group(1)
        ruote_list = []
        
        # Cerca le righe delle tabelle contenenti i numeri
        for tr in soup.find_all("tr"):
            cols = [td.get_text().strip() for td in tr.find_all(["td", "th"])]
            if len(cols) >= 6:
                nome_r = cols[0].upper()
                if nome_r in RUOTE_MAP:
                    ruote_list.append({
                        "Ruota": RUOTE_MAP[nome_r],
                        "N1": cols[1],
                        "N2": cols[2],
                        "N3": cols[3],
                        "N4": cols[4],
                        "N5": cols[5]
                    })
                    
        if len(ruote_list) >= 10:
            print(f"Estratti recuperati con successo per la data {data_estrazione}")
            return {"Data": data_estrazione, "Ruote": ruote_list}
        else:
            print(f"Trovate solo {len(ruote_list)} ruote su 11.")
            
    except Exception as e:
        print(f"Errore durante lo scraping: {e}")
        
    return None

def aggiorna_json():
    nuova_estrazione = scarica_da_estrazionedellotto()
    
    if not nuova_estrazione:
        print("CRITICO: Impossibile scaricare i dati dal sito.")
        return

    try:
        with open("estrazioni.json", "r", encoding="utf-8") as f:
            archivio = json.load(f)
    except Exception:
        archivio = []

    if archivio:
        ultima_data_salvata = archivio[-1]["Data"]
        if nuova_estrazione["Data"] == ultima_data_salvata:
            print(f"Archivio già aggiornato all'ultima estrazione del {nuova_estrazione['Data']}.")
            return
    else:
        ultima_data_salvata = ""

    # Calcolo del numero di estrazione progressivo annuo
    anno_nuovo = datetime.strptime(nuova_estrazione["Data"], "%d/%m/%Y").year
    anno_ultimo = datetime.strptime(ultima_data_salvata, "%d/%m/%Y").year if ultima_data_salvata else 0

    numero_estrazione = 1 if anno_nuovo != anno_ultimo else archivio[-1]["Numero"] + 1

    estrazione_finale = {
        "Data": nuova_estrazione["Data"],
        "Numero": numero_estrazione,
        "Ruote": nuova_estrazione["Ruote"]
    }

    archivio.append(estrazione_finale)

    with open("estrazioni.json", "w", encoding="utf-8") as f:
        json.dump(archivio, f, indent=2, ensure_ascii=False)

    print(f"COMPLETATO: Aggiunta estrazione del {nuova_estrazione['Data']} (N. {numero_estrazione})")

if __name__ == "__main__":
    aggiorna_json()
