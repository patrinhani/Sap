# Importa a função 'execute' de cada um dos scripts modulares
from .hp import execute as run_hp
from .zdp1_worker import execute as run_zdp1
from .hp_com import execute as run_hp_com
# Importa a nossa função centralizada de 'keep_alive'
from .sap_utils import keep_alive

def execute(session, matriculas, periodo, config, output_base_path, progress_queue=None):
    """
    Orquestra a execução da sequência completa de Holerites,
    enviando um sinal 'keep-alive' entre as etapas principais.
    """
    print("--- INICIANDO PROCESSO HP COMPLETO ---")
    
    # Etapa 1: HP
    sucesso, mensagem = run_hp(session, matriculas, periodo, config, output_base_path, progress_queue)
    if not sucesso: return False, mensagem
    
    # ALTERAÇÃO: Envia o sinal de vida após a primeira etapa
    keep_alive(session) 
    
    # Etapa 2: ZDP1
    sucesso, mensagem = run_zdp1(session, matriculas, periodo, config, output_base_path, progress_queue)
    if not sucesso: return False, mensagem
    
    # ALTERAÇÃO: Envia o sinal de vida após a segunda etapa
    keep_alive(session) 
    
    # Etapa 3: HP-COM
    sucesso, mensagem = run_hp_com(session, matriculas, periodo, config, output_base_path, progress_queue)
    if not sucesso: return False, mensagem
        
    return True, "Execução completa de Holerites finalizada com sucesso."