import threading
import tkinter as tk
from tkinter import ttk, messagebox

import cv2
from PIL import Image, ImageTk

from Desktop.helper import wait_for_esp_measurement
from helper import compile_doc, get_random_aura_color, remove_background, cleanup_fs, get_serial_ports
from send_mail import send_mail

BG_COLOR = "#0b0e1c"
PANEL_COLOR = "#13204d"
ACCENT_COLOR = "#1dd3b0"
TEXT_COLOR = "#eaf7ff"
BAR_COLOR = "#6c63ff"
ALT_COLOR = "#ff6ad5"
DESIGN_COLOR = "#9fb3ff"


class AuraGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Aura Console")
        self.configure(bg=BG_COLOR)
        self.geometry("840x700")
        self.minsize(820, 660)
        self.resizable(False, False)

        self.name_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.serial_port_var = tk.StringVar()
        self.serial_ports = []
        self.mail_enabled = tk.BooleanVar(value=True)
        self.use_picture = tk.BooleanVar(value=True)
        self.current_frame = None

        self._build_starfield()
        self._style_controls()
        self._build_chrome()
        self._refresh_ports()
        self._build_form()
        self._build_camera_panel()

        self.cap = None
        self.running = True
        self._set_camera_state(self.use_picture.get())
        self.after(20, self._update_frame)

    def _build_starfield(self):
        self.starfield = tk.Canvas(self, bg=BG_COLOR, highlightthickness=0, bd=0)
        self.starfield.place(relx=0, rely=0, relwidth=1, relheight=1)
        import random
        for _ in range(80):
            x = random.randint(0, 1200)
            y = random.randint(0, 900)
            r = random.randint(1, 2)
            self.starfield.create_oval(x, y, x + r, y + r, fill=DESIGN_COLOR, outline="")
        # Background canvas is created first, so it stays behind later widgets

    def _style_controls(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TEntry", fieldbackground=BG_COLOR, foreground=TEXT_COLOR, padding=6,
                        bordercolor=PANEL_COLOR, lightcolor=PANEL_COLOR, darkcolor=PANEL_COLOR)
        style.map("TEntry", fieldbackground=[("active", BG_COLOR)], foreground=[("disabled", "#777")])

    def _build_chrome(self):
        top = tk.Frame(self, bg=PANEL_COLOR, height=50)
        top.pack(fill=tk.X, side=tk.TOP)
        tk.Frame(top, bg=BAR_COLOR, height=10).pack(fill=tk.X, side=tk.BOTTOM)
        tk.Label(top, text="AURAMESSUNG", bg=PANEL_COLOR, fg=TEXT_COLOR,
                 font=("Helvetica", 18, "bold")).pack(side=tk.LEFT, padx=16, pady=6)
        top_right = tk.Frame(top, bg=PANEL_COLOR)
        top_right.pack(side=tk.RIGHT, padx=16, pady=6)
        tk.Label(top_right, text="USB-Port:", bg=PANEL_COLOR, fg=ALT_COLOR,
                 font=("Helvetica", 11, "bold")).grid(row=0, column=0, sticky="e")
        self.port_combo = ttk.Combobox(top_right, textvariable=self.serial_port_var, width=18,
                                       values=self.serial_ports,
                                       state="readonly" if self.serial_ports else "disabled")
        self.port_combo.grid(row=0, column=1, padx=8)
        tk.Button(top_right, text="Refresh", command=self._refresh_ports, bg=BAR_COLOR, fg=TEXT_COLOR,
                  activebackground=ALT_COLOR, activeforeground=BG_COLOR,
                  relief=tk.FLAT, padx=8, pady=2).grid(row=0, column=2)
        top_right.grid_columnconfigure(1, weight=1)

        left = tk.Frame(self, bg=PANEL_COLOR, width=40)
        left.pack(fill=tk.Y, side=tk.LEFT, padx=(12, 8), pady=(60, 16))
        tk.Frame(left, bg=BAR_COLOR, height=140, width=40).pack(fill=tk.X, side=tk.TOP, pady=(12, 8))
        tk.Frame(left, bg=ACCENT_COLOR, height=90, width=40).pack(fill=tk.X, side=tk.TOP, pady=8)
        tk.Frame(left, bg=ALT_COLOR, height=70, width=40).pack(fill=tk.X, side=tk.TOP, pady=8)

        right = tk.Frame(self, bg=ALT_COLOR, width=16)
        right.pack(fill=tk.Y, side=tk.RIGHT, padx=(6, 12), pady=(60, 16))

    def _build_form(self):
        form = tk.Frame(self, bg=BG_COLOR)
        form.pack(side=tk.TOP, fill=tk.X, padx=18, pady=12)

        self._add_labeled_entry(form, "Name:", self.name_var, 0)
        self._add_labeled_entry(form, "E-Mail:", self.email_var, 1)

        tk.Checkbutton(form, text="Send Mail", variable=self.mail_enabled, fg=TEXT_COLOR,
                       selectcolor=PANEL_COLOR, bg=BG_COLOR, activebackground=BG_COLOR,
                       activeforeground=TEXT_COLOR, highlightthickness=0).grid(row=0, column=2, padx=10, sticky="w")
        tk.Checkbutton(form, text="Include Picture", variable=self.use_picture, fg=TEXT_COLOR,
                       selectcolor=PANEL_COLOR, bg=BG_COLOR, activebackground=BG_COLOR,
                       activeforeground=TEXT_COLOR, highlightthickness=0,
                       command=self._on_toggle_picture).grid(row=1, column=2, padx=10, sticky="w")

    def _add_labeled_entry(self, parent, text, var, row):
        tk.Label(parent, text=text, fg=TEXT_COLOR, bg=BG_COLOR,
                 font=("Helvetica", 12, "bold")).grid(row=row, column=0, sticky="w", pady=4)
        entry = ttk.Entry(parent, textvariable=var, width=34)
        entry.grid(row=row, column=1, sticky="w", pady=4, padx=8)

    def _build_camera_panel(self):
        cam_frame = tk.Frame(self, bg=PANEL_COLOR, bd=10, relief=tk.FLAT)
        cam_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=18, pady=(4, 0))
        cam_frame.pack_propagate(False)

        glow = tk.Frame(cam_frame, bg=ALT_COLOR, height=6)
        glow.pack(fill=tk.X, side=tk.TOP, pady=(0, 4))

        self.video_label = tk.Label(cam_frame, bg=PANEL_COLOR)
        self.video_label.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=8, pady=8)

        button_row = tk.Frame(self, bg=ACCENT_COLOR, height=94)
        button_row.pack(side=tk.BOTTOM, fill=tk.X, padx=18, pady=(10, 14))
        button_row.pack_propagate(False)

        tk.Label(button_row, text="START", bg=ACCENT_COLOR, fg=BG_COLOR,
                 font=("Helvetica", 16, "bold")).pack(side=tk.LEFT, padx=18)

        self.shutter_button = tk.Button(button_row, text="CONNECT", bg=BAR_COLOR, fg=TEXT_COLOR,
                                        font=("Helvetica", 20, "bold"), activebackground=ALT_COLOR,
                                        activeforeground=BG_COLOR, relief=tk.FLAT, padx=38, pady=14,
                                        command=self.on_shutter)
        self.shutter_button.pack(side=tk.RIGHT, padx=18, pady=10)

    def _set_camera_state(self, enabled: bool):
        if enabled and self.cap is None:
            self.cap = cv2.VideoCapture(0)
        if not enabled and self.cap is not None:
            self.cap.release()
            self.cap = None
            self.current_frame = None
            self.video_label.configure(image="", text="Camera disabled", fg=TEXT_COLOR,
                                       bg=PANEL_COLOR, font=("Helvetica", 16, "bold"))

    def _on_toggle_picture(self):
        self._set_camera_state(self.use_picture.get())

    def _update_frame(self):
        if not self.running:
            return

        if not self.use_picture.get():
            self._set_camera_state(False)
            self.after(300, self._update_frame)
            return

        if self.cap is None:
            self._set_camera_state(True)

        ret, frame = self.cap.read() if self.cap else (False, None)
        if ret:
            self.current_frame = frame.copy()
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb).resize((660, 340))
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk, text="")
        else:
            self.video_label.configure(image="", text="Camera not available", fg=TEXT_COLOR,
                                       bg=PANEL_COLOR, font=("Helvetica", 16, "bold"))
        self.after(30, self._update_frame)

    def get_selected_port(self) -> str:
        """Return the USB/serial port picked in the dropdown (empty string if nothing is selected)."""
        return self.serial_port_var.get().strip()


    def on_shutter(self):
        self.shutter_button.configure(state=tk.DISABLED, text="Processing...")
        # Access the currently selected USB port via self.get_selected_port() when talking to the device.
        threading.Thread(target=self._capture_and_compile, daemon=True).start()

    def _capture_and_compile(self):
        name = self.name_var.get().strip() or "Unbekannt"
        email = self.email_var.get().strip()
        include_pic = self.use_picture.get()

        try:
            cleanup_fs()
            if include_pic:
                if self.current_frame is None:
                    raise RuntimeError("Keine Kameradaten verfügbar.")
                cv2.imwrite("captured_image.png", self.current_frame)
                remove_background("captured_image.png", "tex/face.png")

            color_one, color_two = get_random_aura_color()
            device_con = wait_for_esp_measurement(self.get_selected_port())
            #device_con = "done"
            if device_con == "error while measuring" or device_con == "connection to device failed":
                print("Something went wrong while measuring, please retry")
            elif device_con == "done":
                filename = compile_doc(name, color_one, color_two)

                if self.mail_enabled.get() and email:
                    send_mail(email, "Deine Auramessung",
                              "Hallo!\nIm Anhang kannst du deine Auramessung einsehen!\nGaLiGrü Dein Auramessungsteam",
                              files=[f"Measurements/{filename}"])
                self._notify(lambda: messagebox.showinfo("Fertig", "Auradokument erstellt."))
                self._notify(lambda: self.shutter_button.configure(state=tk.NORMAL, text="CONNECT"))
                cleanup_fs()
        except Exception as exc:
            self._notify(lambda: messagebox.showerror("Fehler", str(exc)))
        finally:
            self._notify(lambda: self.shutter_button.configure(state=tk.NORMAL, text="CONNECT"))

    def _notify(self, func):
        self.after(0, func)


    def _refresh_ports(self):
        ports = get_serial_ports()
        self.serial_ports = ports
        if ports:
            if self.serial_port_var.get() not in ports:
                self.serial_port_var.set(ports[0])
        else:
            self.serial_port_var.set("")

        if hasattr(self, "port_combo"):
            state = "readonly" if ports else "disabled"
            self.port_combo.configure(values=ports, state=state)
            if not ports:
                self.port_combo.set("")

    def on_close(self):
        self.running = False
        if self.cap:
            self.cap.release()
        self.destroy()


def main():
    app = AuraGUI()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()


if __name__ == "__main__":
    main()

