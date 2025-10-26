import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from pathlib import Path
import backend_super
import main_super  # módulo principal
from datetime import datetime
import under_super
now = datetime.now()

# --- Botón de Logout ---
def do_logout(session_id, station, root):
    try:
        conn = under_super.get_connection()
        cursor = conn.cursor()
        log_Out = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 🔹 Fecha/hora actual para Log_Out
        log_out_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[DEBUG] log_out_time = {log_out_time}")
        print(f"[DEBUG] session_id   = {session_id}")

# 🔹 Ejecutar el UPDATE
        print("[DEBUG] Ejecutando UPDATE Sesiones...")
        cursor.execute("""
            UPDATE Sesiones
            SET Log_Out = %s, Is_Active = '0'
            WHERE ID_Sesion = %s AND Is_Active = '-1'
        """, (log_out_time, int(session_id)))
        print(f"[DEBUG] Filas afectadas: {cursor.rowcount}")

        print("[DEBUG] UPDATE Sesiones OK ✅")

        # 🔹 Liberar estación (ahora usando Station_Number)
        cursor.execute("""
            UPDATE Estaciones
            SET User_Logged = NULL
            WHERE Station_Number=%s
        """, (station,))
        print("[DEBUG] Estación liberada en tabla Estaciones")

        conn.commit()
        conn.close()

        # Cerrar ventana y volver al login
        try:
            if root.winfo_exists():
                root.destroy()
        except tk.TclError:
            # La ventana ya fue destruida, no hacer nada
            pass
        show_login()

    except Exception as e:
        messagebox.showerror("Error", f"No se pudo cerrar sesión correctamente:\n{e}")
        print(f"[DEBUG] ERROR logout: {e}")
    
    # Verificar si la ventana aún existe antes de destruirla
    try:
        if root.winfo_exists():
            root.destroy()
    except tk.TclError:
        # La ventana ya fue destruida, no hacer nada
        pass
    
    show_login()  # ✅ vuelve al login

def show_login():
    win = tk.Tk()
    win.title("Login")
    win.geometry("500x350")
    win.resizable(False, False)

    # --- Fondo con imagen ---
    FONDO_PATH = Path(r"\\192.168.7.12\Data SIG\Central Station SLC-COLOMBIA\1. Daily Logs - Operators\DataBase\icons\fondo.jpg")
    if not FONDO_PATH.exists():
        raise FileNotFoundError(f"No se encuentra la imagen: {FONDO_PATH}")

    bg_image = Image.open(FONDO_PATH).resize((500, 350))
    bg_photo = ImageTk.PhotoImage(bg_image)

    canvas = tk.Canvas(win, width=500, height=600, highlightthickness=0)
    canvas.pack(fill="both", expand=True)
    canvas.create_image(0, 0, anchor="nw", image=bg_photo)

    # --- Frame para widgets ---
    frame = tk.Frame(win, bg="#1c1c1c")
    frame.place(x=75, y=60, width=350, height=260)

    # --- Rectángulo semi-transparente ---
    rect = canvas.create_rectangle(75, 60, 350, 260, fill="#1c1c1c", outline="#1c1c1c")
    canvas.itemconfig(rect, stipple="gray50")

    # Título
    tk.Label(frame, text="Iniciar Sesión", bg="#1c1c1c", fg="#4aa3ff",
             font=("Segoe UI", 18, "bold")).pack(pady=(9, 12))

    # Usuario
    tk.Label(frame, text="Usuario:", bg="#1c1c1c", fg="white", font=("Segoe UI", 9)).pack(anchor="w", padx=20)
    username_entry = ttk.Entry(frame, width=30)
    username_entry.pack(pady=2, padx=20)

    # Contraseña
    tk.Label(frame, text="Contraseña:", bg="#1c1c1c", fg="white", font=("Segoe UI", 9)).pack(anchor="w", padx=20)
    password_entry = ttk.Entry(frame, show="*", width=30)
    password_entry.pack(pady=2, padx=20)

    # Estacion
    tk.Label(frame, text="Estacion:", bg="#1c1c1c", fg="white", font=("Segoe UI", 9)).pack(anchor="w", padx=20)
    station_entry = ttk.Entry(frame, width=30)
    station_entry.pack(pady=2, padx=20)
    

    # --- Botón personalizado con hover ---
    def on_enter(e):
        login_btn.config(bg="#4aa3ff", fg="white")

    def on_leave(e):
        login_btn.config(bg="#2b2b2b", fg="white")


    def do_login():
        username = username_entry.get()
        password = password_entry.get()
        station_input = station_entry.get()

        # Validar estación
        if not station_input.isdigit():
            messagebox.showerror("Error", "Debes ingresar un número de estación válido")
            return
        station = int(station_input)  # Número lógico de estación

        print(f"[DEBUG] username: {username} ({type(username)})")
        print(f"[DEBUG] password: {password} ({type(password)})")
        print(f"[DEBUG] station: {station} ({type(station)})")

        try:
            conn = under_super.get_connection()
            cursor = conn.cursor()

            # Validar usuario
            cursor.execute(
                    "SELECT Contraseña, Rol FROM user WHERE Nombre_Usuario=%s",
                (username,)
            )
            result = cursor.fetchone()
            print(f"[DEBUG] SELECT user result: {result}")

            if not result:
                messagebox.showerror("Error", "Usuario no encontrado")
                conn.close()
                return

            db_password, role = result
            if db_password != password:
                messagebox.showerror("Error", "Contraseña incorrecta")
                conn.close()
                return

            # Insertar nueva sesión
            cursor.execute("""
                INSERT INTO Sesiones (Nombre_Usuario, Stations_ID, Login_Time, Is_Active)
                VALUES (%s, %s, %s, %s)
            """, (username, station, datetime.now(), "-1"))
            print("[DEBUG] INSERT Sesiones ejecutado")

            # 🔹 Obtener último ID insertado
            cursor.execute("SELECT LAST_INSERT_ID()")
            session_id = cursor.fetchone()[0]
            print(f"[DEBUG] Nuevo Session_ID generado: {session_id}")

            # 🔹 Verificar si la estación ya está ocupada
            cursor.execute("SELECT User_Logged FROM Estaciones WHERE Station_Number=%s", (station,))
            row = cursor.fetchone()

            if row and row[0]:  # Si ya hay alguien logeado
                print(f"❌ La estación {station} ya está siendo usada por {row[0]}")
                return

            # 🔹 Actualizar estación si está libre
            cursor.execute("""INSERT INTO estaciones (User_Logged, Station_Number)
            VALUES (%s, %s)
            """, (username, station))

            print("[DEBUG] INSERT Estaciones ejecutado")
            conn.commit()
            conn.close()

            backend_super.prompt_exit_active_cover(username, win)

            # Mensaje de bienvenida
            messagebox.showinfo("Login", f"Bienvenido {username} ({role})")
            win.destroy()
            main_super.open_main_window(username, station, role, session_id)

        except Exception as e:
            messagebox.showerror("Error", f"Fallo en la conexión a la base de datos:\n{e}")
            print(f"[DEBUG] ERROR: {e}")

    login_btn = tk.Button(frame, text="Ingresar", command=do_login,
                        bg="#2b2b2b", fg="white", font=("Segoe UI", 11, "bold"),
                        relief="flat", padx=20, pady=5)
    login_btn.pack(pady=15)
    login_btn.bind("<Enter>", on_enter)
    login_btn.bind("<Leave>", on_leave)

    # Enter para login
    win.bind("<Return>", lambda event: do_login())

    win.mainloop()


