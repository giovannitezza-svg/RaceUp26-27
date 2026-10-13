import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
from mysql.connector import Error


def create_connection():
    """Create a connection to the MySQL server"""
    try:
        return mysql.connector.connect(
            host='localhost',
            user='root',
            password='password123'
        )
    except Error as e:
        messagebox.showerror("Database Error", f"Unable to connect to MySQL:\n{e}")
        return None


def load_table_data(tree, query, view_name, action_frame, refresh_callback, params=None):
    """Load data into the main table and manage the contextual buttons"""
    for item in tree.get_children():
        tree.delete(item)

    for widget in action_frame.winfo_children():
        widget.destroy()

    conn = create_connection()
    if not conn:
        return

    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute("USE raceup_tdm;")
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        columns = [desc[0] for desc in cursor.description]
        tree["columns"] = columns
        tree["show"] = "headings"

        for col in columns:
            tree.heading(col, text=col.upper())
            tree.column(col, width=130, anchor="center")

        for row in cursor.fetchall():
            tree.insert("", "end", values=row)

    except Error as e:
        messagebox.showerror("Query Error", f"Error while running the query:\n{e}")
    finally:
        if cursor: cursor.close()
        conn.close()

    if view_name == "tests":
        tk.Button(
            action_frame, text="+ Add Test", bg="#1976D2", fg="white",
            font=("Arial", 10, "bold"), command=lambda: open_add_test_window(refresh_callback)
        ).pack(side=tk.LEFT, padx=5)

        info_lbl = tk.Label(action_frame, text="💡 Double-click a test to open the detail and management panel",
                            fg="#555", font=("Arial", 9, "italic"))
        info_lbl.pack(side=tk.LEFT, padx=15)

    elif view_name == "advanced_query":
        build_advanced_search_form(action_frame, tree, refresh_callback)


def build_advanced_search_form(frame, tree, refresh_callback):
    """Create the filter fields for the advanced historical queries"""
    tk.Label(frame, text="Driver Filter:", font=("Arial", 9)).pack(side=tk.LEFT, padx=2)
    e_driver = tk.Entry(frame, width=12); e_driver.pack(side=tk.LEFT, padx=2)

    tk.Label(frame, text="Tire Compound:", font=("Arial", 9)).pack(side=tk.LEFT, padx=2)
    e_tire = tk.Entry(frame, width=10); e_tire.pack(side=tk.LEFT, padx=2)

    tk.Label(frame, text="Asphalt Min (°C):", font=("Arial", 9)).pack(side=tk.LEFT, padx=2)
    e_tmin = tk.Entry(frame, width=6); e_tmin.pack(side=tk.LEFT, padx=2); e_tmin.insert(0, "0")

    tk.Label(frame, text="Max (°C):", font=("Arial", 9)).pack(side=tk.LEFT, padx=2)
    e_tmax = tk.Entry(frame, width=6); e_tmax.pack(side=tk.LEFT, padx=2); e_tmax.insert(0, "100")

    def execute_filter():
        driver_filter = f"%{e_driver.get().strip()}%"
        tire_filter = f"%{e_tire.get().strip()}%"
        try:
            t_min = float(e_tmin.get().replace(",", "."))
            t_max = float(e_tmax.get().replace(",", "."))
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numeric values for the temperatures.")
            return

        query = """
            SELECT r.run_id, t.test_id, CONCAT(d.first_name, ' ', d.last_name) AS driver,
                   ti.compound AS tire, r.asphalt_temp, r.status
            FROM runs r
            JOIN drivers d ON r.driver_id = d.driver_id
            JOIN tires ti ON r.tire_id = ti.tire_id
            JOIN tests t ON r.test_id = t.test_id
            WHERE (d.last_name LIKE %s OR d.first_name LIKE %s)
              AND ti.compound LIKE %s
              AND r.asphalt_temp BETWEEN %s AND %s;
        """
        load_table_data(tree, query, "advanced_query", frame, refresh_callback,
                        params=(driver_filter, driver_filter, tire_filter, t_min, t_max))

    tk.Button(frame, text="🔍 Filter", bg="#7B1FA2", fg="white", font=("Arial", 9, "bold"),
              command=execute_filter).pack(side=tk.LEFT, padx=10)


