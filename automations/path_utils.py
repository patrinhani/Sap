import os
from datetime import datetime

def get_save_path(base_path, process_name, ano=None, mes=None, matricula=None):
    """
    Cria e retorna o caminho completo para salvar os arquivos,
    seguindo a estrutura dos scripts VBA originais.
    """
    hoje = datetime.now().strftime("%d.%m")
    
    # Define um nome para a pasta raiz da execução do dia
    root_folder_name = f"SAP Files - {hoje}"
    
    # Casos especiais para processos que tinham nomes de pasta diferentes no VBA/Python original
    if process_name == "CTPS":
        root_folder_name = f"CTPS Digital SAP - {hoje}"
    elif process_name == "FichaFinanceira":
        root_folder_name = f"Ficha Financeira SAP - {hoje}"
    elif process_name == "HP_Individual":
        root_folder_name = f"HP Individual SAP - {hoje}"

    root_folder = os.path.join(base_path, root_folder_name)
    final_path = root_folder

    # Define a subpasta e o nome do arquivo/pasta final com base no processo
    if process_name in ["HP", "ZDP1", "HP-COM"]:
        final_path = os.path.join(root_folder, "HP", f"HP - {int(mes)}.{ano}")
    elif process_name in ["HQ", "ZDP2"]:
        final_path = os.path.join(root_folder, "HPQ", f"HPQ - {int(mes)}.{ano}")
    elif process_name == "HP13_1":
        final_path = os.path.join(root_folder, f"HP 13 - 01 {ano}")
    elif process_name == "HP13_2":
        final_path = os.path.join(root_folder, f"HP 13 - 02 {ano}")
    elif process_name == "PLR_2022":
        final_path = os.path.join(root_folder, "HPL 2022")
    elif process_name == "PLR_2025":
        final_path = os.path.join(root_folder, "HPL 2025")
    elif process_name == "CTPS":
        final_path = os.path.join(root_folder, "CTPS")
    
    # Garante que a estrutura de pastas seja criada no disco
    os.makedirs(final_path, exist_ok=True)
    
    return final_path