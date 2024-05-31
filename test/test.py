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
from colorama import Fore, Style, init

init(autoreset=True)

WALLET_URL = "https://localhost:5003/index.html"
SERVER_URL = "https://localhost:5001/index.html"

def esegui_registrazione_server(driver, index):
    try:
        print(f"[SERVER] Thread {index}: Inizio registrazione")
        driver.get(SERVER_URL)
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "register")))
        click_element(driver, By.ID, 'register')
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "username")))
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "displayname")))
        driver.find_element(By.ID, 'username').send_keys("loritest_server" + str(index))
        driver.find_element(By.ID, 'displayname').send_keys("loritest_server" + str(index))
        WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.ID, "register")))
        click_element(driver, By.ID, 'register')
        if handle_alert(driver, "Registration successful"):
            print(Fore.GREEN + f"[SERVER] Registrazione nella scheda {index} completata con successo.")
        else:
            print(Fore.RED + f"[SERVER] Registrazione nella scheda {index} fallita.")
    except Exception as e:
        print(Fore.RED + f"[SERVER] Errore nella registrazione scheda {index}: {e}")


def esegui_autenticazione_server(driver, index):
    try:
        print(f"[SERVER] Thread {index}: Inizio autenticazione")
        driver.get(SERVER_URL)
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "authenticate")))
        click_element(driver, By.ID, 'authenticate')
        click_element(driver, By.ID, 'authenticate')

        if handle_alert(driver, "Authentication successful"):
            print(Fore.GREEN + f"[SERVER] Autenticazione nella scheda {index} completata con successo.")
        else:
            print(Fore.RED + f"[SERVER] Autenticazione nella scheda {index} fallita.")
    except Exception as e:
        print(Fore.RED + f"[SERVER] Errore nell'autenticazione scheda {index}: {e}")


def esegui_registrazione_wallet(driver, index):
    try:
        print(f"[WALLET] Thread {index}: Inizio registrazione")
        driver.get(WALLET_URL)
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "register")))
        click_element(driver, By.ID, 'register')
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "username")))
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "displayname")))
        driver.find_element(By.ID, 'username').send_keys("loritest_wallet" + str(index))
        driver.find_element(By.ID, 'displayname').send_keys("loritest_wallet" + str(index))
        WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.ID, "register")))
        click_element(driver, By.ID, 'register')
        if handle_alert(driver, "Registration successful"):
            print(Fore.GREEN + f"[WALLET] Registrazione nella scheda {index} completata con successo.")
        else:
            print(Fore.RED + f"[WALLET] Registrazione nella scheda {index} fallita.")
    except Exception as e:
        print(Fore.RED + f"[WALLET] Errore nella registrazione scheda {index}: {e}")


def esegui_autenticazione_wallet(driver, index):
    try:
        print(f"[WALLET] Thread {index}: Inizio autenticazione")
        driver.get(WALLET_URL)
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "authenticate")))
        click_element(driver, By.ID, 'authenticate')
        click_element(driver, By.ID, 'authenticate')
        if handle_alert(driver, "Authentication successful"):
            print(Fore.GREEN + f"[WALLET] Autenticazione nella scheda {index} completata con successo.")
        else:
            print(Fore.RED + f"[WALLET] Autenticazione nella scheda {index} fallita.")
    except Exception as e:
        print(Fore.RED + f"[WALLET] Errore nell'autenticazione scheda {index}: {e}")

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

def eseguioperazioni_wallet(driver,index):
    esegui_registrazione_wallet(driver, index)
    esegui_autenticazione_wallet(driver, index)
    return

def eseguioperazioni_server(driver,index):
    esegui_registrazione_server(driver, index)
    esegui_autenticazione_server(driver, index)
    return

def operazioni_thread(index):
    start_time = time.time()
    chrome_driver = ChromeDriverManager().install()
    chrome_options = Options()
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--allow-insecure-localhost')
   # chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--headless')  # Disabilitare la modalità headless per il debug
    chrome_options.add_argument('--window-size=200,200')  # Aggiungere dimensione finestra per vedere cosa succede

    driver = Chrome(service=Service(chrome_driver), options=chrome_options)
    
    eseguioperazioni_wallet(driver=driver,index=index)
    
    eseguioperazioni_server(driver=driver,index=index)
    
    driver.quit()
    end_time = time.time()
    print(f"Operazioni nella scheda {index} completate in {end_time - start_time:.2f} secondi.")

def main():
    threads_number = 2  # Modificare a 1 thread per il debug
    threads = []

    for i in range(threads_number):
        thread = threading.Thread(target=operazioni_thread, args=(i,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

main()
