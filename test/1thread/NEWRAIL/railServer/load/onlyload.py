from selenium.webdriver import Chrome
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import threading
import time
import csv
from colorama import Fore, Style, init

init(autoreset=True)

WALLET_URL = "https://localhost:5003/index.html"
SERVER_URL = "https://localhost:5001/index.html"
CSV_FILE = "only_load_50.csv"

# Funzione per scrivere i risultati nel file CSV
def scrivi_risultato_csv(index, operazione, tempo_load):
    with open(CSV_FILE, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([index, operazione, tempo_load])

def misura_tempo_load(driver, url):
    start_time = time.time()
    driver.get(url)
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    WebDriverWait(driver, 30).until(
        lambda d: d.execute_script('return document.readyState') == 'complete'
    )
    return time.time() - start_time

def eseguioperazioni_wallet(driver, index):
    tempo_load = misura_tempo_load(driver, WALLET_URL)
    scrivi_risultato_csv(index, "Load Wallet", tempo_load)

def eseguioperazioni_server(driver, index):
    tempo_load = misura_tempo_load(driver, SERVER_URL)
    scrivi_risultato_csv(index, "Load Server", tempo_load)

def operazioni_thread(index):
    chrome_driver = ChromeDriverManager().install()
    chrome_options = Options()
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--allow-insecure-localhost')
    #chrome_options.add_argument('--headless')  # Disabilitare la modalità headless per il debug

    driver = Chrome(service=Service(chrome_driver), options=chrome_options)
    
    eseguioperazioni_wallet(driver, index)
    driver.quit()
    
    driver = Chrome(service=Service(chrome_driver), options=chrome_options)
    eseguioperazioni_server(driver, index)
    driver.quit()

def main():
    # Inizializzazione del file CSV
    with open(CSV_FILE, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Thread Index", "Operazione", "Tempo Load (s)"])

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
