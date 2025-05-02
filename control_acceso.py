import cv2
import tkinter as tk
from tkinter import messagebox
import os
import face_recognition
from PIL import Image, ImageTk
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import datetime
import pytesseract
import PyPDF2

# Ruta base
DB_PATH = r"C:\Users\practicasnetw\Desktop\Hola\base de datos"

# Configurar Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Función para generar folio
def get_next_folio():
    folios_path = os.path.join(DB_PATH, "folios.txt")
    if not os.path.exists(folios_path):
        with open(folios_path, "w") as f:
            f.write("1")
        return "F0001"
    else:
        with open(folios_path, "r+") as f:
            folio_num = int(f.read().strip())
            f.seek(0)
            f.write(str(folio_num + 1))
            f.truncate()
        return f"F{folio_num:04d}"

# Crear ventana principal
root = tk.Tk()
root.title("Reconocimiento Facial e INE")
root.geometry("1100x600")

# Etiqueta de mensaje superior
message_label = tk.Label(root, text="", font=("Helvetica", 14))
message_label.pack(pady=10)

# Marcos para cámara y comparación
frame_left = tk.Frame(root)
frame_left.pack(side="left", fill="both", expand=True, padx=10)

frame_right = tk.Frame(root)
frame_right.pack(side="right", fill="both", expand=True, padx=10)

video_label = tk.Label(frame_left)
video_label.pack(pady=10)

photo_label = tk.Label(frame_right)
photo_label.pack(pady=10)

# Variables globales
capture_button = None
register_button = None
face_image = None

# Cámara en vivo
def show_video_stream(cap):
    ret, frame = cap.read()
    if ret:
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        img_tk = ImageTk.PhotoImage(img)
        video_label.config(image=img_tk)
        video_label.image = img_tk
    root.after(100, show_video_stream, cap)

# Captura de foto
def take_photo_for_recognition():
    global capture_button, face_image

    for widget in frame_right.winfo_children():
        widget.destroy()

    if capture_button:
        capture_button.destroy()

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        messagebox.showerror("Error", "No se pudo acceder a la cámara.")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    message_label.config(text="Presiona el botón para tomar la foto")
    root.update()

    show_video_stream(cap)

    def capture_photo():
        global face_image
        ret, frame = cap.read()
        if ret:
            face_image = frame
            compare_with_database(frame)
        else:
            messagebox.showerror("Error", "No se pudo capturar la foto.")
        cap.release()

    capture_button = tk.Button(root, text="Capturar Foto", width=20, command=capture_photo, bg="black", fg="white")
    capture_button.pack(pady=10)

# Comparación facial
def compare_with_database(frame):
    global register_button, photo_label

    known_faces = []
    known_names = []
    known_images = []

    for folder in os.listdir(DB_PATH):
        folder_path = os.path.join(DB_PATH, folder)
        if os.path.isdir(folder_path):
            for file in os.listdir(folder_path):
                if file.endswith(".jpg") and "_INE" not in file:
                    image_path = os.path.join(folder_path, file)
                    image = face_recognition.load_image_file(image_path)
                    encoding = face_recognition.face_encodings(image)
                    if encoding:
                        known_faces.append(encoding[0])
                        known_names.append(folder)
                        known_images.append(image_path)

    unknown_encoding = face_recognition.face_encodings(frame)

    if unknown_encoding:
        matches = face_recognition.compare_faces(known_faces, unknown_encoding[0])
        if True in matches:
            matched_index = matches.index(True)
            matched_name = known_names[matched_index]
            matched_image_path = known_images[matched_index]

            for widget in frame_right.winfo_children():
                widget.destroy()

            matched_img = Image.open(matched_image_path)
            matched_img = matched_img.resize((300, 250))
            matched_img_tk = ImageTk.PhotoImage(matched_img)

            photo_label = tk.Label(frame_right, image=matched_img_tk)
            photo_label.image = matched_img_tk
            photo_label.pack(pady=10)

            message_label.config(text=f"Persona reconocida: {matched_name}")
            message_label.config(font=("Helvetica", 16))

            user_folder = os.path.join(DB_PATH, matched_name)
            for file in os.listdir(user_folder):
                if file.endswith(".pdf"):
                    pdf_path = os.path.join(user_folder, file)
                    tk.Button(frame_right, text="Abrir PDF", command=lambda: os.startfile(pdf_path), bg="blue", fg="white").pack(pady=5)
                    try:
                        with open(pdf_path, "rb") as f:
                            reader = PyPDF2.PdfReader(f)
                            text = ""
                            for page in reader.pages:
                                text += page.extract_text()

                        info_label = tk.Label(frame_right, text="Información del registro:", font=("Helvetica", 12, "bold"))
                        info_label.pack(pady=(10, 0))

                        text_box = tk.Text(frame_right, height=10, width=50, wrap="word")
                        text_box.insert("1.0", text.strip())
                        text_box.config(state="disabled")
                        text_box.pack(pady=5)

                    except Exception as e:
                        print("Error al leer el PDF:", e)
                    break

            root.bind('<Return>', on_enter_pressed)
        else:
            message_label.config(text="No se reconoció a la persona. Por favor regístrate.")
            if not register_button:
                register_button = tk.Button(root, text="Registrarse", command=open_registration_window, bg="green", fg="white")
                register_button.pack(pady=10)
            root.bind('<Return>', on_enter_pressed)
    else:
        message_label.config(text="No se detectó ninguna cara en la foto.")
        root.bind('<Return>', on_enter_pressed)

