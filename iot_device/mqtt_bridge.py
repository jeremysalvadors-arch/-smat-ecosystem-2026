import paho.mqtt.client as mqtt
import requests
import json
import sys
import time
import os

# CONFIGURACIÓN
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC = "fisi/smat/estaciones/+/lecturas"
API_URL = os.environ.get("API_URL", "http://backend:8000/lecturas/")
TOKEN_URL = os.environ.get("TOKEN_URL", "http://backend:8000/token")

# NUEVO: credenciales para autenticarse contra /token
ADMIN_USER = os.environ.get("DEFAULT_ADMIN_USER", "admin_fisi")
ADMIN_PASSWORD = os.environ.get("DEFAULT_ADMIN_PASSWORD", "smat2026")

cache_lecturas = {}
UMBRAL_CAMBIO = 0.05   # 5% de variación mínima para insertar
INTERVALO_FORZADO = 60  # segundos máximos sin insertar (reporte mínimo de vida)

def debe_insertar(estacion_id: int, nuevo_valor: float) -> tuple[bool, str]:
    """
    Decide si se debe enviar el dato al backend.
    Retorna (True/False, motivo)
    """
    ahora = time.time()

    # Si es la primera lectura de esta estación, siempre insertar
    if estacion_id not in cache_lecturas:
        return True, "Primera lectura de la estacion"

    ultimo = cache_lecturas[estacion_id]
    ultimo_valor = ultimo["valor"]
    ultimo_tiempo = ultimo["timestamp"]

    # Regla 1: Han pasado más de 60 segundos (reporte mínimo de vida)
    segundos_transcurridos = ahora - ultimo_tiempo
    if segundos_transcurridos >= INTERVALO_FORZADO:
        return True, f"Reporte forzado ({int(segundos_transcurridos)}s sin insertar)"

    # Regla 2: El valor varió más del 5%
    if ultimo_valor == 0:
        return True, "Valor anterior era 0, insertando"
    
    variacion = abs(nuevo_valor - ultimo_valor) / abs(ultimo_valor)
    if variacion > UMBRAL_CAMBIO:
        return True, f"Cambio significativo ({variacion*100:.1f}% > 5%)"

    # Si no cumple ninguna regla, filtrar
    return False, f"Filtrado (variacion={variacion*100:.1f}%, {int(segundos_transcurridos)}s)"

def obtener_token():
    """Obtiene el JWT del backend automáticamente."""
    try:
        response = requests.post(
            TOKEN_URL,
            data={
                "username": ADMIN_USER,
                "password": ADMIN_PASSWORD
            }
        )
        if response.status_code == 200:
            token = response.json()["access_token"]
            print("[AUTH] Token obtenido correctamente.")
            return token
        else:
            print(f"[AUTH ERROR] Código: {response.status_code}")
            print(f"[AUTH ERROR] Detalle: {response.text}")
            return None
    except Exception as e:
        print(f"[AUTH CRITICO] No hay conexión con el backend: {e}")
        return None

# Obtener token al iniciar
JWT_TOKEN = obtener_token()
if not JWT_TOKEN:
    print("[CRITICO] No se puede iniciar sin token. ¿Está el backend corriendo?")
    sys.exit(1)

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("[OK] Conectado exitosamente al Broker MQTT")
        client.subscribe(MQTT_TOPIC)
        print(f"[BRIDGE] Escuchando tópico: '{MQTT_TOPIC}'")
    else:
        print(f"[ERROR] Error de conexión al Broker. Código: {rc}")
        sys.exit(1)

def on_message(client, userdata, msg):
    global JWT_TOKEN
    try:
        # 1. Decodificar payload MQTT
        payload_raw = msg.payload.decode("utf-8")
        data_json = json.loads(payload_raw)

        # 2. Extraer ID de estación desde el tópico
        # Ejemplo: "fisi/smat/estaciones/5/lecturas" -> parts[3] = "5"
        topic_parts = msg.topic.split('/')
        estacion_id = int(topic_parts[3])
        nuevo_valor = float(data_json["valor"])

        print(f"[MQTT] Telemetría recibida — Estación {estacion_id}: {nuevo_valor} cm")

        # 3. Aplicar filtro de ruido (Deadband Filter)
        insertar, motivo = debe_insertar(estacion_id, nuevo_valor)

        if not insertar:
            print(f"[FILTRO] Dato bloqueado — {motivo}")
            return  # No enviar al backend

        print(f"[FILTRO] Dato aceptado — {motivo}")

        # 4. Enviar al backend
        api_payload = {
            "valor": nuevo_valor,
            "estacion_id": estacion_id
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {JWT_TOKEN}"
        }
        response = requests.post(API_URL, json=api_payload, headers=headers)

        if response.status_code in [200, 201]:
            # 5. Actualizar caché solo si se insertó correctamente
            cache_lecturas[estacion_id] = {
                "valor": nuevo_valor,
                "timestamp": time.time()
            }
            print(f"[DB] Lectura guardada: {nuevo_valor} cm — Estación {estacion_id}")

        elif response.status_code == 401:
            print("[AUTH] Token expirado. Renovando...")
            JWT_TOKEN = obtener_token()

        else:
            print(f"[ERROR] API rechazó el dato. Código: {response.status_code} — {response.text}")

    except KeyError as e:
        print(f"[ERROR] Falta la llave {e} en el payload MQTT.")
    except ValueError:
        print("[ERROR] El valor o ID de estación no son numéricos.")
    except Exception as e:
        print(f"[CRITICO] Error en el Bridge: {e}")

# Inicializar cliente MQTT
bridge_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
bridge_client.on_connect = on_connect
bridge_client.on_message = on_message

try:
    print("[BRIDGE] Inicializando Bridge de Acoplamiento SMAT...")
    bridge_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    bridge_client.loop_forever()
except KeyboardInterrupt:
    print("\n[BRIDGE] Detenido por el administrador.")