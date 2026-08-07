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
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
}

def scarica_da_estrazionidellotto():
    """ Fonte primaria: EstrazionidelLotto.it (Molto stabile e compatibile con GitHub) """
    url = "https://www.estrazionidellotto.it/"
    try:
        res = requests.get(url, headers=HEADERS, timeout=12)
        if res.status_code != 200:
            return None
            
        soup = BeautifulSoup(res.text, "html.parser")
        text = soup.get_text()
        
        # Cerca la data nel formato dd/MM/yyyy
        match = re.search(r"(\d{2}/\d{2}/\d{4})", text)
        if not match:
            return None
            
        data_estrazione = match.group(1)
        ruote_list = []
        
        # Cerca le righe della tabella contenente le ruote
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
            print(f"Dati recuperati con successo da EstrazionidelLotto ({data_estrazione})")
            return {"Data": data_estrazione, "Ruote": ruote_list}
    except Exception as e:
        print(f"Errore Fonte 1: {e}")
    return None

def scarica_da_adm():
    """ Fonte secondaria: ADM Ufficiale """
    url = "https://www.adm.gov.it/portale/monopoli/giochi/gioco-del-lotto/lotto_g"
    try:
        res = requests.get(url, headers=HEADERS, timeout=12)
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
            print(f"Dati recuperati con successo da ADM ({data_estrazione})")
            return {"Data": data_estrazione, "Ruote": ruote_list}
    except Exception as e:
        print(f"Errore ADM: {e}")
    return None

def aggiorna_json():
    # Tenta la prima fonte, in caso di errore prova la seconda
    nuova_estrazione = scarica_da_estrazionidellotto() or scarica_da_adm()
    
    if not nuova_estrazione:
        print("CRITICO: Impossibile scaricare i dati da nessuna fonte.")
        return

    try:
        with open("estrazioni.json", "r", encoding="utf-8") as f:
            archivio = json.load(f)
    except Exception:
        archivio = []

    if archivio:
        ultima_data_salvata = archivio[-1]["Data"]
        if nuova_estrazione["Data"] == ultima_data_salvata:
            print(f"Archivio già aggiornato. Nessuna nuova estrazione da aggiungere ({nuova_estrazione['Data']}).")
            return
    else:
        ultima_data_salvata = ""

    # Calcolo progressivo annuo del numero di estrazione
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
