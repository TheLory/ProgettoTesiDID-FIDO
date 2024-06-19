from selenium.webdriver import Chrome
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.alert import Alert
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import threading
import time
import random
import csv
from colorama import Fore, Style, init

init(autoreset=True)


CSV_FILE = "test_results_VP_30.csv"
VP_HOME_URL= "https://localhost:5003/vcmanager?username=lori_test"
# Funzione per scrivere i risultati nel file CSV
def scrivi_risultato_csv(index, operazione, tempo, successo):
    with open(CSV_FILE, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([index, operazione, tempo, successo])

def click_element(driver, by, value, attempts=30):
    for attempt in range(attempts):
        try:
            element = driver.find_element(by, value)
            #time.sleep(random.uniform(0.5, 2.0))  # Delay randomico prima del click
            element.click()
            return
        except Exception as e:
            if attempt < attempts - 1:
                time.sleep(1)
            else:
                raise e

def handle_alert(driver, expected_text):
    try:
        WebDriverWait(driver, 30).until(EC.alert_is_present())
        alert = Alert(driver)
        alert_text = alert.text
        alert.accept()
        return expected_text in alert_text
    except Exception as e:
        print(f"Errore nell'handle dell'alert: {e}")
        return False


def esegui_generazione_vp(driver,index):
    start_time = time.time()
    successo = False
    try:
        print(f"[WALLET] Thread {index}: Inizio generazione VP")
        driver.get(VP_HOME_URL)
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "GeneraVP")))
        click_element(driver, By.ID, 'GeneraVP')
        if handle_alert(driver, "Authentication successful"):
            print(Fore.GREEN + f"[WALLET] generazione VP nella scheda {index} completata con successo.")
            successo = True
        else:
            print(Fore.RED + f"[WALLET] generazione VP nella scheda {index} fallita.")
    except Exception as e:
        print(Fore.RED + f"[WALLET] Errore nella generazione della VP {index}: {e}")
    finally:
        end_time = time.time()
        scrivi_risultato_csv(index, "Generazione VP", end_time - start_time, successo)

def operazioni_thread(index):
    start_time = time.time()
    chrome_driver = ChromeDriverManager().install()
    chrome_options = Options()
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--allow-insecure-localhost')
   
    chrome_options.add_argument('--headless')  # Disabilitare la modalità headless per il debug
    #chrome_options.add_argument('--window-size=200,200')  # Aggiungere dimensione finestra per vedere cosa succede

    driver = Chrome(service=Service(chrome_driver), options=chrome_options)
    
    #eseguioperazioni_wallet(driver=driver, index=index)
    #eseguioperazioni_server(driver=driver, index=index)
    esegui_generazione_vp(driver=driver,index=index)
    driver.quit()
    end_time = time.time()
    scrivi_risultato_csv(index, "Operazioni Totali", end_time - start_time, True)
    print(f"Operazioni nella scheda {index} completate in {end_time - start_time:.2f} secondi.")

def main():
    # Inizializzazione del file CSV
    with open(CSV_FILE, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Thread Index", "Operazione", "Tempo (s)", "Successo"])

    threads_number = 30 # Modificare a 1 thread per il debug
    threads = []

    for i in range(threads_number):
        thread = threading.Thread(target=operazioni_thread, args=(i,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

if __name__ == "__main__":
    main()
