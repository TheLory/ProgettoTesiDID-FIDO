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
import csv
from colorama import Fore, Style, init

init(autoreset=True)

CSV_FILE = "test_results_VP_1.csv"
VP_HOME_URL = "https://localhost:5003/vcmanager?username=lori_test"

# Funzione per scrivere i risultati nel file CSV
def scrivi_risultato_csv(index, operazione, tempo, successo):
    with open(CSV_FILE, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([index, operazione, tempo, successo])

def click_element(driver, by, value, attempts=30):
    for attempt in range(attempts):
        try:
            element = driver.find_element(by, value)
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

def esegui_generazione_vp(driver, index):
    start_time = time.time()
    successo = False
    try:
        print(f"[WALLET] Thread {index}: Inizio generazione VP")
        driver.get(VP_HOME_URL)
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "GeneraVP")))
        click_element(driver, By.ID, 'GeneraVP')
        
        if handle_alert(driver, "Authentication successful"):
            WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "ValidaVp")))
            print(Fore.GREEN + f"[WALLET] Generazione VP nella scheda {index} completata con successo.")
            successo = True
        else:
            print(Fore.RED + f"[WALLET] Generazione VP nella scheda {index} fallita.")
    except Exception as e:
        print(Fore.RED + f"[WALLET] Errore nella generazione della VP {index}: {e}")
    finally:
        end_time = time.time()
        scrivi_risultato_csv(index, "Generazione VP", end_time - start_time, successo)

def operazioni_thread(index):
    chrome_driver = ChromeDriverManager().install()
    chrome_options = Options()
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--allow-insecure-localhost')
    chrome_options.add_argument('--headless')  # Abilitare la modalità headless per il debug
    driver = Chrome(service=Service(chrome_driver), options=chrome_options)
    
    esegui_generazione_vp(driver=driver, index=index)
    driver.quit()

def main():
    # Inizializzazione del file CSV
    with open(CSV_FILE, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Thread Index", "Operazione", "Tempo (s)", "Successo"])

    threads_number = 1  # Modificare a 1 thread per il debug
    threads = []
    number_iteration = 1
    for j in range(number_iteration):
        for i in range(threads_number):
            thread = threading.Thread(target=operazioni_thread, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

if __name__ == "__main__":
    main()
