import time
import random
import requests

ORION = "http://orion:1026/v2/op/update"

ENTITY = "Crusher:001"

HEADERS = {
    "Content-Type": "application/json",
    "fiware-service": "default",
    "fiware-servicepath": "/"
}

def generate_data():
    base_prod = 90

    temperature = random.uniform(60, 95)
    vibration = random.uniform(3, 15)
    production = base_prod + random.uniform(-20, 10)

    status = "ALERTA" if temperature > 85 or vibration > 12 else "NORMAL"

    return {
        "actionType": "append",
        "entities": [
            {
                "id": ENTITY,
                "type": "Crusher",
                "temperature": {"value": round(temperature, 2), "type": "Float"},
                "vibration": {"value": round(vibration, 2), "type": "Float"},
                "production": {"value": round(production, 2), "type": "Float"},
                "status": {"value": status, "type": "Text"}
            }
        ]
    }

def send(payload):
    try:
        r = requests.post(ORION, json=payload, headers=HEADERS, timeout=5)
        print("Sent:", r.status_code, payload["entities"][0]["status"]["value"])
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    while True:
        data = generate_data()
        send(data)
        time.sleep(3)