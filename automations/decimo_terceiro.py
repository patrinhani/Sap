# Importa a função 'execute' de cada um dos scripts modulares
from .hp13_1 import execute as run_hp13_1
from .hp13_2 import execute as run_hp13_2

# ALTERADO: A assinatura da função agora aceita 'progress_queue'
def execute(session, matriculas, periodo, config, output_base_path, progress_queue=None):
    """
    Orquestra a execução das duas parcelas do 13º Salário,
    repassando a fila de progresso para cada módulo.
    """
    print("--- INICIANDO PROCESSO COMPLETO: 13º Salário ---")
    
    # ALTERADO: O 'progress_queue' é passado para cada chamada
    sucesso, mensagem = run_hp13_1(session, matriculas, periodo, config, output_base_path, progress_queue)
    if not sucesso:
        return False, f"Erro na 1ª Parcela do 13º: {mensagem}"
    
    sucesso, mensagem = run_hp13_2(session, matriculas, periodo, config, output_base_path, progress_queue)
    if not sucesso:
        return False, f"Erro na 2ª Parcela do 13º: {mensagem}"
        
    print(">>> Processo de 13º Salário finalizado com sucesso! <<<")
    return True, "Execução do 13º Salário (ambas parcelas) finalizada com sucesso."