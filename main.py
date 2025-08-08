import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import os
import json
from datetime import datetime
from tkinter import filedialog, messagebox
import ctypes

# --- LÓGICA DA APLICAÇÃO (sem alterações) ---
# (Toda a parte de imports, PROCESS_MAP, SEQUENCES e funções de controle continua aqui, exatamente como antes)
# ...
from automations.sap_utils import connect_to_sap
from automations.hp_completo import execute as run_hp_completo
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

PROCESS_MAP = {
    "HP Completo": run_hp_completo,"HQ Completo": run_hq_completo,"13º Salário": run_decimo_terceiro,"PLRs": run_plrs,"CTPS Digital": run_ctps_digital, "Ficha Financeira": run_ficha_financeira,"HP Individual (Off-Cycle)": run_hp_individual,"1ª Parcela 13º": run_hp13_1,"2ª Parcela 13º": run_hp13_2,"PLR 2022": run_plr_2022,"PLR 2025": run_plr_2025,
}

SEQUENCES = {
    "HP Completo": ["HP Completo"],"HQ Completo": ["HQ Completo"],"13º Salário": ["13º Salário"],"PLRs": ["PLRs"],"Ficha Financeira": ["Ficha Financeira"],"CTPS Digital": ["CTPS Digital"],"HP Individual (Off-Cycle)": ["HP Individual (Off-Cycle)"],"1ª Parcela 13º": ["1ª Parcela 13º"],"2ª Parcela 13º": ["2ª Parcela 13º"],"PLR 2022": ["PLR 2022"],"PLR 2025": ["PLR 2025"],"HP e HQ Combinados": ["HP Completo", "HQ Completo"],"Massa Completa de Holerites": ["HP Completo", "HQ Completo", "13º Salário", "PLRs"],"EXECUTAR TUDO": ["Massa Completa de Holerites", "Ficha Financeira", "CTPS Digital", "HP Individual (Off-Cycle)"],
}

CONFIG_FILE = "config.json"
output_base_path = ""

def save_last_period():
    config_data = { "mes_inicio": combo_mes_inicio.get(), "ano_inicio": combo_ano_inicio.get(), "mes_fim": combo_mes_fim.get(), "ano_fim": combo_ano_fim.get() }
    try:
        with open(CONFIG_FILE, "w") as f: json.dump(config_data, f)
    except Exception as e: print(f"Erro ao salvar configuração: {e}")

def load_last_period():
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                config_data = json.load(f)
                now = datetime.now()
                combo_mes_inicio.set(config_data.get("mes_inicio", f"{now.month:02d}"))
                combo_ano_inicio.set(config_data.get("ano_inicio", str(now.year)))
                combo_mes_fim.set(config_data.get("mes_fim", f"{now.month:02d}"))
                combo_ano_fim.set(config_data.get("ano_fim", str(now.year)))
    except Exception as e: print(f"Erro ao carregar configuração: {e}")

def select_output_folder():
    global output_base_path
    path = filedialog.askdirectory(title="Selecione a Pasta Principal de Saída")
    if path:
        output_base_path = path
        path_entry_var.set(output_base_path)

