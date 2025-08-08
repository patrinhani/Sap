# Importa a função 'execute' de cada um dos scripts modulares
from .hp import execute as run_hp
from .zdp1 import execute as run_zdp1
from .hp_com import execute as run_hp_com

# ALTERADO: A assinatura da função agora aceita 'progress_queue'
def execute(session, matriculas, periodo, config, output_base_path, progress_queue=None):
    """
    Orquestra a execução da sequência completa de Holerites,
    repassando a fila de progresso para cada módulo.
    """
    print("--- INICIANDO PROCESSO HP COMPLETO ---")
    
    # ALTERADO: O 'progress_queue' é passado para cada chamada
    sucesso, mensagem = run_hp(session, matriculas, periodo, config, output_base_path, progress_queue)
    if not sucesso:
        return False, mensagem
    
    sucesso, mensagem = run_zdp1(session, matriculas, periodo, config, output_base_path, progress_queue)
    if not sucesso:
        return False, mensagem
    
    sucesso, mensagem = run_hp_com(session, matriculas, periodo, config, output_base_path, progress_queue)
    if not sucesso:
        return False, mensagem
        
    return True, "Execução completa de Holerites finalizada com sucesso."