import os
import sys
from datetime import datetime  # <-- ALTERAÇÃO 1: Adicionado o import
import time
from .path_utils import get_save_path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
try:
    from automations.sap_utils import connect_to_sap, keep_alive
except ImportError:
    try:
        from sap_utils import connect_to_sap, keep_alive
    except ImportError:
        def connect_to_sap(): return None
        def keep_alive(session): print("AVISO: Função keep_alive não encontrada.")

def execute(session, matriculas, periodo, config, output_base_path, progress_queue=None):
    """
    Gera o Holerite Individual (Off-Cycle), espelhando a lógica VBA 1-para-1,
    incluindo os filtros de motivo e data.
    """
    try:
        print("--- Iniciando execução de HP Individual (Lógica 1-para-1 com VBA) ---")
        
        caminho_de_saida = get_save_path(output_base_path, "HP_Individual")
        data_filtro_inicio = "01.07.2021"
        # <-- ALTERAÇÃO 2: A data final agora é a data atual
        data_filtro_fim = datetime.now().strftime("%d.%m.%Y")
        
        matriculas_validas = [m.strip() for m in matriculas if m.strip()]
        if progress_queue:
            progress_queue.put({"type": "task_list", "tasks": [f"HP Indiv. {m}" for m in matriculas_validas]})

        arquivos_salvos = 0
        erros = 0
        for i, matricula in enumerate(matriculas_validas):
            task_id = f"HP Indiv. {matricula}"
            
            if progress_queue:
                progress_queue.put({"type": "status", "detalhe": f"Processando Matrícula {i+1}/{len(matriculas_validas)}: {matricula}"})
                progress_queue.put({"type": "task_update", "task_id": task_id, "status": "Executando..."})

            sucesso_matricula = False
            try:
                session.StartTransaction("PUOC_37"); time.sleep(1)
                session.findById("wnd[0]/usr/ctxtDIALOG-EE_NUMBER").text = matricula
                session.findById("wnd[0]").sendVKey(0); time.sleep(3)
                
                grid = session.findById("wnd[0]/usr/tabsOC_WORKBENCH_U/tabpTAB1U/ssubTABNU:SAPLHRPAY99_OC:1121/cntlGRID_CONTAINER/shellcont/shell")
                
                # --- FILTRO DE MOTIVO (Espelhado do VBA) ---
                grid.setCurrentCell(-1, "OCRTX"); grid.selectColumn("OCRTX"); grid.contextMenu(); time.sleep(0.5)
                try: grid.selectContextMenuItem("&FILTER")
                except: grid.selectContextMenuItem("&FILTRAR") # Fallback para português
                time.sleep(1)
                session.findById("wnd[1]/usr/ssub%_SUBSCREEN_FREESEL:SAPLSSEL:1105/btn%_%%DYN001_%_APP_%-VALU_PUSH").press(); time.sleep(1)
                session.findById("wnd[2]/usr/tabsTAB_STRIP/tabpSIVA/ssubSCREEN_HEADER:SAPLALDB:3010/tblSAPLALDBSINGLE/ctxtRSCSEL_255-SLOW_I[1,0]").text = "Ajuste"
                session.findById("wnd[2]/usr/tabsTAB_STRIP/tabpSIVA/ssubSCREEN_HEADER:SAPLALDB:3010/tblSAPLALDBSINGLE/ctxtRSCSEL_255-SLOW_I[1,1]").text = "Férias"
                session.findById("wnd[2]/usr/tabsTAB_STRIP/tabpSIVA/ssubSCREEN_HEADER:SAPLALDB:3010/tblSAPLALDBSINGLE/ctxtRSCSEL_255-SLOW_I[1,2]").text = "Rescisão"
                session.findById("wnd[2]/tbar[0]/btn[8]").press(); time.sleep(0.5)
                session.findById("wnd[1]/tbar[0]/btn[0]").press(); time.sleep(1)
                
                # --- FILTRO DE DATA (Espelhado do VBA) ---
                grid.setCurrentCell(-1, "PAYDT"); grid.selectColumn("PAYDT"); grid.contextMenu(); time.sleep(0.5)
                try: grid.selectContextMenuItem("&FILTER")
                except: grid.selectContextMenuItem("&FILTRAR")
                time.sleep(1)
                session.findById("wnd[1]/usr/ssub%_SUBSCREEN_FREESEL:SAPLSSEL:1105/ctxt%%DYN001-LOW").text = data_filtro_inicio
                session.findById("wnd[1]/usr/ssub%_SUBSCREEN_FREESEL:SAPLSSEL:1105/ctxt%%DYN001-HIGH").text = data_filtro_fim
                session.findById("wnd[1]/tbar[0]/btn[0]").press(); time.sleep(2)

                if grid.RowCount == 0:
                    print(f"  -> Nenhum registro encontrado para a matrícula {matricula} após os filtros.")
                    session.findById("wnd[0]/tbar[0]/btn[3]").press(); time.sleep(1)
                    sucesso_matricula = True
                else:
                    print(f"  -> Encontrados {grid.RowCount} registros. Salvando comprovantes...")
                    for j in range(grid.RowCount):
                        motivo = grid.GetCellValue(j, "OCRTX").strip()
                        data_pagamento = grid.GetCellValue(j, "PAYDT").strip()
                        if not motivo or not data_pagamento: continue
                        
                        grid.selectedRows = str(j)
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
                        while os.path.exists(os.path.join(caminho_de_saida, nome_arquivo_final)):
                            nome_arquivo_final = f"{base_nome_arquivo} -{contador}.html"
                            contador += 1
                            
                        session.findById("wnd[0]/usr/tabsOC_WORKBENCH_U/tabpTAB1U/ssubTABNU:SAPLHRPAY99_OC:1121/btnBUTTON_FORM").press(); time.sleep(1)
                        session.findById("wnd[0]/mbar/menu[0]/menu[1]").Select(); time.sleep(1)
                        session.findById("wnd[1]/usr/subSUBSCREEN_STEPLOOP:SAPLSPO5:0150/sub:SAPLSPO5:0150/radSPOPLI-SELFLAG[3,0]").select()
                        session.findById("wnd[1]/tbar[0]/btn[0]").press(); time.sleep(1)
                        session.findById("wnd[1]/usr/ctxtDY_PATH").text = caminho_de_saida
                        session.findById("wnd[1]/usr/ctxtDY_FILENAME").text = nome_arquivo_final
                        session.findById("wnd[1]/tbar[0]/btn[0]").press()
                        print(f"    Arquivo salvo: {nome_arquivo_final}"); arquivos_salvos += 1; time.sleep(1)
                        session.findById("wnd[0]").sendVKey(3); time.sleep(1)
                    
                    session.findById("wnd[0]/tbar[0]/btn[3]").press(); time.sleep(1)
                    sucesso_matricula = True
            except Exception as e:
                print(f"  ERRO: Falha ao processar matrícula {matricula}. Detalhes: {e}")
                erros += 1
                try: 
                    session.findById("wnd[0]/tbar[0]/btn[3]").press(); time.sleep(1)
                except: pass

            if progress_queue:
                status_final = "✅ Concluído" if sucesso_matricula else "❌ Erro"
                progress_queue.put({"type": "task_update", "task_id": task_id, "status": status_final})

        mensagem_final = f"Processo Concluído! {arquivos_salvos} comprovante(s) salvo(s), {erros} matrícula(s) com erro."
        return True, mensagem_final

    except Exception as e:
        if progress_queue and 'task_id' in locals():
            progress_queue.put({"type": "task_update", "task_id": task_id, "status": "❌ Erro"})
        return False, f"Erro crítico no script: {e}"