def execute_sequence(sequence_name):
    if not output_base_path:
        messagebox.showerror("Erro", "Por favor, selecione uma pasta de destino primeiro!")
        return
    matriculas_lista = [linha for linha in textbox_matriculas.get("1.0", "end-1c").split("\n") if linha.strip()]
    if not matriculas_lista:
        messagebox.showerror("Erro", "Nenhuma matrícula inserida. Por favor, insira pelo menos uma matrícula.")
        return
    periodo = {"inicio": f"{combo_mes_inicio.get()}/{combo_ano_inicio.get()}", "fim": f"{combo_mes_fim.get()}/{combo_ano_fim.get()}"}
    tarefas_iniciais = SEQUENCES.get(sequence_name, [])
    tarefas_finais_para_executar = []
    for tarefa in tarefas_iniciais:
        if tarefa in SEQUENCES:
            tarefas_finais_para_executar.extend(SEQUENCES.get(tarefa, []))
        else:
            tarefas_finais_para_executar.append(tarefa)
    tarefas_finais_para_executar = list(dict.fromkeys(tarefas_finais_para_executar))
    if not tarefas_finais_para_executar:
        messagebox.showwarning("Aviso", f"A sequência '{sequence_name}' está vazia ou não foi definida corretamente.")
        return
    status_label_var.set("Conectando ao SAP...")
    status_label.configure(bootstyle="warning")
    app.update_idletasks()
    session = connect_to_sap()
    if session is None:
        status_label_var.set("Falha na conexão com o SAP. Verifique se o SAP GUI está aberto.")
        status_label.configure(bootstyle="danger")
        return
    print(f"--- INICIANDO EXECUÇÃO DA SEQUÊNCIA: {sequence_name} ---")
    for processo_nome in tarefas_finais_para_executar:
        if processo_nome in PROCESS_MAP:
            status_label_var.set(f"Executando: {processo_nome}...")
            status_label.configure(bootstyle="warning")
            app.update_idletasks()
            funcao_a_executar = PROCESS_MAP[processo_nome]
            sucesso, mensagem = funcao_a_executar(session, matriculas_lista, periodo, {}, output_base_path)
            if not sucesso:
                status_label_var.set(f"ERRO em '{processo_nome}': {mensagem}")
                status_label.configure(bootstyle="danger")
                messagebox.showerror("Erro na Execução", f"Ocorreu um erro durante o processo '{processo_nome}':\n\n{mensagem}")
                return
        else:
            print(f"AVISO: Processo '{processo_nome}' não encontrado no PROCESS_MAP.")
    status_label_var.set(f"Sequência '{sequence_name}' concluída com sucesso!")
    status_label.configure(bootstyle="success")
    messagebox.showinfo("Concluído", f"A sequência '{sequence_name}' foi executada com sucesso!")
    save_last_period()

# --- Interface Gráfica ---
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

app = ttk.Window(themename="vapor")
app.title("Painel de Automação SAP")
app.state('zoomed') 
app.minsize(width=800, height=700)

main_frame = ttk.Frame(app, padding=20)
main_frame.pack(fill=BOTH, expand=YES)

title_label = ttk.Label(main_frame, text="Painel de Automação SAP", font=("", 22, "bold"), bootstyle="primary")
title_label.pack(pady=(0, 10))

path_frame = ttk.Labelframe(main_frame, text=" 1. Defina a Pasta de Destino ", padding=10)
path_frame.pack(pady=10, fill=X)
path_button = ttk.Button(path_frame, text="Selecionar Pasta...", command=select_output_folder, bootstyle="info")
path_button.pack(side=LEFT, padx=(0, 10))
path_entry_var = ttk.StringVar(value="Nenhuma pasta selecionada")
path_entry = ttk.Entry(path_frame, textvariable=path_entry_var, state="readonly")
path_entry.pack(side=LEFT, fill=X, expand=YES)

status_label_var = ttk.StringVar(value="Pronto para iniciar.")
status_label = ttk.Label(main_frame, textvariable=status_label_var, font=("", 10), bootstyle="secondary")
status_label.pack(side=BOTTOM, pady=(10, 0), fill=X)

massa_frame = ttk.Frame(main_frame)
massa_frame.pack(side=BOTTOM, pady=10, fill=X)
massa_frame.grid_columnconfigure((0, 1), weight=1)

# ALTERADO: Usando o estilo 'outline' para um visual mais sutil e legível
ttk.Button(massa_frame, text="Massa Completa de Holerites", command=lambda: execute_sequence("Massa Completa de Holerites"), bootstyle="success-outline").grid(row=0, column=0, sticky=EW, padx=(0,5), ipady=5)
ttk.Button(massa_frame, text="EXECUTAR TUDO", command=lambda: execute_sequence("EXECUTAR TUDO"), bootstyle="danger").grid(row=0, column=1, sticky=EW, padx=(5,0), ipady=5)

tab_view = ttk.Notebook(main_frame)
tab_view.pack(side=BOTTOM, pady=10, fill=X)

tab_holerites = ttk.Frame(tab_view, padding=10)
tab_anuais = ttk.Frame(tab_view, padding=10)
tab_individuais = ttk.Frame(tab_view, padding=10)
tab_view.add(tab_holerites, text=" Holerites ")
tab_view.add(tab_anuais, text=" Pagamentos Anuais ")
tab_view.add(tab_individuais, text=" Documentos e Individuais ")

ttk.Button(tab_holerites, text="Executar HP Completo", command=lambda: execute_sequence("HP Completo"), bootstyle="primary").pack(pady=5, fill=X)
ttk.Button(tab_holerites, text="Executar HQ Completo", command=lambda: execute_sequence("HQ Completo"), bootstyle="primary").pack(pady=5, fill=X)
ttk.Button(tab_holerites, text="Executar HP + HQ Combinados", command=lambda: execute_sequence("HP e HQ Combinados"), bootstyle="info").pack(pady=5, fill=X)

