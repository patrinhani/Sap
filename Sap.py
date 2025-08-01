import customtkinter as ctk

# --- Configurações da Janela Principal ---
# Define o tema (System, Dark, Light) e a cor padrão
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

# Cria a janela principal da aplicação
app = ctk.CTk()
app.title("Painel de Automação SAP v1.0")
app.geometry("750x800") # Define o tamanho inicial da janela

# --- Função de Placeholder ---
# Apenas para simular o clique dos botões, não faz nada de verdade
def placeholder_function(processo):
    """Função que será chamada pelos botões para dar feedback visual."""
    matriculas_texto = textbox_matriculas.get("1.0", "end-1c")
    num_matriculas = len([linha for linha in matriculas_texto.split("\n") if linha.strip()])
    
    print(f"Botão '{processo}' foi clicado.")
    print(f"Período: {combo_mes_inicio.get()}/{combo_ano_inicio.get()} a {combo_mes_fim.get()}/{combo_ano_fim.get()}")
    print(f"Número de matrículas inseridas: {num_matriculas}")
    
    status_label.configure(text=f"Executando: {processo}...", text_color="orange")
    app.after(2000, lambda: status_label.configure(text=f"Processo '{processo}' concluído!", text_color="green"))


# --- Título Principal ---
title_label = ctk.CTkLabel(app, text="Painel de Automação SAP", font=ctk.CTkFont(size=22, weight="bold"))
title_label.pack(pady=(20, 15))


# --- Seção 1: Parâmetros de Período ---
params_frame = ctk.CTkFrame(app)
params_frame.pack(pady=10, padx=20, fill="x")

params_label = ctk.CTkLabel(params_frame, text="1. Defina o Período de Execução", font=ctk.CTkFont(weight="bold"))
params_label.pack()

periodo_frame = ctk.CTkFrame(params_frame, fg_color="transparent")
periodo_frame.pack(pady=10)

# Widgets para o período inicial
ctk.CTkLabel(periodo_frame, text="Início:").pack(side="left", padx=(10, 5))
combo_mes_inicio = ctk.CTkComboBox(periodo_frame, width=80, values=[f"{i:02d}" for i in range(1, 13)])
combo_mes_inicio.pack(side="left", padx=5)
combo_ano_inicio = ctk.CTkComboBox(periodo_frame, width=100, values=[str(i) for i in range(2021, 2026)])
combo_ano_inicio.pack(side="left", padx=5)

# Widgets para o período final
ctk.CTkLabel(periodo_frame, text="Fim:").pack(side="left", padx=(20, 5))
combo_mes_fim = ctk.CTkComboBox(periodo_frame, width=80, values=[f"{i:02d}" for i in range(1, 13)])
combo_mes_fim.pack(side="left", padx=5)
combo_ano_fim = ctk.CTkComboBox(periodo_frame, width=100, values=[str(i) for i in range(2021, 2026)])
combo_ano_fim.pack(side="left", padx=10)


# --- Seção 2: Lista de Matrículas ---
matriculas_frame = ctk.CTkFrame(app)
matriculas_frame.pack(pady=10, padx=20, fill="x")

matriculas_label = ctk.CTkLabel(matriculas_frame, text="2. Cole as Matrículas (uma por linha)", font=ctk.CTkFont(weight="bold"))
matriculas_label.pack()

textbox_matriculas = ctk.CTkTextbox(matriculas_frame, height=180)
textbox_matriculas.pack(pady=10, padx=10, fill="x", expand=True)


# --- Seção 3: Botões de Automação ---
actions_frame = ctk.CTkFrame(app)
actions_frame.pack(pady=10, padx=20, fill="x")

actions_label = ctk.CTkLabel(actions_frame, text="3. Escolha o Processo para Executar", font=ctk.CTkFont(weight="bold"))
actions_label.pack()

# Frame para organizar os botões em uma grade (grid)
buttons_grid_frame = ctk.CTkFrame(actions_frame, fg_color="transparent")
buttons_grid_frame.pack(pady=10, padx=10)
# Configura as colunas da grade para terem o mesmo tamanho
buttons_grid_frame.grid_columnconfigure((0, 1), weight=1)

# Lista de processos para criar os botões dinamicamente
processos = [
    "HP + HPCOMM", "HP + HQ", "HPS 13.1 e 13.2",
    "HQ + ZDP", "PLRs (2022 e 2025)", "Ficha Financeira",
    "CTPS Digital", "HP Individual (Off-Cycle)"
]

# Cria os botões em um loop e os posiciona na grade
for i, processo_nome in enumerate(processos):
    row = i // 2
    column = i % 2
    button = ctk.CTkButton(buttons_grid_frame, text=processo_nome, command=lambda p=processo_nome: placeholder_function(p))
    button.grid(row=row, column=column, padx=10, pady=7, sticky="ew") # sticky="ew" faz o botão esticar horizontalmente

# Botão especial para "Rodar TUDO"
run_all_button = ctk.CTkButton(actions_frame, text="EXECUTAR TUDO", 
                               fg_color="#990000", hover_color="#660000",
                               font=ctk.CTkFont(weight="bold"),
                               command=lambda: placeholder_function("EXECUTAR TUDO"))
run_all_button.pack(pady=10, padx=10, fill="x")


# --- Seção 4: Barra de Status ---
status_frame = ctk.CTkFrame(app, height=40)
status_frame.pack(pady=(15, 20), padx=20, fill="x")

status_label = ctk.CTkLabel(status_frame, text="Pronto para iniciar.", text_color="gray")
status_label.pack(pady=10)

# --- Inicia a aplicação ---
app.mainloop()