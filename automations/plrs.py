from .plr_2022 import execute as run_plr_2022
from .plr_2025 import execute as run_plr_2025

def execute(session, matriculas, periodo, config, output_base_path):
    """Orquestra a execução dos PLRs."""
    print("--- INICIANDO PROCESSO COMPLETO: PLRs ---")
    
    # Etapa 1: PLR 2022
    sucesso, mensagem = run_plr_2022(session, matriculas, periodo, config, output_base_path)
    if not sucesso:
        return False, f"Erro no PLR 2022: {mensagem}"
    
    # Etapa 2: PLR 2025
    sucesso, mensagem = run_plr_2025(session, matriculas, periodo, config, output_base_path)
    if not sucesso:
        return False, f"Erro no PLR 2025: {mensagem}"
        
    print(">>> Processo de PLRs finalizado com sucesso! <<<")
    return True, "Execução de PLRs finalizada com sucesso."