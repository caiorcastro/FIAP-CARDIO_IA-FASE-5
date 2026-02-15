
import sqlite3
import json
import os
import time
from datetime import datetime
from dotenv import load_dotenv

# Carrega ambiente procurando em locais comuns:
# - `./.env` (raiz do repo)
# - `./FASE5/.env` (compatibilidade com estrutura antiga)
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for env_path in [os.path.join(repo_root, ".env"), os.path.join(repo_root, "FASE5", ".env")]:
    load_dotenv(env_path)

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'patients.db')
LOG_PATH = os.path.join(os.path.dirname(__file__), 'data', 'logs.json')
api_key = (os.getenv("GEMINI_API_KEY") or "").strip()
model_name = (os.getenv("GEMINI_MODEL") or "").strip()
model = None

# Evita carregar a lib/stack do Gemini quando nao ha chave.
if api_key:
    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)

        candidates = [model_name] if model_name else []
        candidates += ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"]
        candidates = [c for c in candidates if c]

        for name in candidates:
            try:
                model = genai.GenerativeModel(name)
                break
            except Exception:
                model = None
                continue
    except Exception:
        model = None

def analyze_risk_with_ai(patient_name, sys, dia, bpm):
    """Usa IA para gerar uma descrição clínica do alerta."""
    if not model:
        return f"Alerta automático: {patient_name} com vitais alterados (PA {sys}/{dia}, FC {bpm} bpm)."
    
    prompt = f"O paciente {patient_name} apresentou PA {sys}/{dia} mmHg e FC {bpm} bpm. Gere um breve log clínico de 1 frase recomendando ação."
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except:
        # Nao quebra a rastreabilidade; apenas faz fallback.
        return f"Alerta automático: {patient_name} com vitais alterados (PA {sys}/{dia}, FC {bpm} bpm)."

def run_rpa_cycle():
    print("--- Iniciando Ciclo RPA ---")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Busca últimas medições
    cursor.execute('''
        SELECT p.name, m.systolic, m.diastolic, m.heart_rate, m.timestamp 
        FROM monitoring m 
        JOIN patients p ON m.patient_id = p.id
        ORDER BY m.timestamp DESC LIMIT 5
    ''')
    
    records = cursor.fetchall()
    conn.close()
    
    logs = []
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH, 'r', encoding='utf-8') as f:
            try: logs = json.load(f)
            except: logs = []

    for name, sys, dia, bpm, ts in records:
        # Regra de Negócio: Pressão > 140/90 ou BPM > 100
        is_anomaly = (sys > 140 or dia > 90) or (bpm > 100)
        
        if is_anomaly:
            print(f"[ALERTA] Anomalia detectada para {name}: PA {sys}/{dia}")
            
            # Verifica se já não foi logado recentemente (simples deduplicação)
            # Para protótipo, vamos logar sempre que rodar e detectar
            
            ai_description = analyze_risk_with_ai(name, sys, dia, bpm)
            
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "patient": name,
                "status": "CRITICAL",
                "vitals": {"bp": f"{sys}/{dia}", "hr": bpm},
                "ai_analysis": ai_description,
                "action": "Notificar Equipe Médica"
            }
            logs.append(log_entry)
        else:
            print(f"[OK] {name} está estável.")

    # Salva no NoSQL (JSON)
    with open(LOG_PATH, 'w', encoding='utf-8') as f:
        json.dump(logs, f, indent=4, ensure_ascii=False)
    print("--- Ciclo finalizado. Logs atualizados. ---")

if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        print("Banco de dados não encontrado. Rode database_setup.py primeiro.")
    else:
        # Loop infinito simulado (roda uma vez para teste no reporte)
        run_rpa_cycle()
