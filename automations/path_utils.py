import os
from datetime import datetime

def get_save_path(base_path, process_name, ano=None, mes=None, matricula=None):
    """
    Cria e retorna o caminho completo para salvar os arquivos,
    seguindo a nova estrutura de pastas centralizada.
    """
    hoje = datetime.now().strftime("%d.%m")
    
    # 1. Cria a pasta raiz principal com a data do dia
    daily_root = os.path.join(base_path, hoje)
    os.makedirs(daily_root, exist_ok=True)

    # NOVO: Cria a pasta vazia "GeDoc" dentro da pasta do dia
    gedoc_path = os.path.join(daily_root, "GeDoc")
    os.makedirs(gedoc_path, exist_ok=True)
    
    # 2. Define o caminho final baseado no processo
    final_path = daily_root # O padrão é salvar na raiz da pasta do dia

    # Processos de Holerite, 13º e PLR vão para uma subpasta "HP SAP - {data}"
    if process_name in ["HP", "ZDP1", "HP-COM", "HQ", "ZDP2", "HP13_1", "HP13_2", "PLR_2022", "PLR_2025"]:
        hp_root = os.path.join(daily_root, f"HP SAP - {hoje}")
        
        # Define as sub-subpastas dentro de "HP SAP - {data}"
        if process_name in ["HP", "ZDP1", "HP-COM"]:
            final_path = os.path.join(hp_root, "HP", f"HP - {int(mes)}.{ano}")
        elif process_name in ["HQ", "ZDP2"]:
            final_path = os.path.join(hp_root, "HPQ", f"HPQ - {int(mes)}.{ano}")
        elif process_name == "HP13_1":
            final_path = os.path.join(hp_root, f"HP 13 - 01 {ano}")
        elif process_name == "HP13_2":
            final_path = os.path.join(hp_root, f"HP 13 - 02 {ano}")
        elif process_name == "PLR_2022":
            final_path = os.path.join(hp_root, "HPL 2022")
        elif process_name == "PLR_2025":
            final_path = os.path.join(hp_root, "HPL 2025")

    # CTPS vai para sua própria pasta dentro da pasta do dia
    elif process_name == "CTPS":
        final_path = os.path.join(daily_root, "CTPS")

    # Ficha Financeira e HP Individual salvam diretamente na pasta do dia
    elif process_name in ["FichaFinanceira", "HP_Individual"]:
        final_path = daily_root

    # 3. Garante que a estrutura de pastas final seja criada no disco
    os.makedirs(final_path, exist_ok=True)
    
    return final_path