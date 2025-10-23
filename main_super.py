import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
from tkinter import ttk, messagebox, simpledialog
import backend_super
import login  # ✅ para volver al login después de logout
import under
import json
import os



def open_main_window(username, station, role, session_id):
    global global_root, global_station
    root = tk.Tk()
    # al inicio del archivo
    global_root = None
    global_station = None
    root.title(f"Panel Principal - {username} ({role})")
    width, height = 320, 400
    root.geometry(f"{width}x{height}+0+{root.winfo_screenheight()-height}")
    root.configure(bg="#2b2b2b")
    root.resizable(False, False)

        # Fondo con puntos + texto
    bg = backend_super.create_background(root)

    # Frame principal para los botones (lo pongo encima del fondo)
    frame = tk.Frame(root, bg="#353c47")
    frame.place(x=15, y=70, width=width-40, height=height-205)

 # =========================
    # Botón Info redondo con hover
    # =========================
    def info():
        backend_super.show_info()

    canvas_btn = tk.Canvas(root, width=30, height=30, bg="#2b2b2b", highlightthickness=0)
    canvas_btn.place(x=8, y=3)

    # Dibujar círculo
    circle = canvas_btn.create_oval(2, 2, 26, 26, fill="#314052", outline="#1e3a5f")

    # Texto "i" en el centro
    text = canvas_btn.create_text(14, 13, text="i", fill="white", font=("Segoe UI", 12, "bold"))

    # Evento de click
    canvas_btn.tag_bind(circle, "<Button-1>", lambda e: info())
    canvas_btn.tag_bind(text, "<Button-1>", lambda e: info())

    # =========================
    # Efecto hover
    # =========================
    def on_enter(event):
        canvas_btn.itemconfig(circle, fill="#54657a")   # color más claro al pasar el mouse

    def on_leave(event):
        canvas_btn.itemconfig(circle, fill="#314052")   # vuelve al color original

    canvas_btn.tag_bind(circle, "<Enter>", on_enter)
    canvas_btn.tag_bind(circle, "<Leave>", on_leave)
    canvas_btn.tag_bind(text, "<Enter>", on_enter)
    canvas_btn.tag_bind(text, "<Leave>", on_leave)

    # Canvas de fondo
    canvas = tk.Canvas(root, width=width-8, height=height-145, bg="#2b2b2b", highlightthickness=0)
    canvas.pack(pady=30)

    def create_rounded_rect(canvas, x1, y1, x2, y2, radius=15, fill="#353c47", outline="", width=0):
        points = [
            x1+radius, y1, x2-radius, y1, x2, y1, x2, y1+radius,
            x2, y2-radius, x2, y2, x2-radius, y2, x1+radius, y2,
            x1, y2, x1, y2-radius, x1, y1+radius, x1, y1
        ]
        return canvas.create_polygon(points, smooth=True, fill=fill, outline=outline, width=width)

    create_rounded_rect(canvas, 10, 10, width-10, height-155, radius=20, fill="#1a1a1a")
    create_rounded_rect(canvas, 6, 6, width-14, height-150, radius=15, fill="#353c47", outline="#1e3a5f", width=2)

    frame = tk.Frame(canvas, bg="#353c47")
    frame.place(x=15, y=20, width=width-35, height=height-186)

   
    # Estilo botones
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Card.TButton", background="#3f4a5a", foreground="#d0d0d0",
                    font=("Segoe UI", 11, "bold"), relief="flat", padding=10)
    style.map("Card.TButton", background=[("active", "#54657a")], foreground=[("active", "#a3c9f9")])
    
    global login_time
    login_time = datetime.now()

    def do_export():
        try:
            export_path = backend_super.export_events_to_excel_from_db(
                user_name=username,
                conn_str=under.get_connection,  # ✅ correcto
                output_folder=r"\\192.168.7.12\Data SIG\Central Station SLC-COLOMBIA\1. Daily Logs - Operators\2025\09. September\PRUEBA"
            )
            messagebox.showinfo("Éxito", f"Eventos exportados a:\n{export_path}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar:\n{e}")
    

    # ------------------------------
    # Definir TODOS los botones
    # ------------------------------
    all_buttons = {
        "Register": ("add.png", lambda: backend_super.open_register_form(root, username)),
        "Event": ("event.png", lambda: backend_super.show_events(username)),
        "Report": ("report.png", lambda: backend_super.open_report_window(username)),
        "Cover": ("settings.png", lambda: backend_super.cover_mode(session_id, station, root, username)),
        "Extra": ("extra.png", backend_super.open_admin_window),
        "Rol": ("rol.png", backend_super.open_rol_window),
        "View": ("view.png", backend_super.open_view_window),
        "Map": ("map.png", backend_super.show_map),
        "Specials": ("specials.png", lambda: backend_super.open_specials_window(username)),
        "Audit": ("audit.png", lambda: backend_super.audit_view(parent=None)),
        "Time Zone": ("time_zone.png", backend_super.open_tz_editor)
        
    }

    # Cargar configuración desde el archivo JSON
    def load_role_permissions():
        try:
            with open(under.CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ No se pudo cargar roles_config.json: {e}")
            # En caso de error, devolvemos permisos mínimos para no romper la app
            return {}

    # 🔹 Ahora role_permissions se carga dinámicamente
    role_permissions = load_role_permissions()

    allowed = role_permissions.get(role, [])
    filtered_buttons = {name: all_buttons[name] for name in allowed}

    # Cargar íconos solo de botones permitidos
    icons = {}
    for name, (filename, _) in filtered_buttons.items():
        icon_key = filename.replace(".png", "")
        icons[icon_key] = backend_super.load_icon(filename)

    # --- Botón independiente para exportar ---
    export_btn = ttk.Button(
        root,
        text="Exportar Excel",
        style="Card.TButton",
        command=do_export
    ) 
    export_btn.pack(pady=10, fill="x", padx=10)

    # Crear botones en cuadrícula
    i = 0
    for name, (filename, cmd) in filtered_buttons.items():
        icon_key = filename.replace(".png", "")
        ttk.Button(
            frame, text=name, image=icons[icon_key],
            compound="top", style="Card.TButton", command=cmd
        ).grid(row=i // 2, column=i % 2, padx=8, pady=8, sticky="nsew")
        i += 1
    
    
    
    canvas_logout_btn = tk.Canvas(root, width=115, height=21, bg="#2b2b2b", highlightthickness=0)

    # Posicionar el canvas del botón en pantalla
    canvas_logout_btn.place(x=220, y=4)  # Ajusta posición donde quieras el botón

    # Dibujar forma de píldora (rectángulo con esquinas redondeadas)
    x1, y1, x2, y2 = 55, 5, 40, 18  # coordenadas del botón
    radius = 17

    # Rectángulo central
    rect = canvas_logout_btn.create_rectangle(
        x1 + radius, y1, x2 - radius, y2,
        fill="#314052", outline="#1e3a5f"
    )

    # Círculo izquierdo
    left = canvas_logout_btn.create_oval(
        x1, y1, x1 + 2*radius, y2,
        fill="#314052", outline="#1e3a5f"
    )

    # Círculo derecho
    right = canvas_logout_btn.create_oval(
        x2 - 2*radius, y1, x2, y2,
        fill="#314052", outline="#1e3a5f"
    )

    # Texto "Log Out" en el centro
    text_logout = canvas_logout_btn.create_text(
        (x1 + x2) // 2, (y1 + y2) // 2,
        text="Log Out",
        fill="white",
        font=("Segoe UI", 7, "bold")
    )

    # Agrupamos los IDs de las partes del botón
    logout_items = [rect, left, right, text_logout]

    # --- Eventos de click ---
    for item in logout_items:
        # Asociar logout con los argumentos
        canvas_logout_btn.tag_bind(item, "<Button-1>", 
            lambda e, sid=session_id, st=station, r=root: login.do_logout(sid, st, r))

    # --- Efecto hover ---
    def on_enter(event):
        for item in (rect, left, right):
            canvas_logout_btn.itemconfig(item, fill="#54657a")

    def on_leave(event):
        for item in (rect, left, right):
            canvas_logout_btn.itemconfig(item, fill="#314052")  # ✅ corregido aquí

    for item in logout_items:
        canvas_logout_btn.tag_bind(item, "<Enter>", on_enter)
        canvas_logout_btn.tag_bind(item, "<Leave>", on_leave)


    root.mainloop()
    
