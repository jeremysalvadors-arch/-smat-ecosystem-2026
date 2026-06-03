import requests
import time
import random

# CONFIGURACIÓN
API_URL = "http://127.0.0.1:8000/lecturas/"
TOKEN_URL = "http://127.0.0.1:8000/token"
ESTACION_ID = 1

def obtener_token():
    """Obtiene el JWT del backend automáticamente."""
    try:
        response = requests.post(TOKEN_URL)
        if response.status_code == 200:
            token = response.json()["access_token"]
            print("[AUTH] Token obtenido correctamente.")
            return token
        else:
            print(f"[AUTH ERROR] No se pudo obtener el token: {response.status_code}")
            return None
    except Exception as e:
        print(f"[AUTH CRÍTICO] No hay conexión con el servidor: {e}")
        return None

def leer_sensor_emulado():
    """Simula una lectura de nivel de río (0 a 100 cm)."""
    return round(random.uniform(10.5, 85.0), 2)

def enviar_telemetria():
    print(f"--- Iniciando Emisor IoT para Estación {ESTACION_ID} ---")

    # Obtener token automáticamente al iniciar
    token = obtener_token()
    if not token:
        print("[CRÍTICO] No se puede iniciar sin token. Verifica que el backend esté corriendo.")
        return

    while True:
        valor = leer_sensor_emulado()
        payload = {
            "valor": valor,
            "estacion_id": ESTACION_ID
        }
        headers = {
            "Authorization": f"Bearer {token}"
        }

        # Lógica de alarma y frecuencia dinámica (Reto semana 9)
        if valor > 70.0:
            print(f"[ALERTA] Umbral de inundación superado.")
            intervalo_envio = 2  # Modo emergencia
        else:
            intervalo_envio = 10  # Modo normal

        try:
            response = requests.post(API_URL, json=payload, headers=headers)
            if response.status_code in [200, 201]:
                print(f"[OK] Lectura enviada: {valor} cm — próximo envío en {intervalo_envio}s")
            elif response.status_code == 401:
                # Token expirado — obtener uno nuevo
                print("[AUTH] Token expirado. Renovando...")
                token = obtener_token()
                if not token:
                    print("[CRÍTICO] No se pudo renovar el token.")
                    break
            else:
                print(f"[ERROR] Código: {response.status_code}")
        except Exception as e:
            print(f"[CRÍTICO] No hay conexión con el servidor: {e}")

        time.sleep(intervalo_envio)

if __name__ == "__main__":
    enviar_telemetria()