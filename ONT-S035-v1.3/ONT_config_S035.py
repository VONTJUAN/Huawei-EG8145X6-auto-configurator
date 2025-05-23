import os
import threading
import time
import tkinter as tk
from tkinter import ttk
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium import webdriver

ONT_IP = "http://192.168.100.1"
USERNAME = "telecomadmin"
PASSWORD = "admintelecom"


### CODIGO CREADO POR AITOR MARTINEZ GARCIA Y JUAN ZORNOZA GARCIA###


def start_process(browser, status_callback):
    try:
        status_callback("🚀 Iniciando navegador...")

        if browser == "Chrome":
            driver = webdriver.Chrome()
        elif browser == "Edge":
            service = EdgeService()
            options = webdriver.EdgeOptions()
            options.add_argument("--start-maximized")
            driver = webdriver.Edge(service=service, options=options)
        elif browser == "Firefox":
            service = FirefoxService()
            options = webdriver.FirefoxOptions()
            options.add_argument("--start-maximized")
            driver = webdriver.Firefox(service=service, options=options)
        else:
            status_callback("❌ Navegador no soportado.")
            return

        wait = WebDriverWait(driver, 15)
        driver.get(ONT_IP)

        status_callback("⌛ Esperando carga de la página...")
        time.sleep(0)
        wait.until(EC.presence_of_element_located((By.ID, "txt_Username")))

        # Login vía JavaScript
        script = '''
            let u = document.getElementById("txt_Username");
            let p = document.getElementById("txt_Password");
            u.focus(); u.value = arguments[0];
            u.dispatchEvent(new Event("input", { bubbles: true }));
            p.focus(); p.value = arguments[1];
            p.dispatchEvent(new Event("input", { bubbles: true }));
            setTimeout(() => { LoginSubmit("loginbutton"); }, 500);
        '''
        driver.execute_script(script, USERNAME, PASSWORD)
        status_callback("✅ Login enviado por JS con LoginSubmit()")

        time.sleep(0)

        try:
            short_wait = WebDriverWait(driver, 3)
            exit_btn = short_wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//input[@value='Exit']"))
            )
            exit_btn.click()
            status_callback(
                "🔁 Asistente inicial detectado y cerrado con 'Exit'")
            time.sleep(0)
        except:
            status_callback(
                "✅ No se detectó asistente inicial, continuando rápido...")

        # Esperar a que la página cargue completamente
        status_callback("🧭 Navegando al menú de carga...")
        advanced_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//div[normalize-space()='Advanced']")))
        advanced_btn.click()
        time.sleep(0)

        # Acceder al submenú de configuración
        maintenance_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//div[contains(text(),'Maintenance Diagno')]")))
        maintenance_btn.click()
        time.sleep(0)

        # Acceder directamente al submenú por su ID conocido
        config_menu = wait.until(
            EC.element_to_be_clickable((By.ID, "cfgconfig")))
        config_menu.click()
        time.sleep(0)

        # Asegúrate de estar dentro del iframe si aplica (por si la ONT lo usa)
        try:
            driver.switch_to.frame(driver.find_element(By.ID, "menuIframe"))
        except:
            status_callback(
                "⚠️ No se encontró iframe 'menuIframe', continuando sin cambiar de frame.")

        # Subir archivo directamente al input
        input_file = wait.until(EC.presence_of_element_located(
            (By.XPATH, "//input[@type='file']")))

        base_dir = os.path.dirname(os.path.abspath(__file__))
        xml_path = os.path.join(base_dir, "S035.xml")

        if not os.path.exists(xml_path):
            status_callback("❌ Archivo XML no encontrado.")
            return

        input_file.send_keys(xml_path)
        status_callback(
            f"✅ Archivo subido automáticamente: {os.path.basename(xml_path)}")

        # Click al botón "Update Configuration File"
        update_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//input[@value='Update Configuration File']")))
        update_btn.click()
        status_callback("⚙️ Se hizo click en 'Update Configuration File'")

        # Aceptar el cuadro de confirmación del navegador
        alert = wait.until(EC.alert_is_present())
        alert.accept()
        status_callback(
            "🟢 Confirmación aceptada, la ONT iniciará la carga y reinicio.")

    except Exception as e:
        status_callback(f"❌ Error: {str(e)}")


class ONTUploaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ONT Config Uploader S035")
        self.root.geometry("800x500")
        self.root.minsize(500, 300)
        self.root.resizable(False, False)

        # Configurar grid para que sea expandible
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(3, weight=1)

        self.browser = tk.StringVar(value="Chrome")

        self.label_browser = tk.Label(root, text="Navegador:")
        self.label_browser.grid(
            row=0, column=0, sticky="w", padx=10, pady=(10, 0))

        self.combo_browser = ttk.Combobox(
            root,
            textvariable=self.browser,
            values=["Chrome", "Edge", "Firefox"],
            state="readonly"
        )
        self.combo_browser.grid(row=1, column=0, padx=10, sticky="ew")

        self.btn_upload = tk.Button(
            root,
            text="● INICIAR",
            bg="green",
            fg="white",
            font=("Arial", 14, "bold"),
            command=self.run_upload
        )
        self.btn_upload.grid(row=2, column=0, pady=10)

        self.text_status = tk.Text(root, wrap="word")
        self.text_status.grid(row=3, column=0, padx=10, pady=10, sticky="nsew")

        # Barra de scroll para el Text
        scroll = tk.Scrollbar(root, command=self.text_status.yview)
        scroll.grid(row=3, column=1, sticky="ns", pady=10)
        self.text_status.config(yscrollcommand=scroll.set)

    def update_status(self, message):
        self.text_status.insert(tk.END, message + "\n")
        self.text_status.see(tk.END)

    def run_upload(self):
        threading.Thread(
            target=start_process,
            args=(self.browser.get(), self.update_status),
            daemon=True
        ).start()


if __name__ == "__main__":
    root = tk.Tk()
    app = ONTUploaderGUI(root)
    root.mainloop()
