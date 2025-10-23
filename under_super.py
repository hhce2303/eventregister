import backend_super
import os
import  csv
from tkinter import ttk
from datetime import datetime, date
from mysql.connector import Error
import pymysql
from pathlib import Path

ICON_PATH = r"\\192.168.7.12\Data SIG\Central Station SLC-COLOMBIA\1. Daily Logs - Operators\DataBase\icons"
import pyodbc

ACCESS_DB_PATH = r"\\192.168.7.12\Data SIG\Central Station SLC-COLOMBIA\1. Daily Logs - Operators\DataBase\Base de Datos\Daily_log1.accdb"
# 📂 Ruta compartida para el archivo de configuración
CONFIG_PATH = Path=r"\\192.168.7.12\Data SIG\Central Station SLC-COLOMBIA\1. Daily Logs - Operators\DataBase\Base de Datos\roles_config.json"

class FilteredCombobox(ttk.Combobox):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.original_values = self['values']
        self.bind('<KeyRelease>', self.check_key)
        # Preserve any initial value/textvariable provided by the caller
        # (don't clear the widget on creation)

    def check_key(self, event):
        value = self.get()
        if value == '':
            self['values'] = self.original_values
        else:
            filtered = [item for item in self.original_values if value.lower() in str(item).lower()]
            self['values'] = filtered
    

def get_connection():
    """
    Establece una conexión segura con la base de datos MySQL.
    Lanza errores claros en caso de fallo (credenciales, servidor, etc.).
    """
    try:
        conn = pymysql.connect(
            host="192.168.101.135",
            user="app_user",
            password="1234",
            database="daily",
            port=3306
        )
        print("✅ Conexión exitosa")
    except pymysql.Error as e:
        print("❌ Error de conexión:", e)
        return None
    return conn


def get_events():
    print("events")

    return 

def single_window(name, func):
        if name in opened_windows and opened_windows[name].winfo_exists():
            opened_windows[name].focus()
            return
        win = func()
        opened_windows[name] = win

        opened_windows = {}  # Para controlar ventanas abiertas

def get_sites():
    """Obtiene la lista de sitios de la tabla Sitios"""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT CONCAT(Nombre_Sitio, ' ', ID_Sitio) AS Sitio
            FROM Sitios
            ORDER BY Nombre_Sitio
        """)

        sites = [row[0] for row in cursor.fetchall()]
        print(f"[DEBUG] Sitios cargados")  # debug
        return sites

    except Exception as e:
        print(f"[ERROR] get_sites: {e}")
        return []
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass

def get_activities():
    """Obtiene la lista de actividades de la tabla Actividades"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""SELECT Nombre_Actividad FROM Actividades ORDER BY Nombre_Actividad""")
        
        activities = [row[0] for row in cursor.fetchall()]
        print(f"[DEBUG] Actividades cargadas")  # debug
        return activities
    except Exception as e:
        print(f"[ERROR] get_activities: {e}")
        return []
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass

