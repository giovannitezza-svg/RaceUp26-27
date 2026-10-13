# Thought Process

This document is intended for the candidate to explain the choices made while
completing the Test Data Manager assignment and why those choices were
appropriate.


Race UP Team — Test Data Engineering
Domain Model and ER/UML Architecture
The model follows a strict operational hierarchy: Season - Test - Run - Lap.
To ensure stability and performance, all tables use auto-incrementing surrogate primary keys (*_id), accompanied by logical uniqueness constraints on identifiers and licenses. To avoid flat and redundant tables, setup parameters (setups) and tires (tires) have been normalized into dedicated entities linked to runs via foreign keys. The application also handles free-text input for descriptive fields (e.g., setup configurations and compounds), which the backend automatically maps and persists.

Technology Stack and Interface
The application relies on a local MySQL backend and a Python graphical interface (tkinter), interfaced through secure parameterized queries.
The interface adopts a drill-down navigation:
-Main Screen: Displays the list of Tests and an Advanced Historical Query engine to filter data by crossing drivers, compounds, and asphalt temperatures.
-Detail Dashboard:Allows targeted visualization of Runs, Laps, Vehicles, and Drivers for the individual test, integrating operational modules for the rapid insertion of new data with dynamic view updates.

Historical Spreadsheet Data Migration Strategy
For the future integration of legacy heterogeneous spreadsheets, an automated import strategy has been defined:
-Parsing and Sanitization: Utilizing Python libraries (pandas) to extract data from .xlsx/.csv files, convert time formats into SI units, and eliminate anomalous values.
-Transactional Hierarchical Insertion: Sequential insertion to respect Foreign Key constraints, first populating independent entities (seasons, tracks, vehicles, drivers with anti-duplication checks), then support entities (setups, tires), and finally tests, runs, and laps.


The password is written in the code (password='password123'). Whoever receives the files will need to have a MySQL [database] with the same username and password, or change it in database.py.


erDiagram
    SEASONS ||--o{ TESTS : "contains"
    TRACKS ||--o{ TESTS : "hosts"
    VEHICLES ||--o{ TESTS : "used in"
    
    TESTS ||--o{ RUNS : "includes"
    DRIVERS ||--o{ RUNS : "drives"
    SETUPS ||--o{ RUNS : "configured with"
    TIRES ||--o{ RUNS : "fitted with"
    
    RUNS ||--o{ LAPS : "records"

    SEASONS {
        int season_id PK
        int year "Year (e.g., 2026)"
    }
    TRACKS {
        int track_id PK
        varchar name "Track Name"
    }
    VEHICLES {
        int vehicle_id PK
        varchar model_name "Car Model"
    }
    DRIVERS {
        int driver_id PK
        varchar first_name "Driver First Name"
        varchar last_name "Driver Last Name"
    }
    TESTS {
        int test_id PK
        date test_date "Test Date"
        varchar status "Status"
    }
    TIRES {
        int tire_id PK
        varchar compound "Compound (e.g., Slick)"
    }
    SETUPS {
        int setup_id PK
        text description "Setup Description"
    }
    RUNS {
        int run_id PK
        int run_number "Run Number"
        decimal asphalt_temp "Asphalt Temp."
    }
    LAPS {
        int lap_id PK
        int lap_number "Lap Number"
        decimal lap_time_seconds "Lap Time (s)"
        boolean is_best_lap "Best Lap"
    }

