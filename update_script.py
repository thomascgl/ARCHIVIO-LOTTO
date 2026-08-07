import json
import requests
from datetime import datetime

# Mappatura dei nomi delle ruote
RUOTE_MAP = {
    "BARI": "Bari", "CAGLIARI": "Cagliari", "FIRENZE": "Firenze", 
    "GENOVA": "Genova", "MILANO": "Milano", "NAPOLI": "Napoli", 
    "PALERMO": "Palermo", "ROMA": "Roma", "TORINO": "Torino", 
    "VENEZIA": "Venezia", "NAZIONALE": "Nazionale"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

def scarica_da_api():
    """ Scarica l'ultima estrazione dall'API JSON diretta di Lottomatica/Mazinga """
    url = "https://www.lottomatica.it/api/gdl/estrazioni/lotto/ultima"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            data_json = res.json()
            
            # Estrazione della data (formato ISO o dd/MM/yyyy)
            data_raw = data_json.get("dataEstrazione", "")
            if "-" in data_raw:
                dt = datetime.strptime(data_raw.split("T")[0], "%Y-%m-%d")
                data_formatted = dt.strftime("%d/%m/%Y")
            else:
                data_formatted = data_raw

            ruote_list = []
            for item in data_json.get("estrazioniRuota", []):
                nome_r = item.get("ruota", "").upper()
                numeri = item.get("estratti", [])
                
                if nome_r in RUOTE_MAP and len(numeri) >= 5:
                    ruote_list.append({
                        "Ruota": RUOTE_MAP[nome_r],
                        "N1": str(numeri[0]),
                        "N2": str(numeri[1]),
                        "N3": str(numeri[2]),
                        "N4": str(numeri[3]),
                        "N5": str(numeri[4])
                    })

            if len(ruote_list) >= 10:
                print(f"Dati recuperati con successo via API JSON ({data_formatted})")
                return {"Data": data_formatted, "Ruote": ruote_list}
    except Exception as e:
        print(f"Errore API Lottomatica: {e}")
        
    return None

def scarica_fallback_html():
    """ Backup su fonte secondaria se l'API principale è momentaneamente offline """
    url = "https://www.lottoitalia.it/lotto/estrazioni"
    try:
        from bs4 import BeautifulSoup
        import re
        
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            text = soup.get_text()
            
            match = re.search(r"(\d{2}/\d{2}/\d{4})", text)
            if match:
                data_formatted = match.group(1)
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
                    print(f"Dati recuperati da Fallback HTML ({data_formatted})")
                    return {"Data": data_formatted, "Ruote": ruote_list}
    except Exception as e:
        print(f"Errore Fallback HTML: {e}")
        
    return None

def aggiorna_json():
    # Prova l'API diretta, altrimenti passa al fallback
    nuova_estrazione = scarica_da_api() or scarica_fallback_html()
    
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
            print(f"Archivio già aggiornato all'ultima estrazione del {nuova_estrazione['Data']}.")
            return
    else:
        ultima_data_salvata = ""

    # Conteggio progressivo per l'anno
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
