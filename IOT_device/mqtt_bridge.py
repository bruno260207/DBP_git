import paho.mqtt.client as mqtt
import requests
import json
import time
import threading

# CONFIGURACIÓN
BROKER = "broker.hivemq.com"
TOPIC = "fisi/smat/estaciones/5"  # Escucha todas las estaciones
API_URL = "http://localhost:8000/lecturas/"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbl9zbWF0IiwiZXhwIjoxNzgwODYwMTYwfQ.XzvV1UK5QE47rC6rMEUfq0I5Tf789Ts8vfKhNCB15gU"  # Pega tu token aquí

# Rastrear último mensaje de cada estación
last_seen = {}

def check_deadlines():
    while True:
        current_time = time.time()
        for eid, t in list(last_seen.items()):
            if current_time - t > 30:  # 30 segundos de gracia
                print(f"🚨 ALERTA: Estación {eid} está OFFLINE")
        time.sleep(10)

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        print(f"📩 Mensaje recibido en {msg.topic}: {payload}")

        # Extraer ID de estación del tópico
        estacion_id = msg.topic.split('/')[-1]

        # Actualizar último mensaje visto
        last_seen[estacion_id] = time.time()

        # Preparar datos para el backend
        data_to_send = {
            "valor": payload["valor"],
            "estacion_id": int(estacion_id)
        }

        # Enviar a la API
        headers = {"Authorization": f"Bearer {TOKEN}"}
        response = requests.post(API_URL, json=data_to_send, headers=headers)

        if response.status_code in [200, 201]:
            print(f"✅ Dato persistido en DB para estación {estacion_id}")
        else:
            print(f"⚠️ Error API ({response.status_code}): {response.text}")

    except Exception as e:
        print(f"❌ Error procesando mensaje: {e}")

# Lanzar hilo de monitoreo de estaciones offline
threading.Thread(target=check_deadlines, daemon=True).start()

# Configuración del cliente MQTT
client = mqtt.Client()
client.on_message = on_message

print("🚀 Bridge SMAT iniciado. Esperando datos...")
client.connect(BROKER, 1883)
client.subscribe(TOPIC)
client.loop_forever()