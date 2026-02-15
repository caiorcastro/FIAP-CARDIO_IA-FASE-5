
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'patients.db')
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def create_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Tabela de Pacientes
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        age INTEGER
    )
    ''')

    # Tabela de Monitoramento (Sinais Vitais)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS monitoring (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER,
        systolic INTEGER,
        diastolic INTEGER,
        heart_rate INTEGER,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(patient_id) REFERENCES patients(id)
    )
    ''')
    
    # Inserir dados mockados se estiver vazia
    cursor.execute('SELECT count(*) FROM patients')
    if cursor.fetchone()[0] == 0:
        print("Populando banco de dados com dados fictícios...")
        cursor.execute("INSERT INTO patients (name, age) VALUES ('Carlos Drummond', 72)")
        cursor.execute("INSERT INTO patients (name, age) VALUES ('Cecília Meireles', 68)")
        
        # Carlos: Pressão Alta (Anomalia)
        cursor.execute("INSERT INTO monitoring (patient_id, systolic, diastolic, heart_rate) VALUES (1, 150, 95, 88)")
        # Cecília: Normal
        cursor.execute("INSERT INTO monitoring (patient_id, systolic, diastolic, heart_rate) VALUES (2, 120, 80, 72)")
        
        conn.commit()
    
    conn.close()
    print(f"Banco de dados criado em: {DB_PATH}")

if __name__ == "__main__":
    create_database()
