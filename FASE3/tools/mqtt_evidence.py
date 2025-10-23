import os
import ssl
import time
import json
import threading
from datetime import datetime
from paho.mqtt import client as mqtt


HOST = os.getenv("MQTT_HOST", "817c2430152f460ba0cb75228198eb57.s1.eu.hivemq.cloud")
PORT = int(os.getenv("MQTT_PORT", "8883"))
USER = os.getenv("MQTT_USERNAME") or "cardioia-client"
PASS = os.getenv("MQTT_PASSWORD") or "FIAP102030i"
TOPIC = os.getenv("MQTT_TOPIC", "cardioia/grupo1/vitals")


def build_client(cid_suffix: str):
    cid = f"cardioia-{cid_suffix}-{int(time.time()*1000)}"
    client = mqtt.Client(client_id=cid, protocol=mqtt.MQTTv311)
    client.username_pw_set(USER, PASS)
    ctx = ssl.create_default_context()
    client.tls_set_context(ctx)
    return client


def run_evidence():
    logs = []

    sub = build_client("sub")
    pub = build_client("pub")

    def log(msg):
        line = f"[{datetime.utcnow().isoformat()}Z] {msg}"
        print(line)
        logs.append(line)

    def on_connect(c, u, flags, rc):
        log(f"CONNECT rc={rc} cid={c._client_id.decode()}")

    def on_message(c, u, m):
        log(f"RECV topic={m.topic} payload={m.payload.decode(errors='ignore')}")

    sub.on_connect = on_connect
    sub.on_message = on_message
    pub.on_connect = on_connect

    sub.connect(HOST, PORT, keepalive=60)
    pub.connect(HOST, PORT, keepalive=60)

    sub.loop_start()
    pub.loop_start()
    time.sleep(1)
    sub.subscribe(TOPIC, qos=0)
    log(f"SUB {TOPIC}")

    # Publica 5 mensagens de teste
    for i in range(5):
        payload = {
            "ts": int(time.time()),
            "temp": round(36.5 + (i * 0.1), 2),
            "hum": round(55 + (i * 0.5), 1),
            "bpm": 125 if i == 0 else 75 + i
        }
        j = json.dumps(payload, ensure_ascii=False)
        pub.publish(TOPIC, j, qos=0)
        log(f"SEND topic={TOPIC} payload={j}")
        time.sleep(1)

    time.sleep(3)
    sub.loop_stop()
    pub.loop_stop()
    sub.disconnect()
    pub.disconnect()

    # Escreve evidências em arquivo
    out_dir = os.path.join("FASE3", "reports")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "evidence_mqtt.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(logs) + "\n")
    print(f"Saved evidence to {out_path}")


if __name__ == "__main__":
    run_evidence()

