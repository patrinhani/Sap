import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import os
import json
from datetime import datetime
from tkinter import filedialog, messagebox, Listbox, END
import ctypes
import threading
import queue
import sys
import time

def resource_path(relative_path):
    """ Obtém o caminho absoluto para o recurso, funciona para dev e PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- Imports dos módulos de automação ---
# Simulações das funções de automação para o código ser executável
def connect_to_sap():
    print("Simulando conexão com SAP...")
    time.sleep(1)
    return "session_mock"

def run_hp_completo(session, matriculas, periodo, config, output, progress_queue):
    print(f"Executando HP Completo para {len(matriculas)} matrículas...")
    progress_queue.put({"type": "task_list", "tasks": matriculas})
    for mat in matriculas:
        progress_queue.put({"type": "task_update", "task_id": mat, "status": "Executando HP..."})
        time.sleep(0.5)
        progress_queue.put({"type": "task_update", "task_id": mat, "status": "HP Concluído"})
    return True, "HP Completo finalizado"

# Adicione outras funções de simulação conforme necessário para os outros processos
run_hq_completo = run_decimo_terceiro = run_plrs = run_ctps_digital = run_ficha_financeira = run_hp_individual = run_hp13_1 = run_hp13_2 = run_plr_2022 = run_plr_2025 = run_hp_completo
# from automations.trct import execute as run_trct # --- TRCT TRAVADO --- Módulo ainda não finalizado

# --- Dicionários e constantes ---
PROCESS_MAP = {
    "HP Completo": run_hp_completo, "HQ Completo": run_hq_completo, "13º Salário": run_decimo_terceiro,
    "PLRs": run_plrs, "CTPS Digital": run_ctps_digital, "Ficha Financeira": run_ficha_financeira,
    "HP Individual (Off-Cycle)": run_hp_individual, "1ª Parcela 13º": run_hp13_1,
    "2ª Parcela 13º": run_hp13_2, "PLR 2022": run_plr_2022, "PLR 2025": run_plr_2025,
    # "TRCT": run_trct, # --- TRCT TRAVADO ---
}
SEQUENCES = {
    "HP Completo": ["HP Completo"], "HQ Completo": ["HQ Completo"], "13º Salário": ["13º Salário"],
    "PLRs": ["PLRs"], "Ficha Financeira": ["Ficha Financeira"], "CTPS Digital": ["CTPS Digital"],
    "HP Individual (Off-Cycle)": ["HP Individual (Off-Cycle)"], "1ª Parcela 13º": ["1ª Parcela 13º"],
    "2ª Parcela 13º": ["2ª Parcela 13º"], "PLR 2022": ["PLR 2022"], "PLR 2025": ["PLR 2025"],
    "HP e HQ Combinados": ["HP Completo", "HQ Completo"],
    "Massa Completa de Holerites": ["HP Completo", "HQ Completo", "13º Salário", "PLRs"],
    # --- TRCT TRAVADO --- Removido "TRCT" da lista "EXECUTAR TUDO"
    "EXECUTAR TUDO": ["Massa Completa de Holerites", "Ficha Financeira", "CTPS Digital", "HP Individual (Off-Cycle)"],
    # "TRCT": ["TRCT"], # --- TRCT TRAVADO ---
}

CONFIG_FILE = resource_path("config.json")
output_base_path = ""
base_file_paths = []
progress_queue = queue.Queue()
automation_thread = None

# --- Funções de Lógica da GUI (sem alterações) ---
def save_config():
    current_theme = app.style.theme.name
    theme_to_save = current_theme
    if current_theme == 'vapor': theme_to_save = 'darkly'
    elif current_theme == 'solar': theme_to_save = 'litera'
    config_data = {
        "mes_inicio": combo_mes_inicio.get(), "ano_inicio": combo_ano_inicio.get(),
        "mes_fim": combo_mes_fim.get(), "ano_fim": combo_ano_fim.get(),
        "theme": theme_to_save
    }
    try:
        with open(CONFIG_FILE, "w") as f: json.dump(config_data, f)
    except Exception as e: print(f"Erro ao salvar configuração: {e}")

def load_config():
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                config_data = json.load(f)
                now = datetime.now()
                combo_mes_inicio.set(config_data.get("mes_inicio", f"{now.month:02d}"))
                combo_ano_inicio.set(config_data.get("ano_inicio", str(now.year)))
                combo_mes_fim.set(config_data.get("mes_fim", f"{now.month:02d}"))
                combo_ano_fim.set(config_data.get("ano_fim", str(now.year)))
                saved_theme = config_data.get("theme", "darkly")
                app.style.theme_use(saved_theme)
                theme_switch_var.set(saved_theme in ['litera', 'solar'])
    except Exception as e: print(f"Erro ao carregar configuração: {e}")

def select_output_folder():
    global output_base_path
    path = filedialog.askdirectory(title="Selecione a Pasta Principal de Saída")
    if path:
        output_base_path = path
        path_entry_var.set(output_base_path)

def add_base_files():
    global base_file_paths
    paths = filedialog.askopenfilenames(title="Selecione uma ou mais Planilhas Base", filetypes=[("Arquivos Excel", "*.xlsx *.xls")])
    if paths:
        for path in paths:
            if path not in base_file_paths:
                base_file_paths.append(path)
        update_base_file_listbox()

def remove_selected_base_files():
    global base_file_paths
    selected_indices = base_file_listbox.curselection()
    for index in sorted(selected_indices, reverse=True):
        base_file_paths.pop(index)
    update_base_file_listbox()

def update_base_file_listbox():
    base_file_listbox.delete(0, END)
    for path in base_file_paths:
        base_file_listbox.insert(END, os.path.basename(path))

def toggle_theme():
    if theme_switch_var.get(): app.style.theme_use('litera')
    else: app.style.theme_use('darkly')

vapor_clicks, solar_clicks = 0, 0
last_click_time = 0

def activate_theme(theme_name, message, is_light):
    app.style.theme_use(theme_name)
    theme_switch_var.set(is_light)
    messagebox.showinfo("Easter Egg!", message)

def vapor_easter_egg_check(event):
    global vapor_clicks, last_click_time
    current_time = time.time();
    if current_time - last_click_time > 1: vapor_clicks = 0
    last_click_time = current_time; vapor_clicks += 1
    if vapor_clicks >= 7:
        activate_theme('vapor', "Tema Vaporwave Ativado!", is_light=False); vapor_clicks = 0

def solar_easter_egg_check(event):
    global solar_clicks, last_click_time
    current_time = time.time()
    if current_time - last_click_time > 1: solar_clicks = 0
    last_click_time = current_time; solar_clicks += 1
    if solar_clicks >= 7:
        activate_theme('solar', "Tema Solar Ativado!", is_light=True); solar_clicks = 0

def automation_worker(sequence_name, matriculas_lista, periodo, config):
    try:
        progress_queue.put({"type": "status", "geral": "Conectando ao SAP...", "detalhe": ""})
        session = connect_to_sap()
        if session is None: raise ConnectionError("Falha na conexão com o SAP.")

        tarefas_iniciais = SEQUENCES.get(sequence_name, [])
        tarefas_finais_para_executar = []
        for tarefa in tarefas_iniciais:
            if tarefa in SEQUENCES: tarefas_finais_para_executar.extend(SEQUENCES.get(tarefa, []))
            else: tarefas_finais_para_executar.append(tarefa)
        tarefas_finais_para_executar = list(dict.fromkeys(tarefas_finais_para_executar))
        
        progress_queue.put({"type": "task_list", "tasks": matriculas_lista})

        total_procs = len(tarefas_finais_para_executar)
        for i, processo_nome in enumerate(tarefas_finais_para_executar):
            progresso_geral = ((i) / total_procs) * 100
            progress_queue.put({"type": "status", "geral": f"Etapa {i+1}/{total_procs}: {processo_nome}", "detalhe": "Iniciando...", "progresso_geral": progresso_geral})
            
            if processo_nome in PROCESS_MAP:
                funcao_a_executar = PROCESS_MAP[processo_nome]
                sucesso, mensagem = funcao_a_executar(session, matriculas_lista, periodo, config, output_base_path, progress_queue=progress_queue)
                if not sucesso: raise RuntimeError(f"Erro em '{processo_nome}': {mensagem}")
            else: print(f"AVISO: Processo '{processo_nome}' não encontrado no PROCESS_MAP.")
        
        progress_queue.put({"type": "success", "msg": f"Sequência '{sequence_name}' concluída com sucesso!"})
    except Exception as e:
        progress_queue.put({"type": "error", "msg": str(e)})
    finally:
        progress_queue.put({"type": "done"})

def start_automation(sequence_name):
    global automation_thread
    if automation_thread and automation_thread.is_alive():
        messagebox.showwarning("Aviso", "Uma automação já está em andamento."); return
    if not output_base_path:
        messagebox.showerror("Erro", "Por favor, selecione uma pasta de destino primeiro!"); return
    matriculas_lista = [linha for linha in textbox_matriculas.get("1.0", "end-1c").split("\n") if linha.strip()]
    if not matriculas_lista:
        messagebox.showerror("Erro", "Nenhuma matrícula inserida."); return
    periodo = {"inicio": f"{combo_mes_inicio.get()}/{combo_ano_inicio.get()}", "fim": f"{combo_mes_fim.get()}/{combo_ano_fim.get()}"}
    config = {"base_file_paths": base_file_paths}
    for btn in all_buttons: btn.configure(state="disabled")
    progress_list.delete(*progress_list.get_children()); progress_list_items.clear()
    automation_thread = threading.Thread(target=automation_worker, args=(sequence_name, matriculas_lista, periodo, config), daemon=True)
    automation_thread.start()
    app.after(100, process_queue)

def process_queue():
    try:
        while True:
            msg = progress_queue.get_nowait()
            if msg["type"] == "status":
                if "geral" in msg: geral_status_var.set(msg["geral"])
                if "detalhe" in msg: detalhe_status_var.set(msg["detalhe"])
                if "progresso_geral" in msg: progress_geral_var.set(msg["progresso_geral"])
            elif msg["type"] == "task_list":
                for task_id in msg["tasks"]:
                    if task_id not in progress_list_items:
                        item_id = progress_list.insert("", END, values=(task_id, "Pendente"))
                        progress_list_items[task_id] = item_id
            elif msg["type"] == "task_update":
                task_id = msg.get("task_id")
                if task_id not in progress_list_items:
                    item_id = progress_list.insert("", END, values=(task_id, "Pendente"))
                    progress_list_items[task_id] = item_id
                if task_id in progress_list_items:
                    progress_list.item(progress_list_items[task_id], values=(task_id, msg["status"]))
                    if "Executando" in msg["status"]:
                        progress_list.selection_set(progress_list_items[task_id])
                        progress_list.see(progress_list_items[task_id])
            elif msg["type"] == "error":
                messagebox.showerror("Erro na Execução", msg["msg"])
                geral_status_var.set("Erro!"); detalhe_status_var.set(msg["msg"][:100] + "...")
            elif msg["type"] == "success":
                messagebox.showinfo("Concluído", msg["msg"])
                geral_status_var.set("Sequência concluída com sucesso!")
                detalhe_status_var.set(""); progress_geral_var.set(100)
                save_config()
            elif msg["type"] == "done":
                for btn in all_buttons: btn.configure(state="normal")
                return
    except queue.Empty:
        app.after(100, process_queue)

def on_closing():
    save_config()
    app.destroy()

# --- Bloco Principal de Criação da GUI ---
if __name__ == "__main__":
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    app = ttk.Window(themename="darkly")
    app.title("Painel de Automação SAP")
    app.state('zoomed') 
    app.minsize(width=600, height=500)
    app.protocol("WM_DELETE_WINDOW", on_closing)

    app.grid_columnconfigure(0, weight=1)
    app.grid_rowconfigure(2, weight=1)

    all_buttons = []

    header_frame = ttk.Frame(app)
    header_frame.grid(row=0, column=0, padx=10, pady=(10, 5), sticky='ew')
    header_frame.grid_columnconfigure(0, weight=1)
    
    title_label = ttk.Label(header_frame, text="Painel de Automação SAP", font=("", 22, "bold"), bootstyle="primary")
    title_label.grid(row=0, column=0, sticky='w')
    title_label.bind("<Button-1>", vapor_easter_egg_check)
    
    theme_switch_var = ttk.BooleanVar()
    theme_switch = ttk.Checkbutton(header_frame, text="Tema Claro", variable=theme_switch_var, command=toggle_theme, bootstyle="success-round-toggle")
    theme_switch.grid(row=0, column=1, padx=10)

    top_frame = ttk.Frame(app)
    top_frame.grid(row=1, column=0, padx=10, pady=5, sticky='ew')
    top_frame.grid_columnconfigure(0, weight=1)

    center_pane = ttk.PanedWindow(app, orient=HORIZONTAL)
    center_pane.grid(row=2, column=0, padx=10, pady=5, sticky='nsew')

    bottom_frame = ttk.Frame(app)
    bottom_frame.grid(row=3, column=0, padx=10, pady=(5, 10), sticky='ew')
    bottom_frame.grid_columnconfigure(0, weight=1)
    
    path_frame = ttk.Labelframe(top_frame, text=" 1. Defina a Pasta de Destino ", padding=10)
    path_frame.grid(row=0, column=0, pady=(0, 10), sticky='ew')
    path_frame.grid_columnconfigure(1, weight=1)
    path_button = ttk.Button(path_frame, text="Selecionar Pasta...", command=select_output_folder, bootstyle="info")
    path_button.grid(row=0, column=0, padx=(0, 10))
    path_entry_var = ttk.StringVar(value="Nenhuma pasta selecionada")
    path_entry = ttk.Entry(path_frame, textvariable=path_entry_var, state="readonly")
    path_entry.grid(row=0, column=1, sticky='ew')
    
    base_file_frame = ttk.Labelframe(top_frame, text=" 2. Selecione a(s) Planilha(s) Base (Opcional) ", padding=10)
    base_file_frame.grid(row=1, column=0, sticky='ew')
    base_file_frame.grid_columnconfigure(0, weight=1)
    base_buttons_frame = ttk.Frame(base_file_frame)
    base_buttons_frame.grid(row=0, column=0, sticky='ew', pady=(0, 5))
    add_button = ttk.Button(base_buttons_frame, text="Adicionar Arquivos...", command=add_base_files, bootstyle="info")
    add_button.pack(side=LEFT, padx=(0, 10)); all_buttons.append(add_button)
    remove_button = ttk.Button(base_buttons_frame, text="Remover Selecionado(s)", command=remove_selected_base_files, bootstyle="danger-outline")
    remove_button.pack(side=LEFT); all_buttons.append(remove_button)
    listbox_frame = ttk.Frame(base_file_frame)
    listbox_frame.grid(row=1, column=0, sticky='ew')
    listbox_frame.grid_columnconfigure(0, weight=1)
    listbox_frame.grid_rowconfigure(0, weight=1)
    base_file_listbox = Listbox(listbox_frame, height=3, bg="#212529", fg="white", selectbackground="#4e5d6c", selectforeground="white", borderwidth=1, relief="solid")
    base_file_listbox.grid(row=0, column=0, sticky='ew')
    scrollbar_listbox = ttk.Scrollbar(listbox_frame, orient=VERTICAL, command=base_file_listbox.yview)
    scrollbar_listbox.grid(row=0, column=1, sticky='ns')
    base_file_listbox.config(yscrollcommand=scrollbar_listbox.set)

    params_frame = ttk.Labelframe(center_pane, text=" 3. Entradas ", padding=10)
    center_pane.add(params_frame, weight=1)
    params_frame.grid_columnconfigure(0, weight=1)
    params_frame.grid_rowconfigure(1, weight=1)

    periodo_frame = ttk.Frame(params_frame)
    periodo_frame.grid(row=0, column=0, pady=(0, 10), sticky='ew')
    periodo_frame.grid_columnconfigure((1, 2, 5, 6), weight=1)

    ttk.Label(periodo_frame, text="Início:").grid(row=0, column=0, padx=(0, 5))
    combo_mes_inicio = ttk.Combobox(periodo_frame, state="readonly", values=[f"{i:02d}" for i in range(1, 13)])
    combo_mes_inicio.grid(row=0, column=1, padx=(0,5), sticky='ew')
    combo_ano_inicio = ttk.Combobox(periodo_frame, state="readonly", values=[str(i) for i in range(2021, 2029)])
    combo_ano_inicio.grid(row=0, column=2, padx=(5,0), sticky='ew')
    ttk.Separator(periodo_frame, orient=VERTICAL).grid(row=0, column=3, padx=15, sticky='ns')
    ttk.Label(periodo_frame, text="Fim:").grid(row=0, column=4, padx=(0, 5))
    combo_mes_fim = ttk.Combobox(periodo_frame, state="readonly", values=[f"{i:02d}" for i in range(1, 13)])
    combo_mes_fim.grid(row=0, column=5, padx=(0,5), sticky='ew')
    combo_ano_fim = ttk.Combobox(periodo_frame, state="readonly", values=[str(i) for i in range(2021, 2029)])
    combo_ano_fim.grid(row=0, column=6, padx=(5,0), sticky='ew')

    textbox_matriculas = ttk.Text(params_frame, font=("Consolas", 12), wrap=WORD)
    textbox_matriculas.grid(row=1, column=0, sticky='nsew')
    scrollbar = ttk.Scrollbar(params_frame, orient=VERTICAL, command=textbox_matriculas.yview)
    scrollbar.grid(row=1, column=1, sticky='ns')
    textbox_matriculas.config(yscrollcommand=scrollbar.set)
    
    right_pane_frame = ttk.Frame(center_pane)
    center_pane.add(right_pane_frame, weight=1)
    right_pane_frame.grid_columnconfigure(0, weight=1)
    right_pane_frame.grid_rowconfigure(1, weight=1)

    tab_view = ttk.Notebook(right_pane_frame)
    tab_view.grid(row=0, column=0, sticky='ew')
    
    progress_frame = ttk.Labelframe(right_pane_frame, text=" 4. Progresso Detalhado ", padding=10)
    progress_frame.grid(row=1, column=0, pady=(10,0), sticky='nsew')
    progress_frame.grid_columnconfigure(0, weight=1)
    progress_frame.grid_rowconfigure(0, weight=1)
    
    columns = ('tarefa', 'status')
    progress_list = ttk.Treeview(progress_frame, columns=columns, show='headings', bootstyle="primary")
    progress_list.heading('tarefa', text='Matrícula'); progress_list.heading('status', text='Status')
    progress_list.column('tarefa', width=150, anchor=W); progress_list.column('status', width=100, anchor=CENTER)
    progress_list.grid(row=0, column=0, sticky='nsew')
    scrollbar_list = ttk.Scrollbar(progress_frame, orient=VERTICAL, command=progress_list.yview)
    scrollbar_list.grid(row=0, column=1, sticky='ns')
    progress_list.config(yscrollcommand=scrollbar_list.set)
    progress_list_items = {}

    tab_holerites = ttk.Frame(tab_view, padding=10); tab_anuais = ttk.Frame(tab_view, padding=10); tab_individuais = ttk.Frame(tab_view, padding=10); tab_rescisao = ttk.Frame(tab_view, padding=10)
    tab_view.add(tab_holerites, text=" Holerites "); tab_view.add(tab_anuais, text=" Pagamentos Anuais "); tab_view.add(tab_individuais, text=" Documentos e Individuais "); #tab_view.add(tab_rescisao, text=" Rescisão ")

    btn = ttk.Button(tab_holerites, text="Executar HP", command=lambda: start_automation("HP Completo"), bootstyle="primary"); btn.pack(pady=5, fill=X); all_buttons.append(btn)
    btn = ttk.Button(tab_holerites, text="Executar HQ", command=lambda: start_automation("HQ Completo"), bootstyle="primary"); btn.pack(pady=5, fill=X); all_buttons.append(btn)
    btn = ttk.Button(tab_holerites, text="Executar HP + HQ", command=lambda: start_automation("HP e HQ Combinados"), bootstyle="info"); btn.pack(pady=5, fill=X); all_buttons.append(btn)
    decimo_frame = ttk.Frame(tab_anuais); decimo_frame.pack(pady=5, fill=X); decimo_frame.grid_columnconfigure((0, 1), weight=1)
    btn = ttk.Button(decimo_frame, text="Executar 13º Salário", command=lambda: start_automation("13º Salário"), bootstyle="primary"); btn.grid(row=0, column=0, columnspan=2, sticky=EW, pady=(0,5)); all_buttons.append(btn)
    btn = ttk.Button(decimo_frame, text="Apenas 1ª Parcela", command=lambda: start_automation("1ª Parcela 13º"), bootstyle="secondary"); btn.grid(row=1, column=0, sticky=EW, padx=(0,5)); all_buttons.append(btn)
    btn = ttk.Button(decimo_frame, text="Apenas 2ª Parcela", command=lambda: start_automation("2ª Parcela 13º"), bootstyle="secondary"); btn.grid(row=1, column=1, sticky=EW, padx=(5,0)); all_buttons.append(btn)
    plr_frame = ttk.Frame(tab_anuais); plr_frame.pack(pady=5, fill=X); plr_frame.grid_columnconfigure((0, 1), weight=1)
    btn = ttk.Button(plr_frame, text="Executar PLRs", command=lambda: start_automation("PLRs"), bootstyle="primary"); btn.grid(row=0, column=0, columnspan=2, sticky=EW, pady=(0,5)); all_buttons.append(btn)
    btn = ttk.Button(plr_frame, text="Apenas PLR 2022", command=lambda: start_automation("PLR 2022"), bootstyle="secondary"); btn.grid(row=1, column=0, sticky=EW, padx=(0,5)); all_buttons.append(btn)
    btn = ttk.Button(plr_frame, text="Apenas PLR 2025", command=lambda: start_automation("PLR 2025"), bootstyle="secondary"); btn.grid(row=1, column=1, sticky=EW, padx=(5,0)); all_buttons.append(btn)
    btn = ttk.Button(tab_individuais, text="Gerar Ficha Financeira", command=lambda: start_automation("Ficha Financeira"), bootstyle="primary"); btn.pack(pady=10, fill=X); all_buttons.append(btn)
    btn = ttk.Button(tab_individuais, text="Gerar CTPS Digital", command=lambda: start_automation("CTPS Digital"), bootstyle="primary"); btn.pack(pady=10, fill=X); all_buttons.append(btn)
    btn = ttk.Button(tab_individuais, text="Gerar HP Individual", command=lambda: start_automation("HP Individual (Off-Cycle)"), bootstyle="primary"); btn.pack(pady=10, fill=X); all_buttons.append(btn)
    
    # --- TRCT TRAVADO --- Botão desabilitado
    btn = ttk.Button(tab_rescisao, text="Gerar Termo de Rescisão (TRCT)", command=lambda: start_automation("TRCT"), bootstyle="primary", state="disabled"); btn.pack(pady=10, fill=X); all_buttons.append(btn)

    massa_frame = ttk.Frame(bottom_frame)
    massa_frame.grid(row=0, column=0, pady=(0,10), sticky='ew')
    massa_frame.grid_columnconfigure((0, 1), weight=1)
    btn_massa = ttk.Button(massa_frame, text="Massa Completa de Holerites", command=lambda: start_automation("Massa Completa de Holerites"), bootstyle="success-outline")
    btn_massa.grid(row=0, column=0, sticky='ew', padx=(0,5), ipady=5); all_buttons.append(btn_massa)
    btn_tudo = ttk.Button(massa_frame, text="EXECUTAR TUDO", command=lambda: start_automation("EXECUTAR TUDO"), bootstyle="danger")
    btn_tudo.grid(row=0, column=1, sticky='ew', padx=(5,0), ipady=5); all_buttons.append(btn_tudo)

    exec_frame = ttk.Labelframe(bottom_frame, text=" Status da Execução ", padding=10)
    exec_frame.grid(row=1, column=0, sticky='ew')
    exec_frame.grid_columnconfigure(0, weight=1)
    exec_frame.bind("<Button-1>", solar_easter_egg_check)
    geral_status_var = ttk.StringVar(value="Pronto para iniciar.")
    detalhe_status_var = ttk.StringVar(value="")
    ttk.Label(exec_frame, textvariable=geral_status_var, font=("", 12, "bold")).grid(row=0, column=0, sticky='w')
    ttk.Label(exec_frame, textvariable=detalhe_status_var, bootstyle="secondary").grid(row=1, column=0, sticky='w')
    progress_geral_var = ttk.DoubleVar(value=0)
    ttk.Progressbar(exec_frame, variable=progress_geral_var, bootstyle="info-striped").grid(row=2, column=0, pady=5, sticky='ew')
    
    load_config()
    app.mainloop()