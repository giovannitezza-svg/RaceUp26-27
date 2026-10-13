-- Creazione del database (se non esiste già)
CREATE DATABASE IF NOT EXISTS raceup_tdm;
USE raceup_tdm;

-- 1. Tabella delle Stagioni (es. 2025, 2026)
CREATE TABLE IF NOT EXISTS seasons (
    season_id INT AUTO_INCREMENT PRIMARY KEY,
    year INT NOT NULL UNIQUE,
    description TEXT
);
-- 2. Tabella dei Veicoli (generazioni di auto)
CREATE TABLE IF NOT EXISTS vehicles (
    vehicle_id INT AUTO_INCREMENT PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    generation VARCHAR(50),
    notes TEXT
);
-- 3. Tabella delle Piste (Track Locations e Layout)
CREATE TABLE IF NOT EXISTS tracks (
    track_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    layout_name VARCHAR(50),
    length_meters DECIMAL(8, 2) NOT NULL,
    activity_type VARCHAR(50) -- es. Skidpad, Endurance, Autocross
);
-- 4. Tabella dei Piloti
CREATE TABLE IF NOT EXISTS drivers (
    driver_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    license_number VARCHAR(50)
);
-- 5. Tabella dei Test (L'hub centrale della giornata di prova)
CREATE TABLE IF NOT EXISTS tests (
    test_id INT AUTO_INCREMENT PRIMARY KEY,
    season_id INT NOT NULL,
    vehicle_id INT NOT NULL,
    track_id INT NOT NULL,
    test_date DATE NOT NULL,
    objectives TEXT,
    status VARCHAR(50), -- es. Planned, Completed
    problems_encountered TEXT,
    conclusions TEXT,
    FOREIGN KEY (season_id) REFERENCES seasons(season_id),
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(vehicle_id),
    FOREIGN KEY (track_id) REFERENCES tracks(track_id)
);
-- 6. Tabella delle Gomme (Tires) e set fisici
CREATE TABLE IF NOT EXISTS tires (
    tire_id INT AUTO_INCREMENT PRIMARY KEY,
    compound VARCHAR(50) NOT NULL, -- es. Slick, Wet
    set_identifier VARCHAR(50) NOT NULL UNIQUE, -- es. SET-01
    status VARCHAR(50) DEFAULT 'New' -- New, Used, Worn
);
-- 7. Tabella dei Setup della Vettura (Sospensioni, angoli, ecc.)
CREATE TABLE IF NOT EXISTS setups (
    setup_id INT AUTO_INCREMENT PRIMARY KEY,
    description VARCHAR(100),
    spring_rate_fl DECIMAL(6,2), -- Anteriore sinistra
    spring_rate_fr DECIMAL(6,2), -- Anteriore destra
    spring_rate_rl DECIMAL(6,2), -- Posteriore sinistra
    spring_rate_rr DECIMAL(6,2), -- Posteriore destra
    static_camber DECIMAL(4,2),
    toe_settings DECIMAL(4,2),
    power_limit_kw INT,
    notes TEXT
);
-- 8. Tabella dei Run (Sessioni in pista)
CREATE TABLE IF NOT EXISTS runs (
    run_id INT AUTO_INCREMENT PRIMARY KEY,
    test_id INT NOT NULL,
    driver_id INT NOT NULL,
    setup_id INT NOT NULL,
    tire_id INT NOT NULL,
    run_number INT NOT NULL,
    is_planned BOOLEAN DEFAULT TRUE, -- Per distinguere pianificato vs effettivo
    ambient_temp DECIMAL(4,1),
    asphalt_temp DECIMAL(4,1),
    status VARCHAR(50), -- Completed, Cancelled, Modified
    FOREIGN KEY (test_id) REFERENCES tests(test_id),
    FOREIGN KEY (driver_id) REFERENCES drivers(driver_id),
    FOREIGN KEY (setup_id) REFERENCES setups(setup_id),
    FOREIGN KEY (tire_id) REFERENCES tires(tire_id)
);
-- 9. Tabella dei Giri (Laps)
CREATE TABLE IF NOT EXISTS laps (
    lap_id INT AUTO_INCREMENT PRIMARY KEY,
    run_id INT NOT NULL,
    lap_number INT NOT NULL,
    lap_time_seconds DECIMAL(7,3) NOT NULL, -- Tempo in secondi (es. 58.452)
    penalty_seconds DECIMAL(5,2) DEFAULT 0.00,
    is_best_lap BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
);
