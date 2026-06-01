import os
import sys
from datetime import datetime
import time
from .path_utils import get_save_path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
try:
    from automations.sap_utils import connect_to_sap, keep_alive, start_sapgui_security_watcher
except ImportError:
    try:
        from sap_utils import connect_to_sap, keep_alive, start_sapgui_security_watcher
    except ImportError:
        def connect_to_sap(): return None
        def keep_alive(session): print("AVISO: Função keep_alive não encontrada.")

def inserir_matriculas(session, matriculas):
    """Insere matrículas replicando a lógica de dupla interação do VBA."""
    try:
        session.findById("wnd[0]/usr/btn%_PNPPERNR_%_APP_%-VALU_PUSH").press(); time.sleep(1)
        session.findById("wnd[1]/tbar[0]/btn[16]").press(); time.sleep(1)
        session.findById("wnd[0]/usr/btn%_PNPPERNR_%_APP_%-VALU_PUSH").press(); time.sleep(1)
        for i, matricula in enumerate(matriculas):
            session.findById("wnd[1]/usr/tabsTAB_STRIP/tabpSIVA/ssubSCREEN_HEADER:SAPLALDB:3010/tblSAPLALDBSINGLE/ctxtRSCSEL_255-SLOW_I[1,1]").text = matricula.strip()
            session.findById("wnd[1]/usr/tabsTAB_STRIP/tabpSIVA/ssubSCREEN_HEADER:SAPLALDB:3010/tblSAPLALDBSINGLE").verticalScrollbar.position = i + 1
        session.findById("wnd[1]/tbar[0]/btn[8]").press()
        return True
    except Exception as e:
        print(f"Erro ao inserir matrículas: {e}")
        try: session.findById("wnd[1]/tbar[0]/btn[12]").press()
        except: pass
        return False

def execute(session, matriculas, periodo, mes, ano, output_base_path, progress_queue=None):
    """Executa a variante ZCT2 para um lote de matrículas e um mês/ano específico."""
    
    # Se o orquestrador não enviou nenhuma matrícula para este "balde", não faz nada.
    if not matriculas:
        return True, "Nenhuma matrícula para processar com ZCT2 neste período."
        
    task_id = f"ZCT2 - {mes}/{ano}"
    try:
        print(f"--- Iniciando processo '{task_id}' ---")
        if progress_queue:
            progress_queue.put({"type": "task_list", "tasks": [task_id]})
            if hasattr(progress_queue, "should_skip") and progress_queue.should_skip(task_id):
                progress_queue.put({"type": "task_update", "task_id": task_id, "status": "✅ Concluído (checkpoint)"})
                return True, f"{task_id} já concluído no checkpoint."
            progress_queue.put({"type": "status", "detalhe": f"Processando {len(matriculas)} matrículas para {task_id}"})
            progress_queue.put({"type": "task_update", "task_id": task_id, "status": "Executando..."})

        # A lógica de navegação e seleção da variante ZCT2 (linha 20)
        session.findById("wnd[0]/usr/cntlIMAGE_CONTAINER/shellcont/shell/shellcont[0]/shell").doubleClickNode("0000000015")
        time.sleep(1)
        session.findById("wnd[0]/tbar[1]/btn[17]").press(); time.sleep(1)
        session.findById("wnd[1]/usr/txtENAME-LOW").text = ""
        session.findById("wnd[1]/tbar[0]/btn[8]").press(); time.sleep(1)
        
        shell = session.findById("wnd[1]/usr/cntlALV_CONTAINER_1/shellcont/shell")
        shell.setCurrentCell(20, "TEXT"); shell.selectedRows = "20"
        shell.doubleClickCurrentCell(); time.sleep(1)
        
        # Preenche os dados na tela principal
        session.findById("wnd[0]/usr/radPNPTIMRA").select()
        session.findById("wnd[0]/usr/chkP_PDF").selected = True
        session.findById("wnd[0]/usr/txtPNPPABRP").text = mes
        session.findById("wnd[0]/usr/txtPNPPABRJ").text = ano
        
        caminho_de_saida = get_save_path(output_base_path, "ZDP1", ano=ano, mes=mes) # Salva na mesma estrutura do ZDP1
        session.findById("wnd[0]/usr/ctxtP_DIR").text = caminho_de_saida
        
        if not inserir_matriculas(session, matriculas):
            raise RuntimeError("Falha ao inserir matrículas no processo ZCT2.")
        time.sleep(1)

        keep_alive(session)
        start_sapgui_security_watcher(timeout=10)
        session.findById("wnd[0]/tbar[1]/btn[8]").press(); time.sleep(2)
        
        # Volta para a tela de menu principal para se preparar para o próximo processo do orquestrador
        session.findById("wnd[0]/tbar[0]/btn[15]").press(); time.sleep(1) 

        if progress_queue:
            progress_queue.put({"type": "task_update", "task_id": task_id, "status": "✅ Concluído"})

        return True, "ZCT2 processado com sucesso."
    except Exception as e:
        if progress_queue:
            progress_queue.put({"type": "task_update", "task_id": task_id, "status": "❌ Erro"})
        print(f"ERRO no processo ZCT2: {e}")
        return False, f"Erro no processo ZCT2: {e}"