def add_event(username, site, activity, quantity, camera, desc, hour, minute, second):
    """
    Inserta un nuevo evento en la tabla Eventos en MySQL con tipos correctos.
    """
    conn = get_connection()
    if conn is None:
        print("❌ No se pudo conectar a la base de datos")
        return

    try:
        cursor = conn.cursor()

        # 🔹 Obtener ID_Usuario
        cursor.execute("SELECT ID_Usuario FROM user WHERE Nombre_Usuario=%s", (username,))
        row = cursor.fetchone()
        if not row:
            raise Exception(f"Usuario '{username}' no encontrado")
        user_id = int(row[0])

        # 🔹 Obtener ID_Sitio desde el site_value (ej: "NombreSitio 305")
        try:
            site_id = int(site.split()[-1])
        except Exception:
            raise Exception(f"No se pudo obtener el ID del sitio desde '{site}'")

        # 🔹 Construir datetime editable
        event_time = datetime.now().replace(hour=hour, minute=minute, second=second, microsecond=0)

        # 🔹 Convertir cantidad a número
        try:
            quantity_val = float(quantity)  # o int(quantity) si siempre es entero
        except Exception:
            quantity_val = 0  # fallback

        # 🔹 Insertar en tabla Eventos
        cursor.execute("""
            INSERT INTO Eventos (FechaHora, ID_Sitio, Nombre_Actividad, Cantidad, Camera, Descripcion, ID_Usuario)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (event_time, site_id, str(activity), quantity_val, str(camera), str(desc), user_id))

        conn.commit()
        print(f"[DEBUG] Evento registrado correctamente por {username}")

    except Exception as e:
        print(f"[ERROR] add_event: {e}")

    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass

def add_cover(station_id, username, new_user, cover_reason):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO Eventos (FechaHora, Nombre_Actividad, Cantidad, Camera, Descripcion, ID_Usuario)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            now,                  # FechaHora → datetime válido
            f"{username} - Covered by {new_user}",              # Nombre_Actividad → texto                    # Cantidad → número
            f"Station: {station_id}",           # Camera o Station → número si la columna es Number
            cover_reason,
            0,                                  # Descripcion → texto
            10                     # ID_Usuario → ajusta a un id real existente
        ))
        conn.commit()
        print("[DEBUG] Evento insertado correctamente")
    except Exception as e:
        print("[ERROR]", e)
    finally:
        cursor.close()
        conn.close()



def admin_mode():
     print("admin mode")

# ------------------------------
# Combobox filtrable
# ------------------------------
class FilteredCombobox(ttk.Combobox):
    def __init__(self, master=None, **kwargs):
        # Filter out invalid ttk options
        valid_kwargs = {}
        style_options = {}
        
        # Valid ttk.Combobox options
        valid_options = {
            'textvariable', 'values', 'font', 'height', 'width', 'state',
            'exportselection', 'justify', 'postcommand', 'validate', 'validatecommand'
        }
        
        for key, value in kwargs.items():
            if key in valid_options:
                valid_kwargs[key] = value
            else:
                # Store styling options for later use
                style_options[key] = value
        
        super().__init__(master, **valid_kwargs)

        # Apply custom styling if needed. If no style options were provided,
        # create a safe default dark style so the entry portion is readable
        # on dark backgrounds (many ttk themes don't honor bg/fg otherwise).
        if style_options:
            self._apply_custom_style(style_options)
        else:
            # Try to infer background from master or fall back to dark defaults
            try:
                master_bg = master.cget('bg')
            except Exception:
                master_bg = None
            default_style_opts = {
                'background': master_bg or '#23272a',
                'foreground': '#e0e0e0',
                'bordercolor': '#23272a',
                'arrowcolor': '#a3c9f9'
            }
            try:
                self._apply_custom_style(default_style_opts)
            except Exception:
                # Best-effort: ignore styling failures and continue
                pass

        # Preserve any initial value/textvariable provided by the caller
        # and capture the original values for filtering
        vals = self['values']
        # Normalize to a tuple (ttk may return a string if a single value)
        try:
            self.original_values = tuple(vals) if vals is not None else ()
        except Exception:
            # Fallback: try to coerce
            try:
                self.original_values = tuple([vals])
            except Exception:
                self.original_values = ()

        # During initialization we don't want the key handler to clear the
        # visible text (some platforms fire events on widget creation). Use
        # a short-lived suppress flag and then allow normal filtering.
        self._suppress_clear = True
        self.bind('<KeyRelease>', self.check_key)

        # If the widget was created with a non-empty textvariable or value,
        # make sure it's shown and, if present in the values list, select it.
        try:
            init_val = self.get()
            if init_val:
                try:
                    self.set(init_val)
                except Exception:
                    pass
                if init_val in self.original_values:
                    try:
                        self.current(self.original_values.index(init_val))
                    except Exception:
                        pass
        finally:
            # Release the suppress flag after the widget finishes initial setup
            try:
                self.after(50, lambda: setattr(self, '_suppress_clear', False))
            except Exception:
                self._suppress_clear = False
    
    def _apply_custom_style(self, style_options):
        """Apply custom styling using ttk.Style"""
        style = ttk.Style()

        # Create a unique style name for this widget (must end with the class suffix)
        style_name = f"CustomCombobox{ id(self) }.TCombobox"

        # Map custom options to ttk style options
        style_map = {}
        if 'background' in style_options:
            style_map['fieldbackground'] = style_options['background']
        if 'foreground' in style_options:
            style_map['foreground'] = style_options['foreground']
        if 'bordercolor' in style_options:
            style_map['bordercolor'] = style_options['bordercolor']
        if 'arrowcolor' in style_options:
            style_map['arrowcolor'] = style_options['arrowcolor']

        if style_map:
            # Create the style by copying from existing Combobox style
            try:
                style.layout(style_name, style.layout('TCombobox'))
            except Exception:
                # If layout copy fails, continue and attempt to configure
                pass
            style.configure(style_name, **style_map)
            try:
                self.configure(style=style_name)
            except Exception:
                pass

            # Best-effort: also set widget-level options if supported so the
            # entry portion shows the configured foreground/background.
            try:
                if 'foreground' in style_map:
                    self.configure(foreground=style_map.get('foreground'))
                if 'fieldbackground' in style_map:
                    # some themes honor 'background' on the widget
                    self.configure(background=style_map.get('fieldbackground'))
            except Exception:
                pass

            # Try to access internal entry child and set its colors (may fail on some ttk implementations)
            try:
                children = self.winfo_children()
                if children:
                    for ch in children:
                        try:
                            ch.configure(foreground=style_map.get('foreground'), background=style_map.get('fieldbackground'))
                        except Exception:
                            pass
            except Exception:
                pass

    def check_key(self, event):
        # Don't clear/modify values during init
        if getattr(self, '_suppress_clear', False):
            return

        value = self.get()
        if value == '':
            # restore full list
            try:
                self['values'] = self.original_values
            except Exception:
                self.configure(values=self.original_values)
        else:
            filtered = [item for item in self.original_values if value.lower() in str(item).lower()]
            try:
                self['values'] = filtered
            except Exception:
                self.configure(values=filtered)