def open_test_details(event, tree):
    """Open the test detail dashboard with options to view and add data"""
    selected_item = tree.selection()
    if not selected_item:
        return

    item_data = tree.item(selected_item)
    test_id = item_data['values'][0]

    win = tk.Toplevel()
    win.title(f"Test Detail Dashboard #{test_id}")
    win.geometry("1020x550")
    win.grab_set()

    tk.Label(win, text=f"Test Session Overview - ID: {test_id}", font=("Arial", 14, "bold"),
             fg="#1976D2").pack(pady=8)

    control_panel = tk.Frame(win)
    control_panel.pack(pady=5, fill=tk.X, padx=15)

    view_btns_frame = tk.Frame(control_panel)
    view_btns_frame.pack(side=tk.LEFT)

    action_btns_frame = tk.Frame(control_panel)
    action_btns_frame.pack(side=tk.RIGHT)

    frame = tk.Frame(win)
    frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

    scroll_y = ttk.Scrollbar(frame, orient=tk.VERTICAL)
    scroll_x = ttk.Scrollbar(frame, orient=tk.HORIZONTAL)

    detail_tree = ttk.Treeview(frame, yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
    scroll_y.config(command=detail_tree.yview)
    scroll_x.config(command=detail_tree.xview)

    scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
    scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
    detail_tree.pack(fill=tk.BOTH, expand=True)

    current_view = {"type": "runs_laps"}

    def load_sub_view(query_type):
        current_view["type"] = query_type
        for item in detail_tree.get_children():
            detail_tree.delete(item)

        conn = create_connection()
        if not conn: return
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute("USE raceup_tdm;")

            if query_type == "runs_laps":
                query = """
                    SELECT r.run_number,
                           IFNULL(CONCAT(d.first_name, ' ', d.last_name), 'N/A') AS driver,
                           IFNULL(s.description, 'N/A') AS setup,
                           IFNULL(t.compound, 'N/A') AS tire,
                           IFNULL(r.asphalt_temp, '-') AS asphalt_temp,
                           IFNULL(l.lap_number, '-') AS lap_num,
                           IFNULL(l.lap_time_seconds, '-') AS lap_time,
                           IFNULL(l.is_best_lap, '-') AS best
                    FROM runs r
                    LEFT JOIN drivers d ON r.driver_id = d.driver_id
                    LEFT JOIN setups s ON r.setup_id = s.setup_id
                    LEFT JOIN tires t ON r.tire_id = t.tire_id
                    LEFT JOIN laps l ON r.run_id = l.run_id
                    WHERE r.test_id = %s
                    ORDER BY r.run_number, l.lap_number;
                """
                cursor.execute(query, (test_id,))
            elif query_type == "vehicles":
                query = """
                    SELECT v.vehicle_id, v.model_name, v.generation, v.notes
                    FROM vehicles v;
                """
                cursor.execute(query)
            elif query_type == "drivers":
                query = """
                    SELECT d.driver_id, d.first_name, d.last_name, d.license_number
                    FROM drivers d;
                """
                cursor.execute(query)

            columns = [desc[0] for desc in cursor.description]
            detail_tree["columns"] = columns
            detail_tree["show"] = "headings"

            for col in columns:
                detail_tree.heading(col, text=col.upper())
                detail_tree.column(col, width=120, anchor="center")

            rows = cursor.fetchall()
            if not rows:
                detail_tree["columns"] = ["NOTICE"]
                detail_tree.heading("NOTICE", text="STATUS")
                detail_tree.column("NOTICE", width=400, anchor="center")
                detail_tree.insert("", "end", values=("No data recorded in this category.",))
            else:
                for row in rows:
                    detail_tree.insert("", "end", values=row)

        except Error as err:
            messagebox.showerror("Error", f"{err}", parent=win)
        finally:
            if cursor: cursor.close()
            conn.close()

    refresh_current_view = lambda: load_sub_view(current_view["type"])

    # Internal view buttons
    tk.Button(view_btns_frame, text="🏁 Runs & Laps", font=("Arial", 9, "bold"),
              command=lambda: load_sub_view("runs_laps"), width=12).pack(side=tk.LEFT, padx=2)
    tk.Button(view_btns_frame, text="🏎️ Vehicles", font=("Arial", 9, "bold"),
              command=lambda: load_sub_view("vehicles"), width=10).pack(side=tk.LEFT, padx=2)
    tk.Button(view_btns_frame, text="👤 Drivers", font=("Arial", 9, "bold"),
              command=lambda: load_sub_view("drivers"), width=10).pack(side=tk.LEFT, padx=2)

    # Action buttons, linked to the dynamic refresh of the active view
    tk.Button(action_btns_frame, text="+ Driver", bg="#2E7D32", fg="white", font=("Arial", 9, "bold"),
              command=lambda: open_add_driver_window(refresh_current_view)).pack(side=tk.LEFT, padx=2)
    tk.Button(action_btns_frame, text="+ Vehicle", bg="#0288D1", fg="white", font=("Arial", 9, "bold"),
              command=lambda: open_add_vehicle_window(refresh_current_view)).pack(side=tk.LEFT, padx=2)
    tk.Button(action_btns_frame, text="+ Lap", bg="#E65100", fg="white", font=("Arial", 9, "bold"),
              command=lambda: open_add_full_lap_window(test_id, refresh_current_view)).pack(side=tk.LEFT, padx=2)

    load_sub_view("runs_laps")


def open_add_driver_window(refresh_callback):
    win = tk.Toplevel()
    win.title("Add New Driver")
    win.geometry("350x300"); win.grab_set()
    tk.Label(win, text="New Driver", font=("Arial", 12, "bold")).pack(pady=10)
    tk.Label(win, text="First Name:").pack(anchor="w", padx=30)
    e_name = tk.Entry(win, width=30); e_name.pack(pady=5, padx=30)
    tk.Label(win, text="Last Name:").pack(anchor="w", padx=30)
    e_surname = tk.Entry(win, width=30); e_surname.pack(pady=5, padx=30)
    tk.Label(win, text="License Number:").pack(anchor="w", padx=30)
    e_license = tk.Entry(win, width=30); e_license.pack(pady=5, padx=30)

    def save():
        if not e_name.get().strip() or not e_surname.get().strip():
            messagebox.showerror("Error", "First name and last name are required!", parent=win)
            return
        conn = create_connection()
        if not conn: return
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute("USE raceup_tdm;")
            cursor.execute("INSERT INTO drivers (first_name, last_name, license_number) VALUES (%s, %s, %s);",
                           (e_name.get().strip(), e_surname.get().strip(), e_license.get().strip() or None))
            conn.commit()
            messagebox.showinfo("Success", "Driver added successfully!", parent=win)
            win.destroy()
            refresh_callback()
        except Error as err:
            messagebox.showerror("Database Error", f"{err}", parent=win)
        finally:
            if cursor: cursor.close()
            conn.close()

    tk.Button(win, text="Save Driver", bg="#2E7D32", fg="white", font=("Arial", 10, "bold"),
              command=save).pack(pady=15)


def open_add_vehicle_window(refresh_callback):
    win = tk.Toplevel()
    win.title("Add New Vehicle")
    win.geometry("350x300"); win.grab_set()
    tk.Label(win, text="New Vehicle", font=("Arial", 12, "bold")).pack(pady=10)
    tk.Label(win, text="Model:").pack(anchor="w", padx=30)
    e_model = tk.Entry(win, width=30); e_model.pack(pady=5, padx=30)
    tk.Label(win, text="Generation (e.g. 2026):").pack(anchor="w", padx=30)
    e_gen = tk.Entry(win, width=30); e_gen.pack(pady=5, padx=30)
    tk.Label(win, text="Notes:").pack(anchor="w", padx=30)
    e_notes = tk.Entry(win, width=30); e_notes.pack(pady=5, padx=30)

    def save():
        if not e_model.get().strip():
            messagebox.showerror("Error", "The model is required!", parent=win)
            return
        conn = create_connection()
        if not conn: return
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute("USE raceup_tdm;")
            cursor.execute("INSERT INTO vehicles (model_name, generation, notes) VALUES (%s, %s, %s);",
                           (e_model.get().strip(), e_gen.get().strip() or None, e_notes.get().strip() or None))
            conn.commit()
            messagebox.showinfo("Success", "Vehicle added successfully!", parent=win)
            win.destroy()
            refresh_callback()
        except Error as err:
            messagebox.showerror("Database Error", f"{err}", parent=win)
        finally:
            if cursor: cursor.close()
            conn.close()

    tk.Button(win, text="Save Vehicle", bg="#0288D1", fg="white", font=("Arial", 10, "bold"),
              command=save).pack(pady=15)


def open_add_test_window(refresh_callback):
    win = tk.Toplevel()
    win.title("Register New Test")
    win.geometry("400x400"); win.grab_set()
    tk.Label(win, text="New Test Session", font=("Arial", 12, "bold")).pack(pady=10)

    tk.Label(win, text="Season (year, e.g. 2026):").pack(anchor="w", padx=30)
    e_season = tk.Entry(win, width=30); e_season.pack(pady=2, padx=30)

    tk.Label(win, text="Track:").pack(anchor="w", padx=30)
    e_track = tk.Entry(win, width=30); e_track.pack(pady=2, padx=30)

    tk.Label(win, text="Date (YYYY-MM-DD):").pack(anchor="w", padx=30)
    e_date = tk.Entry(win, width=30); e_date.pack(pady=2, padx=30); e_date.insert(0, "2026-03-26")

    tk.Label(win, text="Objectives:").pack(anchor="w", padx=30)
    e_obj = tk.Entry(win, width=30); e_obj.pack(pady=2, padx=30)

    tk.Label(win, text="Status (e.g. Completed):").pack(anchor="w", padx=30)
    e_status = tk.Entry(win, width=30); e_status.pack(pady=2, padx=30); e_status.insert(0, "Completed")

    def save():
        season_txt = e_season.get().strip()
        track_txt = e_track.get().strip()

        if not season_txt or not track_txt:
            messagebox.showerror("Error", "Season and Track are required!", parent=win)
            return
        try:
            season_year = int(season_txt)
        except ValueError:
            messagebox.showerror("Error", "The season must be a numeric year (e.g. 2026).", parent=win)
            return

        conn = create_connection()
        if not conn: return
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute("USE raceup_tdm;")

            # SEASON: look it up by year, create it if it does not exist
            cursor.execute("SELECT season_id FROM seasons WHERE year = %s;", (season_year,))
            row = cursor.fetchone()
            if row:
                season_id = row[0]
            else:
                cursor.execute("INSERT INTO seasons (year) VALUES (%s);", (season_year,))
                season_id = cursor.lastrowid

            # TRACK: look it up by name, create it if it does not exist
            cursor.execute("SELECT track_id FROM tracks WHERE name = %s;", (track_txt,))
            row = cursor.fetchone()
            if row:
                track_id = row[0]
            else:
                # length_meters is NOT NULL: use 0 until the real length is set
                cursor.execute("INSERT INTO tracks (name, length_meters) VALUES (%s, 0);", (track_txt,))
                track_id = cursor.lastrowid

            # VEHICLE: no longer in the form, use the first available one
            cursor.execute("SELECT vehicle_id FROM vehicles ORDER BY vehicle_id LIMIT 1;")
            row = cursor.fetchone()
            if not row:
                messagebox.showerror("Error", "No vehicle in the database. Add one first.", parent=win)
                return
            vehicle_id = row[0]

            cursor.execute("""
                INSERT INTO tests (season_id, vehicle_id, track_id, test_date, objectives, status)
                VALUES (%s, %s, %s, %s, %s, %s);
            """, (season_id, vehicle_id, track_id, e_date.get().strip(), e_obj.get().strip(), e_status.get().strip()))
            conn.commit()
            messagebox.showinfo("Success", "Test registered successfully!", parent=win)
            win.destroy(); refresh_callback()
        except Error as err:
            conn.rollback()
            messagebox.showerror("Error", f"{err}", parent=win)
        finally:
            if cursor: cursor.close()
            conn.close()

    tk.Button(win, text="Save Test", bg="#1976D2", fg="white", font=("Arial", 10, "bold"),
              command=save).pack(pady=15)


def open_add_full_lap_window(test_id, refresh_callback):
    """Open the popup to add a lap, asking for Driver, Setup, Tire, Run and Asphalt temperature"""

    # Load the existing drivers for the dropdown menu
    conn = create_connection()
    if not conn: return
    drivers = []
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute("USE raceup_tdm;")
        cursor.execute("SELECT driver_id, first_name, last_name FROM drivers ORDER BY last_name, first_name;")
        drivers = [f"{r[0]} - {r[1]} {r[2]}" for r in cursor.fetchall()]
    except Error as err:
        messagebox.showerror("Database Error", f"{err}")
        return
    finally:
        if cursor: cursor.close()
        conn.close()

    if not drivers:
        messagebox.showerror("Error", "No driver in the database. Add one with the '+ Driver' button.")
        return

    win = tk.Toplevel()
    win.title(f"Register Lap for Test #{test_id}")
    win.geometry("420x540")
    win.grab_set()

    tk.Label(win, text=f"Register Lap & Run (Test #{test_id})", font=("Arial", 12, "bold")).pack(pady=10)

    tk.Label(win, text="Driver:", font=("Arial", 9)).pack(anchor="w", padx=30)
    cb_driver = ttk.Combobox(win, values=drivers, state="readonly", width=32)
    cb_driver.pack(pady=2, padx=30)
    cb_driver.current(0)

    tk.Label(win, text="Setup Description (free text):", font=("Arial", 9)).pack(anchor="w", padx=30)
    e_setup_desc = tk.Entry(win, width=35); e_setup_desc.pack(pady=2, padx=30); e_setup_desc.insert(0, "Standard Setup")

    tk.Label(win, text="Tire Compound (free text):", font=("Arial", 9)).pack(anchor="w", padx=30)
    e_tire_comp = tk.Entry(win, width=35); e_tire_comp.pack(pady=2, padx=30); e_tire_comp.insert(0, "Slick Soft")

    tk.Label(win, text="Asphalt Temperature in °C (e.g. 35.5):", font=("Arial", 9)).pack(anchor="w", padx=30)
    e_asphalt = tk.Entry(win, width=35); e_asphalt.pack(pady=2, padx=30)

    tk.Label(win, text="Run Number (e.g. 1):", font=("Arial", 9)).pack(anchor="w", padx=30)
    e_run_num = tk.Entry(win, width=35); e_run_num.pack(pady=2, padx=30); e_run_num.insert(0, "1")

    tk.Label(win, text="Lap Number (e.g. 1):", font=("Arial", 9)).pack(anchor="w", padx=30)
    e_lapnum = tk.Entry(win, width=35); e_lapnum.pack(pady=2, padx=30)

    tk.Label(win, text="Time in seconds (e.g. 58.120):", font=("Arial", 9)).pack(anchor="w", padx=30)
    e_time = tk.Entry(win, width=35); e_time.pack(pady=2, padx=30)

    is_best_var = tk.BooleanVar()
    tk.Checkbutton(win, text="Best Lap", variable=is_best_var).pack(pady=5, anchor="w", padx=30)

    def read_number(entry, label, cast, allow_negative=False):
        """Read a numeric field and say exactly what is wrong with it"""
        raw = entry.get().strip().replace(",", ".")
        if not raw:
            raise ValueError(f"The field '{label}' is empty.")
        try:
            value = cast(raw)
        except ValueError:
            raise ValueError(f"The field '{label}' is not a valid number (you entered: '{raw}').")
        if not allow_negative and value <= 0:
            raise ValueError(f"The field '{label}' must be greater than zero.")
        return value

    def save():
        try:
            driver_id = int(cb_driver.get().split(" - ")[0])
            run_number = read_number(e_run_num, "Run Number", int)
            lap_number = read_number(e_lapnum, "Lap Number", int)
            lap_time = read_number(e_time, "Time", float)
            asphalt_temp = read_number(e_asphalt, "Asphalt Temperature", float, allow_negative=True)
            if not -50 <= asphalt_temp <= 100:
                raise ValueError("The asphalt temperature must be between -50 and 100 °C.")
        except ValueError as err:
            messagebox.showerror("Invalid Data", str(err), parent=win)
            return

        conn = create_connection()
        if not conn: return
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute("USE raceup_tdm;")

            # Check whether the run already exists for this test, number and driver
            cursor.execute("""
                SELECT run_id FROM runs
                WHERE test_id = %s AND run_number = %s AND driver_id = %s;
            """, (test_id, run_number, driver_id))
            run_result = cursor.fetchone()

            if run_result:
                # The run already exists: update the asphalt temperature and add the lap
                run_id = run_result[0]
                cursor.execute("UPDATE runs SET asphalt_temp = %s WHERE run_id = %s;",
                               (asphalt_temp, run_id))
            else:
                # The run does not exist: create the setup and the tire first
                cursor.execute("INSERT INTO setups (description) VALUES (%s);",
                               (e_setup_desc.get().strip() or "Default Setup",))
                setup_id = cursor.lastrowid

                set_code = f"SET-{test_id}-{run_number}-{setup_id}"
                cursor.execute("INSERT INTO tires (compound, set_identifier, status) VALUES (%s, %s, 'Available');",
                               (e_tire_comp.get().strip() or "Slick", set_code))
                tire_id = cursor.lastrowid

                # NB: no vehicle_id here, the vehicle is already linked to the test
                cursor.execute("""
                    INSERT INTO runs (test_id, driver_id, setup_id, tire_id, run_number,
                                      is_planned, asphalt_temp, ambient_temp, status)
                    VALUES (%s, %s, %s, %s, %s, TRUE, %s, 22.0, 'Completed');
                """, (test_id, driver_id, setup_id, tire_id, run_number, asphalt_temp))
                run_id = cursor.lastrowid

            cursor.execute("""
                INSERT INTO laps (run_id, lap_number, lap_time_seconds, is_best_lap)
                VALUES (%s, %s, %s, %s);
            """, (run_id, lap_number, lap_time, is_best_var.get()))

            conn.commit()
            messagebox.showinfo("Success", "Lap saved successfully!", parent=win)
            win.destroy()
            refresh_callback()
        except Error as err:
            conn.rollback()
            messagebox.showerror("Database Error", f"{err}", parent=win)
        finally:
            if cursor: cursor.close()
            conn.close()

    tk.Button(win, text="Save Lap & Run", bg="#E65100", fg="white",
              font=("Arial", 10, "bold"), command=save).pack(pady=15)


def create_gui():
    root = tk.Tk()
    root.title("Race UP Team - Test Data Manager")
    root.geometry("1050x600")

    title_label = tk.Label(root, text="Race UP Test Data Manager", font=("Arial", 16, "bold"))
    title_label.pack(pady=10)

    nav_frame = tk.Frame(root)
    nav_frame.pack(pady=5)

    action_frame = tk.Frame(root)
    action_frame.pack(pady=5, fill=tk.X, padx=25)

    table_frame = tk.Frame(root)
    table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

    tree_scroll_y = ttk.Scrollbar(table_frame, orient=tk.VERTICAL)
    tree_scroll_x = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL)

    tree = ttk.Treeview(table_frame, yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)
    tree_scroll_y.config(command=tree.yview); tree_scroll_x.config(command=tree.xview)
    tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y); tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
    tree.pack(fill=tk.BOTH, expand=True)

    tree.bind("<Double-1>", lambda event: open_test_details(event, tree))

    q_tests = """
        SELECT t.test_id, s.year, v.model_name, tr.name AS track, t.test_date, t.status
        FROM tests t
        JOIN seasons s ON t.season_id = s.season_id
        JOIN vehicles v ON t.vehicle_id = v.vehicle_id
        JOIN tracks tr ON t.track_id = tr.track_id;
    """

    q_advanced_default = """
        SELECT r.run_id, t.test_id, CONCAT(d.first_name, ' ', d.last_name) AS driver,
               ti.compound AS tire, r.asphalt_temp, r.status
        FROM runs r
        JOIN drivers d ON r.driver_id = d.driver_id
        JOIN tires ti ON r.tire_id = ti.tire_id
        JOIN tests t ON r.test_id = t.test_id;
    """

    refresh_tests = lambda: load_table_data(tree, q_tests, "tests", action_frame, refresh_tests)
    refresh_advanced = lambda: load_table_data(tree, q_advanced_default, "advanced_query", action_frame, refresh_advanced)

    tk.Button(nav_frame, text="📋 View Tests", font=("Arial", 10, "bold"), command=refresh_tests,
              width=18).pack(side=tk.LEFT, padx=5)
    tk.Button(nav_frame, text="🔍 Historical Queries", font=("Arial", 10, "bold"), bg="#E1BEE7",
              command=refresh_advanced, width=18).pack(side=tk.LEFT, padx=5)

    refresh_tests()
    root.mainloop()


if __name__ == "__main__":
    create_gui()