if __name__ == "__main__":
    show_login()


# === Programmatic helpers for cover flow ===
def logout_silent(session_id, station):
    """Logout without showing login UI; updates Sesiones and frees Estaciones."""
    try:
        conn = under_super.get_connection()
        cursor = conn.cursor()
        log_out_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            """
            UPDATE Sesiones
            SET Log_Out = %s, Is_Active = '0'
            WHERE ID_Sesion = %s AND Is_Active = '-1'
            """,
            (log_out_time, int(session_id))
        )
        cursor.execute(
            """
            UPDATE Estaciones
            SET User_Logged = NULL
            WHERE Station_Number=%s
            """,
            (station,)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[ERROR] logout_silent: {e}")
        return False


def auto_login(username, station, password="1234", parent=None, silent=True):
    """Perform login programmatically and open main window, without showing login UI.

    Returns (ok, session_id, role) and opens main_super.open_main_window on success.
    """
    try:
        # Validate station
        if isinstance(station, str):
            if not station.isdigit():
                raise ValueError("Station must be numeric")
            station = int(station)

        conn = under_super.get_connection()
        cursor = conn.cursor()

        # Validate user
        cursor.execute(
            "SELECT Contraseña, Rol FROM user WHERE Nombre_Usuario=%s",
            (username,)
        )
        result = cursor.fetchone()
        if not result:
            raise ValueError("Usuario no encontrado")
        db_password, role = result
        if db_password != password:
            raise ValueError("Contraseña incorrecta")

        # Start session
        cursor.execute(
            """
            INSERT INTO Sesiones (Nombre_Usuario, Stations_ID, Login_Time, Is_Active)
            VALUES (%s, %s, %s, %s)
            """,
            (username, station, datetime.now(), "-1")
        )
        cursor.execute("SELECT LAST_INSERT_ID()")
        session_id = cursor.fetchone()[0]

        # Check station availability
        cursor.execute("SELECT User_Logged FROM Estaciones WHERE Station_Number=%s", (station,))
        row = cursor.fetchone()
        if row and row[0]:
            # Occupied
            conn.commit(); conn.close()
            raise RuntimeError(f"La estación {station} ya está siendo usada por {row[0]}")

        # Update station status (insert as in UI flow)
        cursor.execute(
            """INSERT INTO estaciones (User_Logged, Station_Number)
            VALUES (%s, %s)
            """,
            (username, station)
        )
        conn.commit(); conn.close()

        # Open main window
        try:
            if not silent:
                messagebox.showinfo("Login", f"Bienvenido {username} ({role})")
        except Exception:
            pass

        main_super.open_main_window(username, station, role, session_id)
        return True, session_id, role
    except Exception as e:
        print(f"[ERROR] auto_login: {e}")
        try:
            messagebox.showerror("Auto Login", str(e), parent=parent)
        except Exception:
            pass
        return False, None, None
