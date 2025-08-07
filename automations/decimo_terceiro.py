from .hp13_1 import execute as run_hp13_1
from .hp13_2 import execute as run_hp13_2

def execute(session, matriculas, periodo, config, output_base_path):
    """Orquestra a execução das duas parcelas do 13º Salário."""
    print("--- INICIANDO PROCESSO COMPLETO: 13º Salário ---")
    
    # Etapa 1: 1ª Parcela
    sucesso, mensagem = run_hp13_1(session, matriculas, periodo, config, output_base_path)
    if not sucesso:
        return False, f"Erro na 1ª Parcela do 13º: {mensagem}"
    
    # Etapa 2: 2ª Parcela
    sucesso, mensagem = run_hp13_2(session, matriculas, periodo, config, output_base_path)
    if not sucesso:
        return False, f"Erro na 2ª Parcela do 13º: {mensagem}"
        
    print(">>> Processo de 13º Salário finalizado com sucesso! <<<")
    return True, "Execução do 13º Salário (ambas parcelas) finalizada com sucesso."