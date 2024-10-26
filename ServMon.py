import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import socket
import time
import threading
import csv
from PIL import Image, ImageTk

class ServiceChecker:
    def __init__(self, master):
        self.master = master
        self.setup_main_window()
        self.create_menu()
        self.create_main_frame()
        self.create_widgets()
        self.services = []
        self.check_thread = None
        self.is_checking = False
        self.stop_event = threading.Event()
        self.unavailable_count = 0

    def setup_main_window(self):
        self.master.title("ServMon")
        self.master.geometry("900x600")
        self.master.configure(bg='#f0f0f0')  

    def create_menu(self):
        self.menu_bar = tk.Menu(self.master)
        self.master.config(menu=self.menu_bar)
        help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)

    def create_main_frame(self):
        self.main_frame = ttk.Frame(self.master)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.master.grid_rowconfigure(0, weight=1)
        self.master.grid_columnconfigure(0, weight=1)

    def create_widgets(self):
        self.create_logo_frame()
        self.create_header_frame()
        self.create_file_input()
        self.create_interval_input()
        self.create_control_button()
        self.create_service_list()
        self.main_frame.grid_rowconfigure(4, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=1)

    def create_logo_frame(self):
        self.logo_frame = ttk.Frame(self.main_frame, width=150)
        self.logo_frame.grid(row=0, column=0, rowspan=6, sticky="ns", padx=10, pady=10)
        self.logo_frame.grid_propagate(False)
        self.load_logo()

    def create_header_frame(self):
        self.header_frame = ttk.Frame(self.main_frame)
        self.header_frame.grid(row=0, column=1, columnspan=2, sticky="ew", padx=10, pady=5)
        
        self.unavailable_label = ttk.Label(self.header_frame, text="Unavailable Services: 0", font=("Arial", 18, "bold"))
        self.unavailable_label.pack(side=tk.RIGHT)

    def create_file_input(self):
        self.file_frame = ttk.Frame(self.main_frame)
        self.file_frame.grid(row=1, column=1, columnspan=2, sticky="ew", padx=10, pady=5)
        self.file_button = ttk.Button(self.file_frame, text="Import Asset List", command=self.import_file)
        self.file_button.pack(side=tk.LEFT)
        self.file_label = ttk.Label(self.file_frame, text="No file selected")
        self.file_label.pack(side=tk.LEFT, padx=10)

    def create_interval_input(self):
        self.interval_frame = ttk.Frame(self.main_frame)
        self.interval_frame.grid(row=2, column=1, columnspan=2, sticky="ew", padx=10, pady=5)
        ttk.Label(self.interval_frame, text="Check interval (seconds):").pack(side=tk.LEFT)
        self.interval_entry = ttk.Entry(self.interval_frame, width=10)
        self.interval_entry.insert(0, "5")
        self.interval_entry.pack(side=tk.LEFT, padx=10)

    def create_control_button(self):
        self.control_button = ttk.Button(self.main_frame, text="Start Checking", command=self.toggle_checking)
        self.control_button.grid(row=3, column=1, columnspan=2, pady=5)

    def create_service_list(self):
        self.tree = ttk.Treeview(self.main_frame, columns=('IP', 'Port', 'Info', 'Status', 'Response Time'), show='headings')
        self.tree.heading('IP', text='IP')
        self.tree.heading('Port', text='Port')
        self.tree.heading('Info', text='Info')
        self.tree.heading('Status', text='Status')
        self.tree.heading('Response Time', text='Response Time (s)')
        self.tree.grid(row=4, column=1, columnspan=2, sticky="nsew", padx=10, pady=5)
        scrollbar = ttk.Scrollbar(self.main_frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=4, column=3, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

    def load_logo(self):
        try:
            logo_img = Image.open("logo.png")
            logo_img = logo_img.resize((120, 80), Image.LANCZOS)
            self.logo_photo = ImageTk.PhotoImage(logo_img)
            self.logo_label = ttk.Label(self.logo_frame, image=self.logo_photo)
            self.logo_label.pack(pady=10)
        except FileNotFoundError:
            print("Logo file not found. Please add a logo.png file to the same directory as the script.")
        except Exception as e:
            print(f"Error loading logo: {e}")

    def show_about(self):
        about_text = """
        Service Availability Monitor
        Version 1.0

        This application checks the services availability
        using port checking .

        Created by yasser.magdy9876@gmail.com
        """
        messagebox.showinfo("About", about_text)

    def import_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if file_path:
            self.file_label.config(text=file_path.split('/')[-1])
            self.services.clear()
            with open(file_path, 'r') as file:
                csv_reader = csv.reader(file)
                for row in csv_reader:
                    if len(row) >= 3:
                        self.services.append((row[0], int(row[1]), row[2]))
            self.update_tree()

    def update_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for service in self.services:
            self.tree.insert('', 'end', values=service + ('Unknown', 'N/A'))

    def check_service(self, host, port):
        start_time = time.time()
        try:
            with socket.create_connection((host, port), timeout=5) as sock:
                end_time = time.time()
                return True, end_time - start_time
        except (socket.timeout, socket.error):
            end_time = time.time()
            return False, end_time - start_time

    def check_services(self):
        while not self.stop_event.is_set():
            unavailable_services = []
            available_services = []
            for item in self.tree.get_children():
                if self.stop_event.is_set():
                    break
                values = self.tree.item(item)['values']
                status, response_time = self.check_service(values[0], int(values[1]))
                status_text = 'Available' if status else 'Unavailable'
                color = 'green' if status else 'red'
                new_values = (values[0], values[1], values[2], status_text, f'{response_time:.3f}')
                if status:
                    available_services.append((item, new_values, color))
                else:
                    unavailable_services.append((item, new_values, color))

            
            self.unavailable_count = len(unavailable_services)
            self.master.after(0, self.update_unavailable_label)

            
            for item, values, color in unavailable_services + available_services:
                self.tree.move(item, '', 'end')
                self.tree.item(item, values=values, tags=(color,))

            self.tree.tag_configure('green', background='light green')
            self.tree.tag_configure('red', background='light coral')
            
            try:
                interval = float(self.interval_entry.get())
                for _ in range(int(interval * 2)):
                    if self.stop_event.is_set():
                        break
                    time.sleep(0.5)
            except ValueError:
                time.sleep(5)

    def update_unavailable_label(self):
        self.unavailable_label.config(text=f"Unavailable Services: {self.unavailable_count}")

    def toggle_checking(self):
        if self.is_checking:
            self.stop_event.set()
            self.control_button.config(text="Start Checking")
            self.is_checking = False
        else:
            self.stop_event.clear()
            self.is_checking = True
            self.control_button.config(text="Stop")
            self.check_thread = threading.Thread(target=self.check_services)
            self.check_thread.start()

if __name__ == "__main__":
    root = tk.Tk()
    app = ServiceChecker(root)
    root.mainloop()
