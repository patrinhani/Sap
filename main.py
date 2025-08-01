# main_interface.py

import customtkinter as ctk
import time
import pyperclip
import os
from datetime import datetime

# --- 1. IMPORTAÇÕES DA LÓGICA ---
from automations.sap_utils import connect_to_sap 
from automations.ctps_digital import execute as run_ctps_digital
from automations.ficha_financeira import execute as run_ficha_financeira
from automations.hp_individual import execute as run_hp_individual
from automations.hp import execute as run_hp
from automations.hp_com import execute as run_hp_com
from automations.hq import execute as run_hq
from automations.zdp1 import execute as run_zdp1
from automations.zdp2 import execute as run_zdp2
from automations.hp13_1 import execute as run_hp13_1
from automations.hp13_2 import execute as run_hp13_2
from automations.plr_2022 import execute as run_plr_2022
from automations.plr_2025 import execute as run_plr_2025

# --- 2. MAPEAMENTO DE PROCESSOS ---
PROCESS_MAP = {
    "CTPS Digital": run_ctps_digital, "Ficha Financeira": run_ficha_financeira,
    "HP Individual": run_hp_individual, "HP": run_hp,
    "HP-COM": run_hp_com, "HQ": run_hq, "ZDP1": run_zdp1, "ZDP2": run_zdp2,
    "HP13.1": run_hp13_1, "HP13.2": run_hp13_2, "PLR 2022": run_plr_2022,
    "PLR 2025": run_plr_2025,
}

# --- Variáveis Globais ---
output_base_path = ""
sidebar_checkboxes = {}

# --- FUNÇÕES DE CONTROLE DA UI ---
def select_output_folder():
    global output_base_path
    try:
        path = ctk.filedialog.askdirectory(title="Selecione a Pasta Principal para Salvar os Arquivos")
        if path:
            output_base_path = path
            path_entry.configure(state="normal")
            path_entry.delete(0, "end")
            path_entry.insert(0, output_base_path)
            path_entry.configure(state="readonly")
    except Exception as e:
        status_label.configure(text="Erro ao selecionar pasta.", text_color="red")

def toggle_sidebar():
    if sidebar_frame.winfo_viewable(): sidebar_frame.grid_remove(); toggle_button.configure(text="▶")
    else: sidebar_frame.grid(); toggle_button.configure(text="◀")

# --- FUNÇÃO PRINCIPAL DE EXECUÇÃO ---
def execute_sequence(sequence_name, custom_sequence=None):
    if not output_base_path:
        status_label.configure(text="ERRO: Por favor, selecione uma pasta de destino primeiro!", text_color="red")
        return
    matriculas_lista = [linha for linha in textbox_matriculas.get("1.0", "end-1c").split("\n") if linha.strip()]
    if not matriculas_lista:
        status_label.configure(text="Erro: Nenhuma matrícula inserida.", text_color="red"); return
    
    periodo = {"inicio": f"{combo_mes_inicio.get()}/{combo_ano_inicio.get()}", "fim": f"{combo_mes_fim.get()}/{combo_ano_fim.get()}"}
    
    status_label.configure(text="Conectando ao SAP...", text_color="orange"); app.update_idletasks()
    session = connect_to_sap()
    if session is None:
        status_label.configure(text="Falha na conexão com o SAP.", text_color="red"); return

    sequencia_a_executar = []
    if sequence_name == "Holerites em Massa":
        sequencia_a_executar = ["HP", "HP-COM", "HQ", "ZDP1", "ZDP2", "HP13.1", "HP13.2", "PLR 2022", "PLR 2025"]
    elif sequence_name == "EXECUTAR TUDO":
        sequencia_a_executar = list(PROCESS_MAP.keys())
    elif sequence_name == "Executar Selecionados":
        sequencia_a_executar = custom_sequence if custom_sequence else []

    if not sequencia_a_executar:
        status_label.configure(text="Nenhum processo foi selecionado para execução.", text_color="orange")
        return

    print(f"--- INICIANDO EXECUÇÃO: {sequence_name} ---")
    print(f"Processos na fila: {', '.join(sequencia_a_executar)}")
    
    for processo_da_vez in sequencia_a_executar:
        if processo_da_vez in PROCESS_MAP:
            status_label.configure(text=f"Executando: {processo_da_vez}...", text_color="orange"); app.update_idletasks()
            funcao_a_executar = PROCESS_MAP[processo_da_vez]
            sucesso, mensagem = funcao_a_executar(session, matriculas_lista, periodo, {}, output_base_path)
            if not sucesso:
                status_label.configure(text=f"ERRO em '{processo_da_vez}': {mensagem}", text_color="red"); return 
        else:
            status_label.configure(text=f"AVISO: '{processo_da_vez}' não implementado. Pulando.", text_color="#FF8C00"); time.sleep(2)
    
    status_label.configure(text=f"Execução '{sequence_name}' concluída com sucesso!", text_color="green")

def run_custom_selection():
    selected_processes = [name for name, checkbox in sidebar_checkboxes.items() if checkbox.get() == 1]
    execute_sequence("Executar Selecionados", custom_sequence=selected_processes)

# --- Interface Gráfica ---
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")
app = ctk.CTk()
app.title("Painel de Automação SAP v6.0 Final")
app.geometry("850x700")

