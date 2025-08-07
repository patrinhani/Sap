# Importa a função 'execute' de cada um dos nossos scripts modulares.
# Usamos 'as' para dar nomes únicos e evitar conflitos.
from .hp import execute as run_hp
from .zdp1 import execute as run_zdp1
from .hp_com import execute as run_hp_com

def execute(session, matriculas, periodo, config, output_base_path):
    """
    Orquestra a execução da sequência completa de Holerites,
    chamando cada processo modularmente.
    """
    print("--- INICIANDO PROCESSO COMPLETO DE HOLERITES ---")
    
    # Etapa 1: Executar o processo HP
    # ----------------------------------------------------
    sucesso, mensagem = run_hp(session, matriculas, periodo, config, output_base_path)
    if not sucesso:
        print(f"!!! PROCESSO COMPLETO INTERROMPIDO DEVIDO A ERRO NO HP !!!")
        # Retorna a mensagem de erro específica do módulo que falhou
        return False, mensagem
    
    print("--- Etapa HP concluída com sucesso. ---")
    
    # Etapa 2: Executar o processo ZDP1
    # ----------------------------------------------------
    sucesso, mensagem = run_zdp1(session, matriculas, periodo, config, output_base_path)
    if not sucesso:
        print(f"!!! PROCESSO COMPLETO INTERROMPIDO DEVIDO A ERRO NO ZDP1 !!!")
        return False, mensagem
        
    print("--- Etapa ZDP1 concluída com sucesso. ---")
    
    # Etapa 3: Executar o processo HP-COM
    # ----------------------------------------------------
    sucesso, mensagem = run_hp_com(session, matriculas, periodo, config, output_base_path)
    if not sucesso:
        print(f"!!! PROCESSO COMPLETO INTERROMPIDO DEVIDO A ERRO NO HP-COM !!!")
        return False, mensagem
        
    print("--- Etapa HP-COM concluída com sucesso. ---")
    
    print("\n>>> PROCESSO COMPLETO DE HOLERITES FINALIZADO COM SUCESSO! <<<")
    return True, "Execução completa de Holerites finalizada com sucesso."