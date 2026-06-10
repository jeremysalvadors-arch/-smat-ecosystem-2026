import paho.mqtt.client as mqtt
import json
import time
import random

# CONFIGURACIÓN
BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC = "fisi/smat/estaciones/1"  # Cambia el 1 por tu estacion_id

client = mqtt.Client()
client.connect(BROKER, PORT)

print(f"--- Sensor MQTT iniciado. Publicando en '{TOPIC}' ---")

while True:
    valor = round(random.uniform(10.5, 85.0), 2)
    payload = {
        "valor": valor,
        "timestamp": time.time()
    }

    client.publish(TOPIC, json.dumps(payload))
    print(f"[MQTT] Enviado: {payload}")
    time.sleep(10)