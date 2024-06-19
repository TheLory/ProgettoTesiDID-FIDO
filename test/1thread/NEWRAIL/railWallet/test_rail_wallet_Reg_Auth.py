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

WALLET_URL = "https://localhost:5003/index.html"
SERVER_URL = "https://localhost:5001/index.html"
CSV_FILE = "test_results_rail_server_50.csv"

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
    return driver.execute_script("return window.performance.timing.domContentLoadedEventEnd - window.performance.timing.navigationStart;") / 1000

def misura_tempo_animation(driver):
    js_code = """
    var startTime = performance.now();
    var frameTimes = [];

    function measureFPS(timestamp) {
        frameTimes.push(timestamp);
        if (timestamp - startTime < 1000) {
            requestAnimationFrame(measureFPS);
        } else {
            var fps = frameTimes.length / ((timestamp - startTime) / 1000);
            document.body.dataset.fps = fps;
        }
    }

    requestAnimationFrame(measureFPS);
    document.body.style.transition = 'opacity 1s';
    document.body.style.opacity = '0';
    """

    driver.execute_script(js_code)
    time.sleep(1.1)
    fps = driver.execute_script("return document.body.dataset.fps;")
    return float(fps)

def misura_tempo_idle(driver):
    return 0.0

def misura_tempo_response(driver, by, value):
    try:
        start_time = time.time()
        click_element(driver, by, value)
        end_time = time.time()
        return end_time - start_time
    except Exception as e:
        print(f"Errore nella misurazione del tempo di risposta: {e}")
        return None

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

def esegui_registrazione_server(driver, index):
    successo = False
    try:
        print(f"[SERVER] Thread {index}: Inizio registrazione")
        driver.get(SERVER_URL)
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "register")))
        tempo_response_1 = misura_tempo_response(driver, By.ID, 'register')
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "username")))
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "displayname")))
        driver.find_element(By.ID, 'username').send_keys("loritest_server" + str(index))
        driver.find_element(By.ID, 'displayname').send_keys("loritest_server" + str(index))
        WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.ID, "register")))
        tempo_response_2 = misura_tempo_response(driver, By.ID, 'register')
        if handle_alert(driver, "Registration successful"):
            successo = True
            print(Fore.GREEN + f"[SERVER] Registrazione nella scheda {index} completata con successo.")
        else:
            print(Fore.RED + f"[SERVER] Registrazione nella scheda {index} fallita.")
        tempo_response = tempo_response_1 + tempo_response_2
    except Exception as e:
        print(Fore.RED + f"[SERVER] Errore nella registrazione scheda {index}: {e}")
        tempo_response = None
    return successo, tempo_response

def esegui_autenticazione_server(driver, index):
    successo = False
    try:
        print(f"[SERVER] Thread {index}: Inizio autenticazione")
        driver.get(SERVER_URL)
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "authenticate")))
        tempo_response_1 = misura_tempo_response(driver, By.ID, 'authenticate')
        driver.find_element(By.ID, 'username').send_keys("loritest_server" + str(index))
        tempo_response_2 = misura_tempo_response(driver, By.ID, 'authenticate')
        if handle_alert(driver, "Authentication successful"):
            successo = True
            print(Fore.GREEN + f"[SERVER] Autenticazione nella scheda {index} completata con successo.")
        else:
            print(Fore.RED + f"[SERVER] Autenticazione nella scheda {index} fallita.")
        tempo_response = tempo_response_1 + tempo_response_2
    except Exception as e:
        print(Fore.RED + f"[SERVER] Errore nell'autenticazione scheda {index}: {e}")
        tempo_response = None
    return successo, tempo_response

