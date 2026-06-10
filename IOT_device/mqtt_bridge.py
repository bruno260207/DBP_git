import paho.mqtt.client as mqtt
import requests
import json
import time
import sys

# CONFIGURACIÓN
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC = "fisi/smat/estaciones/1/lecturas"
API_URL = "http://localhost:8000/lecturas/"
JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbl9zbWF0IiwiZXhwIjoxNzgxMTA4Mjc5fQ.gApG5-0NZABx2prbVLWkd2Txn8ANuR_WpjC1ljlQYh4" 

# MEMORIA CACHÉ LOCAL (Añadido para el Reto de la Semana 11)
cache_estaciones = {}

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("🟢 Conectado exitosamente al Broker MQTT")
        # Suscribirse al tópico global de lecturas de estaciones
        client.subscribe(MQTT_TOPIC)
        print(f"📡 Escuchando transmisiones en el tópico: {MQTT_TOPIC}")
    else:
        print(f"🔴 Error de conexión al Broker. Código de retorno: {rc}")
        sys.exit(1)

def on_message(client, userdata, msg):
    try:
        # 1. Decodificar el payload binario de MQTT a JSON string
        payload_raw = msg.payload.decode("utf-8")
        data_json = json.loads(payload_raw)
        
        # 2. Extraer el ID dinámico de la estación desde la estructura del tópico
        topic_parts = msg.topic.split('/')
        estacion_id = int(topic_parts[3])
        
        print(f"📩 Telemetría recibida de Estación [{estacion_id}]: {data_json}")

        # 3. Formatear la carga útil para cumplir con el esquema (Pydantic Model) de FastAPI
        api_payload = {
            "valor": float(data_json["valor"]),
            "estacion_id": estacion_id
        }

        # --- LÓGICA DEL RETO: FILTRO POR UMBRAL DE CAMBIO (DEADBAND FILTER) ---
        valor_nuevo = api_payload["valor"]
        tiempo_actual = time.time()
        hacer_ingesta = False

        if estacion_id not in cache_estaciones:
            print(f"🆕 Primer reporte de Estación [{estacion_id}]. Pasa filtro inicial.")
            hacer_ingesta = True
        else:
            valor_anterior = cache_estaciones[estacion_id]["ultimo_valor"]
            tiempo_anterior = cache_estaciones[estacion_id]["ultimo_tiempo"]
            
            diferencia_tiempo = tiempo_actual - tiempo_anterior
            variacion = (abs(valor_nuevo - valor_anterior) / valor_anterior) * 100 if valor_anterior != 0 else 100

            if variacion > 5.0:
                print(f"📈 [Filtro] Variación del {variacion:.2f}% detectada (> 5%).")
                hacer_ingesta = True
            elif diferencia_tiempo > 60.0:
                print(f"⏱️ [Filtro] Reporte de vida: Pasaron {diferencia_tiempo:.1f}s (> 60s).")
                hacer_ingesta = True
            else:
                print(f"🛑 [Filtro Bloqueado] Dato redundante. Var: {variacion:.1f}%, Tiempo: {diferencia_tiempo:.1f}s.")
        # ----------------------------------------------------------------------

        # 4. Ingestión de datos segura mediante HTTP POST con Header Bearer Token
        if hacer_ingesta:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {JWT_TOKEN}"
            }
            
            response = requests.post(API_URL, json=api_payload, headers=headers)

            if response.status_code == 200 or response.status_code == 201:
                print(f"💾 [DB Sincronizada] Lectura de {api_payload['valor']} cm guardada en SQLite.")
                # Actualizar caché solo si la persistencia fue exitosa
                cache_estaciones[estacion_id] = {
                    "ultimo_valor": valor_nuevo,
                    "ultimo_tiempo": tiempo_actual
                }
            else:
                print(f"⚠️ [Fallo de Ingesta] API rechazó el dato. Código: {response.status_code} - {response.text}")

    except KeyError as e:
        print(f"❌ Error de esquema: Falta la llave {e} en el payload MQTT.")
    except ValueError:
        print("❌ Error de casteo: El valor o el ID de la estación no son numéricos.")
    except Exception as e:
        print(f"❌ Error crítico en el Bridge: {e}")


# Inicialización del cliente de red MQTT
bridge_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
bridge_client.on_connect = on_connect
bridge_client.on_message = on_message

try:
    print("🚀 Inicializando el Bridge de Acoplamiento SMAT...")
    bridge_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    # Mantener el hilo escuchando activamente de forma síncrona
    bridge_client.loop_forever()
except KeyboardInterrupt:
    print("\n🛑 Bridge detenido por el administrador.")