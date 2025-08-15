from .hq import execute as run_hq
from .zdp2 import execute as run_zdp2
from .sap_utils import keep_alive

def execute(session, matriculas, periodo, config, output_base_path, progress_queue=None):
    print("--- INICIANDO PROCESSO HQ COMPLETO ---")
    
    sucesso, mensagem = run_hq(session, matriculas, periodo, config, output_base_path, progress_queue)
    if not sucesso: return False, mensagem
    
    keep_alive(session)
    
    sucesso, mensagem = run_zdp2(session, matriculas, periodo, config, output_base_path, progress_queue)
    if not sucesso: return False, mensagem
        
    return True, "Execução completa de Holerites Quinzenais finalizada com sucesso."