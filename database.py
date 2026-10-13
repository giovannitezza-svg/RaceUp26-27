import mysql.connector
from mysql.connector import Error

def create_connection():
    """Crea una connessione al server MySQL"""
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='password123'  # La password che abbiamo configurato
        )
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Errore di connessione a MySQL: {e}")
    return None

def initialize_database():
    conn = create_connection()
    if not conn:
        return

    cursor = conn.cursor()

    # 1. Creazione del Database
    cursor.execute("CREATE DATABASE IF NOT EXISTS raceup_tdm;")
    cursor.execute("USE raceup_tdm;")

    # 2. Creazione delle Tabelle principali (con UNIQUE per evitare duplicati)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS seasons (
        season_id INT AUTO_INCREMENT PRIMARY KEY,
        year INT NOT NULL UNIQUE,
        description TEXT
    );""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vehicles (
        vehicle_id INT AUTO_INCREMENT PRIMARY KEY,
        model_name VARCHAR(100) NOT NULL,
        generation VARCHAR(50),
        notes TEXT,
        UNIQUE (model_name, generation)
    );""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tracks (
        track_id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        layout_name VARCHAR(50),
        length_meters DECIMAL(8, 2) NOT NULL,
        activity_type VARCHAR(50)
    );""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS drivers (
        driver_id INT AUTO_INCREMENT PRIMARY KEY,
        first_name VARCHAR(50) NOT NULL,
        last_name VARCHAR(50) NOT NULL,
        license_number VARCHAR(50) UNIQUE
    );""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tests (
        test_id INT AUTO_INCREMENT PRIMARY KEY,
        season_id INT NOT NULL,
        vehicle_id INT NOT NULL,
        track_id INT NOT NULL,
        test_date DATE NOT NULL,
        objectives TEXT,
        status VARCHAR(50),
        problems_encountered TEXT,
        conclusions TEXT,
        FOREIGN KEY (season_id) REFERENCES seasons(season_id),
        FOREIGN KEY (vehicle_id) REFERENCES vehicles(vehicle_id),
        FOREIGN KEY (track_id) REFERENCES tracks(track_id)
    );""")

    # 3. Nuove tabelle: Tires, Setups, Runs, Laps
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tires (
        tire_id INT AUTO_INCREMENT PRIMARY KEY,
        compound VARCHAR(50) NOT NULL,
        set_identifier VARCHAR(50) NOT NULL UNIQUE,
        status VARCHAR(50) DEFAULT 'New'
    );""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS setups (
        setup_id INT AUTO_INCREMENT PRIMARY KEY,
        description VARCHAR(100),
        spring_rate_fl DECIMAL(6,2),
        spring_rate_fr DECIMAL(6,2),
        spring_rate_rl DECIMAL(6,2),
        spring_rate_rr DECIMAL(6,2),
        static_camber DECIMAL(4,2),
        toe_settings DECIMAL(4,2),
        power_limit_kw INT,
        notes TEXT
    );""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS runs (
        run_id INT AUTO_INCREMENT PRIMARY KEY,
        test_id INT NOT NULL,
        driver_id INT NOT NULL,
        setup_id INT NOT NULL,
        tire_id INT NOT NULL,
        run_number INT NOT NULL,
        is_planned BOOLEAN DEFAULT TRUE,
        ambient_temp DECIMAL(4,1),
        asphalt_temp DECIMAL(4,1),
        status VARCHAR(50),
        FOREIGN KEY (test_id) REFERENCES tests(test_id),
        FOREIGN KEY (driver_id) REFERENCES drivers(driver_id),
        FOREIGN KEY (setup_id) REFERENCES setups(setup_id),
        FOREIGN KEY (tire_id) REFERENCES tires(tire_id)
    );""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS laps (
        lap_id INT AUTO_INCREMENT PRIMARY KEY,
        run_id INT NOT NULL,
        lap_number INT NOT NULL,
        lap_time_seconds DECIMAL(7,3) NOT NULL,
        penalty_seconds DECIMAL(5,2) DEFAULT 0.00,
        is_best_lap BOOLEAN DEFAULT FALSE,
        FOREIGN KEY (run_id) REFERENCES runs(run_id)
    );""")

    print(" Tutte le tabelle sono state create con successo!")

        # 4. Inserimento di dati di prova completi (Seed Data)
    # ID espliciti + INSERT IGNORE: rilanciare lo script non duplica nulla.
    seed = {
        "seasons": (
            "INSERT IGNORE INTO seasons (season_id, year, description) VALUES (%s, %s, %s);",
            [(1, 2026, 'Stagione di test principale'),
             (2, 2025, 'Stagione precedente')]),
        "vehicles": (
            "INSERT IGNORE INTO vehicles (vehicle_id, model_name, generation, notes) VALUES (%s, %s, %s, %s);",
            [(1, 'Race Up Electric', 'EV-2026', 'Ultimo prototipo'),
             (2, 'Race Up Electric', 'EV-2025', 'Prototipo stagione precedente')]),
        "tracks": (
            "INSERT IGNORE INTO tracks (track_id, name, layout_name, length_meters, activity_type) VALUES (%s, %s, %s, %s, %s);",
            [(1, 'Varano de Melegari', 'Autodromo', 2350.00, 'Endurance'),
             (2, 'Vallelunga', 'Circuito Pista', 4085.00, 'Autocross'),
             (3, 'Franciacorta', 'Circuito Internazionale', 2520.00, 'Skidpad')]),
        "drivers": (
            "INSERT IGNORE INTO drivers (driver_id, first_name, last_name, license_number) VALUES (%s, %s, %s, %s);",
            [(1, 'Mario', 'Rossi', 'AB123CD'),
             (2, 'Luca', 'Bianchi', 'EF456GH'),
             (3, 'Giulia', 'Verdi', 'IJ789KL')]),
        "tests": (
            """INSERT IGNORE INTO tests (test_id, season_id, vehicle_id, track_id, test_date,
                                        objectives, status, problems_encountered, conclusions)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);""",
            [(1, 1, 1, 1, '2026-03-25', 'Test frenata rigenerativa e consumo', 'Completed',
              'Nessun problema critico', 'Ottimo bilanciamento'),
             (2, 1, 1, 2, '2026-04-12', 'Test setup sospensioni', 'Completed',
              'Surriscaldamento anteriore dopo il run 2', 'Setup morbido migliore sul veloce'),
             (3, 1, 1, 3, '2026-05-03', 'Confronto mescole gomme', 'Completed',
              'Nessuno', 'Mescola soft più veloce ma degrada prima'),
             (4, 2, 2, 1, '2025-09-14', 'Validazione batteria', 'Completed',
              'Calo di potenza a fine run', 'Da rivedere il raffreddamento'),
             (5, 1, 1, 2, '2026-11-20', 'Test aerodinamica', 'Planned', None, None)]),
        "tires": (
            "INSERT IGNORE INTO tires (tire_id, compound, set_identifier, status) VALUES (%s, %s, %s, %s);",
            [(1, 'Slick', 'SET-01', 'New'),
             (2, 'Slick Soft', 'SET-02', 'Used'),
             (3, 'Slick Medium', 'SET-03', 'Used'),
             (4, 'Rain', 'SET-04', 'New')]),
        "setups": (
            """INSERT IGNORE INTO setups (setup_id, description, spring_rate_fl, spring_rate_fr,
                                         spring_rate_rl, spring_rate_rr, power_limit_kw)
               VALUES (%s, %s, %s, %s, %s, %s, %s);""",
            [(1, 'Setup Standard Base', 45.00, 45.00, 50.00, 50.00, 80),
             (2, 'Setup Morbido', 38.00, 38.00, 42.00, 42.00, 80),
             (3, 'Setup Rigido', 55.00, 55.00, 60.00, 60.00, 80),
             (4, 'Setup Potenza Ridotta', 45.00, 45.00, 50.00, 50.00, 60)]),
        # run_id, test_id, driver_id, setup_id, tire_id, run_number, ambient, asphalt, status
        "runs": (
            """INSERT IGNORE INTO runs (run_id, test_id, driver_id, setup_id, tire_id, run_number,
                                        ambient_temp, asphalt_temp, status)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);""",
            [(1, 1, 1, 1, 1, 1, 22.5, 35.0, 'Completed'),
             (2, 1, 2, 1, 2, 2, 23.0, 36.5, 'Completed'),
             (3, 2, 1, 2, 1, 1, 19.0, 28.0, 'Completed'),
             (4, 2, 1, 3, 1, 2, 20.5, 31.5, 'Completed'),
             (5, 2, 3, 2, 3, 3, 21.0, 33.0, 'Completed'),
             (6, 3, 2, 1, 2, 1, 24.0, 41.0, 'Completed'),
             (7, 3, 3, 1, 3, 2, 25.5, 44.5, 'Completed'),
             (8, 4, 1, 4, 4, 1, 17.0, 22.0, 'Completed')]),
        "laps": (
            "INSERT IGNORE INTO laps (lap_id, run_id, lap_number, lap_time_seconds, is_best_lap) VALUES (%s, %s, %s, %s, %s);",
            [(1, 1, 1, 58.452, True),  (2, 1, 2, 58.910, False),  (3, 1, 3, 59.230, False),
             (4, 2, 1, 59.100, False), (5, 2, 2, 58.700, True),
             (6, 3, 1, 1.0 * 92.340, False), (7, 3, 2, 91.870, True), (8, 3, 3, 92.510, False),
             (9, 4, 1, 90.980, False), (10, 4, 2, 90.420, True),
             (11, 5, 1, 91.650, True), (12, 5, 2, 92.200, False),
             (13, 6, 1, 61.380, False), (14, 6, 2, 60.950, True), (15, 6, 3, 61.700, False),
             (16, 7, 1, 61.120, True), (17, 7, 2, 61.890, False),
             (18, 8, 1, 59.800, False), (19, 8, 2, 59.350, True), (20, 8, 3, 60.100, False)]),
    }
    # L'ordine rispetta le chiavi esterne (prima le tabelle "padre")
    for table in ["seasons", "vehicles", "tracks", "drivers", "tests",
                  "tires", "setups", "runs", "laps"]:
        sql, rows = seed[table]
        cursor.executemany(sql, rows)

    conn.commit()
    cursor.close()
    conn.close()
    print(" Dati di prova avanzati inseriti correttamente!")

def read_database_data():
    conn = create_connection()
    if not conn:
        return

    cursor = conn.cursor()
    cursor.execute("USE raceup_tdm;")

    print("\n--- GIRI (LAPS) REGISTRATI ---")
    cursor.execute("""
        SELECT l.lap_number, l.lap_time_seconds, l.is_best_lap, r.run_number, d.first_name, d.last_name
        FROM laps l
        JOIN runs r ON l.run_id = r.run_id
        JOIN drivers d ON r.driver_id = d.driver_id;
    """)
    for row in cursor.fetchall():
        best_str = " (BEST)" if row[2] else ""
        print(f"Run #{row[3]} | Pilota: {row[4]} {row[5]} | Giro {row[0]}: {row[1]}s{best_str}")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    initialize_database()
    read_database_data()