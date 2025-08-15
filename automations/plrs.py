from .plr_2022 import execute as run_plr_2022
from .plr_2025 import execute as run_plr_2025
from .sap_utils import keep_alive

def execute(session, matriculas, periodo, config, output_base_path, progress_queue=None):
    print("--- INICIANDO PROCESSO COMPLETO: PLRs ---")
    
    sucesso, mensagem = run_plr_2022(session, matriculas, periodo, config, output_base_path, progress_queue)
    if not sucesso:
        return False, f"Erro no PLR 2022: {mensagem}"
    
    keep_alive(session)
    
    sucesso, mensagem = run_plr_2025(session, matriculas, periodo, config, output_base_path, progress_queue)
    if not sucesso:
        return False, f"Erro no PLR 2025: {mensagem}"
        
    return True, "Execução de PLRs finalizada com sucesso."