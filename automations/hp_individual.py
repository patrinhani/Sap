import time
import os
from datetime import datetime

def execute(session, matriculas, periodo, options, base_path):
    print("--- Iniciando execução de HP Individual (Off-Cycle) ---")
    
    hoje = datetime.now().strftime("%d.%m")
    pasta_data = os.path.join(base_path, hoje)
    caminho_vba = pasta_data
    if not os.path.exists(caminho_vba):
        os.makedirs(caminho_vba)

    data_filtro_inicio = "01.07.2021"
    data_filtro_fim = "28.05.2025"
    print(f"Usando filtro de data FIXO: de {data_filtro_inicio} a {data_filtro_fim}")

    arquivos_salvos = 0
    try:
        for matricula in matriculas:
            matricula = matricula.strip()
            if not matricula: continue
            print(f"Processando Matrícula: {matricula}")

            session.StartTransaction("PUOC_37")
            time.sleep(1)

            session.findById("wnd[0]/usr/ctxtDIALOG-EE_NUMBER").text = matricula
            session.findById("wnd[0]").sendVKey(0)
            print("  Aguardando grade de dados carregar...")
            time.sleep(3) # Aumentei ligeiramente a espera por segurança

            try:
                grid = session.findById("wnd[0]/usr/tabsOC_WORKBENCH_U/tabpTAB1U/ssubTABNU:SAPLHRPAY99_OC:1121/cntlGRID_CONTAINER/shellcont/shell")
            except Exception:
                print(f"  ERRO: Grade de dados não encontrada para a matrícula {matricula}. Pulando...")
                continue

            # --- BLOCO DE FILTRO DE MOTIVO (MAIS ROBUSTO) ---
            print("  Aplicando filtro de motivo...")
            grid.setCurrentCell(-1, "OCRTX") # Passo 1: Focar na coluna (como no VBA)
            time.sleep(0.5)
            grid.selectColumn("OCRTX")      # Passo 2: Selecionar a coluna
            grid.contextMenu()              # Passo 3: Abrir menu de contexto
            time.sleep(0.5)
            
            try: # Tenta filtrar em português
                grid.selectContextMenuItem("&FILTRAR")
            except: # Se falhar, tenta em inglês
                print("  Aviso: Falha ao usar '&FILTRAR'. Tentando comando em inglês '&FILTER'.")
                grid.selectContextMenuItem("&FILTER")
            
            time.sleep(1)
            
            session.findById("wnd[1]/usr/ssub%_SUBSCREEN_FREESEL:SAPLSSEL:1105/btn%_%%DYN001_%_APP_%-VALU_PUSH").press(); time.sleep(1)
            session.findById("wnd[2]/usr/tabsTAB_STRIP/tabpSIVA/ssubSCREEN_HEADER:SAPLALDB:3010/tblSAPLALDBSINGLE/ctxtRSCSEL_255-SLOW_I[1,0]").text = "Ajuste"
            session.findById("wnd[2]/usr/tabsTAB_STRIP/tabpSIVA/ssubSCREEN_HEADER:SAPLALDB:3010/tblSAPLALDBSINGLE/ctxtRSCSEL_255-SLOW_I[1,1]").text = "Férias"
            session.findById("wnd[2]/usr/tabsTAB_STRIP/tabpSIVA/ssubSCREEN_HEADER:SAPLALDB:3010/tblSAPLALDBSINGLE/ctxtRSCSEL_255-SLOW_I[1,2]").text = "Rescisão"
            session.findById("wnd[2]/tbar[0]/btn[8]").press(); time.sleep(0.5)
            session.findById("wnd[1]/tbar[0]/btn[0]").press(); time.sleep(1)

            # --- BLOCO DE FILTRO DE DATA (MAIS ROBUSTO) ---
            print("  Aplicando filtro de data...")
            grid.setCurrentCell(-1, "PAYDT") # Passo 1: Focar na coluna de data
            time.sleep(0.5)
            grid.selectColumn("PAYDT")      # Passo 2: Selecionar a coluna
            grid.contextMenu()              # Passo 3: Abrir menu de contexto
            time.sleep(0.5)
            
            try: # Tenta filtrar em português
                grid.selectContextMenuItem("&FILTRAR")
            except: # Se falhar, tenta em inglês
                print("  Aviso: Falha ao usar '&FILTRAR'. Tentando comando em inglês '&FILTER'.")
                grid.selectContextMenuItem("&FILTER")
                
            time.sleep(1)
            
            session.findById("wnd[1]/usr/ssub%_SUBSCREEN_FREESEL:SAPLSSEL:1105/ctxt%%DYN001-LOW").text = data_filtro_inicio
            session.findById("wnd[1]/usr/ssub%_SUBSCREEN_FREESEL:SAPLSSEL:1105/ctxt%%DYN001-HIGH").text = data_filtro_fim
            session.findById("wnd[1]/tbar[0]/btn[0]").press()
            
            print("  Aguardando grade filtrar...")
            time.sleep(2)

            if grid.RowCount == 0:
                print("  Nenhum registro encontrado após os filtros.")
                session.findById("wnd[0]/tbar[0]/btn[3]").press() 
                time.sleep(1)
                continue

            # --- O restante do código para salvar os arquivos (sem alterações) ---
            print(f"  Encontrados {grid.RowCount} registros. Salvando comprovantes...")
            for i in range(grid.RowCount):
                motivo = grid.GetCellValue(i, "OCRTX").strip()
                data_pagamento = grid.GetCellValue(i, "PAYDT").strip()
                if not motivo or not data_pagamento: continue
                grid.selectedRows = str(i)
                motivo_lower = motivo.lower()
                if "férias" in motivo_lower: motivo_codigo = "hpf"
                elif "rescisão" in motivo_lower: motivo_codigo = "hpr"
                elif "ajuste" in motivo_lower: motivo_codigo = "hp ajuste"
                else: motivo_codigo = motivo.replace("/", "-")
                try: ano_str = data_pagamento.split('.')[-1][-2:]
                except: ano_str = "XX"
                base_nome_arquivo = f"{matricula} - {motivo_codigo} {ano_str}"
                nome_arquivo_final = f"{base_nome_arquivo}.html"
                contador = 1
                while os.path.exists(os.path.join(caminho_vba, nome_arquivo_final)):
                    nome_arquivo_final = f"{base_nome_arquivo} -{contador}.html"
                    contador += 1
                session.findById("wnd[0]/usr/tabsOC_WORKBENCH_U/tabpTAB1U/ssubTABNU:SAPLHRPAY99_OC:1121/btnBUTTON_FORM").press(); time.sleep(1)
                session.findById("wnd[0]/mbar/menu[0]/menu[1]").select(); time.sleep(1)
                session.findById("wnd[1]/usr/subSUBSCREEN_STEPLOOP:SAPLSPO5:0150/sub:SAPLSPO5:0150/radSPOPLI-SELFLAG[3,0]").select()
                session.findById("wnd[1]/tbar[0]/btn[0]").press(); time.sleep(1)
                session.findById("wnd[1]/usr/ctxtDY_PATH").text = caminho_vba
                session.findById("wnd[1]/usr/ctxtDY_FILENAME").text = nome_arquivo_final
                session.findById("wnd[1]/tbar[0]/btn[0]").press()
                print(f"    Arquivo salvo: {nome_arquivo_final}"); arquivos_salvos += 1; time.sleep(1)
                session.findById("wnd[0]").sendVKey(3)
                time.sleep(1)

        return True, f"Processo Concluído! {arquivos_salvos} comprovante(s) salvo(s)."
    except Exception as e:
        print(f"ERRO CRÍTICO no processo de HP Individual: {e}")
        return False, f"Erro crítico no script: {e}"