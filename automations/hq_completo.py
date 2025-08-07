# automations/hq_completo.py

# Importa a função 'execute' de cada um dos nossos scripts modulares.
from .hq import execute as run_hq
from .zdp2 import execute as run_zdp2

def execute(session, matriculas, periodo, config, output_base_path):
    """
    Orquestra a execução da sequência completa de Holerites Quinzenais,
    chamando cada processo modularmente.
    """
    print("--- INICIANDO PROCESSO COMPLETO DE HOLERITES QUINZENAIS (HQ) ---")
    
    # Etapa 1: Executar o processo HQ
    # ----------------------------------------------------
    sucesso, mensagem = run_hq(session, matriculas, periodo, config, output_base_path)
    if not sucesso:
        print(f"!!! PROCESSO COMPLETO INTERROMPIDO DEVIDO A ERRO NO HQ !!!")
        # Retorna a mensagem de erro específica do módulo que falhou
        return False, mensagem
    
    print("--- Etapa HQ concluída com sucesso. ---")
    
    # Etapa 2: Executar o processo ZDP2
    # ----------------------------------------------------
    sucesso, mensagem = run_zdp2(session, matriculas, periodo, config, output_base_path)
    if not sucesso:
        print(f"!!! PROCESSO COMPLETO INTERROMPIDO DEVIDO A ERRO NO ZDP2 !!!")
        return False, mensagem
        
    print("--- Etapa ZDP2 concluída com sucesso. ---")
    
    print("\n>>> PROCESSO COMPLETO DE HOLERITES QUINZENAIS FINALIZADO COM SUCESSO! <<<")
    return True, "Execução completa de Holerites Quinzenais finalizada com sucesso."