import mysql.connector
from mysql.connector import Error

def create_connection():
    """Crea una connessione al server MySQL"""
    try:
        return mysql.connector.connect(
            host='localhost',
            user='root',
            password='password123'
        )
    except Error as e:
        print(f"Errore di connessione: {e}")
        return None

def show_tests():
    conn = create_connection()
    if not conn: return
    cursor = conn.cursor()
    cursor.execute("USE raceup_tdm;")
    
    cursor.execute("""
        SELECT t.test_id, s.year, v.model_name, tr.name, t.test_date, t.status 
        FROM tests t
        JOIN seasons s ON t.season_id = s.season_id
        JOIN vehicles v ON t.vehicle_id = v.vehicle_id
        JOIN tracks tr ON t.track_id = tr.track_id;
    """)
    print("\n=== LISTA TEST EFFETTUATI ===")
    for row in cursor.fetchall():
        print(f"[ID Test: {row[0]}] Anno: {row[1]} | Auto: {row[2]} | Pista: {row[3]} | Data: {row[4]} | Stato: {row[5]}")
    cursor.close()
    conn.close()

def show_laps():
    conn = create_connection()
    if not conn: return
    cursor = conn.cursor()
    cursor.execute("USE raceup_tdm;")
    
    cursor.execute("""
        SELECT l.lap_number, l.lap_time_seconds, l.is_best_lap, r.run_number, d.first_name, d.last_name
        FROM laps l
        JOIN runs r ON l.run_id = r.run_id
        JOIN drivers d ON r.driver_id = d.driver_id;
    """)
    print("\n=== TEMPI AL GIRO REGISTRATI ===")
    for row in cursor.fetchall():
        best = " ⭐ (BEST)" if row[2] else ""
        print(f"Run #{row[3]} | Pilota: {row[4]} {row[5]} | Giro {row[0]}: {row[1]}s{best}")
    cursor.close()
    conn.close()

def add_lap():
    conn = create_connection()
    if not conn: return
    cursor = conn.cursor()
    cursor.execute("USE raceup_tdm;")
    
    try:
        run_id = int(input("Inserisci l'ID del Run (es. 1): "))
        lap_number = int(input("Numero del giro: "))
        lap_time = float(input("Tempo al giro in secondi (es. 58.452): "))
        is_best = input("È il miglior giro? (s/n): ").lower() == 's'
        
        cursor.execute("""
            INSERT INTO laps (run_id, lap_number, lap_time_seconds, is_best_lap)
            VALUES (%s, %s, %s, %s);
        """, (run_id, lap_number, lap_time, is_best))
        
        conn.commit()
        print(" Giro aggiunto con successo!")
    except Exception as e:
        print(f"Errore durante l'inserimento: {e}")
    finally:
        cursor.close()
        conn.close()

def main_menu():
    while True:
        print("\n--- RACE UP TEST DATA MANAGER ---")
        print("1. Visualizza tutti i Test")
        print("2. Visualizza tutti i Giri in pista")
        print("3. Aggiungi un nuovo Giro a un Run")
        print("4. Esci")
        
        choice = input("\nScegli un'opzione (1-4): ")
        
        if choice == '1':
            show_tests()
        elif choice == '2':
            show_laps()
        elif choice == '3':
            add_lap()
        elif choice == '4':
            print("Chiusura programma. Ciao!")
            break
        else:
            print("Scelta non valida. Riprova.")

if __name__ == "__main__":
    main_menu()