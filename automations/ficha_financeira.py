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

def get_sap_error_message(session, fallback_exception):
    try:
        message = session.findById("wnd[0]/sbar/pane[0]").text
        if message: return message.strip()
    except: pass
    return str(fallback_exception)

def execute(session, matriculas, periodo, config, output_base_path, progress_queue=None):
    """
    Gera a Ficha Financeira.
    - PDF: Salva direto com nome padronizado (Matricula - ff YY.pdf).
    - HTML: Método legado com loop de empresas.
    """
    try:
        tipo_saida = config.get("tipo_saida", "HTML")
        print(f"--- Iniciando Ficha Financeira (Modo: {tipo_saida}) ---")
        
        try:
            ano_inicio = int(periodo['inicio'].split('/')[1])
            ano_fim = int(periodo['fim'].split('/')[1])
        except (ValueError, IndexError) as e:
            return False, f"Erro: Período inválido. Detalhe: {e}"

        tarefas = []
        matriculas_validas = [m.strip() for m in matriculas if m.strip()]
        for matricula in matriculas_validas:
            for ano in range(ano_inicio, ano_fim + 1):
                tarefas.append(f"FF {matricula} - {ano}")
        
        if progress_queue:
            progress_queue.put({"type": "task_list", "tasks": tarefas})
        
        KEEP_ALIVE_INTERVAL = 180
        last_ping_time = time.time()
        arquivos_gerados = 0
        task_id = None 

        for i, task_id in enumerate(tarefas):
            current_time = time.time()
            if current_time - last_ping_time > KEEP_ALIVE_INTERVAL:
                keep_alive(session)
                last_ping_time = current_time

            matricula, ano_str = task_id.replace("FF ", "").split(" - ")
            ano = int(ano_str)
            ano_curto = str(ano)[-2:] # Pega os dois últimos dígitos (ex: 2024 -> 24)
            
            if progress_queue:
                progress_queue.put({"type": "status", "detalhe": f"Tarefa {i+1}/{len(tarefas)}: {task_id} ({tipo_saida})"})
                progress_queue.put({"type": "task_update", "task_id": task_id, "status": "Executando..."})
            
            caminho_de_saida = get_save_path(output_base_path, "FichaFinanceira")
            
            # =========================================================================
            # LÓGICA PARA PDF (Exportação Direta com Renomeação)
            # =========================================================================
            if "PDF" in tipo_saida:
                try:
                    # Define o nome exato conforme padrão antigo: "12345678 - ff 24.pdf"
                    nome_arquivo_pdf = f"{matricula} - ff {ano_curto}.pdf"
                    caminho_completo_pdf = os.path.join(caminho_de_saida, nome_arquivo_pdf)

                    # 1. Inicia Transação
                    session.StartTransaction("ZHCMTR0084"); time.sleep(1)
                    
                    # 2. Carrega Variante (Se necessário/existir)
                    try:
                        session.findById("wnd[0]/tbar[1]/btn[17]").press(); time.sleep(1)
                        session.findById("wnd[1]/usr/cntlALV_CONTAINER_1/shellcont/shell").currentCellColumn = "TEXT"
                        session.findById("wnd[1]/usr/cntlALV_CONTAINER_1/shellcont/shell").selectedRows = "0"
                        session.findById("wnd[1]/usr/cntlALV_CONTAINER_1/shellcont/shell").doubleClickCurrentCell(); time.sleep(1)
                    except:
                        pass 

                    # 3. Preenche Dados Básicos
                    session.findById("wnd[0]/usr/ctxtPNPBEGDA").text = f"01.01.{ano}"
                    session.findById("wnd[0]/usr/ctxtPNPENDDA").text = f"31.12.{ano}"
                    session.findById("wnd[0]/usr/ctxtPNPPERNR-LOW").text = matricula
                    session.findById("wnd[0]/usr/txtP_PAGA").text = str(ano)

                    # 4. Configura Exportação PDF e insere o CAMINHO COMPLETO COM NOME
                    session.findById("wnd[0]/usr/radP_EXPORT").setFocus()
                    session.findById("wnd[0]/usr/radP_EXPORT").select()
                    session.findById("wnd[0]/usr/radP_PDF").select()
                    
                    # AQUI ESTÁ A MUDANÇA: Envia pasta + nome do arquivo
                    session.findById("wnd[0]/usr/ctxtP_FILE").text = caminho_completo_pdf
                    
                    session.findById("wnd[0]/usr/radP_PDF").setFocus()
                    
                    # 5. Executa (O SAP salva automaticamente com o nome fornecido)
                    session.findById("wnd[0]/tbar[1]/btn[8]").press()
                    
                    # Verifica erros
                    try:
                        msg = session.findById("wnd[0]/sbar/pane[0]").text
                        if "Nenhum dado" in msg or "No data" in msg:
                            raise RuntimeError(msg)
                    except: pass
                    
                    time.sleep(1)
                    arquivos_gerados += 1
                    
                    print(f"    Salvo (PDF): {nome_arquivo_pdf}")
                    if progress_queue:
                        progress_queue.put({"type": "task_update", "task_id": task_id, "status": "✅ Concluído (PDF)"})

                except Exception as e_pdf:
                    sap_error = get_sap_error_message(session, e_pdf)
                    print(f"Erro PDF: {sap_error}")
                    if progress_queue:
                        progress_queue.put({"type": "task_update", "task_id": task_id, "status": f"❌ Erro: {sap_error}"})
                    try: session.findById("wnd[0]").sendVKey(3) 
                    except: pass

            # =========================================================================
            # LÓGICA PARA HTML (Legado)
            # =========================================================================
            else:
                empresas_para_testar = ["0021", "0029", "0004", "0049"]
                encontrou_empresa_valida = False
                erros_empresas = []

                try:
                    session.StartTransaction("ZHCMTR0084"); time.sleep(1)
                    try:
                        session.findById("wnd[0]/tbar[1]/btn[17]").press(); time.sleep(0.5)
                        session.findById("wnd[1]/usr/cntlALV_CONTAINER_1/shellcont/shell").selectedRows = "0"
                        session.findById("wnd[1]/usr/cntlALV_CONTAINER_1/shellcont/shell").doubleClickCurrentCell(); time.sleep(0.5)
                    except: pass

                    session.findById("wnd[0]/usr/ctxtPNPBEGDA").text = f"01.01.{ano}"
                    session.findById("wnd[0]/usr/ctxtPNPENDDA").text = f"31.12.{ano}"
                    session.findById("wnd[0]/usr/txtP_PAGA").text = str(ano) 
                    session.findById("wnd[0]/usr/ctxtPNPPERNR-LOW").text = matricula

                    for empresa in empresas_para_testar:
                        if encontrou_empresa_valida: break
                        try:
                            session.findById("wnd[0]/usr/ctxtPNPBUKRS-LOW").text = empresa
                            session.findById("wnd[0]/tbar[1]/btn[8]").press(); time.sleep(2)
                            
                            session.findById("wnd[0]/tbar[1]/btn[45]").press(); time.sleep(0.5) 
                            
                            session.findById("wnd[1]/usr/subSUBSCREEN_STEPLOOP:SAPLSPO5:0150/sub:SAPLSPO5:0150/radSPOPLI-SELFLAG[3,0]").select()
                            session.findById("wnd[1]/tbar[0]/btn[0]").press(); time.sleep(0.5)
                            
                            # Nome manual para HTML
                            nome_arquivo_html = f"{matricula} - ff {ano_curto}.htm"
                            session.findById("wnd[1]/usr/ctxtDY_PATH").text = caminho_de_saida
                            session.findById("wnd[1]/usr/ctxtDY_FILENAME").text = nome_arquivo_html
                            session.findById("wnd[1]/tbar[0]/btn[0]").press()
                            
                            arquivos_gerados += 1
                            encontrou_empresa_valida = True
                            print(f"    Salvo (HTML): {nome_arquivo_html}")
                        except Exception as e_inner:
                            sap_error = get_sap_error_message(session, e_inner)
                            erros_empresas.append(f"{empresa}: {sap_error}")
                            try: session.findById("wnd[1]").close() 
                            except: pass 
                            try:
                                session.findById("wnd[0]/tbar[1]/btn[45]")
                                session.findById("wnd[0]").sendVKey(3)
                            except: pass
                            time.sleep(0.5)
                    
                    status_final = "✅ Concluído" if encontrou_empresa_valida else f"❌ Falha ({', '.join(erros_empresas)})"
                    if progress_queue:
                        progress_queue.put({"type": "task_update", "task_id": task_id, "status": status_final})

                except Exception as e_html:
                    if progress_queue:
                        progress_queue.put({"type": "task_update", "task_id": task_id, "status": f"❌ Erro Setup HTML: {e_html}"})

        return True, f"Processo concluído! {arquivos_gerados} arquivos ({tipo_saida})."

    except Exception as e_main:
        return False, f"Erro Crítico em Ficha Financeira: {e_main}"