# Reinicio con Enter
def on_enter_pressed(event):
    global capture_button, register_button
    photo_label.config(image="")
    message_label.config(text="")
    if capture_button:
        capture_button.destroy()
    if register_button:
        register_button.destroy()
    take_photo_for_recognition()

# Captura de INE
def take_ine_after_registration(name, folder):
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        messagebox.showerror("Error", "No se pudo acceder a la cámara.")
        return

    def show_ine_preview():
        ret, frame = cap.read()
        if ret:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            img_tk = ImageTk.PhotoImage(img)
            video_label.config(image=img_tk)
            video_label.image = img_tk
        root.after(100, show_ine_preview)

    def capture_ine():
        ret, frame = cap.read()
        if ret:
            ine_path = os.path.join(folder, f"{name}_INE.jpg")
            cv2.imwrite(ine_path, frame)
            image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            text = pytesseract.image_to_string(image)
            text_path = os.path.join(folder, f"{name}_INE.txt")
            with open(text_path, "w", encoding="utf-8") as file:
                file.write(text)
            messagebox.showinfo("Guardado", f"INE y texto guardados correctamente para {name}.")
            cap.release()
            take_photo_for_recognition()
        else:
            messagebox.showerror("Error", "No se pudo capturar la INE.")

    message_label.config(text="Acomoda tu INE frente a la cámara y presiona Capturar INE.")
    show_ine_preview()
    tk.Button(root, text="Capturar INE", command=capture_ine, bg="black", fg="white").pack(pady=10)

# Registro
def open_registration_window():
    global register_button, face_image

    for widget in frame_right.winfo_children():
        widget.destroy()

    if face_image is not None:
        preview_img = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(preview_img)
        img_pil = img_pil.resize((300, 250))
        img_tk = ImageTk.PhotoImage(img_pil)
        face_preview_label = tk.Label(frame_right, image=img_tk)
        face_preview_label.image = img_tk
        face_preview_label.pack(pady=10)

    def limit_length(entry_text, limit):
        return len(entry_text) <= limit

    vcmd_name = root.register(lambda text: limit_length(text, 60))
    vcmd_address = root.register(lambda text: limit_length(text, 100))
    vcmd_curp = root.register(lambda text: limit_length(text, 18))

    tk.Label(frame_right, text="Nombre completo (máx. 60 caracteres):").pack()
    name_entry = tk.Entry(frame_right, width=40, validate="key", validatecommand=(vcmd_name, "%P"))
    name_entry.pack()

    tk.Label(frame_right, text="Domicilio (máx. 100 caracteres):").pack()
    address_entry = tk.Entry(frame_right, width=40, validate="key", validatecommand=(vcmd_address, "%P"))
    address_entry.pack()

    tk.Label(frame_right, text="CURP (exactamente 18 caracteres):").pack()
    curp_entry = tk.Entry(frame_right, width=40, validate="key", validatecommand=(vcmd_curp, "%P"))
    curp_entry.pack()

    def save_registration():
        name = name_entry.get().strip()
        address = address_entry.get().strip()
        curp = curp_entry.get().strip()

        if len(name) > 60 or not name:
            messagebox.showwarning("Nombre inválido", "El nombre debe tener entre 1 y 60 caracteres.")
            return
        if len(address) > 100 or not address:
            messagebox.showwarning("Domicilio inválido", "El domicilio debe tener entre 1 y 100 caracteres.")
            return
        if len(curp) != 18:
            messagebox.showwarning("CURP inválido", "La CURP debe contener exactamente 18 caracteres.")
            return

        today = datetime.now().strftime("%Y-%m-%d")
        folio = get_next_folio()
        folder_name = f"{name}{today}{folio}"
        user_folder = os.path.join(DB_PATH, folder_name)
        os.makedirs(user_folder, exist_ok=True)

        if face_image is not None:
            cv2.imwrite(os.path.join(user_folder, f"{name}.jpg"), face_image)

        pdf_path = os.path.join(user_folder, f"{name}.pdf")
        c = canvas.Canvas(pdf_path, pagesize=letter)
        c.setFont("Helvetica", 12)
        c.drawString(50, 750, "FICHA DE REGISTRO")
        c.drawString(50, 710, f"Folio: {folio}")
        c.drawString(50, 690, f"Fecha: {today}")
        c.drawString(50, 660, f"Nombre: {name}")
        c.drawString(50, 630, f"Domicilio: {address}")
        c.drawString(50, 600, f"CURP: {curp}")
        c.save()

        for widget in frame_right.winfo_children():
            widget.destroy()

        take_ine_after_registration(name, user_folder)

    tk.Button(frame_right, text="Guardar y Capturar INE", command=save_registration, bg="black", fg="white").pack(pady=10)

# Iniciar proceso
root.after(100, take_photo_for_recognition)

# Cierre seguro
def on_closing():
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()