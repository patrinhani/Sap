from .hp13_1 import execute as run_hp13_1
from .hp13_2 import execute as run_hp13_2
from .sap_utils import keep_alive

def execute(session, matriculas, periodo, config, output_base_path, progress_queue=None):
    print("--- INICIANDO PROCESSO COMPLETO: 13º Salário ---")
    
    sucesso, mensagem = run_hp13_1(session, matriculas, periodo, config, output_base_path, progress_queue)
    if not sucesso:
        return False, f"Erro na 1ª Parcela do 13º: {mensagem}"
    
    keep_alive(session)
    
    sucesso, mensagem = run_hp13_2(session, matriculas, periodo, config, output_base_path, progress_queue)
    if not sucesso:
        return False, f"Erro na 2ª Parcela do 13º: {mensagem}"
        
    return True, "Execução do 13º Salário (ambas parcelas) finalizada com sucesso."