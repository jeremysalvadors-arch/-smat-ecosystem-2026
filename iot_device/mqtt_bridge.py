import paho.mqtt.client as mqtt
import requests
import json
import time
import threading

# CONFIGURACIÓN
BROKER = "broker.hivemq.com"
TOPIC = "fisi/smat/estaciones/#"  # Escucha todas las estaciones
API_URL = "http://127.0.0.1:8000/lecturas/"
TOKEN_URL = "http://127.0.0.1:8000/token"

# Rastrear el último mensaje de cada estación (para detectar Offline)
last_seen = {}

def obtener_token():
    """Obtiene el JWT del backend automáticamente."""
    try:
        response = requests.post(TOKEN_URL)
        if response.status_code == 200:
            token = response.json()["access_token"]
            print("[AUTH] Token obtenido correctamente.")
            return token
        else:
            print(f"[AUTH ERROR] Código: {response.status_code}")
            return None
    except Exception as e:
        print(f"[AUTH CRÍTICO] No hay conexión con el backend: {e}")
        return None

# Obtener token al iniciar
TOKEN = obtener_token()

def on_message(client, userdata, msg):
    """Se ejecuta cada vez que llega un mensaje MQTT."""
    global TOKEN  # ← debe ir primero, antes de usar TOKEN
    try:
        # 1. Decodificar el mensaje
        payload = json.loads(msg.payload.decode())
        print(f"[MQTT] Mensaje recibido en '{msg.topic}': {payload}")

        # 2. Extraer el ID de la estación desde el tópico
        estacion_id = int(msg.topic.split('/')[-1])

        # 3. Actualizar el registro de última vez visto
        last_seen[estacion_id] = time.time()

        # 4. Preparar datos para el backend
        data_to_send = {
            "valor": payload["valor"],
            "estacion_id": estacion_id
        }

        # 5. Enviar al backend via HTTP POST
        headers = {"Authorization": f"Bearer {TOKEN}"}
        response = requests.post(API_URL, json=data_to_send, headers=headers)

        if response.status_code in [200, 201]:
            print(f"[OK] Dato guardado en DB — Estación {estacion_id}, valor: {payload['valor']}")
        elif response.status_code == 401:
            print("[AUTH] Token expirado. Renovando...")
            TOKEN = obtener_token()
        else:
            print(f"[ERROR] API respondió {response.status_code}: {response.text}")

    except Exception as e:
        print(f"[CRÍTICO] Error procesando mensaje: {e}")

def check_deadlines():
    """Hilo que detecta estaciones sin enviar datos por más de 30 segundos."""
    while True:
        current_time = time.time()
        for estacion_id, ultimo_tiempo in list(last_seen.items()):
            segundos_sin_datos = current_time - ultimo_tiempo
            if segundos_sin_datos > 30:
                print(f"[OFFLINE] ALERTA: Estación {estacion_id} está OFFLINE "
                      f"(sin datos hace {int(segundos_sin_datos)}s)")
        time.sleep(10)

# Lanzar hilo de monitoreo de estaciones offline
threading.Thread(target=check_deadlines, daemon=True).start()

# Configurar y conectar el cliente MQTT
client = mqtt.Client()
client.on_message = on_message

print("[BRIDGE] Conectando al broker MQTT...")
client.connect(BROKER, 1883)
client.subscribe(TOPIC)
print(f"[BRIDGE] Escuchando tópico: '{TOPIC}' — Esperando datos...")

client.loop_forever()