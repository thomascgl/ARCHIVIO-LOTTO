import json
import re
from datetime import datetime
import requests
from bs4 import BeautifulSoup

RUOTE_MAP = {
    "BARI": "Bari", "CAGLIARI": "Cagliari", "FIRENZE": "Firenze", 
    "GENOVA": "Genova", "MILANO": "Milano", "NAPOLI": "Napoli", 
    "PALERMO": "Palermo", "ROMA": "Roma", "TORINO": "Torino", 
    "VENEZIA": "Venezia", "NAZIONALE": "Nazionale"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7"
}

def scarica_da_adm():
    url = "https://www.adm.gov.it/portale/monopoli/giochi/gioco-del-lotto/lotto_g"
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        if res.status_code != 200:
            return None
            
        soup = BeautifulSoup(res.text, "html.parser")
        text = soup.get_text()
        
        match = re.search(r"Estrazione\s+n°?\s*\d+\s+del\s+(\d{2}/\d{2}/\d{4})", text, re.IGNORECASE)
        if not match:
            return None
            
        data_estrazione = match.group(1)
        ruote_list = []
        
        for tr in soup.find_all("tr"):
            cols = [td.get_text().strip() for td in tr.find_all(["td", "th"])]
            if len(cols) >= 6:
                nome_r = cols[0].upper()
                if nome_r in RUOTE_MAP:
                    ruote_list.append({
                        "Ruota": RUOTE_MAP[nome_r],
                        "N1": cols[1], "N2": cols[2], "N3": cols[3], "N4": cols[4], "N5": cols[5]
                    })
                    
        if len(ruote_list) >= 10:
            return {"Data": data_estrazione, "Ruote": ruote_list}
    except Exception as e:
        print(f"Errore ADM: {e}")
    return None

def aggiorna_json():
    # Prova il recupero dati
    nuova_estrazione = scarica_da_adm()
    
    if not nuova_estrazione:
        print("ATTENZIONE: Impossibile recuperare la nuova estrazione. Nessun aggiornamento effettuato.")
        return

    try:
        with open("estrazioni.json", "r", encoding="utf-8") as f:
            archivio = json.load(f)
    except Exception:
        archivio = []

    if archivio:
        ultima_data_salvata = archivio[-1]["Data"]
        if nuova_estrazione["Data"] == ultima_data_salvata:
            print(f"Archivio già aggiornato alla data del {nuova_estrazione['Data']}.")
            return
    else:
        ultima_data_salvata = ""

    # Calcolo progressivo numero estrazione annuo
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

    print(f"OK: Aggiunta estrazione del {nuova_estrazione['Data']} n.{numero_estrazione}")

if __name__ == "__main__":
    aggiorna_json()
