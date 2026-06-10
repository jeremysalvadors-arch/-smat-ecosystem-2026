import paho.mqtt.client as mqtt
import json
import time
import random

# CONFIGURACIÓN
BROKER = "broker.hivemq.com"
PORT = 1883
ESTACION_ID = 1
TOPIC = f"fisi/smat/estaciones/{ESTACION_ID}/lecturas"  # nuevo formato Lab 11

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)  # evita el DeprecationWarning
client.connect(BROKER, PORT)

print(f"--- Sensor MQTT iniciado. Publicando en '{TOPIC}' ---")

while True:
    valor = round(random.uniform(10.5, 85.0), 2)
    payload = {
        "valor": valor,
        "timestamp": time.time()
    }
    client.publish(TOPIC, json.dumps(payload))
    print(f"[MQTT] Enviado: valor={valor} cm")
    time.sleep(10)