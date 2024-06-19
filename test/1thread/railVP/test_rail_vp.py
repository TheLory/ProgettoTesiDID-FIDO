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

WALLET_URL = "https://localhost:5003/index.html"
SERVER_URL = "https://localhost:5001/index.html"
CSV_FILE = "test_results_rail_vp_50.csv"
VP_HOME_URL = "https://localhost:5003/vcmanager?username=lori_test"

# Funzione per scrivere i risultati nel file CSV
def scrivi_risultato_csv(index, operazione, tempo_response, tempo_animation, tempo_idle, tempo_load, successo):
    with open(CSV_FILE, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([index, operazione, tempo_response, tempo_animation, tempo_idle, tempo_load, successo])

def misura_tempo(funzione):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = funzione(*args, **kwargs)
        end_time = time.time()
        return result, end_time - start_time
    return wrapper

def misura_tempo_load(driver):
    return driver.execute_script("return window.performance.timing.loadEventEnd - window.performance.timing.navigationStart;") / 1000

def misura_tempo_animation(driver):
    # Esempio di misurazione semplice di animazione (da adattare secondo i casi d'uso specifici)
    start = time.time()
    driver.execute_script("document.body.style.transition = 'opacity 1s'; document.body.style.opacity = '0';")
    end = time.time()
    return end - start

def misura_tempo_idle(driver):
    return 0.0



@misura_tempo
def esegui_generazione_vp(driver, index):
    successo = False
    try:
        print(f"[WALLET] Thread {index}: Inizio generazione VP")
        driver.get(VP_HOME_URL)
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "GeneraVP")))
        click_element(driver, By.ID, 'GeneraVP')
        
        if handle_alert(driver, "Authentication successful"):
            print(Fore.GREEN + f"[WALLET] Generazione VP nella scheda {index} completata con successo.")
            successo = True
        else:
            print(Fore.RED + f"[WALLET] Generazione VP nella scheda {index} fallita.")
    except Exception as e:
        print(Fore.RED + f"[WALLET] Errore nella generazione della VP {index}: {e}")
    return successo

def click_element(driver, by, value, attempts=15):
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
        WebDriverWait(driver, 15).until(EC.alert_is_present())
        alert = Alert(driver)
        alert_text = alert.text
        alert.accept()
        return expected_text in alert_text
    except Exception as e:
        print(f"Errore nell'handle dell'alert: {e}")
        return False


def eseguioperazioni_vp(driver,index):
    success, tempo_response = esegui_generazione_vp(driver, index)
    tempo_load = misura_tempo_load(driver)
    tempo_animation = misura_tempo_animation(driver)
    tempo_idle = misura_tempo_idle(driver)
    scrivi_risultato_csv(index, "Generazione VP", tempo_response, tempo_animation, tempo_idle, tempo_load, success)


 
def operazioni_thread(index):
    chrome_driver = ChromeDriverManager().install()
    chrome_options = Options()
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--allow-insecure-localhost')
    chrome_options.add_argument('--headless')  # Disabilitare la modalità headless per il debug
 #  chrome_options.add_argument('--window-size=200,200')  # Aggiungere dimensione finestra per vedere cosa succede

    driver = Chrome(service=Service(chrome_driver), options=chrome_options)
    
  #  eseguioperazioni_wallet(driver=driver, index=index)
   # eseguioperazioni_server(driver=driver, index=index)
    eseguioperazioni_vp(driver,index)
    driver.quit()

def main():
    # Inizializzazione del file CSV
    with open(CSV_FILE, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Thread Index", "Operazione", "Tempo Response (s)", "Tempo Animation (s)", "Tempo Idle (s)", "Tempo Load (s)", "Successo"])

    threads_number = 1  # Modificare a 1 thread per il debug
    threads = []
    number_of_iterations = 50
    for j in range(number_of_iterations):
        for i in range(threads_number):
            thread = threading.Thread(target=operazioni_thread, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

if __name__ == "__main__":
    main()
