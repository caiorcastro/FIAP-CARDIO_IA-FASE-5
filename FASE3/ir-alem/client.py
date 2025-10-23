import time
import random
import requests

URL = "http://127.0.0.1:8000/vitals"

def gen_sample():
    # Gera valores plausíveis, com chance de evento
    temp = 36.5 + random.random() * 2.0
    bpm = 70 + random.randint(-5, 5)
    # 1 em 8 chance de alerta
    if random.randint(1, 8) == 1:
        if random.choice([True, False]):
            bpm = 125
        else:
            temp = 38.5
    return {"temp": round(temp, 2), "bpm": bpm}

def main():
    print("Enviando amostras para o servidor REST (Ctrl+C para sair)...")
    while True:
        data = gen_sample()
        try:
            r = requests.post(URL, json=data, timeout=5)
            print("POST", data, "→", r.json())
        except Exception as e:
            print("Falha ao enviar:", e)
        time.sleep(2)

if __name__ == "__main__":
    main()

