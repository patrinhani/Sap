import os
import sys
from datetime import datetime
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
    Gera Holerites Individuais (Off-Cycle) unificando Férias, Rescisão, Ajustes e PLR (PPR).
    Lógica espelhada do VBA: Transação PUOC_37 com filtros múltiplos.
    """
    try:
        print("--- Iniciando HP Individual Unificado (Lógica VBA: Férias/Rescisão/PPR) ---")
        
        # Cria pasta unificada. Se preferir separar, podemos ajustar a lógica de pastas depois.
        caminho_de_saida = get_save_path(output_base_path, "Documentos_OffCycle_Unificados")
        
        # Filtros de data fixos conforme VBA (ajustados para pegar até o dia atual)
        data_filtro_inicio = "01.07.2021"
        data_filtro_fim = datetime.now().strftime("%d.%m.%Y")
        
        matriculas_validas = [m.strip() for m in matriculas if m.strip()]
        if progress_queue:
            progress_queue.put({"type": "task_list", "tasks": [f"Processando {m}" for m in matriculas_validas]})

        arquivos_salvos = 0
        erros = 0

        for i, matricula in enumerate(matriculas_validas):
            task_id = f"Processando {matricula}"
            
            if progress_queue:
                progress_queue.put({"type": "status", "detalhe": f"Matrícula {i+1}/{len(matriculas_validas)}: {matricula}"})
                progress_queue.put({"type": "task_update", "task_id": task_id, "status": "Executando..."})

            sucesso_matricula = False
            try:
                # 1. Abre Transação
                session.StartTransaction("PUOC_37"); time.sleep(1)
                session.findById("wnd[0]/usr/ctxtDIALOG-EE_NUMBER").text = matricula
                session.findById("wnd[0]").sendVKey(0); time.sleep(2)
                
                # Referência ao Grid
                try:
                    grid = session.findById("wnd[0]/usr/tabsOC_WORKBENCH_U/tabpTAB1U/ssubTABNU:SAPLHRPAY99_OC:1121/cntlGRID_CONTAINER/shellcont/shell")
                except:
                    print(f"  -> Grid não carregou para {matricula}. Pulando.")
                    if progress_queue: progress_queue.put({"type": "task_update", "task_id": task_id, "status": "⚠️ Sem dados"})
                    continue

                # --- 2. FILTRO DE MOTIVO (Espelhado do VBA) ---
                # O VBA preenche 5 linhas de filtro (SLOW_I[1,0] até [1,4])
                grid.setCurrentCell(-1, "OCRTX"); grid.selectColumn("OCRTX"); grid.contextMenu(); time.sleep(0.5)
                try: grid.selectContextMenuItem("&FILTER")
                except: grid.selectContextMenuItem("&FILTRAR")
                time.sleep(1)
                
                # Preenchendo os critérios exatos do VBA
                base_path_filter = "wnd[1]/usr/ssub%_SUBSCREEN_FREESEL:SAPLSSEL:1105"
                # Botão de extensão de valores (setinha amarela/verde se necessário, ou direto na lista)
                # O VBA acessa wnd[2] direto após apertar o botão de valores múltiplos.
                # Vamos tentar replicar a abertura da janela de seleção múltipla:
                try:
                    session.findById(f"{base_path_filter}/btn%_%%DYN001_%_APP_%-VALU_PUSH").press(); time.sleep(1)
                    # Janela de seleção múltipla (wnd[2] ou wnd[1] dependendo do contexto, o VBA usa wnd[2])
                    sel_table = "wnd[2]/usr/tabsTAB_STRIP/tabpSIVA/ssubSCREEN_HEADER:SAPLALDB:3010/tblSAPLALDBSINGLE"
                    
                    session.findById(f"{sel_table}/ctxtRSCSEL_255-SLOW_I[1,0]").text = "Ajuste"
                    session.findById(f"{sel_table}/ctxtRSCSEL_255-SLOW_I[1,1]").text = "Férias"
                    # session.findById(f"{sel_table}/ctxtRSCSEL_255-SLOW_I[1,2]").text = "Adiantamento Diversos"
                    session.findById(f"{sel_table}/ctxtRSCSEL_255-SLOW_I[1,3]").text = "PPR Pagamento Final"
                    session.findById(f"{sel_table}/ctxtRSCSEL_255-SLOW_I[1,4]").text = "Adiantamento PPR"
                    # Adicionando Rescisão na linha 5 (indice 5) se houver espaço, ou sobrescrevendo caso o VBA tenha lógica diferente
                    # O VBA repete [1,2] para Rescisão no seu código, o que parece um erro de digitação no original, 
                    # mas vamos colocar na próxima livre [1,5] para garantir.
                    session.findById(f"{sel_table}/ctxtRSCSEL_255-SLOW_I[1,5]").text = "Rescisão"
                    
                    session.findById("wnd[2]/tbar[0]/btn[8]").press(); time.sleep(0.5) # Executar filtro
                except Exception as e_filtro:
                    print(f"Erro ao preencher filtro avançado: {e_filtro}. Tentando filtro simples.")
                
                session.findById("wnd[1]/tbar[0]/btn[0]").press(); time.sleep(1) # Confirma filtro
                
                # --- 3. FILTRO DE DATA (Espelhado do VBA) ---
                grid.setCurrentCell(-1, "PAYDT"); grid.selectColumn("PAYDT"); grid.contextMenu(); time.sleep(0.5)
                try: grid.selectContextMenuItem("&FILTER")
                except: grid.selectContextMenuItem("&FILTRAR")
                time.sleep(1)
                session.findById(f"{base_path_filter}/ctxt%%DYN001-LOW").text = data_filtro_inicio
                session.findById(f"{base_path_filter}/ctxt%%DYN001-HIGH").text = data_filtro_fim
                session.findById("wnd[1]/tbar[0]/btn[0]").press(); time.sleep(2)

                # --- 4. ITERAÇÃO E SALVAMENTO ---
                if grid.RowCount == 0:
                    print(f"  -> Nenhum registro encontrado para {matricula}.")
                    sucesso_matricula = True
                else:
                    print(f"  -> {grid.RowCount} registros encontrados.")
                    # Precisamos iterar com cuidado pois ao voltar do form, o grid pode resetar a seleção
                    # O método mais seguro em Python/SAP GUI Scripting é iterar e processar
                    
                    for j in range(grid.RowCount):
                        motivo = grid.GetCellValue(j, "OCRTX").strip()
                        data_pagamento = grid.GetCellValue(j, "PAYDT").strip()
                        if not motivo or not data_pagamento: continue
                        
                        grid.selectedRows = str(j)
                        
                        # TRADUÇÃO DOS NOMES (CASE do VBA)
                        motivo_lower = motivo.lower()
                        motivo_codigo = motivo # Default
                        
                        if "férias" in motivo_lower: motivo_codigo = "hpf"
                        elif "rescisão" in motivo_lower: motivo_codigo = "hpr"
                        elif "ajuste" in motivo_lower: motivo_codigo = "hp ajuste"
                        elif "ppr pagamento final" in motivo_lower: motivo_codigo = "PLR Pagamento Final" # Mapeamento VBA
                        elif "adiantamento ppr" in motivo_lower: motivo_codigo = "Adiantamento PLR"
                        # elif "adiantamento diversos" in motivo_lower: motivo_codigo = "Adiantamento"
                        else: motivo_codigo = motivo.replace("/", "-")
                        
                        # Extrai ano (VBA: Right(arrData(2), 2))
                        try: ano_str = data_pagamento.split('.')[-1][-2:]
                        except: ano_str = "XX"
                            
                        base_nome_arquivo = f"{matricula} - {motivo_codigo} {ano_str}"
                        nome_arquivo_final = f"{base_nome_arquivo}.html"
                        
                        # Evita sobrescrever
                        contador = 1
                        while os.path.exists(os.path.join(caminho_de_saida, nome_arquivo_final)):
                            nome_arquivo_final = f"{base_nome_arquivo} -{contador}.html"
                            contador += 1
                        
                        # Abre o formulário e salva
                        session.findById("wnd[0]/usr/tabsOC_WORKBENCH_U/tabpTAB1U/ssubTABNU:SAPLHRPAY99_OC:1121/btnBUTTON_FORM").press(); time.sleep(2)
                        
                        # Menu: Lista -> Exportar -> Arquivo Local (ou via menu de impressão)
                        # O VBA usa: wnd[0]/mbar/menu[0]/menu[1] (Imprimir/Visualizar -> Download?)
                        try:
                            session.findById("wnd[0]/mbar/menu[0]/menu[1]").Select(); time.sleep(1)
                            # Janela de opção de formato
                            session.findById("wnd[1]/usr/subSUBSCREEN_STEPLOOP:SAPLSPO5:0150/sub:SAPLSPO5:0150/radSPOPLI-SELFLAG[3,0]").select() # HTML
                            session.findById("wnd[1]/tbar[0]/btn[0]").press(); time.sleep(1)
                            
                            session.findById("wnd[1]/usr/ctxtDY_PATH").text = caminho_de_saida
                            session.findById("wnd[1]/usr/ctxtDY_FILENAME").text = nome_arquivo_final
                            session.findById("wnd[1]/tbar[0]/btn[0]").press() # Salvar
                            
                            print(f"    Salvo: {nome_arquivo_final}")
                            arquivos_salvos += 1
                            time.sleep(1)
                        except Exception as e_save:
                            print(f"    Erro ao salvar form: {e_save}")
                        
                        # Volta para o grid (F3 / Voltar)
                        session.findById("wnd[0]").sendVKey(3); time.sleep(1)
                    
                    sucesso_matricula = True

                # Limpa para a próxima matrícula (F3 para voltar à tela inicial da transação se necessário, ou apenas troca o ID)
                # O VBA não sai da transação, apenas troca o ID. Mas precisamos garantir que estamos na tela inicial
                # Se estivermos na tela do grid, F3 volta para a tela de seleção de matrícula
                session.findById("wnd[0]/tbar[0]/btn[3]").press(); time.sleep(1)

            except Exception as e:
                print(f"  ERRO na matrícula {matricula}: {e}")
                erros += 1
                # Tenta voltar ao início para não travar a próxima
                try: session.findById("wnd[0]/tbar[0]/btn[3]").press(); time.sleep(1)
                except: pass
                try: session.findById("wnd[0]/tbar[0]/btn[3]").press(); time.sleep(1)
                except: pass

            if progress_queue:
                status_final = "✅ Concluído" if sucesso_matricula else "❌ Erro"
                progress_queue.put({"type": "task_update", "task_id": task_id, "status": status_final})

        return True, f"Processo Unificado Concluído! {arquivos_salvos} docs salvos. {erros} erros."

    except Exception as e:
        return False, f"Erro crítico no script unificado: {e}"