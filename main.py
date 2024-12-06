import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import os
from moviepy.editor import VideoFileClip
from random import randint
from proglog import ProgressBarLogger
from tqdm import tqdm

# Crear la ventana principal
ventana = tk.Tk()
ventana.title("Convertidor de Formato de Video")
ventana.iconbitmap('D:\www\Python\convertidorVideos\logo.ico')
ventana.geometry("400x300")
ventana.config(bg="#f0f0f0")

# Variables para la ruta del archivo y el formato de salida
ruta_entrada = tk.StringVar()
progreso = tk.DoubleVar(value=0)
cancelar_conversion = threading.Event()
clip = None

# Función para seleccionar el archivo de video
def seleccionar_video():
    archivo = filedialog.askopenfilename(
        title="Seleccionar archivo de video",
        filetypes=[("Archivos de video", "*.avi *.mov *.mkv *.flv *.wmv *.mp4")]
    )
    if archivo:
        ruta_entrada.set(archivo)

# Crear la interfaz gráfica con estilo mejorado
tk.Label(ventana, text="Seleccione el video a convertir:", bg="#f0f0f0", font=("Arial", 10)).pack(pady=5)
entrada_video = tk.Entry(ventana, textvariable=ruta_entrada, width=40, font=("Arial", 10))
entrada_video.pack(pady=5)
boton_seleccionar = tk.Button(ventana, text="Seleccionar Video", command=seleccionar_video, font=("Arial", 10))
boton_seleccionar.pack(pady=5)

tk.Label(ventana, text="Seleccione el formato de salida:", bg="#f0f0f0", font=("Arial", 10)).pack(pady=5)
formato_salida = tk.StringVar(value="mp4 (Android)")
selector_formato = ttk.Combobox(ventana, textvariable=formato_salida, values=["mp4", "avi", "mov", "mp4 (Android)"], font=("Arial", 10))
selector_formato.pack(pady=5)

# Crear el Canvas para la barra de progreso
canvas_progreso = tk.Canvas(ventana, width=300, height=20, bg="white", highlightthickness=0)
canvas_progreso.pack(pady=10)
# canvas_progreso.create_rectangle(0, 0, 3 * 0, 20, fill="green", tags="progress")

# Función para actualizar la barra de progreso según el porcentaje
def actualizar_progreso(porcentaje):
    canvas_progreso.delete("progress")
    canvas_progreso.create_rectangle(0, 0, 3 * porcentaje, 20, fill="green", tags="progress")
    ventana.update_idletasks()

# Logger personalizado para actualizar la barra de progreso
class CustomLogger(ProgressBarLogger):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pbar = tqdm(total=100, desc="Progreso de conversión")

    def callback(self, **changes):
        global progreso
        progreso.set(progreso.get() + 0.0005)  # Actualizar progreso correctamente
        if progreso.get() > 95:
            progreso.set(randint(80, 95))

        print(progreso.get())
        ventana.after(0, actualizar_progreso, progreso.get())
        if 'bars' in changes:
            for bar in changes['bars']:
                if bar['index'] is not None and bar['total'] is not None:
                    progreso = (bar['index'] / bar['total']) * 100
                    
                    self.pbar.n = progreso
                    self.pbar.refresh()
                if cancelar_conversion.is_set():
                    raise Exception("Conversión cancelada por el usuario")

    def close(self):
        self.pbar.close()

# Función para convertir el video y actualizar la barra de progreso
def conversion_real():
    global clip
    ruta_video = ruta_entrada.get()
    formato = formato_salida.get()
    ruta_salida = os.path.splitext(ruta_video)[0] + f"_convertido.{formato.split()[0]}"

    try:
        clip = VideoFileClip(ruta_video)
        logger = CustomLogger()
        if formato == "mp4 (Android)":
            clip.write_videofile(ruta_salida, codec="libx264", audio_codec="aac", preset="slow", ffmpeg_params=["-profile:v", "baseline", "-level", "3.0"], logger=logger)
        else:
            clip.write_videofile(ruta_salida, codec="libx264" if formato == "mp4" else None, logger=logger)

        # Actualizar la barra de progreso al 100%
        print(clip)
        ventana.after(0, actualizar_progreso, 100)
        ventana.after(0, messagebox.showinfo, "Conversión Completa", f"El video se ha convertido exitosamente y se ha guardado en:\n{ruta_salida}")
    except Exception as e:
        if str(e) == "Conversión cancelada por el usuario":
            ventana.after(0, messagebox.showinfo, "Conversión Cancelada", "La conversión del video ha sido cancelada.")
            # Eliminar archivos temporales
            if os.path.exists(ruta_salida):
                os.remove(ruta_salida)
        else:
            ventana.after(0, messagebox.showerror, "Error", f"Ocurrió un error al convertir el video:\n{str(e)}")
    finally:
        logger.close()
        ventana.after(0, habilitar_controles)

# Función para iniciar la conversión en un hilo separado
def iniciar_conversion():
    if not ruta_entrada.get():
        messagebox.showwarning("Advertencia", "Seleccione un archivo de video primero.")
        return

    if formato_salida.get() == "":
        messagebox.showwarning("Advertencia", "Seleccione un formato de salida.")
        return

    cancelar_conversion.clear()
    deshabilitar_controles()
    # Ejecuta la conversión en un hilo separado para no bloquear la interfaz
    hilo_conversion = threading.Thread(target=conversion_real)
    hilo_conversion.start()

# Función para cancelar la conversión
def cancelar_conversion_func():
    global clip
    cancelar_conversion.set()
    if clip is not None:
        clip.close()
    messagebox.showinfo("Cancelación", "La conversión del video ha sido cancelada.")
    habilitar_controles()

# Función para deshabilitar los controles
def deshabilitar_controles():
    entrada_video.config(state="disabled")
    boton_seleccionar.config(state="disabled")
    selector_formato.config(state="disabled")
    boton_convertir.config(state="disabled")

# Función para habilitar los controles
def habilitar_controles():
    entrada_video.config(state="normal")
    boton_seleccionar.config(state="normal")
    selector_formato.config(state="normal")
    boton_convertir.config(state="normal")

# Función para cerrar la aplicación
def cerrar_aplicacion():
    global clip
    cancelar_conversion.set()
    if clip is not None:
        clip.close()
    ventana.quit()
    ventana.destroy()

# Crear un frame para los botones
frame_botones = tk.Frame(ventana)
frame_botones.pack(pady=10)

# Botón para iniciar la conversión
boton_convertir = tk.Button(frame_botones, text="Convertir Video", command=iniciar_conversion, font=("Arial", 10, "bold"), bg="#4CAF50", fg="white")
boton_convertir.pack(side="left", padx=5)

# Botón para cancelar la conversión
tk.Button(frame_botones, text="Cancelar Conversión", command=cancelar_conversion_func, font=("Arial", 10, "bold"), bg="#f44336", fg="white").pack(side="left", padx=5)

# Botón para cerrar la aplicación
tk.Button(frame_botones, text="Cerrar", command=cerrar_aplicacion, font=("Arial", 10, "bold"), bg="#f44336", fg="white").pack(side="left", padx=5)

# Ejecuta la ventana principal
ventana.mainloop()