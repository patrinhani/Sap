import pandas as pd
import os
import re
from .zdp1_worker import execute as run_zdp1_worker
from .zct1_worker import execute as run_zct1_worker
from .zct2_worker import execute as run_zct2_worker
from .sap_utils import keep_alive

def execute(session, matriculas, periodo, config, output_base_path, progress_queue=None):
    try:
        print("--- Iniciando Orquestrador Inteligente ZDP1/ZCT ---")
        base_file_paths = config.get("base_file_paths", [])
        
        if not base_file_paths:
            print("AVISO: Nenhuma planilha base selecionada. Executando ZDP1 padrão para todas as matrículas.")
            return run_zdp1_worker(session, matriculas, periodo, config, output_base_path, progress_queue)

        for file_path in base_file_paths:
            filename = os.path.basename(file_path)
            print(f"\n--- Processando Arquivo Base: {filename} ---")
            
            # Extrai Mês e Ano do nome do arquivo
            match = re.search(r'(\d{1,2})\s(\d{4})', filename)
            if not match:
                print(f"AVISO: Não foi possível extrair Mês e Ano do nome do arquivo '{filename}'. Pulando.")
                continue
            
            mes, ano = match.groups()
            mes = f"{int(mes):02d}"
            print(f"Período extraído do nome do arquivo: {mes}/{ano}")

            df = pd.read_excel(file_path)
            
            balde_zct1, balde_zct2, balde_zdp1 = [], [], []
            matriculas_na_planilha = set(df['Matrícula'].unique())

            for matricula in matriculas:
                if int(matricula) not in matriculas_na_planilha:
                    balde_zdp1.append(matricula)
                    continue

                linhas_matricula = df[df['Matrícula'] == int(matricula)]
                
                status_list = linhas_matricula['Class. desc. emprst.'].str.lower().tolist()
                
                if "dedução parcial" in status_list:
                    balde_zct1.append(matricula)
                elif "dedução não aplicada" in status_list:
                    balde_zct2.append(matricula)
                else:
                    balde_zdp1.append(matricula)

            sucesso, mensagem = run_zct1_worker(session, balde_zct1, mes, ano, output_base_path, progress_queue)
            if not sucesso:
                return False, mensagem
            keep_alive(session)
            sucesso, mensagem = run_zct2_worker(session, balde_zct2, mes, ano, output_base_path, progress_queue)
            if not sucesso:
                return False, mensagem
            keep_alive(session)
            sucesso, mensagem = run_zdp1_worker(
                session,
                balde_zdp1,
                {"inicio": f"{mes}/{ano}", "fim": f"{mes}/{ano}"},
                config,
                output_base_path,
                progress_queue,
            )
            if not sucesso:
                return False, mensagem

        return True, "Orquestrador ZDP1/ZCT finalizado com sucesso."
    except Exception as e:
        return False, f"Erro no orquestrador ZDP1/ZCT: {e}"
