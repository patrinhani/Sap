# Importa a função 'execute' de cada um dos scripts modulares
from .hq import execute as run_hq
from .zdp2 import execute as run_zdp2

# ALTERADO: A assinatura da função agora aceita 'progress_queue'
def execute(session, matriculas, periodo, config, output_base_path, progress_queue=None):
    """
    Orquestra a execução da sequência completa de Holerites Quinzenais,
    repassando a fila de progresso para cada módulo.
    """
    print("--- INICIANDO PROCESSO HQ COMPLETO ---")
    
    # ALTERADO: O 'progress_queue' é passado para cada chamada
    sucesso, mensagem = run_hq(session, matriculas, periodo, config, output_base_path, progress_queue)
    if not sucesso:
        return False, mensagem
    
    sucesso, mensagem = run_zdp2(session, matriculas, periodo, config, output_base_path, progress_queue)
    if not sucesso:
        return False, mensagem
        
    return True, "Execução completa de Holerites Quinzenais finalizada com sucesso."