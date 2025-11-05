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
    """
    Tenta ler a mensagem de erro da barra de status do SAP.
    Se falhar, retorna a mensagem da exceção do Python.
    """
    try:
        # A barra de status (sbar) no 'pane' 0 geralmente contém mensagens de erro/sucesso
        message = session.findById("wnd[0]/sbar/pane[0]").text
        if message:
            return message.strip() # Remove espaços em branco extras
    except:
        pass # Ignora se a barra de status não puder ser lida
    
    # Se não houver mensagem na barra de status, retorna o erro do Python
    return str(fallback_exception)

def execute(session, matriculas, periodo, config, output_base_path, progress_queue=None):
    """Gera a Ficha Financeira, reportando o progresso por matrícula e ano com logs de erro detalhados."""
    try:
        print("--- Iniciando execução da Ficha Financeira ---")
        empresas_para_testar = ["0021", "0029", "0004", "0049"]
        
        try:
            ano_inicio = int(periodo['inicio'].split('/')[1])
            ano_fim = int(periodo['fim'].split('/')[1])
        except (ValueError, IndexError) as e:
            # Erro antes mesmo de começar
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
        task_id = None # Garante que task_id exista no escopo

        for i, task_id in enumerate(tarefas):
            current_time = time.time()
            if current_time - last_ping_time > KEEP_ALIVE_INTERVAL:
                keep_alive(session)
                last_ping_time = current_time

            matricula, ano_str = task_id.replace("FF ", "").split(" - ")
            ano = int(ano_str)
            
            if progress_queue:
                progress_queue.put({"type": "status", "detalhe": f"Processando Tarefa {i+1}/{len(tarefas)}: {task_id}"})
                progress_queue.put({"type": "task_update", "task_id": task_id, "status": "Executando..."})
            
            caminho_de_saida = get_save_path(output_base_path, "FichaFinanceira")
            encontrou_empresa_valida = False
            
            # Armazena erros específicos de cada empresa
            erros_empresas = []

            try:
                # --- A transação é aberta UMA VEZ por tarefa ---
                session.StartTransaction("ZHCMTR0084"); time.sleep(1)
                session.findById("wnd[0]/tbar[1]/btn[17]").press(); time.sleep(0.5)
                session.findById("wnd[1]/usr/cntlALV_CONTAINER_1/shellcont/shell").selectedRows = "0"
                session.findById("wnd[1]/usr/cntlALV_CONTAINER_1/shellcont/shell").doubleClickCurrentCell()
                time.sleep(0.5)
                
                # Preenche os campos comuns UMA VEZ
                session.findById("wnd[0]/usr/ctxtPNPBEGDA").text = f"01.01.{ano}"
                session.findById("wnd[0]/usr/ctxtPNPENDDA").text = f"31.12.{ano}"
                session.findById("wnd[0]/usr/txtP_PAGA").text = str(ano) 
                session.findById("wnd[0]/usr/ctxtPNPPERNR-LOW").text = matricula

                # --- Loop de empresas ---
                for empresa in empresas_para_testar:
                    if encontrou_empresa_valida: break
                    
                    print(f"--- Tentando Tarefa {task_id} na Empresa {empresa} ---")
                    
                    try:
                        # 1. Define a empresa e executa
                        session.findById("wnd[0]/usr/ctxtPNPBUKRS-LOW").text = empresa
                        session.findById("wnd[0]/tbar[1]/btn[8]").press(); time.sleep(2)
                        
                        # 2. Tenta salvar (se falhar, cai no 'except')
                        session.findById("wnd[0]/tbar[1]/btn[45]").press(); time.sleep(0.5) 
                        
                        print(f"--- Sucesso! Gerando arquivo para Empresa {empresa} ---")
                        
                        session.findById("wnd[1]/usr/subSUBSCREEN_STEPLOOP:SAPLSPO5:0150/sub:SAPLSPO5:0150/radSPOPLI-SELFLAG[3,0]").select()
                        session.findById("wnd[1]/tbar[0]/btn[0]").press(); time.sleep(0.5)
                        
                        nome_arquivo = f"{matricula} - ff {str(ano)[-2:]}.htm" 
                        session.findById("wnd[1]/usr/ctxtDY_PATH").text = caminho_de_saida
                        session.findById("wnd[1]/usr/ctxtDY_FILENAME").text = nome_arquivo
                        session.findById("wnd[1]/tbar[0]/btn[0]").press()
                        
                        arquivos_gerados += 1
                        encontrou_empresa_valida = True
                    
                    except Exception as e_inner:
                        # Captura erro específico da empresa
                        sap_error = get_sap_error_message(session, e_inner)
                        erros_empresas.append(f"{empresa}: {sap_error}")
                        print(f"--- Falha na Empresa {empresa}. Erro: {sap_error} ---")
                        
                        # Lógica de recuperação (tentar voltar à tela de seleção)
                        try: session.findById("wnd[1]").close() # Fecha pop-up
                        except: pass 
                        
                        try:
                            session.findById("wnd[0]/tbar[1]/btn[45]") # Estamos na tela de relatório?
                            session.findById("wnd[0]").sendVKey(3) # Sim, então volte (F3)
                        except:
                            pass # Não, já estamos na tela de seleção (provável)
                        
                        time.sleep(0.5)

            except Exception as e_task_setup:
                # Erro grave na configuração da tarefa
                sap_error = get_sap_error_message(session, e_task_setup)
                print(f"Erro grave na tarefa {task_id}: {sap_error}")
                if progress_queue:
                    # Envia o erro específico para a interface
                    progress_queue.put({"type": "task_update", "task_id": task_id, "status": f"❌ Erro Grave: {sap_error}"})
                
                try: session.findById("wnd[0]").sendVKey(12) # Tenta cancelar para destravar
                except: pass
                continue # Pula para a próxima tarefa do loop principal

            # Reporta o status final detalhado
            if progress_queue:
                status_final = ""
                if encontrou_empresa_valida:
                    status_final = "✅ Concluído"
                else:
                    if erros_empresas:
                        # Concatena todos os erros das tentativas
                        detalhe_erro = ", ".join(erros_empresas)
                        status_final = f"❌ Não encontrado ({detalhe_erro})"
                    else:
                        status_final = "❌ Erro (Não encontrado)"
                
                progress_queue.put({"type": "task_update", "task_id": task_id, "status": status_final})

        mensagem_final = f"Processo concluído! {arquivos_gerados} arquivo(s) gerado(s)."
        return True, mensagem_final

    except Exception as e_main:
        # Erro crítico que quebrou a função inteira
        sap_error = get_sap_error_message(session, e_main)
        print(f"Erro Crítico em Ficha Financeira: {sap_error}")
        
        if progress_queue and task_id: 
            progress_queue.put({"type": "task_update", "task_id": task_id, "status": f"❌ Erro Crítico: {sap_error}"})
        
        return False, f"Erro Crítico em Ficha Financeira: {sap_error}"