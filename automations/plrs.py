# Importa a função 'execute' de cada um dos scripts modulares
from .plr_2022 import execute as run_plr_2022
from .plr_2025 import execute as run_plr_2025

# ALTERADO: A assinatura da função agora aceita 'progress_queue'
def execute(session, matriculas, periodo, config, output_base_path, progress_queue=None):
    """
    Orquestra a execução dos PLRs,
    repassando a fila de progresso para cada módulo.
    """
    print("--- INICIANDO PROCESSO COMPLETO: PLRs ---")
    
    # ALTERADO: O 'progress_queue' é passado para cada chamada
    sucesso, mensagem = run_plr_2022(session, matriculas, periodo, config, output_base_path, progress_queue)
    if not sucesso:
        return False, f"Erro no PLR 2022: {mensagem}"
    
    sucesso, mensagem = run_plr_2025(session, matriculas, periodo, config, output_base_path, progress_queue)
    if not sucesso:
        return False, f"Erro no PLR 2025: {mensagem}"
        
    print(">>> Processo de PLRs finalizado com sucesso! <<<")
    return True, "Execução de PLRs finalizada com sucesso."