decimo_frame = ttk.Frame(tab_anuais)
decimo_frame.pack(pady=5, fill=X)
decimo_frame.grid_columnconfigure((0, 1), weight=1)
ttk.Button(decimo_frame, text="Executar 13º Salário (Completo)", command=lambda: execute_sequence("13º Salário"), bootstyle="primary").grid(row=0, column=0, columnspan=2, sticky=EW, pady=(0,5))
ttk.Button(decimo_frame, text="Apenas 1ª Parcela", command=lambda: execute_sequence("1ª Parcela 13º"), bootstyle="secondary").grid(row=1, column=0, sticky=EW, padx=(0,5))
ttk.Button(decimo_frame, text="Apenas 2ª Parcela", command=lambda: execute_sequence("2ª Parcela 13º"), bootstyle="secondary").grid(row=1, column=1, sticky=EW, padx=(5,0))

plr_frame = ttk.Frame(tab_anuais)
plr_frame.pack(pady=5, fill=X)
plr_frame.grid_columnconfigure((0, 1), weight=1)
ttk.Button(plr_frame, text="Executar PLRs (Completo)", command=lambda: execute_sequence("PLRs"), bootstyle="primary").grid(row=0, column=0, columnspan=2, sticky=EW, pady=(0,5))
ttk.Button(plr_frame, text="Apenas PLR 2022", command=lambda: execute_sequence("PLR 2022"), bootstyle="secondary").grid(row=1, column=0, sticky=EW, padx=(0,5))
ttk.Button(plr_frame, text="Apenas PLR 2025", command=lambda: execute_sequence("PLR 2025"), bootstyle="secondary").grid(row=1, column=1, sticky=EW, padx=(5,0))

ttk.Button(tab_individuais, text="Gerar Ficha Financeira", command=lambda: execute_sequence("Ficha Financeira"), bootstyle="primary").pack(pady=10, fill=X)
ttk.Button(tab_individuais, text="Gerar CTPS Digital", command=lambda: execute_sequence("CTPS Digital"), bootstyle="primary").pack(pady=10, fill=X)
ttk.Button(tab_individuais, text="Gerar HP Individual (Off-Cycle)", command=lambda: execute_sequence("HP Individual (Off-Cycle)"), bootstyle="primary").pack(pady=10, fill=X)

params_frame = ttk.Labelframe(main_frame, text=" 2. Defina o Período e as Matrículas ", padding=10)
params_frame.pack(pady=10, fill=BOTH, expand=YES)

periodo_frame = ttk.Frame(params_frame)
periodo_frame.pack(pady=10, fill=X)
ttk.Label(periodo_frame, text="Início:").pack(side=LEFT, padx=(0, 5))
combo_mes_inicio = ttk.Combobox(periodo_frame, state="readonly", width=5, values=[f"{i:02d}" for i in range(1, 13)])
combo_mes_inicio.pack(side=LEFT, padx=5)
combo_ano_inicio = ttk.Combobox(periodo_frame, state="readonly", width=7, values=[str(i) for i in range(2023, 2029)])
combo_ano_inicio.pack(side=LEFT, padx=5)
ttk.Separator(periodo_frame, orient=VERTICAL).pack(side=LEFT, padx=15, fill=Y, ipady=5)
ttk.Label(periodo_frame, text="Fim:").pack(side=LEFT, padx=(0, 5))
combo_mes_fim = ttk.Combobox(periodo_frame, state="readonly", width=5, values=[f"{i:02d}" for i in range(1, 13)])
combo_mes_fim.pack(side=LEFT, padx=5)
combo_ano_fim = ttk.Combobox(periodo_frame, state="readonly", width=7, values=[str(i) for i in range(2023, 2029)])
combo_ano_fim.pack(side=LEFT, padx=10)

text_frame = ttk.Frame(params_frame)
text_frame.pack(pady=10, fill=BOTH, expand=YES)
text_frame.grid_rowconfigure(0, weight=1)
text_frame.grid_columnconfigure(0, weight=1)
textbox_matriculas = ttk.Text(text_frame, font=("Consolas", 12), wrap=WORD)
textbox_matriculas.grid(row=0, column=0, sticky=NSEW)
scrollbar = ttk.Scrollbar(text_frame, orient=VERTICAL, command=textbox_matriculas.yview)
scrollbar.grid(row=0, column=1, sticky=NS)
textbox_matriculas.config(yscrollcommand=scrollbar.set)

load_last_period()
app.mainloop()