def esegui_registrazione_wallet(driver, index):
    successo = False
    try:
        print(f"[WALLET] Thread {index}: Inizio registrazione")
        driver.get(WALLET_URL)
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "register")))
        tempo_response_1 = misura_tempo_response(driver, By.ID, 'register')
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "username")))
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "displayname")))
        driver.find_element(By.ID, 'username').send_keys("loritest_wallet" + str(index))
        driver.find_element(By.ID, 'displayname').send_keys("loritest_wallet" + str(index))
        WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.ID, "register")))
        tempo_response_2 = misura_tempo_response(driver, By.ID, 'register')
        if handle_alert(driver, "Registration successful"):
            successo = True
            print(Fore.GREEN + f"[WALLET] Registrazione nella scheda {index} completata con successo.")
        else:
            print(Fore.RED + f"[WALLET] Registrazione nella scheda {index} fallita.")
        tempo_response = tempo_response_1 + tempo_response_2
    except Exception as e:
        print(Fore.RED + f"[WALLET] Errore nella registrazione scheda {index}: {e}")
        tempo_response = None
    return successo, tempo_response

def esegui_autenticazione_wallet(driver, index):
    successo = False
    try:
        print(f"[WALLET] Thread {index}: Inizio autenticazione")
        driver.get(WALLET_URL)
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "authenticate")))
        tempo_response_1 = misura_tempo_response(driver, By.ID, 'authenticate')
        driver.find_element(By.ID, 'username').send_keys("loritest_wallet" + str(index))
        tempo_response_2 = misura_tempo_response(driver, By.ID, 'authenticate')
        if handle_alert(driver, "Authentication successful"):
            successo = True
            print(Fore.GREEN + f"[WALLET] Autenticazione nella scheda {index} completata con successo.")
        else:
            print(Fore.RED + f"[WALLET] Autenticazione nella scheda {index} fallita.")
        tempo_response = tempo_response_1 + tempo_response_2
    except Exception as e:
        print(Fore.RED + f"[WALLET] Errore nell'autenticazione scheda {index}: {e}")
        tempo_response = None
    return successo, tempo_response

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

def eseguioperazioni_wallet(driver, index):
    success, tempo_response = esegui_registrazione_wallet(driver, index)
    tempo_load = misura_tempo_load(driver)
    tempo_animation = misura_tempo_animation(driver)
    tempo_idle = misura_tempo_idle(driver)
    scrivi_risultato_csv(index, "Registrazione Wallet", tempo_response, tempo_animation, tempo_idle, tempo_load, success)
    
    success, tempo_response = esegui_autenticazione_wallet(driver, index)
    tempo_load = misura_tempo_load(driver)
    tempo_animation = misura_tempo_animation(driver)
    tempo_idle = misura_tempo_idle(driver)
    scrivi_risultato_csv(index, "Autenticazione Wallet", tempo_response, tempo_animation, tempo_idle, tempo_load, success)

def eseguioperazioni_server(driver, index):
    success, tempo_response = esegui_registrazione_server(driver, index)
    tempo_load = misura_tempo_load(driver)
    tempo_animation = misura_tempo_animation(driver)
    tempo_idle = misura_tempo_idle(driver)
    scrivi_risultato_csv(index, "Registrazione Server", tempo_response, tempo_animation, tempo_idle, tempo_load, success)
    
    success, tempo_response = esegui_autenticazione_server(driver, index)
    tempo_load = misura_tempo_load(driver)
    tempo_animation = misura_tempo_animation(driver)
    tempo_idle = misura_tempo_idle(driver)
    scrivi_risultato_csv(index, "Autenticazione Server", tempo_response, tempo_animation, tempo_idle, tempo_load, success)

def operazioni_thread(index):
    chrome_driver = ChromeDriverManager().install()
    chrome_options = Options()
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--allow-insecure-localhost')
    chrome_options.add_argument('--headless')  # Disabilitare la modalità headless per il debug
    chrome_options.add_argument('--window-size=200,200')  # Aggiungere dimensione finestra per vedere cosa succede

    driver = Chrome(service=Service(chrome_driver), options=chrome_options)
    
    eseguioperazioni_wallet(driver=driver, index=index)
    #eseguioperazioni_server(driver=driver, index=index)
    
    driver.quit()

def main():
    # Inizializzazione del file CSV
    with open(CSV_FILE, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Thread Index", "Operazione", "Tempo Response (s)", "Tempo Animation (HZ)", "Tempo Idle (s)", "Tempo Load (s)", "Successo"])

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