app.grid_columnconfigure(0, weight=0); app.grid_columnconfigure(1, weight=1); app.grid_rowconfigure(0, weight=1)

sidebar_frame = ctk.CTkFrame(app, width=200, corner_radius=0)
sidebar_frame.grid(row=0, column=0, sticky="nsw")
sidebar_label = ctk.CTkLabel(sidebar_frame, text="Selecionar Processos", font=ctk.CTkFont(size=16, weight="bold"))
sidebar_label.pack(pady=20, padx=20)
processos_na_sidebar = [
    "HP", "HP-COM", "HQ", "ZDP1", "ZDP2", "HP13.1", "HP13.2", "PLR 2022", "PLR 2025", 
    "Ficha Financeira", "CTPS Digital", "HP Individual"
]
for processo_nome in processos_na_sidebar:
    checkbox = ctk.CTkCheckBox(sidebar_frame, text=processo_nome)
    checkbox.pack(pady=7, padx=20, anchor="w")
    sidebar_checkboxes[processo_nome] = checkbox

main_content_frame = ctk.CTkFrame(app, corner_radius=0, fg_color="transparent")
main_content_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

toggle_button = ctk.CTkButton(main_content_frame, text="◀", width=30, command=toggle_sidebar)
toggle_button.pack(anchor="nw")
title_label = ctk.CTkLabel(main_content_frame, text="Painel de Automação SAP", font=ctk.CTkFont(size=22, weight="bold"))
title_label.pack(pady=(0, 10))

path_frame = ctk.CTkFrame(main_content_frame)
path_frame.pack(pady=10, fill="x")
path_label = ctk.CTkLabel(path_frame, text="0. Defina a Pasta de Destino Principal", font=ctk.CTkFont(weight="bold"))
path_label.pack(pady=5)
path_button = ctk.CTkButton(path_frame, text="Selecionar Pasta...", command=select_output_folder)
path_button.pack(side="left", padx=10, pady=10)
path_entry = ctk.CTkEntry(path_frame, placeholder_text="Nenhuma pasta selecionada", state="readonly")
path_entry.pack(side="left", fill="x", expand=True, padx=10, pady=10)

params_frame = ctk.CTkFrame(main_content_frame)
params_frame.pack(pady=10, fill="x")
params_label = ctk.CTkLabel(params_frame, text="1. Defina o Período e as Matrículas", font=ctk.CTkFont(weight="bold"))
params_label.pack(pady=5)
periodo_frame = ctk.CTkFrame(params_frame, fg_color="transparent")
periodo_frame.pack(pady=10)
ctk.CTkLabel(periodo_frame, text="Início:").pack(side="left", padx=(10, 5))
combo_mes_inicio = ctk.CTkComboBox(periodo_frame, width=80, values=[f"{i:02d}" for i in range(1, 13)])
combo_mes_inicio.pack(side="left", padx=5)
combo_ano_inicio = ctk.CTkComboBox(periodo_frame, width=100, values=[str(i) for i in range(2020, 2029)])
combo_ano_inicio.pack(side="left", padx=5)
ctk.CTkLabel(periodo_frame, text="Fim:").pack(side="left", padx=(20, 5))
combo_mes_fim = ctk.CTkComboBox(periodo_frame, width=80, values=[f"{i:02d}" for i in range(1, 13)])
combo_mes_fim.pack(side="left", padx=5)
combo_ano_fim = ctk.CTkComboBox(periodo_frame, width=100, values=[str(i) for i in range(2020, 2029)])
combo_ano_fim.pack(side="left", padx=10)

matriculas_frame = ctk.CTkFrame(main_content_frame)
matriculas_frame.pack(pady=10, fill="x", expand=True)
textbox_matriculas = ctk.CTkTextbox(matriculas_frame)
textbox_matriculas.pack(pady=10, padx=10, fill="both", expand=True)

actions_frame = ctk.CTkFrame(main_content_frame)
actions_frame.pack(pady=15, padx=10, fill="x")
actions_frame.grid_columnconfigure((0, 1, 2), weight=1)

run_selected_button = ctk.CTkButton(actions_frame, text="Executar Selecionados", height=40, fg_color="#006400", hover_color="#004d00", font=ctk.CTkFont(weight="bold"), command=run_custom_selection)
run_selected_button.grid(row=0, column=0, padx=5, pady=10, sticky="ew")
massa_holerites_button = ctk.CTkButton(actions_frame, text="Gerar Holerites em Massa", height=40, font=ctk.CTkFont(weight="bold"), command=lambda: execute_sequence("Holerites em Massa"))
massa_holerites_button.grid(row=0, column=1, padx=5, pady=10, sticky="ew")
run_all_button = ctk.CTkButton(actions_frame, text="EXECUTAR TUDO", height=40, fg_color="#990000", hover_color="#660000", font=ctk.CTkFont(weight="bold"), command=lambda: execute_sequence("EXECUTAR TUDO"))
run_all_button.grid(row=0, column=2, padx=5, pady=10, sticky="ew")

status_frame = ctk.CTkFrame(main_content_frame, height=40)
status_frame.pack(pady=10, fill="x")
status_label = ctk.CTkLabel(status_frame, text="Pronto para iniciar.", text_color="gray")
status_label.pack(pady=10)

app.mainloop()