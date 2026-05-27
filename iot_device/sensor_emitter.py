import requests
import time
import random

# CONFIGURACIÓN
API_URL = "http://localhost:8000/lecturas/"
ESTACION_ID = 1  # ID de la estación registrada en la DB
TOKEN = "TU_TOKEN_JWT_AQUI" # Obtenido del login

def leer_sensor_emulado():
    # Simulamos una lectura de nivel de río (0 a 100 cm)
    return round(random.uniform(10.5, 85.0), 2)

def enviar_telemetria():
    print(f"--- Iniciando Emisor IoT Inteligente para Estación {ESTACION_ID} ---")
    
    while True:
        valor = leer_sensor_emulado()
        payload = {
            "valor": valor,
            "estacion_id": ESTACION_ID
        }
        headers = {
            "Authorization": f"Bearer {TOKEN}"
        }

        # --- [RETO PUNTO 1 & 2] LÓGICA DE ALARMA Y FRECUENCIA DINÁMICA ---
        if valor > 70.0:
            print(f"[ALERTA] Umbral de inundación superado. Valor actual: {valor} cm")
            intervalo_envio = 2  # Modo de Emergencia (2 segundos)
        else:
            intervalo_envio = 10  # Modo Normal (10 segundos)
        # -----------------------------------------------------------------

        try:
            response = requests.post(API_URL, json=payload, headers=headers)
            # Nota: Aceptamos 200 o 201 por si tu backend devuelve "Created"
            if response.status_code in [200, 201]:
                print(f"[OK] Lectura enviada: {valor} cm (Próximo envío en {intervalo_envio}s)")
            else:
                print(f"[ERROR] Código: {response.status_code}")
        except Exception as e:
            print(f"[CRÍTICO] No hay conexión con el servidor: {e}")

        # Esperar el tiempo dinámico calculado
        time.sleep(intervalo_envio)

if __name__ == "__main__":
    enviar_telemetria()
