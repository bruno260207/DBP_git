import requests
import time
import random

# CONFIGURACIÓN
API_URL = "http://localhost:8000/lecturas/"
ESTACION_ID = 3  # ID de la estación registrada en tu DB
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbl9zbWF0IiwiZXhwIjoxNzc5OTAzNzk0fQ.BMIA9H-unw-0_wwMBP-kxz-80qTpoEirokikbgYzwMs"

def leer_sensor_emulado():
    # Simulamos una lectura de nivel de río (0 a 100 cm)
    return round(random.uniform(10.5, 85.0), 2)

def enviar_telemetria():
    print(f"--- Iniciando Emisor IoT para Estación {ESTACION_ID} ---")
    
    while True:
        valor = leer_sensor_emulado()
        payload = {
            "valor": valor,
            "estacion_id": ESTACION_ID
        }
        headers = {
            "Authorization": f"Bearer {TOKEN}"
        }

        if valor > 70.0:
            print(f"⚠️ [ALERTA] Umbral de inundación superado! Valor crítico: {valor} cm")
            intervalo = 2 
        else:
            print(f"✅ [INFO] Nivel estable: {valor} cm")
            intervalo = 10  

        try:
            response = requests.post(API_URL, json=payload, headers=headers)
            # Nota: FastAPI suele devolver 200 o 201 Created al guardar
            if response.status_code in [200, 201]:
                print(f"[OK] Telemetría enviada exitosamente ({valor} cm).")
            else:
                print(f"[ERROR API] Código de estado: {response.status_code}")
        except Exception as e:
            print(f"[CRÍTICO] No hay conexión con el servidor local: {e}")

        # Espera dinámica según el estado del río
        print(f"⏳ Próxima lectura en {intervalo} segundos...\n")
        time.sleep(intervalo)

if __name__ == "__main__":
    enviar_telemetria()