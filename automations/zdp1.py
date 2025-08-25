import pandas as pd
import os
from .zdp1_worker import execute as run_zdp1_worker
from .zct1 import execute as run_zct1
from .zct2 import execute as run_zct2
from .sap_utils import keep_alive

def execute(session, matriculas, periodo, config, output_base_path, progress_queue=None):
    try:
        print("--- Iniciando Orquestrador Inteligente ZDP1/ZCT ---")
        
        base_file_paths = config.get("base_file_paths", []) # Pega a LISTA de caminhos
        
        # Se nenhuma planilha foi selecionada, roda o ZDP1 padrão para todos
        if not base_file_paths:
            print("AVISO: Nenhuma planilha base selecionada. Executando ZDP1 padrão para todas as matrículas.")
            return run_zdp1_worker(session, matriculas, periodo, {}, output_base_path, progress_queue)

        # Carrega e combina TODAS as planilhas em uma única base de dados
        print(f"Carregando {len(base_file_paths)} planilha(s) base...")
        all_dfs = [pd.read_excel(path) for path in base_file_paths]
        df = pd.concat(all_dfs, ignore_index=True)
        print("Planilhas combinadas com sucesso.")
        
        for mes, ano in iterar_meses(periodo['inicio'], periodo['fim']):
            keep_alive(session)
            print(f"\n--- Processando Mês/Ano: {mes}/{ano} ---")
            
            balde_zct1, balde_zct2, balde_zdp1 = [], [], []

            for matricula in matriculas:
                # Procura as linhas da matrícula para o mês/ano específico
                linhas_matricula = df[
                    (df['Matrícula'] == int(matricula)) &
                    (df['Mês'] == int(mes)) &
                    (df['Ano'] == int(ano))
                ]
                
                if linhas_matricula.empty:
                    balde_zdp1.append(matricula)
                    continue

                # Aplica a regra de prioridade
                if "dedução parcial" in linhas_matricula['Class. desc. emprst.'].str.lower().values:
                    balde_zct1.append(matricula)
                elif "dedução não aplicada" in linhas_matricula['Class. desc. emprst.'].str.lower().values:
                    balde_zct2.append(matricula)
                else:
                    balde_zdp1.append(matricula)

            # Executa os trabalhadores com os baldes de matrículas
            run_zct1(session, balde_zct1, periodo, mes, ano, output_base_path, progress_queue)
            run_zct2(session, balde_zct2, periodo, mes, ano, output_base_path, progress_queue)
            run_zdp1_worker(session, balde_zdp1, periodo, {}, output_base_path, progress_queue)

        return True, "Orquestrador ZDP1/ZCT finalizado com sucesso."
    except Exception as e:
        return False, f"Erro no orquestrador ZDP1/ZCT: {e}"

# Adicione a função iterar_meses neste arquivo também
def iterar_meses(data_inicio_str, data_fim_str):
    # ... (código da função)
    pass