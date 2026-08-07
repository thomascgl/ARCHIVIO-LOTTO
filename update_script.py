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
        
        # 1. Estrazione della Data dal <p class="drawTitle"><strong>
        draw_title = soup.find("p", class_="drawTitle")
        data_estrazione = None
        
        if draw_title:
            strong_tag = draw_title.find("strong")
            if strong_tag:
                txt_data = strong_tag.get_text()
                # Cerca la data o la converte dal formato "Venerdì 7 agosto 2026"
                match = re.search(r"(\d{1,2}\s+[a-zA-Zàèéìòù]+\s+\d{4})", txt_data)
                if match:
                    # Mappatura mesi in italiano
                    mesi = {
                        "gennaio": "01", "febbraio": "02", "marzo": "03", "aprile": "04",
                        "maggio": "05", "giugno": "06", "luglio": "07", "agosto": "08",
                        "settembre": "09", "ottobre": "10", "novembere": "11", "dicembre": "12"
                    }
                    parti = match.group(1).lower().split()
                    giorno = parti[0].zfill(2)
                    mese = mesi.get(parti[1], "01")
                    anno = parti[2]
                    data_estrazione = f"{giorno}/{mese}/{anno}"

        # Backup se la conversione testo non trova la data in formato esteso
        if not data_estrazione:
            match_numeric = re.search(r"(\d{2}/\d{2}/\d{4})", soup.get_text())
            if match_numeric:
                data_estrazione = match_numeric.group(1)

        if not data_estrazione:
            print("Data dell'estrazione non trovata nell'HTML.")
            return None

        # 2. Estrazione delle ruote da <ul class="ballRow">
        ruote_list = []
        ball_rows = soup.find_all("ul", class_="ballRow")
        
        for ul in ball_rows:
            elementi = [li.get_text().strip() for li in ul.find_all(["li", "span"])]
            
            # Pulisce gli elementi vuoti
            elementi = [e for e in elementi if e]
            
            if len(elementi) >= 6:
                nome_r = elementi[0].upper()
                # Estrae i 5 numeri
                numeri = [e for e in elementi[1:] if e.isdigit()]
                
                for chiave in RUOTE_MAP:
                    if chiave in nome_r and len(numeri) >= 5:
                        ruote_list.append({
                            "Ruota": RUOTE_MAP[chiave],
                            "N1": numeri[0],
                            "N2": numeri[1],
                            "N3": numeri[2],
                            "N4": numeri[3],
                            "N5": numeri[4]
                        })
                        break

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
