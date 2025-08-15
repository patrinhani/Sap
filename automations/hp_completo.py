from .hp import execute as run_hp
from .zdp1 import execute as run_zdp1
from .hp_com import execute as run_hp_com
from .sap_utils import keep_alive # Importa a nova função

def execute(session, matriculas, periodo, config, output_base_path, progress_queue=None):
    print("--- INICIANDO PROCESSO HP COMPLETO ---")
    
    sucesso, mensagem = run_hp(session, matriculas, periodo, config, output_base_path, progress_queue)
    if not sucesso: return False, mensagem
    
    keep_alive(session) # Envia o sinal de vida
    
    sucesso, mensagem = run_zdp1(session, matriculas, periodo, config, output_base_path, progress_queue)
    if not sucesso: return False, mensagem
    
    keep_alive(session) # Envia o sinal de vida
    
    sucesso, mensagem = run_hp_com(session, matriculas, periodo, config, output_base_path, progress_queue)
    if not sucesso: return False, mensagem
        
    return True, "Execução completa de Holerites finalizada com sucesso."