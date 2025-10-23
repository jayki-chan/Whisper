import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import threading
import time
import os
import requests
import json
import random
import string
import imaplib
import email
import re
from datetime import datetime, timedelta
from pathlib import Path
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
import pyautogui
import pyperclip
import atexit
import signal
import psutil
import base64

class TikTokAccountRegister:
    def __init__(self, root):
        self.root = root
        self.root.title("Tool Đăng Ký TikTok - Ver 1.0.0 - By Justin Chan")
        self.root.geometry("1400x800")

        # Dark modern color scheme
        self.colors = {
            'bg': '#0f172a',
            'surface': '#1e293b',
            'surface_light': '#334155',
            'primary': '#3b82f6',
            'primary_hover': '#2563eb',
            'success': '#22c55e',
            'error': '#ef4444',
            'warning': '#f59e0b',
            'text': '#f1f5f9',
            'text_dim': '#94a3b8',
            'border': '#334155'
        }

        # Configure root
        self.root.configure(bg=self.colors['bg'])

        # Data
        self.num_accounts = 1
        self.is_running = False

        # Threading lock for avatar upload (pyautogui is NOT thread-safe)
        self.avatar_upload_lock = threading.Lock()
        self.num_threads = 1
        self.headless_mode = False
        self.created_count = 0
        self.success_count = 0
        self.error_count = 0
        self.results = []

        # IMAP Configuration
        self.imap_server = "mail.codekonami.pro.vn"
        self.imap_port = 993
        self.imap_user = "jayki83@vinacode.co"
        self.imap_pass = "@@@Giang08032004"

        # API Configuration
        self.api_url = "https://justin.vinacode.co/api/push_tiktok.php"  # Sửa lại tên file đúng
        self.api_key = "TikTok_API_9K3mZ8xY2wN7vR5qL4pT6hG1cB0jF"

        # Whisper API Configuration (Hugging Face Spaces)
        self.whisper_api_url = "https://ganggangthao-whisper-transcription.hf.space/api/predict"
        self.use_whisper_api = True  # Mặc định dùng API, set False để dùng local model

        # Proxy Configuration
        self.proxy_list = []
        self.proxy_index = 0
        self.proxy_lock = threading.Lock()

        # Table row mapping: index → row_item_id
        self.index_to_row = {}
        self.row_lock = threading.Lock()

        # IMAP - không dùng lock để tránh block threads
        # Mỗi thread tự connect IMAP riêng

        # Log text widget
        self.log_text = None

        # Track Chrome PIDs để kill khi tắt tool
        self.chrome_pids = set()
        self.pids_lock = threading.Lock()

        # Đăng ký cleanup khi tool bị tắt
        atexit.register(self.cleanup_chrome_processes)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Cleanup Chrome cũ từ lần chạy trước (nếu tool bị crash)
        self.cleanup_old_chrome_on_startup()

        # User Agent pool - danh sách đa dạng các User Agent
        self.user_agents = [
            # Chrome on Windows
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',

            # Chrome on macOS
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',

            # Edge on Windows
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0',

            # Firefox on Windows
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',

            # Firefox on macOS
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0',

            # Safari on macOS
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15',

            # Chrome on Linux
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',

            # Firefox on Linux
            'Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0',

            # Chrome on Windows 11
            'Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',

            # Opera on Windows
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/106.0.0.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 OPR/105.0.0.0',

            # Brave on Windows
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Brave/120.0.0.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Brave/119.0.0.0',

            # Vivaldi on Windows
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Vivaldi/6.5',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Vivaldi/6.4',
        ]

        self.setup_styles()
        self.setup_ui()

    def setup_styles(self):
        """Setup dark modern styles"""
        style = ttk.Style()
        style.theme_use('clam')

        style.configure('Dark.TFrame', background=self.colors['bg'])
        style.configure('Card.TFrame', background=self.colors['surface'])

        style.configure('Card.TLabelframe',
                       background=self.colors['surface'],
                       borderwidth=0,
                       relief='flat')
        style.configure('Card.TLabelframe.Label',
                       background=self.colors['surface'],
                       foreground=self.colors['text'],
                       font=('Segoe UI', 9, 'bold'))

        style.configure('Accent.TButton',
                       background=self.colors['primary'],
                       foreground='white',
                       borderwidth=0,
                       font=('Segoe UI', 9),
                       padding=(15, 8))
        style.map('Accent.TButton',
                 background=[('active', self.colors['primary_hover'])])

        style.configure('Success.TButton',
                       background=self.colors['success'],
                       foreground='white',
                       borderwidth=0,
                       font=('Segoe UI', 9, 'bold'),
                       padding=(15, 10))

        style.configure('Danger.TButton',
                       background=self.colors['error'],
                       foreground='white',
                       borderwidth=0,
                       font=('Segoe UI', 9, 'bold'),
                       padding=(15, 10))

        style.configure('Light.TLabel',
                       background=self.colors['surface'],
                       foreground=self.colors['text'],
                       font=('Segoe UI', 9))

    def setup_ui(self):
        """Thiết lập giao diện"""
        # Header
        header = tk.Frame(self.root, bg=self.colors['surface'], height=50)
        header.pack(fill='x')
        header.pack_propagate(False)

        tk.Label(header,
                text="⚡ TikTok Account Register",
                font=('Segoe UI', 13, 'bold'),
                bg=self.colors['surface'],
                fg=self.colors['text']).pack(side='left', padx=15)

        tele_btn = tk.Label(header,
                text="Liên hệ hỗ trợ => Tele: @justin_chan17",
                font=('Segoe UI', 9),
                bg=self.colors['primary'],
                fg='white',
                padx=10,
                pady=4,
                cursor='hand2')
        tele_btn.pack(side='right', padx=15)
        tele_btn.bind('<Button-1>', lambda e: self.open_telegram())

        # Main
        main = ttk.Frame(self.root, style='Dark.TFrame')
        main.pack(fill='both', expand=True, padx=10, pady=10)

        # Left Panel
        left = ttk.Frame(main, width=350, style='Dark.TFrame')
        left.pack(side='left', fill='y', padx=(0, 10))
        left.pack_propagate(False)

        # Right Panel
        right = ttk.Frame(main, style='Dark.TFrame')
        right.pack(side='right', fill='both', expand=True)

        self.setup_left_panel(left)
        self.setup_right_panel(right)

    def setup_left_panel(self, parent):
        """Setup left panel"""
        # Settings
        set_frame = ttk.LabelFrame(parent, text="⚙️ SETTINGS", padding="10", style='Card.TLabelframe')
        set_frame.pack(fill='x', pady=(0, 8))

        # Number of accounts
        acc_frame = tk.Frame(set_frame, bg=self.colors['surface'])
        acc_frame.pack(fill='x', pady=(0, 8))

        tk.Label(acc_frame, text="Số tài khoản:",
                bg=self.colors['surface'],
                fg=self.colors['text'],
                font=('Segoe UI', 9)).pack(side='left')

        self.num_accounts_var = tk.StringVar(value="1")
        ttk.Spinbox(acc_frame, from_=1, to=100,
                   textvariable=self.num_accounts_var,
                   width=5,
                   font=('Segoe UI', 9)).pack(side='right')

        # Threads
        thread_frame = tk.Frame(set_frame, bg=self.colors['surface'])
        thread_frame.pack(fill='x', pady=(0, 8))

        tk.Label(thread_frame, text="Threads:",
                bg=self.colors['surface'],
                fg=self.colors['text'],
                font=('Segoe UI', 9)).pack(side='left')

        self.thread_var = tk.StringVar(value="1")
        ttk.Spinbox(thread_frame, from_=1, to=5,
                   textvariable=self.thread_var,
                   width=5,
                   font=('Segoe UI', 9)).pack(side='right')

        # Headless mode
        headless_frame = tk.Frame(set_frame, bg=self.colors['surface'])
        headless_frame.pack(fill='x', pady=(0, 8))

        self.headless_var = tk.BooleanVar(value=False)
        headless_check = tk.Checkbutton(headless_frame,
                                       text="Headless Mode (Ẩn trình duyệt)",
                                       variable=self.headless_var,
                                       bg=self.colors['surface'],
                                       fg=self.colors['text'],
                                       selectcolor=self.colors['bg'],
                                       activebackground=self.colors['surface'],
                                       activeforeground=self.colors['text'],
                                       font=('Segoe UI', 9),
                                       cursor='hand2')
        headless_check.pack(anchor='w')

        ttk.Button(set_frame, text="📂 Profiles",
                  command=self.open_profiles_folder,
                  style='Accent.TButton').pack(fill='x', pady=(0, 4))

        # Proxy import button
        proxy_btn_frame = tk.Frame(set_frame, bg=self.colors['surface'])
        proxy_btn_frame.pack(fill='x', pady=(0, 4))

        ttk.Button(proxy_btn_frame, text="📡 Import Proxy",
                  command=self.import_proxy,
                  style='Accent.TButton').pack(side='left', fill='x', expand=True)

        self.proxy_count_label = tk.Label(proxy_btn_frame,
                                          text="(0)",
                                          bg=self.colors['surface'],
                                          fg=self.colors['text_dim'],
                                          font=('Segoe UI', 8))
        self.proxy_count_label.pack(side='left', padx=5)

        # Control
        ctrl_frame = ttk.LabelFrame(parent, text="🎮 CONTROL", padding="10", style='Card.TLabelframe')
        ctrl_frame.pack(fill='x', pady=(0, 8))

        ctrl_buttons = tk.Frame(ctrl_frame, bg=self.colors['surface'])
        ctrl_buttons.pack(fill='x')

        self.start_button = ttk.Button(ctrl_buttons, text="▶ START",
                                      command=self.start_register,
                                      style='Success.TButton')
        self.start_button.pack(side='left', fill='x', expand=True, padx=(0, 3))

        self.stop_button = ttk.Button(ctrl_buttons, text="⏸ STOP",
                                     command=self.stop_register,
                                     state='disabled',
                                     style='Danger.TButton')
        self.stop_button.pack(side='right', fill='x', expand=True, padx=(3, 0))

        # Stats
        stats_frame = ttk.LabelFrame(parent, text="📊 STATS", padding="10", style='Card.TLabelframe')
        stats_frame.pack(fill='x', pady=(0, 8))

        self.created_var = tk.StringVar(value="0/0")
        tk.Label(stats_frame, textvariable=self.created_var,
                font=('Segoe UI', 11, 'bold'),
                bg=self.colors['surface'],
                fg=self.colors['text']).pack(anchor='w', pady=(0, 5))

        stat_grid = tk.Frame(stats_frame, bg=self.colors['surface'])
        stat_grid.pack(fill='x')

        success_box = tk.Frame(stat_grid, bg='#166534', padx=8, pady=5)
        success_box.pack(side='left', fill='x', expand=True, padx=(0, 3))
        self.success_var = tk.StringVar(value="Success: 0")
        tk.Label(success_box, textvariable=self.success_var,
                font=('Segoe UI', 10, 'bold'),
                bg='#166534', fg='#bbf7d0').pack()

        error_box = tk.Frame(stat_grid, bg='#991b1b', padx=8, pady=5)
        error_box.pack(side='right', fill='x', expand=True, padx=(3, 0))
        self.error_var = tk.StringVar(value="Error: 0")
        tk.Label(error_box, textvariable=self.error_var,
                font=('Segoe UI', 10, 'bold'),
                bg='#991b1b', fg='#fecaca').pack()

        # Log
        log_frame = ttk.LabelFrame(parent, text="📝 LOGS", padding="10", style='Card.TLabelframe')
        log_frame.pack(fill='both', expand=True, pady=(0, 8))

        self.log_text = scrolledtext.ScrolledText(log_frame,
                                                  height=10,
                                                  font=('Consolas', 8),
                                                  bg=self.colors['bg'],
                                                  fg=self.colors['text_dim'],
                                                  relief='flat',
                                                  wrap='word')
        self.log_text.pack(fill='both', expand=True)

        # Export
        exp_frame = ttk.LabelFrame(parent, text="💾 EXPORT", padding="10", style='Card.TLabelframe')
        exp_frame.pack(fill='x')

        exp_btns = tk.Frame(exp_frame, bg=self.colors['surface'])
        exp_btns.pack(fill='x')

        ttk.Button(exp_btns, text="Xuất Success TXT",
                  command=self.export_txt,
                  style='Accent.TButton').pack(side='left', fill='x', expand=True, padx=(0, 3))

        ttk.Button(exp_btns, text="Xuất Success EXCEL",
                  command=self.export_excel,
                  style='Accent.TButton').pack(side='right', fill='x', expand=True, padx=(3, 0))

    def setup_right_panel(self, parent):
        """Setup table panel"""
        container = ttk.LabelFrame(parent, text="📋 RESULTS", padding="10", style='Card.TLabelframe')
        container.pack(fill='both', expand=True)

        table_frame = ttk.Frame(container, style='Card.TFrame')
        table_frame.pack(fill='both', expand=True)

        # Columns: STT, Email, Pass, Birthday, Username, IP, Trạng thái, Bắt đầu, Kết thúc
        columns = ("STT", "Email", "Pass", "Birthday", "Username", "IP", "Status", "Start", "End")

        style = ttk.Style()
        style.configure("Treeview",
                       background=self.colors['bg'],
                       foreground=self.colors['text'],
                       fieldbackground=self.colors['bg'],
                       borderwidth=0,
                       rowheight=25,
                       font=('Segoe UI', 8))
        style.configure("Treeview.Heading",
                       background=self.colors['surface_light'],
                       foreground=self.colors['text'],
                       borderwidth=1,
                       relief='flat',
                       font=('Segoe UI', 9, 'bold'))
        style.map('Treeview', background=[('selected', self.colors['primary'])])

        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=25)

        self.tree.heading("STT", text="STT")
        self.tree.heading("Email", text="Email")
        self.tree.heading("Pass", text="Pass")
        self.tree.heading("Birthday", text="Birthday")
        self.tree.heading("Username", text="Username")
        self.tree.heading("IP", text="IP")
        self.tree.heading("Status", text="Trạng Thái")
        self.tree.heading("Start", text="Bắt Đầu")
        self.tree.heading("End", text="Kết Thúc")

        self.tree.column("STT", width=50, anchor='center')
        self.tree.column("Email", width=200)
        self.tree.column("Pass", width=120)
        self.tree.column("Birthday", width=100)
        self.tree.column("Username", width=120)
        self.tree.column("IP", width=120, anchor='center')
        self.tree.column("Status", width=250)
        self.tree.column("Start", width=80, anchor='center')
        self.tree.column("End", width=80, anchor='center')

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

    def log(self, message):
        """Thêm log message"""
        if self.log_text is None:
            return
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_msg = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, log_msg)
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def open_profiles_folder(self):
        """Mở thư mục profiles"""
        try:
            profiles_path = "C:\\temp\\tiktok_reg_profiles"
            os.makedirs(profiles_path, exist_ok=True)
            import subprocess
            subprocess.run(['explorer', profiles_path], check=True)
            self.log(f"Đã mở thư mục profiles: {profiles_path}")
        except Exception as e:
            self.log(f"❌ Lỗi mở thư mục profiles: {e}")

    def open_telegram(self):
        """Mở Telegram"""
        try:
            import webbrowser
            webbrowser.open('https://t.me/justin_chan17')
            self.log(f"📱 Đã mở Telegram: @justin_chan17")
        except Exception as e:
            self.log(f"❌ Lỗi mở Telegram: {e}")

    def import_proxy(self):
        """
        Import danh sách proxy từ file .txt
        Hỗ trợ các định dạng:
        - ip:port
        - ip|port
        - ip:port:username:password (sẽ chỉ lấy ip:port)
        """
        try:
            file_path = filedialog.askopenfilename(
                title="Chọn file proxy",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                initialdir=os.path.dirname(os.path.abspath(__file__))
            )

            if file_path:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                self.proxy_list = []
                skipped = 0

                for line_num, line in enumerate(lines, 1):
                    line = line.strip()

                    # Bỏ qua dòng trống hoặc comment
                    if not line or line.startswith('#'):
                        continue

                    try:
                        # Format 1: ip:port (ưu tiên)
                        if ':' in line:
                            parts = line.split(':')
                            if len(parts) >= 2:
                                ip = parts[0].strip()
                                port = parts[1].strip()

                                # Validate IP và port
                                if ip and port.isdigit():
                                    self.proxy_list.append(f"{ip}:{port}")
                                else:
                                    self.log(f"⚠️ Dòng {line_num} format không hợp lệ: {line}")
                                    skipped += 1
                            else:
                                self.log(f"⚠️ Dòng {line_num} thiếu thông tin: {line}")
                                skipped += 1

                        # Format 2: ip|port (fallback)
                        elif '|' in line:
                            parts = line.split('|')
                            if len(parts) >= 2:
                                ip = parts[0].strip()
                                port = parts[1].strip()

                                if ip and port.isdigit():
                                    self.proxy_list.append(f"{ip}:{port}")
                                else:
                                    self.log(f"⚠️ Dòng {line_num} format không hợp lệ: {line}")
                                    skipped += 1
                            else:
                                self.log(f"⚠️ Dòng {line_num} thiếu thông tin: {line}")
                                skipped += 1

                        else:
                            self.log(f"⚠️ Dòng {line_num} không có dấu ':' hoặc '|': {line}")
                            skipped += 1

                    except Exception as line_error:
                        self.log(f"⚠️ Lỗi đọc dòng {line_num}: {line_error}")
                        skipped += 1

                self.proxy_index = 0
                self.proxy_count_label.config(text=f"({len(self.proxy_list)})")

                success_msg = f"✅ Đã import {len(self.proxy_list)} proxy"
                if skipped > 0:
                    success_msg += f" (bỏ qua {skipped} dòng lỗi)"

                self.log(f"{success_msg} từ file: {os.path.basename(file_path)}")

                if len(self.proxy_list) > 0:
                    self.log(f"📋 Ví dụ proxy đầu tiên: {self.proxy_list[0]}")
                    messagebox.showinfo("Thành công", f"{success_msg}!")
                else:
                    messagebox.showwarning("Cảnh báo", "Không có proxy hợp lệ nào trong file!")

        except Exception as e:
            self.log(f"❌ Lỗi import proxy: {e}")
            messagebox.showerror("Lỗi", f"Không thể import proxy: {e}")

    def get_next_proxy(self):
        """Lấy proxy tiếp theo theo Round-Robin"""
        with self.proxy_lock:
            if not self.proxy_list:
                return None

            proxy = self.proxy_list[self.proxy_index]
            self.proxy_index = (self.proxy_index + 1) % len(self.proxy_list)
            return proxy

    def generate_random_email(self):
        """Tạo email ngẫu nhiên: 12 ký tự (chữ và số) @vinacode.co"""
        chars = string.ascii_lowercase + string.digits
        username = ''.join(random.choice(chars) for _ in range(12))
        return f"{username}@vinacode.co"

    def generate_random_password(self):
        """Tạo password ngẫu nhiên có 1 ký tự @, chữ hoa, chữ thường và số"""
        # Tạo password 12-16 ký tự
        length = random.randint(12, 16)

        # Đảm bảo có ít nhất 1 chữ hoa, 1 chữ thường, 1 số
        password = [
            random.choice(string.ascii_uppercase),
            random.choice(string.ascii_lowercase),
            random.choice(string.digits),
            '@'
        ]

        # Fill the rest
        for _ in range(length - 4):
            password.append(random.choice(string.ascii_letters + string.digits))

        # Shuffle
        random.shuffle(password)
        return ''.join(password)

    def generate_random_birthday(self):
        """Tạo ngày sinh ngẫu nhiên"""
        month = random.randint(1, 12)

        # Days in month
        days_in_month = {
            1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30,
            7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31
        }
        day = random.randint(1, days_in_month[month])

        # Year (18-40 tuổi)
        current_year = datetime.now().year
        year = random.randint(current_year - 40, current_year - 18)

        return month, day, year

    def generate_random_username(self):
        """Tạo username ngẫu nhiên"""
        chars = string.ascii_lowercase + string.digits
        length = random.randint(6, 12)
        return ''.join(random.choice(chars) for _ in range(length))

    def generate_random_bio(self):
        """Tạo tiểu sử ngẫu nhiên"""
        bios = [
            "Never give up",
            "Dream big, work hard",
            "Stay positive",
            "Living my best life",
            "Create your own sunshine",
            "Be yourself",
            "Keep smiling",
            "Just be happy",
            "Love life",
            "Making memories"
        ]
        return random.choice(bios)

    def start_register(self):
        """Bắt đầu đăng ký tài khoản"""
        try:
            self.num_accounts = int(self.num_accounts_var.get())
            self.num_threads = int(self.thread_var.get())
        except:
            self.num_accounts = 1
            self.num_threads = 1

        self.headless_mode = self.headless_var.get()
        self.is_running = True
        self.start_button['state'] = 'disabled'
        self.stop_button['state'] = 'normal'
        self.created_count = 0
        self.success_count = 0
        self.error_count = 0
        self.results = []

        # Clear table
        self.tree.delete(*self.tree.get_children())

        # Reset row mapping
        with self.row_lock:
            self.index_to_row.clear()

        # KHÔNG tạo sẵn dòng trống - chỉ thêm khi account được tạo thành công

        mode_text = "Headless" if self.headless_mode else "Normal"
        self.log(f"▶️ Bắt đầu đăng ký {self.num_accounts} tài khoản với {self.num_threads} luồng ({mode_text} mode)...")

        threading.Thread(target=self.run_register, daemon=True).start()

    def stop_register(self):
        """Dừng đăng ký"""
        self.is_running = False
        self.start_button['state'] = 'normal'
        self.stop_button['state'] = 'disabled'
        self.log("⏸️ Đã dừng đăng ký")

    def cleanup_chrome_processes(self):
        """Kill tất cả Chrome processes đã track khi tool tắt"""
        try:
            with self.pids_lock:
                for pid in self.chrome_pids.copy():
                    try:
                        parent = psutil.Process(pid)
                        # Kill tất cả child processes
                        for child in parent.children(recursive=True):
                            try:
                                child.kill()
                            except:
                                pass
                        # Kill parent process
                        parent.kill()
                    except psutil.NoSuchProcess:
                        pass
                    except Exception as e:
                        pass
                self.chrome_pids.clear()
        except Exception as e:
            pass

    def on_closing(self):
        """Xử lý khi đóng tool"""
        try:
            self.cleanup_chrome_processes()
        except:
            pass
        finally:
            self.root.destroy()

    def cleanup_old_chrome_on_startup(self):
        """Kill tất cả Chrome và ChromeDriver cũ khi tool khởi động"""
        try:
            import subprocess
            # Kill tất cả chrome.exe
            try:
                subprocess.run(['taskkill', '/F', '/IM', 'chrome.exe', '/T'],
                             capture_output=True, timeout=5)
            except:
                pass
            # Kill tất cả undetected_chromedriver.exe
            try:
                subprocess.run(['taskkill', '/F', '/IM', 'undetected_chromedriver.exe', '/T'],
                             capture_output=True, timeout=5)
            except:
                pass
            # Kill tất cả chromedriver.exe
            try:
                subprocess.run(['taskkill', '/F', '/IM', 'chromedriver.exe', '/T'],
                             capture_output=True, timeout=5)
            except:
                pass
        except Exception as e:
            pass  # Không log lỗi để tránh làm phiền user

    def run_register(self):
        """Chạy quá trình đăng ký với multi-threading"""
        try:
            from concurrent.futures import ThreadPoolExecutor, as_completed
            import threading

            active_tasks = 0
            tasks_lock = threading.Lock()

            def task_wrapper(index):
                nonlocal active_tasks
                try:
                    # Đợi nếu đã có đủ số threads đang chạy
                    while True:
                        with tasks_lock:
                            if active_tasks < self.num_threads:
                                active_tasks += 1
                                break
                        time.sleep(0.5)

                    # Chạy task với try-except để catch mọi lỗi
                    try:
                        self.register_account(index)
                    except Exception as e:
                        self.log(f"❌ #{index+1}: Lỗi critical - {str(e)}")
                        import traceback
                        self.log(f"❌ #{index+1}: Traceback: {traceback.format_exc()}")

                except Exception as e:
                    self.log(f"❌ #{index+1}: Lỗi task wrapper - {str(e)}")
                finally:
                    with tasks_lock:
                        active_tasks -= 1

            with ThreadPoolExecutor(max_workers=self.num_threads * 2) as executor:
                futures = []
                for i in range(self.num_accounts):
                    if not self.is_running:
                        break

                    # Submit task
                    future = executor.submit(task_wrapper, i)
                    futures.append(future)

                    # DELAY NGAY SAU KHI SUBMIT để Chrome mở cách nhau
                    if i < self.num_accounts - 1:
                        if i == 0:
                            # Tab thứ 2 delay 4-5 giây
                            time.sleep(random.uniform(4.0, 5.0))
                        else:
                            # Các tab sau delay 2-3 giây
                            time.sleep(random.uniform(2.0, 3.0))

                for future in as_completed(futures):
                    if not self.is_running:
                        break

            self.log("✅ Hoàn thành đăng ký tất cả tài khoản!")
            messagebox.showinfo("Hoàn thành",
                              f"Đã đăng ký xong!\n\n✅ Success: {self.success_count}\n❌ Error: {self.error_count}")

        except Exception as e:
            self.log(f"❌ Lỗi trong quá trình đăng ký: {e}")
        finally:
            self.is_running = False
            self.start_button['state'] = 'normal'
            self.stop_button['state'] = 'disabled'

    def push_to_api(self, email, password, username, display_name, bio, avatar_url, birthday, tiktok_url, account_id=None, status='live', error_message=None, proxy_ip=None):
        """Push thông tin tài khoản lên API server (add hoặc update)"""
        try:
            # Random User Agent từ pool
            random_user_agent = random.choice(self.user_agents)

            headers = {
                'X-API-Key': self.api_key,
                'Content-Type': 'application/json',
                'User-Agent': random_user_agent,
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9,vi;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Origin': 'https://justin.vinacode.co',
                'Referer': 'https://justin.vinacode.co/',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin'
            }

            data = {
                'email': email,
                'password': password,
                'username': username,
                'display_name': display_name,
                'bio': bio,
                'avatar_url': avatar_url,
                'birthday': birthday,
                'status': status,
                'tiktok_url': tiktok_url,
                'ads_registered': True
            }

            # Thêm proxy_ip nếu có
            if proxy_ip:
                data['proxy_ip'] = proxy_ip

            # Thêm error_message nếu có
            if error_message:
                data['error_message'] = error_message

            # Nếu có account_id thì UPDATE, không thì ADD mới
            if account_id:
                data['id'] = account_id
                endpoint = f"{self.api_url}?path=update"
            else:
                endpoint = f"{self.api_url}?path=add"

            # Tạo session với retry để bypass Cloudflare
            session = requests.Session()
            session.headers.update(headers)

            response = session.post(
                endpoint,
                json=data,
                timeout=15,
                verify=True
            )

            if response.status_code in [200, 201]:
                # Kiểm tra Content-Type trước khi parse JSON
                content_type = response.headers.get('Content-Type', '')

                # Debug: Log raw response nếu không phải JSON
                if 'application/json' not in content_type:
                    self.log(f"⚠️ API: Response không phải JSON. Content-Type: {content_type}")
                    self.log(f"⚠️ API: Response preview: {response.text[:200]}")
                    return None

                try:
                    # Clean response text trước khi parse (remove BOM và control characters)
                    response_text = response.text.strip()
                    # Remove BOM nếu có
                    if response_text.startswith('\ufeff'):
                        response_text = response_text[1:]

                    import json
                    result = json.loads(response_text)

                    if result.get('success'):
                        returned_id = result.get('account_id', account_id)
                        action = "Updated" if account_id else "Added"
                        self.log(f"✅ API: {action} (ID: {returned_id})")
                        return returned_id
                    else:
                        self.log(f"⚠️ API: {result.get('error', 'Unknown error')}")
                        return None
                except json.JSONDecodeError as je:
                    # Log chi tiết lỗi JSON
                    self.log(f"⚠️ API: JSON parse error - {str(je)}")
                    self.log(f"⚠️ API: Response preview: {response.text[:200]}")
                    # Log response dưới dạng bytes để xem ký tự ẩn
                    self.log(f"⚠️ API: Response bytes: {response.content[:100]}")
                    return None
            else:
                self.log(f"⚠️ API: HTTP {response.status_code}")
                return None

        except Exception as e:
            self.log(f"⚠️ API: Không thể push lên server - {str(e)}")
            return None

    def register_account(self, index):
        """Đăng ký một tài khoản TikTok"""
        if not self.is_running:
            return

        start_time = datetime.now().strftime("%H:%M:%S")
        self.update_table_row(index, start=start_time)

        # Generate random data
        email = self.generate_random_email()
        password = self.generate_random_password()
        month, day, year = self.generate_random_birthday()
        birthday = f"{month:02d}/{day:02d}/{year}"  # Format MM/DD/YYYY cho TikTok
        birthday_db = f"{year}-{month:02d}-{day:02d}"  # Format YYYY-MM-DD cho MySQL
        username = self.generate_random_username()
        bio = self.generate_random_bio()
        avatar_url = None  # Lưu URL avatar để push lên API
        tiktok_profile_url = None  # Lưu TikTok profile URL
        account_id = None  # Lưu ID từ API để update sau

        self.log(f"🆕 #{index+1}: Email={email}, Pass={password[:4]}***, Birthday={birthday}")
        self.update_table_row(index, email=email, password=password, birthday=birthday)

        driver = None
        proxy_ip = None
        try:
            # Lấy proxy tiếp theo (nếu có)
            proxy_ip = self.get_next_proxy()
            if proxy_ip:
                self.log(f"🌐 #{index+1}: Sử dụng Proxy: {proxy_ip}")

            # Random User Agent từ pool cho mỗi tài khoản
            random_user_agent = random.choice(self.user_agents)
            self.log(f"🌐 #{index+1}: User Agent: {random_user_agent[:50]}...")

            # Start Chrome với undetected-chromedriver (KHÔNG dùng profile riêng để nhẹ máy)
            chrome_options = uc.ChromeOptions()
            chrome_options.add_argument("--no-first-run")
            chrome_options.add_argument("--no-default-browser-check")
            chrome_options.add_argument("--lang=en")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")

            # Thêm proxy nếu có
            if proxy_ip:
                # Thử HTTP proxy trước (phổ biến hơn), nếu lỗi thì dùng SOCKS5
                chrome_options.add_argument(f'--proxy-server=http://{proxy_ip}')

            # Add headless mode if enabled
            if self.headless_mode:
                chrome_options.add_argument("--headless=new")
                chrome_options.add_argument("--disable-gpu")
                chrome_options.add_argument("--window-size=1920,1080")
                chrome_options.add_argument("--disable-blink-features=AutomationControlled")
                chrome_options.add_argument(f"--user-agent={random_user_agent}")
            else:
                # Normal mode - cửa sổ nhỏ
                chrome_options.add_argument("--window-size=600,800")
                # Thêm User Agent cho normal mode
                chrome_options.add_argument(f"--user-agent={random_user_agent}")

            # QUAN TRỌNG: Dùng undetected-chromedriver thay vì Selenium thường
            # Điều này loại bỏ TẤT CẢ dấu hiệu automation mà Selenium bỏ sót
            import warnings
            warnings.filterwarnings('ignore')

            # Tắt logging của ChromeDriver
            chrome_options.add_argument('--log-level=3')

            # Khởi tạo Chrome với error handling tốt hơn
            try:
                driver = uc.Chrome(
                    options=chrome_options,
                    use_subprocess=True,
                    version_main=None,  # Auto-detect Chrome version
                    suppress_welcome=True
                )
            except Exception as chrome_error:
                error_msg = str(chrome_error)
                if "chrome" in error_msg.lower() or "browser" in error_msg.lower():
                    self.log(f"❌ #{index+1}: Không tìm thấy Chrome browser trên máy!")
                    self.log(f"❌ #{index+1}: Vui lòng cài đặt Google Chrome: https://www.google.com/chrome/")
                    self.update_table_row(index, status="❌ Thiếu Chrome")
                    return
                else:
                    self.log(f"❌ #{index+1}: Lỗi khởi tạo Chrome: {error_msg}")
                    self.update_table_row(index, status=f"❌ Lỗi Chrome")
                    return

            # Track Chrome PID để cleanup khi tool đóng
            try:
                # Track ChromeDriver service PID
                if hasattr(driver, 'service') and hasattr(driver.service, 'process'):
                    service_pid = driver.service.process.pid
                    with self.pids_lock:
                        self.chrome_pids.add(service_pid)

                # Track Chrome browser PID (quan trọng!)
                try:
                    # Lấy browser PID từ CDP (Chrome DevTools Protocol)
                    if hasattr(driver, 'browser_pid'):
                        with self.pids_lock:
                            self.chrome_pids.add(driver.browser_pid)

                    # Backup: Tìm Chrome process theo parent PID
                    import psutil
                    for proc in psutil.process_iter(['pid', 'name', 'ppid']):
                        try:
                            if 'chrome' in proc.info['name'].lower():
                                # Thêm tất cả Chrome processes liên quan
                                with self.pids_lock:
                                    self.chrome_pids.add(proc.info['pid'])
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                except:
                    pass
            except:
                pass

            # Set window size sau khi khởi tạo (cho chắc chắn)
            if not self.headless_mode:
                driver.set_window_size(600, 800)
                driver.set_window_position(100, 50)

            # Set page load timeout
            driver.set_page_load_timeout(60)

            # BƯỚC 0: Kiểm tra IP hiện tại (luôn check, kể cả không dùng proxy)
            current_ip = None
            try:
                self.update_table_row(index, status="Đang kiểm tra IP...")
                if proxy_ip:
                    self.log(f"🔍 #{index+1}: Kiểm tra IP với proxy {proxy_ip}...")
                else:
                    self.log(f"🔍 #{index+1}: Kiểm tra IP (không dùng proxy)...")

                driver.get("https://api.ipify.org?format=json")
                time.sleep(2)

                # Lấy IP từ response
                page_source = driver.page_source
                if '"ip"' in page_source:
                    import json
                    try:
                        ip_data = json.loads(driver.find_element(By.TAG_NAME, 'pre').text)
                        current_ip = ip_data.get('ip', 'Unknown')
                        self.log(f"✅ #{index+1}: IP hiện tại: {current_ip}")
                        self.update_table_row(index, ip=current_ip)
                    except:
                        current_ip = page_source.split('"ip":"')[1].split('"')[0] if '"ip":"' in page_source else 'Unknown'
                        self.log(f"✅ #{index+1}: IP hiện tại: {current_ip}")
                        self.update_table_row(index, ip=current_ip)
                else:
                    self.log(f"⚠️ #{index+1}: Không thể kiểm tra IP")
                    self.update_table_row(index, ip="Check failed")
            except Exception as ip_err:
                self.log(f"⚠️ #{index+1}: Lỗi khi check IP: {ip_err}")
                self.update_table_row(index, ip="Error")

            # BƯỚC 1: Mở trực tiếp trang đăng ký
            self.update_table_row(index, status="Đang mở trang đăng ký...")
            self.log(f"📄 #{index+1}: Mở trang đăng ký TikTok")
            driver.get("https://www.tiktok.com/signup/phone-or-email/email")

            # Wait for page load
            time.sleep(3)

            # Bước 2: Chọn Birthday (Month, Day, Year)
            self.update_table_row(index, status="Chọn ngày sinh...")
            self.log(f"📅 #{index+1}: Chọn ngày sinh: {birthday}")

            try:
                # Tìm và click vào Month dropdown
                month_dropdown_selectors = [
                    "//div[contains(text(), 'Month')]",
                    "//input[@placeholder='Month']",
                    "//div[@aria-label='Month']",
                    "//div[contains(@class, 'month')]//input"
                ]

                month_dropdown = self.find_element_multi(driver, month_dropdown_selectors, timeout=15)
                if month_dropdown:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", month_dropdown)
                    time.sleep(0.5)
                    month_dropdown.click()
                    time.sleep(1)

                    # Tìm option month trong dropdown menu (các tháng được hiển thị sau khi click)
                    month_names = ['January', 'February', 'March', 'April', 'May', 'June',
                                   'July', 'August', 'September', 'October', 'November', 'December']
                    month_name = month_names[month - 1]

                    # Tìm dropdown menu container
                    menu_selectors = [
                        "//div[contains(@class, 'dropdown')]",
                        "//div[contains(@class, 'menu')]",
                        "//div[@role='listbox']",
                        "//ul[contains(@class, 'options')]",
                        "//div[contains(@class, 'options')]"
                    ]

                    dropdown_menu = None
                    for selector in menu_selectors:
                        try:
                            menus = driver.find_elements(By.XPATH, selector)
                            for menu in menus:
                                if menu.is_displayed():
                                    dropdown_menu = menu
                                    break
                            if dropdown_menu:
                                break
                        except:
                            continue

                    # Scroll trong dropdown để tìm option (giống hành vi người dùng thật)
                    month_option_selectors = [
                        f"//div[text()='{month_name}']",
                        f"//div[contains(text(), '{month_name}')]",
                        f"//div[contains(@class, 'option') and contains(text(), '{month_name}')]",
                        f"//div[@role='option' and contains(text(), '{month_name}')]",
                        f"//li[contains(text(), '{month_name}')]",
                        f"//*[text()='{month_name}']"
                    ]

                    month_option = self.find_element_multi(driver, month_option_selectors, timeout=10)
                    if month_option:
                        # Scroll option vào view trong dropdown menu
                        if dropdown_menu:
                            driver.execute_script("arguments[0].scrollTop = arguments[1].offsetTop - arguments[0].offsetTop;", dropdown_menu, month_option)
                            time.sleep(0.3)

                        # Scroll option vào view trong page
                        driver.execute_script("arguments[0].scrollIntoView({block: 'nearest', inline: 'nearest'});", month_option)
                        time.sleep(0.3)

                        # Click vào option
                        month_option.click()
                        time.sleep(0.5)
                        self.log(f"✅ #{index+1}: Đã chọn tháng: {month_name}")

                        # QUAN TRỌNG: Click ra ngoài để trigger validation và hiển thị trường tiếp theo
                        driver.find_element(By.TAG_NAME, 'body').click()
                        time.sleep(0.5)
                    else:
                        raise Exception(f"Không tìm thấy option tháng {month_name}")
                else:
                    raise Exception("Không tìm thấy dropdown Month")

                # Tìm và click vào Day dropdown
                day_dropdown_selectors = [
                    "//div[contains(text(), 'Day')]",
                    "//input[@placeholder='Day']",
                    "//div[@aria-label='Day']",
                    "//div[contains(@class, 'day')]//input"
                ]

                day_dropdown = self.find_element_multi(driver, day_dropdown_selectors, timeout=10)
                if day_dropdown:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", day_dropdown)
                    time.sleep(0.5)
                    day_dropdown.click()
                    time.sleep(1)

                    # Tìm dropdown menu container
                    dropdown_menu = None
                    for selector in menu_selectors:
                        try:
                            menus = driver.find_elements(By.XPATH, selector)
                            for menu in menus:
                                if menu.is_displayed():
                                    dropdown_menu = menu
                                    break
                            if dropdown_menu:
                                break
                        except:
                            continue

                    # Tìm option day
                    day_option_selectors = [
                        f"//div[text()='{day}']",
                        f"//div[contains(text(), '{day}')]",
                        f"//div[contains(@class, 'option') and text()='{day}']",
                        f"//div[@role='option' and text()='{day}']",
                        f"//li[text()='{day}']",
                        f"//*[text()='{day}']"
                    ]

                    day_option = self.find_element_multi(driver, day_option_selectors, timeout=10)
                    if day_option:
                        # Scroll option vào view trong dropdown menu
                        if dropdown_menu:
                            driver.execute_script("arguments[0].scrollTop = arguments[1].offsetTop - arguments[0].offsetTop;", dropdown_menu, day_option)
                            time.sleep(0.3)

                        # Scroll option vào view trong page
                        driver.execute_script("arguments[0].scrollIntoView({block: 'nearest', inline: 'nearest'});", day_option)
                        time.sleep(0.3)

                        # Click vào option
                        day_option.click()
                        time.sleep(0.5)
                        self.log(f"✅ #{index+1}: Đã chọn ngày: {day}")

                        # QUAN TRỌNG: Click ra ngoài để trigger validation và hiển thị trường tiếp theo
                        driver.find_element(By.TAG_NAME, 'body').click()
                        time.sleep(0.5)
                    else:
                        raise Exception(f"Không tìm thấy option ngày {day}")
                else:
                    raise Exception("Không tìm thấy dropdown Day")

                # Tìm và click vào Year dropdown
                year_dropdown_selectors = [
                    "//div[contains(text(), 'Year')]",
                    "//input[@placeholder='Year']",
                    "//div[@aria-label='Year']",
                    "//div[contains(@class, 'year')]//input"
                ]

                year_dropdown = self.find_element_multi(driver, year_dropdown_selectors, timeout=10)
                if year_dropdown:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", year_dropdown)
                    time.sleep(0.5)
                    year_dropdown.click()
                    time.sleep(1)

                    # Tìm dropdown menu container
                    dropdown_menu = None
                    for selector in menu_selectors:
                        try:
                            menus = driver.find_elements(By.XPATH, selector)
                            for menu in menus:
                                if menu.is_displayed():
                                    dropdown_menu = menu
                                    break
                            if dropdown_menu:
                                break
                        except:
                            continue

                    # Tìm option year
                    year_option_selectors = [
                        f"//div[text()='{year}']",
                        f"//div[contains(text(), '{year}')]",
                        f"//div[contains(@class, 'option') and text()='{year}']",
                        f"//div[@role='option' and text()='{year}']",
                        f"//li[text()='{year}']",
                        f"//*[text()='{year}']"
                    ]

                    year_option = self.find_element_multi(driver, year_option_selectors, timeout=10)
                    if year_option:
                        # Scroll option vào view trong dropdown menu (QUAN TRỌNG cho Year vì list dài!)
                        if dropdown_menu:
                            driver.execute_script("arguments[0].scrollTop = arguments[1].offsetTop - arguments[0].offsetTop;", dropdown_menu, year_option)
                            time.sleep(0.5)  # Tăng thời gian chờ cho year vì list dài

                        # Scroll option vào view trong page
                        driver.execute_script("arguments[0].scrollIntoView({block: 'nearest', inline: 'nearest'});", year_option)
                        time.sleep(0.3)

                        # Click vào option
                        year_option.click()
                        time.sleep(0.5)
                        self.log(f"✅ #{index+1}: Đã chọn năm: {year}")

                        # QUAN TRỌNG: Click ra ngoài để trigger validation và hiển thị trường tiếp theo
                        driver.find_element(By.TAG_NAME, 'body').click()
                        time.sleep(0.5)
                    else:
                        # Nếu không tìm thấy, thử scroll nhiều lần để tìm năm
                        self.log(f"⚠️ #{index+1}: Thử scroll để tìm năm {year}")

                        if dropdown_menu:
                            # Scroll từ từ trong dropdown để tìm năm
                            max_scrolls = 20
                            for i in range(max_scrolls):
                                driver.execute_script(f"arguments[0].scrollTop = {i * 100};", dropdown_menu)
                                time.sleep(0.2)

                                # Thử tìm lại option sau mỗi lần scroll
                                year_option = self.find_element_multi(driver, year_option_selectors, timeout=1)
                                if year_option:
                                    driver.execute_script("arguments[0].scrollIntoView({block: 'nearest', inline: 'nearest'});", year_option)
                                    time.sleep(0.3)
                                    year_option.click()
                                    time.sleep(0.5)
                                    self.log(f"✅ #{index+1}: Đã chọn năm: {year} sau khi scroll")

                                    # QUAN TRỌNG: Click ra ngoài để trigger validation và hiển thị trường tiếp theo
                                    driver.find_element(By.TAG_NAME, 'body').click()
                                    time.sleep(0.5)
                                    break
                            else:
                                raise Exception(f"Không tìm thấy option năm {year} sau khi scroll")
                        else:
                            raise Exception(f"Không tìm thấy dropdown menu để scroll tìm năm {year}")
                else:
                    raise Exception("Không tìm thấy dropdown Year")

                self.log(f"✅ #{index+1}: Hoàn thành chọn ngày sinh")
                time.sleep(1)

            except Exception as e:
                self.log(f"❌ #{index+1}: Lỗi chọn ngày sinh: {e}")
                # Take screenshot for debugging
                try:
                    screenshot_path = f"C:\\temp\\error_birthday_{index}.png"
                    driver.save_screenshot(screenshot_path)
                    self.log(f"📸 #{index+1}: Đã chụp screenshot: {screenshot_path}")
                except:
                    pass
                raise Exception(f"Không thể chọn ngày sinh: {e}")

            # Bước 3: Input Email
            self.update_table_row(index, status="Nhập Email...")
            self.log(f"📧 #{index+1}: Nhập Email: {email}")

            email_selectors = [
                "//input[@type='email']",
                "//input[@name='email']",
                "//input[@placeholder='Email']",
                "//input[contains(@placeholder, 'email')]"
            ]

            email_input = self.find_element_multi(driver, email_selectors)
            if email_input:
                email_input.clear()
                time.sleep(0.3)
                email_input.send_keys(email)
                time.sleep(0.5)

                # QUAN TRỌNG: Blur để đóng dropdown gợi ý email (KHÔNG dùng ESC vì sẽ đóng modal)
                driver.execute_script("arguments[0].blur();", email_input)
                time.sleep(1.0)

                self.log(f"✅ #{index+1}: Đã nhập Email")
            else:
                raise Exception("Không tìm thấy trường Email")

            # Bước 4: Input Password
            self.update_table_row(index, status="Nhập Password...")
            self.log(f"🔑 #{index+1}: Nhập Password")

            password_selectors = [
                "//input[@type='password']",
                "//input[@placeholder='Password']",
                "//input[contains(@placeholder, 'password')]"
            ]

            password_input = self.find_element_multi(driver, password_selectors)
            if password_input:
                password_input.click()
                time.sleep(random.uniform(0.3, 0.6))

                password_input.clear()
                time.sleep(0.3)

                # Nhập password một phát (nhanh hơn gõ từng ký tự)
                password_input.send_keys(password)
                time.sleep(0.5)

                # Click ra ngoài để trigger JavaScript validation
                driver.execute_script("arguments[0].blur();", password_input)
                time.sleep(0.5)

                # Trigger các event để TikTok validate (input, change, blur)
                driver.execute_script("""
                    var element = arguments[0];
                    element.dispatchEvent(new Event('input', { bubbles: true }));
                    element.dispatchEvent(new Event('change', { bubbles: true }));
                """, password_input)

                # Đợi TikTok validate hoàn toàn
                time.sleep(random.uniform(1.5, 2.0))
                self.log(f"✅ #{index+1}: Đã nhập Password, đang chờ validation...")

                self.log(f"✅ #{index+1}: Password validation hoàn tất")
            else:
                raise Exception("Không tìm thấy trường Password")

            # Bước 5: Click Send code
            self.update_table_row(index, status="Click Send code...")
            self.log(f"📤 #{index+1}: Click Send code")

            # Đợi một chút sau khi nhập password (GIỐNG NGƯỜI THẬT ĐANG ĐỌC/KIỂM TRA)
            # Người thật thường pause 2-4 giây để kiểm tra thông tin trước khi click Send code
            time.sleep(random.uniform(2.0, 4.0))
            self.log(f"✅ #{index+1}: Sẵn sàng click Send code")

            sendcode_selectors = [
                "//button[contains(text(), 'Send code')]",
                "//div[contains(text(), 'Send code')]",
                "//button[contains(text(), 'Get code')]",
                "//button[@type='button' and contains(., 'Send')]",
                "//*[contains(text(), 'Send code')]"
            ]

            sendcode_btn = None
            for selector in sendcode_selectors:
                try:
                    elements = driver.find_elements(By.XPATH, selector)
                    for elem in elements:
                        if elem.is_displayed():
                            # Scroll vào view
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
                            time.sleep(0.5)

                            # Kiểm tra button có enabled không
                            is_disabled = elem.get_attribute('disabled')
                            class_name = elem.get_attribute('class') or ''

                            if not is_disabled and 'disabled' not in class_name.lower():
                                sendcode_btn = elem
                                break
                    if sendcode_btn:
                        break
                except Exception as e:
                    self.log(f"⚠️ #{index+1}: Thử selector tiếp theo: {e}")
                    continue

            if sendcode_btn:
                try:
                    # Di chuyển chuột đến button GIỐNG NGƯỜI THẬT (KHÔNG DÙNG JavaScript click)
                    actions = ActionChains(driver)

                    # Scroll button vào view trước
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", sendcode_btn)
                    time.sleep(random.uniform(0.5, 1.0))

                    # Di chuyển chuột đến button (giống người thật)
                    actions.move_to_element(sendcode_btn).pause(random.uniform(0.3, 0.7))

                    # Click thật
                    actions.click().perform()

                    self.log(f"✅ #{index+1}: Đã click Send code (human-like)")
                except Exception as e:
                    self.log(f"⚠️ #{index+1}: Lỗi click Send code: {e}")
                    # Fallback: click thông thường (KHÔNG dùng JavaScript)
                    sendcode_btn.click()
                    self.log(f"✅ #{index+1}: Đã click Send code (fallback)")
            else:
                # Take screenshot để debug
                screenshot_path = f"C:\\temp\\error_sendcode_{index}.png"
                driver.save_screenshot(screenshot_path)
                self.log(f"📸 #{index+1}: Không tìm thấy button Send code, đã chụp screenshot: {screenshot_path}")
                raise Exception("Không tìm thấy nút Send code hoặc button bị disabled")

            # Bước 6: Đợi Captcha xuất hiện sau khi click Send code
            self.log(f"⏳ #{index+1}: Đang đợi Captcha xuất hiện (hoặc timeout sau 15s)...")

            # Đợi captcha xuất hiện trong tối đa 15 giây
            captcha_appeared = False
            for wait_time in range(15):
                time.sleep(1)
                if self.check_captcha_exists(driver):
                    captcha_appeared = True
                    self.log(f"🔐 #{index+1}: Phát hiện Captcha sau {wait_time+1}s")
                    break

            if captcha_appeared:
                self.update_table_row(index, status="Đang giải Captcha...")

                captcha_solved = self.solve_captcha(driver, email)
                if not captcha_solved:
                    raise Exception("Không thể giải Captcha")

                self.log(f"✅ #{index+1}: Giải Captcha thành công!")
                time.sleep(2)
            else:
                self.log(f"ℹ️ #{index+1}: Không có Captcha sau 15s, tiếp tục đọc email")

            # Bước 7: Đọc email từ IMAP để lấy 6-digit code
            # Chỉ đọc email sau khi đã giải Captcha xong
            self.update_table_row(index, status="Đọc email lấy code...")
            self.log(f"📬 #{index+1}: Bắt đầu đọc email để lấy 6-digit code")

            verification_code = self.read_verification_code_from_imap(email)
            if not verification_code:
                raise Exception("Không lấy được mã xác nhận từ email")

            self.log(f"✅ #{index+1}: Nhận được code: {verification_code}")

            # Bước 8: Input 6-digit verification code
            self.update_table_row(index, status="Nhập mã xác nhận...")
            self.log(f"⌨️ #{index+1}: Nhập 6-digit code")

            code_input_selectors = [
                "//input[@placeholder='Enter 6-digit code']",
                "//input[contains(@placeholder, 'code')]",
                "//input[@type='text' and @maxlength='6']"
            ]

            code_input = self.find_element_multi(driver, code_input_selectors)
            if code_input:
                code_input.clear()
                code_input.send_keys(verification_code)
                time.sleep(1)
            else:
                raise Exception("Không tìm thấy trường nhập code")

            # Bước 9: Click Next (sau khi nhập code)
            self.update_table_row(index, status="Click Next...")
            self.log(f"👉 #{index+1}: Click Next")

            next_selectors = [
                "//button[contains(text(), 'Next')]",
                "//button[@type='submit']",
                "//div[contains(text(), 'Next')]"
            ]

            next_btn = self.find_element_multi(driver, next_selectors)
            if next_btn:
                next_btn.click()
                time.sleep(3)
            else:
                raise Exception("Không tìm thấy nút Next")

            # ===== PUSH LẦN 1: Sau khi nhập code và click Next =====
            try:
                self.log(f"📤 #{index+1}: [Push 1/3] Đang push thông tin cơ bản lên server...")
                response = self.push_to_api(
                    email=email,
                    password=password,
                    username=None,
                    display_name=None,
                    bio=None,
                    avatar_url=None,
                    birthday=birthday_db,
                    tiktok_url=None,
                    proxy_ip=current_ip
                )
                if response:
                    account_id = response  # Lưu ID để update sau
            except Exception as api_err:
                self.log(f"⚠️ #{index+1}: [Push 1/3] Lỗi khi push lên API: {api_err}")

            # Bước 10: Input Username (bỏ qua nếu username không available)
            self.update_table_row(index, status="Nhập Username...")
            self.log(f"👤 #{index+1}: Nhập Username: {username}")

            try:
                username_selectors = [
                    "//input[@placeholder='Username']",
                    "//input[@name='username']",
                    "//input[contains(@placeholder, 'username')]"
                ]

                username_input = self.find_element_multi(driver, username_selectors, timeout=5)
                if username_input:
                    username_input.clear()
                    username_input.send_keys(username)
                    time.sleep(2)  # Đợi TikTok check username
                else:
                    self.log(f"⚠️ #{index+1}: Không tìm thấy trường Username, bỏ qua")
                    raise Exception("Skip username")

                # Update username in table
                self.update_table_row(index, username=username)

                # Bước 11: Click Sign up (kiểm tra button có disabled không)
                self.update_table_row(index, status="Click Sign up...")
                self.log(f"✍️ #{index+1}: Click Sign up")

                signup_selectors = [
                    "//button[contains(text(), 'Sign up')]",
                    "//button[contains(text(), 'Register')]",
                    "//button[@type='submit']"
                ]

                signup_btn = self.find_element_multi(driver, signup_selectors, timeout=5)
                if signup_btn:
                    # Kiểm tra button có disabled không
                    is_disabled = signup_btn.get_attribute('disabled')
                    if is_disabled:
                        self.log(f"⚠️ #{index+1}: Username '{username}' không available, bỏ qua")
                        raise Exception("Skip username")
                    else:
                        signup_btn.click()
                        self.log(f"✅ #{index+1}: Đã click Sign up, đang đợi phản hồi...")

                        # Đợi lâu hơn để xem phản hồi
                        time.sleep(5)

                        # Chụp screenshot để debug
                        try:
                            screenshot_path = f"C:\\temp\\after_signup_{index}_{username}.png"
                            driver.save_screenshot(screenshot_path)
                            self.log(f"📸 #{index+1}: Screenshot sau khi Sign up: {screenshot_path}")
                        except Exception as ss_err:
                            self.log(f"⚠️ #{index+1}: Không thể chụp screenshot: {ss_err}")

                        # Kiểm tra có lỗi "login expired" hoặc lỗi khác không
                        self.log(f"🔍 #{index+1}: Đang kiểm tra lỗi sau khi submit username...")
                        time.sleep(3)

                        # Kiểm tra các loại lỗi phổ biến
                        expired_error_selectors = [
                            "//*[contains(text(), 'login expired')]",
                            "//*[contains(text(), 'Login expired')]",
                            "//*[contains(text(), 'session expired')]",
                            "//*[contains(text(), 'Session expired')]",
                            "//*[contains(text(), 'expired')]",
                            "//*[contains(text(), 'error')]",
                            "//*[contains(text(), 'Error')]",
                            "//*[contains(text(), 'failed')]",
                            "//*[contains(text(), 'Failed')]",
                            "//*[contains(@class, 'error')]",
                            "//div[@role='alert']"
                        ]

                        error_found = False
                        for selector in expired_error_selectors:
                            try:
                                error_elem = driver.find_elements(By.XPATH, selector)
                                if error_elem and error_elem[0].is_displayed():
                                    error_text = error_elem[0].text
                                    self.log(f"❌ #{index+1}: Phát hiện lỗi: {error_text}")
                                    error_found = True

                                    # Chụp screenshot lỗi
                                    try:
                                        error_screenshot = f"C:\\temp\\error_signup_{index}_{username}.png"
                                        driver.save_screenshot(error_screenshot)
                                        self.log(f"📸 #{index+1}: Screenshot lỗi: {error_screenshot}")
                                    except:
                                        pass

                                    # Push lên API với status = 'die'
                                    try:
                                        self.push_to_api(
                                            email=email,
                                            password=password,
                                            username=username,
                                            display_name=username,
                                            bio=None,
                                            avatar_url=None,
                                            birthday=birthday_db,
                                            tiktok_url=f"https://www.tiktok.com/@{username}",
                                            account_id=account_id,
                                            status='die',
                                            error_message=f"Error after username submission: {error_text}",
                                            proxy_ip=current_ip
                                        )
                                        self.log(f"📤 #{index+1}: Đã push status 'die' lên API")
                                    except Exception as push_err:
                                        self.log(f"⚠️ #{index+1}: Lỗi khi push 'die' lên API: {push_err}")

                                    # Update table row status
                                    self.update_table_row(index, status=f"❌ Die: {error_text[:50]}")

                                    # Đợi thêm để xem lỗi trước khi đóng Chrome
                                    self.log(f"⏸️ #{index+1}: Đợi 10s để xem lỗi trước khi đóng Chrome...")
                                    time.sleep(10)

                                    # Raise exception để dừng toàn bộ quá trình
                                    raise Exception(f"Error after signup: {error_text}")
                            except Exception as e:
                                # Nếu là lỗi "Error after signup" thì re-raise để thoát hẳn
                                if "Error after signup" in str(e):
                                    raise
                                # Các lỗi khác (như không tìm thấy element) thì continue
                                continue

                        # Nếu không tìm thấy lỗi nào
                        if not error_found:
                            self.log(f"✅ #{index+1}: Không phát hiện lỗi sau khi submit username")

                        # ===== PUSH LẦN 2: Sau khi tạo username xong =====
                        try:
                            self.log(f"📤 #{index+1}: [Push 2/3] Đang update username lên server...")
                            account_id = self.push_to_api(
                                email=email,
                                password=password,
                                username=username,
                                display_name=username,
                                bio=None,
                                avatar_url=None,
                                birthday=birthday_db,
                                tiktok_url=f"https://www.tiktok.com/@{username}",
                                account_id=account_id,
                                proxy_ip=current_ip
                            )
                        except Exception as api_err:
                            self.log(f"⚠️ #{index+1}: [Push 2/3] Lỗi khi update lên API: {api_err}")

                else:
                    self.log(f"⚠️ #{index+1}: Không tìm thấy nút Sign up, bỏ qua")
                    raise Exception("Skip username")

            except Exception as e:
                if "Skip username" in str(e):
                    self.log(f"ℹ️ #{index+1}: Username không available, bỏ qua edit profile, vào thẳng Ads")
                    # Set flag để skip edit profile
                    skip_edit_profile = True
                elif "Login expired" in str(e):
                    # Re-raise lỗi Login expired để dừng hẳn
                    self.log(f"⚠️ #{index+1}: Login expired, dừng đăng ký")
                    raise
                else:
                    self.log(f"⚠️ #{index+1}: Lỗi: {e}")
                    # Re-raise các lỗi khác để outer exception handler xử lý
                    raise
            else:
                skip_edit_profile = False

            # Bước 12: Click Continue (nếu có)
            if not skip_edit_profile:
                self.update_table_row(index, status="Click Continue...")
                self.log(f"▶️ #{index+1}: Click Continue")

                try:
                    continue_selectors = [
                        "//button[contains(text(), 'Continue')]",
                        "//div[contains(text(), 'Continue')]"
                    ]

                    continue_btn = self.find_element_multi(driver, continue_selectors, timeout=5)
                    if continue_btn:
                        continue_btn.click()
                        time.sleep(3)
                except:
                    self.log(f"ℹ️ #{index+1}: Không có nút Continue, bỏ qua")

            # Bước 13: Edit profile (chỉ khi username OK)
            if not skip_edit_profile:
                self.update_table_row(index, status="Chỉnh sửa hồ sơ...")
                self.log(f"📝 #{index+1}: Vào trang chỉnh sửa hồ sơ")

            try:
                if skip_edit_profile:
                    self.log(f"⏭️ #{index+1}: Bỏ qua edit profile")
                    raise Exception("Skip edit profile")
                # Vào thẳng trang profile
                tiktok_profile_url = f"https://www.tiktok.com/@{username}?lang=en"
                driver.get(tiktok_profile_url)
                time.sleep(3)
                self.log(f"✅ #{index+1}: Đã vào trang profile: {tiktok_profile_url}")

                # Click Edit profile
                edit_selectors = [
                    "//button[@data-e2e='edit-profile-entrance']",
                    "//button[contains(text(), 'Edit profile')]",
                    "//a[contains(text(), 'Edit profile')]"
                ]

                edit_btn = self.find_element_multi(driver, edit_selectors, timeout=10)
                if edit_btn:
                    edit_btn.click()
                    time.sleep(3)
                    self.log(f"✅ #{index+1}: Đã click Edit profile")
                else:
                    raise Exception("Không tìm thấy nút Edit profile")

                # Upload Profile Photo
                self.log(f"📸 #{index+1}: Đang tải ảnh profile...")
                try:
                    # Download random avatar từ DiceBear API (ảnh hoạt hình đẹp)
                    # Các style có thể dùng: adventurer, avataaars, big-smile, bottts, croodles, fun-emoji, icons, identicon, lorelei, micah, miniavs, personas, pixel-art
                    styles = ['avataaars', 'bottts', 'fun-emoji', 'pixel-art', 'adventurer', 'big-smile', 'lorelei', 'micah', 'personas']
                    random_style = random.choice(styles)
                    random_seed = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))

                    avatar_url_temp = f"https://api.dicebear.com/7.x/{random_style}/png?seed={random_seed}&size=200"
                    avatar_response = requests.get(avatar_url_temp, timeout=10)
                    avatar_path = f"C:\\temp\\avatar_{username}.png"

                    # Lưu URL để push lên API sau
                    avatar_url = avatar_url_temp

                    with open(avatar_path, 'wb') as f:
                        f.write(avatar_response.content)

                    self.log(f"✅ #{index+1}: Đã download avatar ({random_style}): {avatar_path}")

                    # ===== SỬ DỤNG LOCK ĐỂ UPLOAD AVATAR (pyautogui không thread-safe) =====
                    with self.avatar_upload_lock:
                        self.log(f"🔒 #{index+1}: Đã lock thread, bắt đầu upload avatar...")

                        # BƯỚC 1: Click vào avatar để mở file picker
                        self.log(f"🖱️ #{index+1}: Click vào avatar để mở file picker...")
                        avatar_click_selectors = [
                            "//div[@data-e2e='edit-profile-avatar-edit-icon']",
                            "//div[contains(@class, 'avatar')]//button",
                            "//button[contains(@aria-label, 'Change photo')]",
                        ]

                        avatar_edit_btn = self.find_element_multi(driver, avatar_click_selectors, timeout=5)
                        if not avatar_edit_btn:
                            raise Exception("Không tìm thấy nút edit avatar")

                        # Click để mở file picker
                        avatar_edit_btn.click()
                        time.sleep(1.5)  # Đợi file picker mở
                        self.log(f"✅ #{index+1}: Đã click vào avatar, file picker đang mở...")

                        # BƯỚC 2: Dùng pyautogui để điều khiển Windows file picker
                        self.log(f"⌨️ #{index+1}: Dùng pyautogui để paste đường dẫn file...")

                        # Đợi file picker mở hoàn toàn
                        time.sleep(1)

                        # Copy đường dẫn file vào clipboard rồi paste (nhanh hơn gõ từng ký tự)
                        pyperclip.copy(avatar_path)
                        time.sleep(0.2)

                        # Paste đường dẫn vào ô "File name"
                        pyautogui.hotkey('ctrl', 'v')
                        time.sleep(0.3)

                        # Nhấn Enter để chọn file
                        pyautogui.press('enter')
                        time.sleep(3)  # Đợi file upload lên TikTok

                        self.log(f"✅ #{index+1}: Đã upload ảnh, đang tìm nút Apply...")

                        # BƯỚC 3: Click nút Apply để xác nhận avatar
                        apply_selectors = [
                            "//button[contains(text(), 'Apply')]",
                            "//button[@class='ef1kawg9 css-1k5h905-5e6d46e3--Button-5e6d46e3--StyledBtn ebef5j00']",
                            "//button[contains(@class, 'StyledBtn') and contains(text(), 'Apply')]",
                            "//button[@type='button' and contains(text(), 'Apply')]"
                        ]

                        apply_btn = self.find_element_multi(driver, apply_selectors, timeout=10)
                        if apply_btn:
                            apply_btn.click()
                            time.sleep(2)
                            self.log(f"✅ #{index+1}: Đã click nút Apply để xác nhận avatar")
                        else:
                            self.log(f"⚠️ #{index+1}: Không tìm thấy nút Apply, có thể đã tự động apply")

                        self.log(f"🔓 #{index+1}: Unlock thread, thread khác có thể tiếp tục upload")

                    # Xóa file avatar tạm sau khi upload thành công (ngoài lock)
                    try:
                        os.remove(avatar_path)
                        self.log(f"🗑️ #{index+1}: Đã xóa file avatar tạm: {avatar_path}")
                    except Exception as del_err:
                        self.log(f"⚠️ #{index+1}: Không thể xóa file avatar: {del_err}")

                except Exception as e:
                    self.log(f"⚠️ #{index+1}: Không thể tải ảnh profile: {e}")

                    # Xóa file avatar tạm nếu có lỗi
                    try:
                        if 'avatar_path' in locals() and os.path.exists(avatar_path):
                            os.remove(avatar_path)
                            self.log(f"🗑️ #{index+1}: Đã xóa file avatar tạm sau lỗi")
                    except:
                        pass

                # Input Bio
                self.log(f"💬 #{index+1}: Nhập tiểu sử: {bio}")
                bio_selectors = [
                    "//textarea[@placeholder='Bio']",
                    "//textarea[contains(@placeholder, 'bio')]",
                    "//textarea[@name='bio']"
                ]

                bio_input = self.find_element_multi(driver, bio_selectors, timeout=10)
                if bio_input:
                    bio_input.clear()
                    bio_input.send_keys(bio)
                    time.sleep(1)

                # Click Save (lưu hồ sơ)
                save_selectors = [
                    "//button[contains(text(), 'Save')]",
                    "//button[@type='submit']"
                ]

                save_btn = self.find_element_multi(driver, save_selectors, timeout=10)
                if save_btn:
                    save_btn.click()
                    time.sleep(3)

                self.log(f"✅ #{index+1}: Đã chỉnh sửa hồ sơ")

                # ===== PUSH LẦN 3: Sau khi Save profile (có đủ avatar, bio) =====
                try:
                    self.log(f"📤 #{index+1}: [Push 3/3] Đang update profile đầy đủ lên server...")
                    account_id = self.push_to_api(
                        email=email,
                        password=password,
                        username=username,
                        display_name=username,
                        bio=bio,
                        avatar_url=avatar_url if avatar_url else "",
                        birthday=birthday_db,
                        tiktok_url=tiktok_profile_url if tiktok_profile_url else f"https://www.tiktok.com/@{username}",
                        account_id=account_id,
                        proxy_ip=current_ip
                    )
                except Exception as api_err:
                    self.log(f"⚠️ #{index+1}: [Push 3/3] Lỗi khi update lên API: {api_err}")

            except Exception as e:
                self.log(f"⚠️ #{index+1}: Không thể chỉnh sửa hồ sơ: {e}")

            # Success - Đã hoàn tất đăng ký TikTok
            self.log(f"✅ #{index+1}: Đăng ký thành công!")
            self.update_result(index, email, password, birthday, username, "Success", start_time)

        except Exception as e:
            error_msg = str(e)
            self.log(f"❌ #{index+1}: Lỗi - {error_msg}")
            self.update_result(index, email, password, birthday, username, f"Error: {error_msg}", start_time)

        finally:
            # Đảm bảo đóng driver và kill process
            if driver:
                try:
                    import psutil

                    # Lấy service PID trước khi quit
                    service_pid = None
                    try:
                        if hasattr(driver, 'service') and hasattr(driver.service, 'process'):
                            service_pid = driver.service.process.pid
                    except:
                        pass

                    # Quit driver
                    try:
                        driver.quit()
                    except:
                        pass

                    # Kill service process và tất cả children
                    if service_pid:
                        try:
                            parent = psutil.Process(service_pid)
                            # Kill tất cả child processes (Chrome browsers)
                            for child in parent.children(recursive=True):
                                try:
                                    child.kill()
                                except:
                                    pass
                            # Kill parent (chromedriver)
                            try:
                                parent.kill()
                            except:
                                pass

                            # Remove PID khỏi tracking set
                            with self.pids_lock:
                                self.chrome_pids.discard(service_pid)
                        except:
                            pass

                    self.log(f"✅ #{index+1}: Đã đóng Chrome")

                except Exception as e:
                    self.log(f"⚠️ #{index+1}: Lỗi khi đóng driver: {e}")

    def check_captcha_exists(self, driver):
        """Kiểm tra có Captcha không"""
        try:
            captcha_selectors = [
                "//iframe[contains(@src, 'captcha')]",
                "//div[contains(@class, 'captcha')]",
                "//*[contains(text(), 'Choose 2 objects')]",
                "//*[contains(text(), 'same shape')]",
                "//div[@id='captcha-verify-container-main-page']"
            ]

            for selector in captcha_selectors:
                try:
                    elements = driver.find_elements(By.XPATH, selector)
                    if elements and elements[0].is_displayed():
                        return True
                except:
                    continue
            return False
        except:
            return False

    def solve_captcha(self, driver, email):
        """Giải Captcha - Audio"""
        try:
            time.sleep(2)

            # Click Audio button
            audio_switch_selectors = [
                "//button[@id='captcha_switch_button']",
                "//button[contains(@class, 'captcha') and .//div[contains(text(), 'Audio')]]",
                "//button[.//div[text()='Audio']]",
            ]

            audio_btn = None
            for selector in audio_switch_selectors:
                try:
                    elements = driver.find_elements(By.XPATH, selector)
                    for elem in elements:
                        if elem.is_displayed():
                            text = elem.text.lower()
                            if 'audio' in text or elem.get_attribute('id') == 'captcha_switch_button':
                                audio_btn = elem
                                break
                    if audio_btn:
                        break
                except:
                    continue

            if not audio_btn:
                return False

            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", audio_btn)
            time.sleep(0.3)
            audio_btn.click()
            time.sleep(2)

            # Try solving audio captcha
            max_retries = 30  # Giảm từ 30 xuống 15 để tránh block quá lâu
            for attempt in range(1, max_retries + 1):
                self.log(f"🔄 {email}: Đang giải Captcha (lần {attempt}/{max_retries})...")

                try:
                    success = self.attempt_audio_solve(driver, email, attempt)

                    if success:
                        self.log(f"✅ {email}: Giải Captcha thành công!")
                        return True

                    if attempt < max_retries:
                        time.sleep(2)
                    else:
                        self.log(f"❌ {email}: Không giải được Captcha sau {max_retries} lần thử")

                except Exception as e:
                    self.log(f"⚠️ {email}: Lỗi khi attempt {attempt}: {e}")
                    if attempt < max_retries:
                        time.sleep(2)
                    continue

            return False

        except Exception as e:
            self.log(f"❌ {email}: Lỗi giải Captcha: {e}")
            import traceback
            self.log(f"❌ Traceback: {traceback.format_exc()}")
            return False

    def attempt_audio_solve(self, driver, email, attempt_num):
        """Một lần thử giải audio captcha"""
        audio_path = None
        try:
            # Get audio URL
            try:
                audio_elem = driver.find_element(By.XPATH, "//audio[@src]")
                audio_url = audio_elem.get_attribute('src')

                if not audio_url or not audio_url.startswith('http'):
                    return False

            except Exception as e:
                return False

            # Download audio file với timestamp để tránh conflict giữa các thread
            timestamp = int(time.time() * 1000)  # millisecond
            audio_path = f"C:\\temp\\audio_{email.replace('@', '_')}_{attempt_num}_{timestamp}.mp3"
            os.makedirs("C:\\temp", exist_ok=True)

            try:
                response = requests.get(audio_url, timeout=30)
                if response.status_code == 200:
                    with open(audio_path, 'wb') as f:
                        f.write(response.content)
                else:
                    return False
            except Exception as e:
                return False

            # Transcribe using Whisper
            transcribed_text = self.transcribe_audio_with_whisper(audio_path)

            if not transcribed_text:
                if audio_path and os.path.exists(audio_path):
                    try:
                        os.remove(audio_path)
                    except:
                        pass
                return False

            # Input captcha
            self.log(f"⌨️ {email}: Nhập mã Captcha: {transcribed_text}")

            input_selectors = [
                "//input[@placeholder='Enter what you hear']",
                "//input[contains(@placeholder, 'hear')]",
                "//input[@type='text' and not(@maxlength='1')]"
            ]

            captcha_input = None
            for selector in input_selectors:
                try:
                    elements = driver.find_elements(By.XPATH, selector)
                    for elem in elements:
                        if elem.is_displayed() and elem.is_enabled():
                            captcha_input = elem
                            break
                    if captcha_input:
                        break
                except:
                    continue

            if not captcha_input:
                return False

            try:
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", captcha_input)
                time.sleep(0.2)
                captcha_input.click()
                time.sleep(0.1)
                driver.execute_script("arguments[0].value = '';", captcha_input)
                captcha_input.send_keys(transcribed_text)
                time.sleep(0.5)
            except Exception as e:
                return False

            # Click Verify
            verify_selectors = [
                "//button[.//div[text()='Verify']]",
                "//button[contains(text(), 'Verify')]",
                "//button[@type='submit']"
            ]

            verify_clicked = False
            for selector in verify_selectors:
                try:
                    verify_btn = driver.find_element(By.XPATH, selector)
                    if verify_btn.is_displayed():
                        btn_classes = verify_btn.get_attribute('class') or ''
                        if 'disabled' in btn_classes.lower():
                            continue

                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", verify_btn)
                        time.sleep(0.2)
                        verify_btn.click()
                        verify_clicked = True
                        time.sleep(2)
                        break
                except:
                    continue

            if not verify_clicked:
                return False

            # Check result
            time.sleep(1.5)

            try:
                captcha_modal = driver.find_elements(By.XPATH, "//div[@id='captcha-verify-container-main-page']")
                if not captcha_modal or not captcha_modal[0].is_displayed():
                    # Success
                    if audio_path and os.path.exists(audio_path):
                        try:
                            os.remove(audio_path)
                        except:
                            pass
                    return True
                else:
                    # Failed
                    if audio_path and os.path.exists(audio_path):
                        try:
                            os.remove(audio_path)
                        except:
                            pass
                    return False
            except:
                # Success
                if audio_path and os.path.exists(audio_path):
                    try:
                        os.remove(audio_path)
                    except:
                        pass
                return True

        except Exception as e:
            if audio_path and os.path.exists(audio_path):
                try:
                    os.remove(audio_path)
                except:
                    pass
            return False

    def transcribe_audio_with_whisper(self, audio_path):
        """
        Sử dụng Whisper API để transcribe audio
        Chỉ dùng API, không có local model fallback
        """
        return self.transcribe_audio_with_api(audio_path)

    def transcribe_audio_with_api(self, audio_path):
        """
        Transcribe audio bằng Whisper API trên Hugging Face Spaces
        Sử dụng gradio_client để gọi API (chuẩn và dễ dàng nhất)

        Args:
            audio_path: Đường dẫn đến file audio

        Returns:
            str: Text đã transcribe (clean text - chỉ chữ và số) hoặc None nếu fail
        """
        try:
            # Import gradio_client
            try:
                from gradio_client import Client
            except ImportError:
                self.log("⚠️ gradio_client chưa cài đặt! Chạy: pip install gradio_client")
                return None

            # Đọc file audio và convert sang base64
            self.log(f"🎤 Đang transcribe audio qua API: {os.path.basename(audio_path)}")

            with open(audio_path, "rb") as audio_file:
                audio_bytes = audio_file.read()
                base64_audio = base64.b64encode(audio_bytes).decode('utf-8')

            # Kết nối đến Space và gọi API
            self.log(f"🌐 Kết nối Whisper API...")

            # Extract base URL từ whisper_api_url (bỏ /api/predict nếu có)
            space_url = self.whisper_api_url.split('/api/')[0] if '/api/' in self.whisper_api_url else self.whisper_api_url

            client = Client(space_url)

            self.log(f"🚀 Đang gọi API transcribe_base64...")

            # Gọi API với gradio_client
            result = client.predict(
                base64_audio,  # base64_input
                "en",          # language (tiếng Anh cho CAPTCHA)
                api_name="/transcribe_base64"  # Tên endpoint cho base64
            )

            # Parse kết quả
            # Format: {'success': True, 'text': '...', 'language': 'en'}
            if isinstance(result, dict) and result.get("success"):
                text = result.get("text", "").strip()

                if not text:
                    self.log("⚠️ API trả về text rỗng")
                    return None

                # Clean text - chỉ giữ chữ và số (giống local model)
                clean_text = ''.join(c for c in text if c.isalnum())

                if clean_text:
                    self.log(f"✅ API transcribed: '{text}' -> '{clean_text}'")
                    return clean_text
                else:
                    self.log("⚠️ Text sau khi clean rỗng")
                    return None
            else:
                error = result.get("error", "Unknown error") if isinstance(result, dict) else "Invalid response"
                self.log(f"❌ API error: {error}")
                return None

        except Exception as e:
            self.log(f"❌ Exception khi gọi Whisper API: {e}")
            # Không log full traceback để tránh spam log
            return None

    def find_element_multi(self, driver, selectors, timeout=10):
        """Tìm element với nhiều selector"""
        if self.headless_mode:
            timeout = timeout * 2

        for selector in selectors:
            try:
                if selector.startswith("//"):
                    element = WebDriverWait(driver, timeout).until(
                        EC.visibility_of_element_located((By.XPATH, selector))
                    )
                else:
                    element = WebDriverWait(driver, timeout).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, selector))
                    )

                if self.headless_mode:
                    time.sleep(0.5)

                return element
            except:
                continue
        return None

    def read_verification_code_from_imap(self, recipient_email, timeout=60):
        """Đọc mã xác nhận 6 chữ số từ email TikTok qua IMAP"""
        try:
            self.log(f"📬 Đang đọc email cho: {recipient_email}")

            start_time = time.time()

            while time.time() - start_time < timeout:
                try:
                    # Connect to IMAP
                    mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
                    mail.login(self.imap_user, self.imap_pass)
                    mail.select('INBOX')

                    # Lấy thời gian hiện tại
                    now = datetime.now()
                    ten_min_ago = now - timedelta(minutes=10)

                    # Search for ALL emails from TikTok hôm nay
                    today = now.strftime("%d-%b-%Y")
                    search_criteria = f'(FROM "TikTok" SINCE {today})'

                    status, messages = mail.search(None, search_criteria)

                    if status == 'OK':
                        email_ids = messages[0].split()
                        self.log(f"📧 Tìm thấy {len(email_ids)} email từ TikTok")

                        # Check chỉ 20 email MỚI NHẤT
                        recent_emails = list(reversed(email_ids))[:20]

                        for email_id in recent_emails:
                            try:
                                status, msg_data = mail.fetch(email_id, '(RFC822)')

                                if status == 'OK':
                                    email_body = msg_data[0][1]
                                    email_message = email.message_from_bytes(email_body)

                                    # Check if email is for our recipient
                                    email_to = email_message.get('To', '')

                                    # Check nếu TO match với recipient_email
                                    if recipient_email.lower() in email_to.lower():
                                        # Parse email body
                                        body = ""
                                        if email_message.is_multipart():
                                            for part in email_message.walk():
                                                if part.get_content_type() == "text/plain":
                                                    body = part.get_payload(decode=True).decode()
                                                    break
                                                elif part.get_content_type() == "text/html":
                                                    body = part.get_payload(decode=True).decode()
                                        else:
                                            body = email_message.get_payload(decode=True).decode()

                                        # Find 6-digit code
                                        code_pattern = r'\b\d{6}\b'
                                        matches = re.findall(code_pattern, body)

                                        if matches:
                                            code = matches[0]
                                            self.log(f"✅ Tìm thấy code cho {recipient_email}: {code}")
                                            mail.close()
                                            mail.logout()
                                            return code

                            except Exception as e:
                                continue

                    mail.close()
                    mail.logout()

                except Exception as e:
                    self.log(f"⚠️ Lỗi khi đọc email: {e}")
                    import traceback
                    self.log(f"⚠️ Traceback: {traceback.format_exc()}")

                # Wait before retry
                time.sleep(5)

            self.log(f"❌ Timeout: Không nhận được email sau {timeout}s")
            return None

        except Exception as e:
            self.log(f"❌ Lỗi IMAP: {e}")
            import traceback
            self.log(f"❌ Traceback: {traceback.format_exc()}")
            return None

    def update_table_row(self, index, email=None, password=None, birthday=None, username=None, ip=None, status=None, start=None, end=None):
        """Cập nhật dòng trong bảng - tự động tạo dòng mới nếu chưa tồn tại"""
        try:
            with self.row_lock:
                # Kiểm tra xem index này đã có row chưa
                if index not in self.index_to_row:
                    # Tạo dòng mới với STT tự động tăng
                    items = self.tree.get_children()
                    stt = len(items) + 1  # STT = số dòng hiện tại + 1

                    row_id = self.tree.insert("", "end", values=(
                        stt,
                        email or "",
                        password or "",
                        birthday or "",
                        username or "",
                        ip or "",
                        status or "",
                        start or "",
                        end or ""
                    ))

                    # Lưu mapping index → row_id
                    self.index_to_row[index] = row_id
                else:
                    # Update dòng đã tồn tại
                    row_id = self.index_to_row[index]
                    values = list(self.tree.item(row_id, 'values'))

                    if email is not None:
                        values[1] = email
                    if password is not None:
                        values[2] = password
                    if birthday is not None:
                        values[3] = birthday
                    if username is not None:
                        values[4] = username
                    if ip is not None:
                        values[5] = ip
                    if status is not None:
                        values[6] = status
                    if start is not None:
                        values[7] = start
                    if end is not None:
                        values[8] = end

                    self.tree.item(row_id, values=values)

                self.root.update_idletasks()
        except Exception as e:
            pass

    def update_result(self, index, email, password, birthday, username, status, start_time):
        """Cập nhật kết quả sau khi đăng ký xong"""
        end_time = datetime.now().strftime("%H:%M:%S")

        self.update_table_row(index, status=status, end=end_time)

        self.created_count += 1
        if "Success" in status:
            self.success_count += 1
        else:
            self.error_count += 1

        self.update_stats()

        self.results.append({
            'email': email,
            'password': password,
            'birthday': birthday,
            'username': username,
            'status': status,
            'start_time': start_time,
            'end_time': end_time
        })

    def update_stats(self):
        """Update stats display"""
        self.created_var.set(f"{self.created_count}/{self.num_accounts}")
        self.success_var.set(f"Success: {self.success_count}")
        self.error_var.set(f"Error: {self.error_count}")
        self.root.update_idletasks()

    def export_txt(self):
        """Xuất kết quả ra file TXT"""
        if not self.results:
            messagebox.showwarning("Cảnh báo", "Chưa có kết quả để xuất!")
            return

        try:
            result_folder = Path("Result")
            result_folder.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            success_results = [r for r in self.results if "Success" in r['status']]
            if success_results:
                success_file = result_folder / f"Success_{timestamp}.txt"
                with open(success_file, 'w', encoding='utf-8') as f:
                    for r in success_results:
                        f.write(f"{r['email']}|{r['password']}|{r['birthday']}|{r['username']}\n")
                self.log(f"✅ Đã xuất {len(success_results)} Success accounts: {success_file}")

            error_results = [r for r in self.results if "Error" in r['status']]
            if error_results:
                error_file = result_folder / f"Error_{timestamp}.txt"
                with open(error_file, 'w', encoding='utf-8') as f:
                    for r in error_results:
                        f.write(f"{r['email']}|{r['password']}|{r['birthday']}|{r['username']}\n")
                self.log(f"✅ Đã xuất {len(error_results)} Error accounts: {error_file}")

            messagebox.showinfo("Thành công",
                              f"Đã xuất kết quả:\n✅ Success: {len(success_results)}\n❌ Error: {len(error_results)}")

        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể xuất file: {e}")
            self.log(f"❌ Lỗi xuất TXT: {e}")

    def export_excel(self):
        """Xuất kết quả ra Excel - chỉ tài khoản Success"""
        if not self.results:
            messagebox.showwarning("Cảnh báo", "Chưa có kết quả để xuất!")
            return

        try:
            import pandas as pd

            result_folder = Path("Result")
            result_folder.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            excel_file = result_folder / f"Success_{timestamp}.xlsx"

            success_results = [r for r in self.results if "Success" in r['status']]

            if not success_results:
                messagebox.showwarning("Cảnh báo", "Không có tài khoản Success để xuất!")
                return

            df = pd.DataFrame(success_results)

            with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Success', index=False)

            self.log(f"✅ Đã xuất {len(success_results)} tài khoản Success: {excel_file}")
            messagebox.showinfo("Thành công", f"Đã xuất {len(success_results)} tài khoản Success:\n{excel_file}")

        except ImportError:
            messagebox.showerror("Lỗi", "Cần cài đặt pandas và openpyxl:\npip install pandas openpyxl")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể xuất Excel: {e}")
            self.log(f"❌ Lỗi xuất Excel: {e}")


def main():
    """Main function"""
    chrome_path = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
    if not os.path.exists(chrome_path):
        messagebox.showerror("Lỗi",
                           f"Không tìm thấy Chrome tại: {chrome_path}\n" +
                           "Vui lòng cài đặt Chrome!")
        return

    root = tk.Tk()
    app = TikTokAccountRegister(root)
    root.mainloop()


if __name__ == "__main__":
    main()