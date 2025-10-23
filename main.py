import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledFrame
from ttkbootstrap.widgets import Meter, Notebook
from tkinter import filedialog, messagebox, VERTICAL, W, E, S, N, LEFT, RIGHT, BOTH, YES, BOTTOM, X, CENTER, WORD, END, SUNKEN
import os
import json
from datetime import datetime
import ctypes
import threading
import queue
import sys
import time

# --- Funções de backend, imports, dicionários e constantes ---

def resource_path(relative_path):
    """ Retorna o caminho absoluto para o recurso, funciona para dev e para PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- Mocks para automação (se os módulos reais não forem encontrados) ---
try:
    from automations.sap_utils import connect_to_sap
    from automations.hp_completo import execute as run_hp_completo # <--- MANTIDO ORIGINAL
    from automations.hq_completo import execute as run_hq_completo
    from automations.decimo_terceiro import execute as run_decimo_terceiro
    from automations.plrs import execute as run_plrs
    from automations.ctps_digital import execute as run_ctps_digital
    from automations.ficha_financeira import execute as run_ficha_financeira
    from automations.hp_individual import execute as run_hp_individual
    from automations.hp13_1 import execute as run_hp13_1
    from automations.hp13_2 import execute as run_hp13_2
    from automations.plr_2022 import execute as run_plr_2022
    from automations.plr_2025 import execute as run_plr_2025
    
    # --- 1. NOVAS IMPORTAÇÕES ADICIONADAS ---
    from automations.hp_com import execute as run_hp_com 
    from automations.zdp1 import execute as run_zdp1
    from automations.zdp2 import execute as run_zdp2 

except ImportError as e:
    print(f"AVISO: Módulos de automação não encontrados. Usando mocks para: {e}")
    def connect_to_sap(): return None
    def mock_execute(*args, **kwargs):
        q = kwargs.get('progress_queue')
        if q:
            for i in range(5):
                time.sleep(0.5)
                q.put({"type": "status", "detalhe": f"Simulando tarefa {i+1}/5..."})
        return True, "Simulação concluída."

    # Mocks para funções originais (se falharem)
    if 'run_hp_completo' not in locals(): run_hp_completo = mock_execute
    if 'run_hq_completo' not in locals(): run_hq_completo = mock_execute
    if 'run_decimo_terceiro' not in locals(): run_decimo_terceiro = mock_execute
    if 'run_plrs' not in locals(): run_plrs = mock_execute
    if 'run_ctps_digital' not in locals(): run_ctps_digital = mock_execute
    if 'run_ficha_financeira' not in locals(): run_ficha_financeira = mock_execute
    if 'run_hp_individual' not in locals(): run_hp_individual = mock_execute
    if 'run_hp13_1' not in locals(): run_hp13_1 = mock_execute
    if 'run_hp13_2' not in locals(): run_hp13_2 = mock_execute
    if 'run_plr_2022' not in locals(): run_plr_2022 = mock_execute
    if 'run_plr_2025' not in locals(): run_plr_2025 = mock_execute

    # Mocks para NOVAS funções (se falharem)
    if 'run_hp_com' not in locals(): run_hp_com = mock_execute
    if 'run_zdp1' not in locals(): run_zdp1 = mock_execute
    if 'run_zdp2' not in locals(): run_zdp2 = mock_execute


# --- Mapeamento de Tarefas e Sequências ---
PROCESS_MAP = {
    "HP Completo": run_hp_completo, # <--- MANTIDO ORIGINAL
    "HQ Completo": run_hq_completo, 
    "13º Salário": run_decimo_terceiro,
    "PLRs": run_plrs, "CTPS Digital": run_ctps_digital, "Ficha Financeira": run_ficha_financeira,
    "HP Individual (Off-Cycle)": run_hp_individual, "1ª Parcela 13º": run_hp13_1,
    "2ª Parcela 13º": run_hp13_2, "PLR 2022": run_plr_2022, "PLR 2025": run_plr_2025,
    
    # --- 2. NOVOS PROCESSOS ADICIONADOS ---
    "HP-COM": run_hp_com,
    "ZDP1": run_zdp1,
    "ZDP2": run_zdp2,
}

SEQUENCES = {
    "HP": ["HP Completo"], # <--- MANTIDO ORIGINAL
    "HQ": ["HQ Completo"], 
    "HP+HQ": ["HP Completo", "HQ Completo"],
    "13º Salário Completo": ["13º Salário"], "PLRs": ["PLRs"], 
    "Ficha Financeira": ["Ficha Financeira"], "CTPS Digital": ["CTPS Digital"], 
    "HP Individual": ["HP Individual (Off-Cycle)"], "1ª Parcela 13º": ["1ª Parcela 13º"],
    "2ª Parcela 13º": ["2ª Parcela 13º"], "PLR 2022": ["PLR 2022"], "PLR 2025": ["PLR 2025"],
    "Massa Completa de Holerites": ["HP Completo", "HQ Completo", "13º Salário", "PLRs"],
    "Ficha + CTPS": ["Ficha Financeira", "CTPS Digital"],
    "EXECUTAR TUDO": ["Massa Completa de Holerites", "Ficha Financeira", "CTPS Digital", "HP Individual (Off-Cycle)"],

    # --- 3. NOVAS SEQUÊNCIAS ADICIONADAS ---
    "HP-COM": ["HP-COM"],
    "ZDP1": ["ZDP1"],
    "ZDP2": ["ZDP2"],
}

CONFIG_FILE = resource_path("config.json")
SIDEBAR_BUTTONS = ["AÇÕES", "STATUS"]

class AppSAP:
    def __init__(self, master):
        self.app = master
        self.app.title("Painel de Automação SAP")
        self.app.state('zoomed') 
        self.app.minsize(width=900, height=700)
        self.app.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.app.attributes("-alpha", 0) 
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

        # Variáveis de Estado
        self.output_base_path = ""
        self.progress_queue = queue.Queue()
        self.automation_thread = None
        self.all_buttons = []
        self.sidebar_buttons = {}
        self.progress_list_items = {}
        self.vapor_clicks, self.solar_clicks = 0, 0
        self.last_click_time = 0

        # Variáveis Tkinter
        self.path_entry_var = ttk.StringVar(value="Nenhuma pasta selecionada")
        self.theme_switch_var = ttk.BooleanVar()
        self.geral_status_var = ttk.StringVar(value="Pronto para iniciar.")
        self.detalhe_status_var = ttk.StringVar(value="Aguardando uma nova tarefa...")
        self.debug_label_var = ttk.StringVar()
        
        self._init_combobox_vars()
        self._create_widgets()
        
        self.load_config()
        self.on_text_focus_out(None)
        self.show_frame("AÇÕES")
        self.fade_in()

    def _init_combobox_vars(self):
        now = datetime.now()
        current_year = now.year
        self.years = [str(i) for i in range(current_year - 4, current_year + 5)]
        self.months = [f"{i:02d}" for i in range(1, 13)]
        
        self.combo_mes_inicio = ttk.StringVar(value=f"{now.month:02d}")
        self.combo_ano_inicio = ttk.StringVar(value=str(now.year))
        self.combo_mes_fim = ttk.StringVar(value=f"{now.month:02d}")
        self.combo_ano_fim = ttk.StringVar(value=str(now.year))

    def _create_widgets(self):
        container = ttk.Frame(self.app)
        container.pack(fill=BOTH, expand=YES)
        
        self.main_frame = ttk.Frame(container, padding=0)
        self.main_frame.pack(fill=BOTH, expand=YES)
        self.main_frame.grid_columnconfigure(1, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)

        self._create_sidebar(self.main_frame)
        
        self.content_frame = ttk.Frame(self.main_frame, padding=(20, 10, 20, 20))
        self.content_frame.grid(row=0, column=1, sticky="nsew")
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(1, weight=1)
        
        self.frames = {}
        self.frames["AÇÕES"] = self._create_actions_page(self.content_frame)
        self.frames["STATUS"] = self._create_status_page(self.content_frame)
        self.frames["CONFIGURAÇÕES"] = self._create_config_page(self.content_frame)
        
        self._create_status_bar(container)

    def _create_status_bar(self, parent):
        status_bar = ttk.Frame(parent, relief=SUNKEN, padding=(5, 2))
        status_bar.pack(side=BOTTOM, fill=X)
        
        ttk.Label(status_bar, textvariable=self.geral_status_var, bootstyle="info", font=("", 10, "bold")).pack(side=LEFT, padx=(5, 10))
        ttk.Label(status_bar, textvariable=self.detalhe_status_var, bootstyle="secondary").pack(side=LEFT, padx=10)
        ttk.Label(status_bar, textvariable=self.debug_label_var, bootstyle="secondary", font=("", 8)).pack(side=RIGHT, padx=5)
        
        self.app.bind("<Configure>", self.on_resize)
        self.app.after(100, self.on_resize, None) 

    def show_frame(self, page_name):
        frame = self.frames.get(page_name)
        if frame:
            for f in self.frames.values():
                f.grid_remove()
            frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
            for name, btn in self.sidebar_buttons.items():
                if name == page_name:
                    btn.configure(bootstyle="primary")
                else:
                    btn.configure(bootstyle="secondary-outline")
    
    def _create_sidebar(self, parent):
        sidebar = ttk.Frame(parent, width=250, padding=10, bootstyle="dark")
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_columnconfigure(0, weight=1)

        title_label = ttk.Label(sidebar, text="SAP", font=("", 18, "bold"), bootstyle="primary")
        title_label.grid(row=0, column=0, sticky="ew", pady=(10, 30))
        title_label.bind("<Button-1>", self.vapor_easter_egg_check)

        for i, name in enumerate(SIDEBAR_BUTTONS):
            btn = ttk.Button(sidebar, text=name, command=lambda n=name: self.show_frame(n), bootstyle="secondary-outline", padding=15, cursor="hand2")
            btn.grid(row=i + 1, column=0, sticky="ew", pady=5)
            self.sidebar_buttons[name] = btn

        sidebar.grid_rowconfigure(len(SIDEBAR_BUTTONS) + 1, weight=1)
        
        theme_switch = ttk.Checkbutton(sidebar, text="Tema Claro/Escuro", variable=self.theme_switch_var, command=self.toggle_theme, bootstyle="success-round-toggle")
        theme_switch.grid(row=len(SIDEBAR_BUTTONS) + 2, column=0, sticky="ew", pady=(20, 10))

    def _create_actions_page(self, parent):
        page_frame = ttk.Frame(parent, padding=10)
        page_frame.grid_columnconfigure(0, weight=1)
        page_frame.grid_rowconfigure(3, weight=1)
        
        ttk.Label(page_frame, text="Controle de Execução", font=("", 18, "bold"), bootstyle="primary").grid(row=0, column=0, sticky="w", pady=(0, 20))

        path_frame = ttk.Labelframe(page_frame, text=" 📂 1. Pasta de Destino ", padding=15)
        path_frame.grid(row=1, column=0, sticky="ew", pady=10) 
        ttk.Button(path_frame, text="Selecionar Pasta...", command=self.select_output_folder, bootstyle="info").pack(side=LEFT, padx=(0, 10))
        ttk.Entry(path_frame, textvariable=self.path_entry_var, state="readonly").pack(side=LEFT, fill=X, expand=YES)
        
        input_details_frame = ttk.Frame(page_frame)
        input_details_frame.grid(row=2, column=0, sticky="ew", pady=10)
        input_details_frame.grid_columnconfigure(0, weight=1)
        input_details_frame.grid_columnconfigure(1, weight=1)

        periodo_frame = ttk.Labelframe(input_details_frame, text=" 🗓️ 2. Período de Execução ", padding=15)
        periodo_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10)) 
        periodo_frame.grid_columnconfigure((1, 2, 4, 5), weight=1)
        self._create_periodo_widgets(periodo_frame)

        matriculas_frame = ttk.Labelframe(input_details_frame, text=" 👤 3. Matrículas ", padding=15)
        matriculas_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        matriculas_frame.grid_rowconfigure(0, weight=1) 
        matriculas_frame.grid_columnconfigure(0, weight=1)
        
        self.textbox_matriculas = ttk.Text(matriculas_frame, font=("Consolas", 11), wrap=WORD, height=4) 
        self.textbox_matriculas.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(matriculas_frame, orient=VERTICAL, command=self.textbox_matriculas.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.textbox_matriculas.config(yscrollcommand=scrollbar.set)
        self.textbox_matriculas.bind("<FocusIn>", self.on_text_focus_in)
        self.textbox_matriculas.bind("<FocusOut>", self.on_text_focus_out)
        
        notebook = Notebook(page_frame)
        notebook.grid(row=3, column=0, sticky="nsew", pady=(10, 10)) 
        
        self._create_holerites_tab(notebook)
        self._create_anuais_tab(notebook)
        self._create_docs_tab(notebook)

        massa_destaque_frame = ttk.Frame(page_frame)
        massa_destaque_frame.grid(row=4, column=0, sticky="ew", pady=(10, 0)) 
        massa_destaque_frame.grid_columnconfigure((0, 1), weight=1)
        
        btn_massa = ttk.Button(massa_destaque_frame, text="Massa Completa de Holerites", command=lambda: self.start_automation("Massa Completa de Holerites"), bootstyle="success")
        btn_massa.grid(row=0, column=0, sticky="ew", padx=(0,5), ipady=10); self.all_buttons.append(btn_massa)
        btn_tudo = ttk.Button(massa_destaque_frame, text="🔥 EXECUTAR TUDO", command=lambda: self.start_automation("EXECUTAR TUDO"), bootstyle="danger")
        btn_tudo.grid(row=0, column=1, sticky="ew", padx=(5,0), ipady=10); self.all_buttons.append(btn_tudo)
        
        return page_frame

    def _create_periodo_widgets(self, parent):
        ttk.Label(parent, text="Início:").grid(row=0, column=0, padx=(0, 5))
        ttk.Combobox(parent, state="readonly", values=self.months, textvariable=self.combo_mes_inicio).grid(row=0, column=1, padx=5, sticky="ew")
        ttk.Combobox(parent, state="readonly", values=self.years, textvariable=self.combo_ano_inicio).grid(row=0, column=2, padx=5, sticky="ew")
        ttk.Label(parent, text="Fim:").grid(row=0, column=3, padx=(15, 5))
        ttk.Combobox(parent, state="readonly", values=self.months, textvariable=self.combo_mes_fim).grid(row=0, column=4, padx=5, sticky="ew")
        ttk.Combobox(parent, state="readonly", values=self.years, textvariable=self.combo_ano_fim).grid(row=0, column=5, padx=5, sticky="ew")
        
    def _create_holerites_tab(self, notebook):
        holerites_tab = ScrolledFrame(notebook, padding=10, autohide=True).container
        notebook.add(holerites_tab, text="Holerites", sticky="nsew")
        holerites_tab.columnconfigure(0, weight=1)
        
        # --- 4. BOTÕES DA ABA HOLERITES ---
        # Botão HP Completo (Original)
        btn = ttk.Button(holerites_tab, text="Executar HP (Completo)", command=lambda: self.start_automation("HP"), bootstyle="primary"); 
        btn.grid(row=0, column=0, sticky="ew", pady=5); 
        self.all_buttons.append(btn)
        
        # Botão HQ Completo (Original)
        btn = ttk.Button(holerites_tab, text="Executar HQ (Completo)", command=lambda: self.start_automation("HQ"), bootstyle="primary"); 
        btn.grid(row=1, column=0, sticky="ew", pady=5); 
        self.all_buttons.append(btn)
        
        # Botão HP + HQ (Original)
        btn = ttk.Button(holerites_tab, text="Executar HP + HQ", command=lambda: self.start_automation("HP+HQ"), bootstyle="info"); 
        btn.grid(row=2, column=0, sticky="ew", pady=10); 
        self.all_buttons.append(btn)
        
        # Botão NOVO HP-COM
        btn = ttk.Button(holerites_tab, text="Executar HP-COM (Avulso)", command=lambda: self.start_automation("HP-COM"), bootstyle="primary-outline"); 
        btn.grid(row=3, column=0, sticky="ew", pady=5); 
        self.all_buttons.append(btn)
        
    def _create_anuais_tab(self, notebook):
        anuais_tab = ScrolledFrame(notebook, padding=10, autohide=True).container
        notebook.add(anuais_tab, text="Anuais", sticky="nsew") 
        anuais_tab.columnconfigure(0, weight=1)
        ttk.Label(anuais_tab, text="Décimo Terceiro:").grid(row=0, column=0, sticky="w", pady=(5, 0))
        btn = ttk.Button(anuais_tab, text="13º Salário (Completo)", command=lambda: self.start_automation("13º Salário Completo"), bootstyle="success"); btn.grid(row=1, column=0, sticky="ew", pady=5); self.all_buttons.append(btn)
        btn = ttk.Button(anuais_tab, text="1ª Parcela 13º", command=lambda: self.start_automation("1ª Parcela 13º"), bootstyle="primary-outline"); btn.grid(row=2, column=0, sticky="ew", pady=2); self.all_buttons.append(btn)
        btn = ttk.Button(anuais_tab, text="2ª Parcela 13º", command=lambda: self.start_automation("2ª Parcela 13º"), bootstyle="primary-outline"); btn.grid(row=3, column=0, sticky="ew", pady=5); self.all_buttons.append(btn)
        ttk.Separator(anuais_tab).grid(row=4, column=0, sticky="ew", pady=10)
        ttk.Label(anuais_tab, text="PLRs:").grid(row=5, column=0, sticky="w", pady=(5, 0))
        btn = ttk.Button(anuais_tab, text="PLRs (Completo)", command=lambda: self.start_automation("PLRs"), bootstyle="success"); btn.grid(row=6, column=0, sticky="ew", pady=5); self.all_buttons.append(btn)
        btn = ttk.Button(anuais_tab, text="PLR 2022 (Avulso)", command=lambda: self.start_automation("PLR 2022"), bootstyle="primary-outline"); btn.grid(row=7, column=0, sticky="ew", pady=2); self.all_buttons.append(btn)
        btn = ttk.Button(anuais_tab, text="PLR 2025 (Avulso)", command=lambda: self.start_automation("PLR 2025"), bootstyle="primary-outline"); btn.grid(row=8, column=0, sticky="ew", pady=5); self.all_buttons.append(btn)
        
    def _create_docs_tab(self, notebook):
        docs_tab = ScrolledFrame(notebook, padding=10, autohide=True).container
        notebook.add(docs_tab, text="Documentos", sticky="nsew")
        docs_tab.columnconfigure(0, weight=1)
        
        # --- 5. BOTÕES DA ABA DOCUMENTOS ---
        # Botão para Ficha Financeira (Original)
        btn = ttk.Button(docs_tab, text="Gerar Ficha Financeira", command=lambda: self.start_automation("Ficha Financeira"), bootstyle="primary"); 
        btn.grid(row=0, column=0, sticky="ew", pady=5); 
        self.all_buttons.append(btn)
        
        # Botão para CTPS Digital (Original)
        btn = ttk.Button(docs_tab, text="Gerar CTPS Digital", command=lambda: self.start_automation("CTPS Digital"), bootstyle="primary"); 
        btn.grid(row=1, column=0, sticky="ew", pady=5); 
        self.all_buttons.append(btn)
        
        # Botão Ficha Financeira + CTPS Digital (Original)
        btn = ttk.Button(docs_tab, text="Ficha Financeira + CTPS Digital (Em Sequência)", command=lambda: self.start_automation("Ficha + CTPS"), bootstyle="success-outline"); 
        btn.grid(row=2, column=0, sticky="ew", pady=10); 
        self.all_buttons.append(btn)
        
        # Botão para HP Individual (Off-Cycle) (Original)
        btn = ttk.Button(docs_tab, text="Gerar HP Individual (Off-Cycle)", command=lambda: self.start_automation("HP Individual"), bootstyle="info"); 
        btn.grid(row=3, column=0, sticky="ew", pady=5); 
        self.all_buttons.append(btn)
        
        # Botão NOVO ZDP1
        btn = ttk.Button(docs_tab, text="Gerar ZDP1", command=lambda: self.start_automation("ZDP1"), bootstyle="warning-outline"); 
        btn.grid(row=4, column=0, sticky="ew", pady=(10, 5)); 
        self.all_buttons.append(btn)

        # Botão NOVO ZDP2
        btn = ttk.Button(docs_tab, text="Gerar ZDP2", command=lambda: self.start_automation("ZDP2"), bootstyle="warning-outline"); 
        btn.grid(row=5, column=0, sticky="ew", pady=5); 
        self.all_buttons.append(btn)
        

    def _create_status_page(self, parent):
        page_frame = ttk.Frame(parent, padding=10)
        page_frame.grid_columnconfigure(0, weight=1)
        page_frame.grid_rowconfigure(2, weight=1)
        ttk.Label(page_frame, text="Status e Progresso da Automação", font=("", 18, "bold"), bootstyle="primary").grid(row=0, column=0, sticky="w", pady=(0, 20))
        page_frame.bind("<Button-1>", self.solar_easter_egg_check)
        
        exec_frame = ttk.Labelframe(page_frame, text=" 📊 Progresso Geral ", padding=20)
        exec_frame.grid(row=1, column=0, sticky="new", pady=(0, 20))
        exec_frame.grid_columnconfigure(1, weight=1)

        self.progress_meter = Meter(exec_frame, metersize=180, padding=10, amountused=0, metertype="semi", subtext="Progresso Geral", interactive=False, bootstyle="info", textright="%")
        self.progress_meter.grid(row=0, column=0, rowspan=2, padx=(0, 20), sticky="ns")
        
        ttk.Label(exec_frame, textvariable=self.geral_status_var, font=("", 14, "bold")).grid(row=0, column=1, sticky="nsw")
        ttk.Label(exec_frame, textvariable=self.detalhe_status_var, bootstyle="secondary").grid(row=1, column=1, sticky="nsw")

        progress_frame = ttk.Labelframe(page_frame, text=" 📜 Progresso Detalhado por Documento ", padding=15)
        progress_frame.grid(row=2, column=0, sticky="nsew")
        progress_frame.grid_rowconfigure(0, weight=1)
        progress_frame.grid_columnconfigure(0, weight=1)
        
        columns = ('tarefa', 'status')
        self.progress_list = ttk.Treeview(progress_frame, columns=columns, show='headings', bootstyle="primary")
        self.progress_list.heading('tarefa', text='Documento')
        self.progress_list.heading('status', text='Status')
        self.progress_list.column('tarefa', width=350, anchor=W)
        self.progress_list.column('status', width=120, anchor=CENTER)
        self.progress_list.grid(row=0, column=0, sticky="nsew")
        
        scrollbar_list = ttk.Scrollbar(progress_frame, orient=VERTICAL, command=self.progress_list.yview)
        scrollbar_list.grid(row=0, column=1, sticky="ns")
        self.progress_list.config(yscrollcommand=scrollbar_list.set)
        return page_frame

    def _create_config_page(self, parent):
        page_frame = ttk.Frame(parent, padding=10)
        page_frame.grid_columnconfigure(0, weight=1)
        ttk.Label(page_frame, text="Configurações Avançadas (Oculta)", font=("", 18, "bold"), bootstyle="primary").grid(row=0, column=0, sticky="w", pady=(0, 20))
        config_box = ttk.Labelframe(page_frame, text=" ⚙️ Opções Globais ", padding=20)
        config_box.grid(row=1, column=0, sticky="ew")
        ttk.Label(config_box, text="Esta área está reservada para futuras configurações, como:").pack(anchor=W, pady=5)
        ttk.Label(config_box, text="- Seleção de Mandantes/Sistemas SAP", bootstyle="secondary").pack(anchor=W, padx=10)
        ttk.Label(config_box, text="- Opções de Logging e Debugging", bootstyle="secondary").pack(anchor=W, padx=10)
        ttk.Label(config_box, text="- Configuração de Impressão/PDFs", bootstyle="secondary").pack(anchor=W, padx=10)
        return page_frame
    
    def load_config(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, "r") as f:
                    config_data = json.load(f)
                    now = datetime.now()
                    self.combo_mes_inicio.set(config_data.get("mes_inicio", f"{now.month:02d}"))
                    self.combo_ano_inicio.set(config_data.get("ano_inicio", str(now.year)))
                    self.combo_mes_fim.set(config_data.get("mes_fim", f"{now.month:02d}"))
                    self.combo_ano_fim.set(config_data.get("ano_fim", str(now.year)))
                    saved_theme = config_data.get("theme", "darkly")
                    if saved_theme not in ['darkly', 'litera', 'vapor', 'solar']:
                        saved_theme = 'darkly'
                    self.app.style.theme_use(saved_theme)
                    self.theme_switch_var.set(saved_theme in ['litera', 'solar'])
        except Exception as e:
            print(f"Erro ao carregar configuração: {e}")

    def save_config(self):
        current_theme = self.app.style.theme.name
        theme_to_save = current_theme
        if current_theme in ['vapor', 'solar']: 
            theme_to_save = 'darkly' if not self.theme_switch_var.get() else 'litera'
        config_data = {
            "mes_inicio": self.combo_mes_inicio.get(), "ano_inicio": self.combo_ano_inicio.get(),
            "mes_fim": self.combo_mes_fim.get(), "ano_fim": self.combo_ano_fim.get(),
            "theme": theme_to_save
        }
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(config_data, f)
        except Exception as e:
            print(f"Erro ao salvar configuração: {e}")

    def select_output_folder(self):
        path = filedialog.askdirectory(title="Selecione a Pasta Principal de Saída")
        if path:
            self.output_base_path = path
            self.path_entry_var.set(self.output_base_path)

    def toggle_theme(self):
        if self.app.style.theme.name in ['vapor', 'solar']:
            return
        new_theme = 'litera' if self.theme_switch_var.get() else 'darkly'
        self.app.style.theme_use(new_theme)

    def activate_theme(self, theme_name, message, is_light):
        self.app.style.theme_use(theme_name)
        self.theme_switch_var.set(is_light)
        messagebox.showinfo("Easter Egg!", message)

    def vapor_easter_egg_check(self, event):
        current_time = time.time()
        if current_time - self.last_click_time > 1:
            self.vapor_clicks = 0
        self.last_click_time = current_time
        self.vapor_clicks += 1
        if self.vapor_clicks >= 7:
            self.activate_theme('vapor', "Tema Vaporwave Ativado!", is_light=False)
            self.vapor_clicks = 0
            
    def solar_easter_egg_check(self, event):
        current_time = time.time()
        if current_time - self.last_click_time > 1:
            self.solar_clicks = 0
        self.last_click_time = current_time
        self.solar_clicks += 1
        if self.solar_clicks >= 7:
            self.activate_theme('solar', "Tema Solar Ativado!", is_light=True)
            self.solar_clicks = 0

    def on_closing(self):
        if self.automation_thread and self.automation_thread.is_alive():
            if messagebox.askyesno("Confirmação", "Uma automação está em andamento. Deseja realmente fechar?"):
                self.save_config()
                os._exit(0)
        else:
            self.save_config()
            self.app.destroy()
            
    def on_text_focus_in(self, event):
        if self.textbox_matriculas.get("1.0", "end-1c").strip() == "Digite ou cole as matrículas aqui,\numa por linha...":
            self.textbox_matriculas.delete("1.0", END)
            default_fg = self.app.style.lookup('TEntry', 'foreground')
            self.textbox_matriculas.config(foreground=default_fg) 

    def on_text_focus_out(self, event):
        if not self.textbox_matriculas.get("1.0", "end-1c").strip():
            self.textbox_matriculas.insert("1.0", "Digite ou cole as matrículas aqui,\numa por linha...")
            self.textbox_matriculas.config(foreground="gray")

    def fade_in(self):
        alpha = self.app.attributes("-alpha")
        if alpha < 1:
            alpha += 0.05
            self.app.attributes("-alpha", alpha)
            self.app.after(15, self.fade_in)

    def start_automation(self, sequence_name):
        if self.automation_thread and self.automation_thread.is_alive():
            messagebox.showwarning("Aviso", "Uma automação já está em andamento.")
            return
        if not self.output_base_path:
            messagebox.showerror("Erro", "Por favor, selecione uma pasta de destino primeiro!")
            return
        
        input_text = self.textbox_matriculas.get("1.0", "end-1c").strip()
        if input_text in ["Digite ou cole as matrículas aqui,\numa por linha...", ""]:
            messagebox.showerror("Erro", "Nenhuma matrícula inserida.")
            return
            
        matriculas_lista = [linha.strip() for linha in input_text.split("\n") if linha.strip()]
        periodo = {"inicio": f"{self.combo_mes_inicio.get()}/{self.combo_ano_inicio.get()}", "fim": f"{self.combo_mes_fim.get()}/{self.combo_ano_fim.get()}"}
        
        for btn in self.all_buttons:
            btn.configure(state="disabled")
        self.show_frame("STATUS")
        for item in self.progress_list.get_children():
            self.progress_list.delete(item)
        self.progress_list_items.clear()
        
        self.app.config(cursor="watch")
        self.automation_thread = threading.Thread(target=self.automation_worker, args=(sequence_name, matriculas_lista, periodo, {}), daemon=True)
        self.automation_thread.start()
        self.app.after(100, self.process_queue)

    def automation_worker(self, sequence_name, matriculas_lista, periodo, config):
        try:
            self.progress_queue.put({"type": "status", "geral": "Conectando ao SAP...", "detalhe": ""})
            session = connect_to_sap()
            
            # Verificação de conexão melhorada
            is_mock_mode = 'run_hp_completo' in locals() and run_hp_completo is mock_execute
            if session is None and not is_mock_mode:
                raise ConnectionError("Falha na conexão com o SAP. Verifique se o SAP GUI está aberto e logado.")
            
            tarefas_para_processar = list(SEQUENCES.get(sequence_name, []))
            tarefas_finais_para_executar = []

            while tarefas_para_processar:
                tarefa = tarefas_para_processar.pop(0)
                if tarefa in SEQUENCES and tarefa not in PROCESS_MAP:
                    sub_tarefas = SEQUENCES.get(tarefa, [])
                    tarefas_para_processar[0:0] = sub_tarefas
                else:
                    tarefas_finais_para_executar.append(tarefa)
            
            tarefas_finais_para_executar = list(dict.fromkeys(tarefas_finais_para_executar)) 
            total_procs = len(tarefas_finais_para_executar)
            
            for i, processo_nome in enumerate(tarefas_finais_para_executar):
                progresso_geral = ((i) / total_procs) * 100
                self.progress_queue.put({"type": "status", "geral": f"Etapa {i+1}/{total_procs}: {processo_nome}", "detalhe": "Iniciando...", "progresso_geral": progresso_geral})
                
                if processo_nome in PROCESS_MAP:
                    funcao_a_executar = PROCESS_MAP[processo_nome]
                    
                    # Para ZDP1 e ZDP2, o 'config' vazio é passado ({}).
                    # Os orquestradores (zdp1.py, zdp2.py) foram projetados
                    # para lidar com isso e executarão o modo 'worker' padrão.
                    
                    sucesso, mensagem = funcao_a_executar(session, matriculas_lista, periodo, config, self.output_base_path, progress_queue=self.progress_queue)
                    if not sucesso:
                        raise RuntimeError(f"Erro em '{processo_nome}': {mensagem}")
                else: 
                    print(f"AVISO: Processo '{processo_nome}' não encontrado no PROCESS_MAP.")
                    
            self.progress_queue.put({"type": "success", "msg": f"Sequência '{sequence_name}' concluída!"})
        except Exception as e:
            self.progress_queue.put({"type": "error", "msg": str(e)})
        finally:
            self.progress_queue.put({"type": "done"})

    def animate_progress(self, target_value):
        current_value = self.progress_meter.amountusedvar.get()
        step = (target_value - current_value) / 10
        def update_step(step_count=0):
            if step_count < 10:
                new_value = current_value + step * (step_count + 1)
                self.progress_meter.amountusedvar.set(round(new_value))
                self.app.after(20, update_step, step_count + 1)
            else:
                self.progress_meter.amountusedvar.set(round(target_value))
        update_step()

    def process_queue(self):
        try:
            while True:
                msg = self.progress_queue.get_nowait()
                if msg["type"] == "status":
                    if "geral" in msg: self.geral_status_var.set(msg["geral"])
                    if "detalhe" in msg: self.detalhe_status_var.set(msg["detalhe"])
                    if "progresso_geral" in msg: self.animate_progress(msg["progresso_geral"])
                elif msg["type"] == "task_update":
                    task_id = msg.get("task_id")
                    if task_id not in self.progress_list_items:
                        item_id = self.progress_list.insert("", END, values=(task_id, "Pendente"))
                        self.progress_list_items[task_id] = item_id
                    if task_id in self.progress_list_items:
                        self.progress_list.item(self.progress_list_items[task_id], values=(task_id, msg["status"]))
                        if "Executando" in msg["status"]:
                            self.progress_list.selection_set(self.progress_list_items[task_id])
                            self.progress_list.see(self.progress_list_items[task_id])
                elif msg["type"] == "error":
                    self.app.config(cursor="")
                    messagebox.showerror("Erro na Execução", msg["msg"])
                    self.geral_status_var.set("Erro!")
                    self.detalhe_status_var.set(msg["msg"][:100] + "...")
                    self.animate_progress(0)
                elif msg["type"] == "success":
                    messagebox.showinfo("Concluído", msg["msg"])
                    self.geral_status_var.set("Sequência concluída com sucesso!")
                    self.detalhe_status_var.set("")
                    self.animate_progress(100)
                    self.save_config()
                elif msg["type"] == "done":
                    self.app.config(cursor="")
                    for btn in self.all_buttons:
                        btn.configure(state="normal")
                    return
        except queue.Empty:
            self.app.after(100, self.process_queue)
            
    def on_resize(self, event):
        width = self.app.winfo_width()
        height = self.app.winfo_height()
        self.debug_label_var.set(f"W: {width}px | H: {height}px")

if __name__ == "__main__":
    app_window = ttk.Window(themename="darkly")
    AppSAP(app_window)
    app_window.mainloop()