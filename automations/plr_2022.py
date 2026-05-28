import os
import sys
from datetime import datetime
import time
from .path_utils import get_save_path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
try:
    from automations.sap_utils import connect_to_sap, start_sapgui_security_watcher
except ImportError:
    try:
        from sap_utils import connect_to_sap, start_sapgui_security_watcher
    except ImportError:
        def connect_to_sap(): return None

def inserir_matriculas(session, matriculas):
    """Insere as matrículas uma a uma, limpando a seleção anterior."""
    try:
        session.findById("wnd[0]/usr/btn%_PNPPERNR_%_APP_%-VALU_PUSH").press(); time.sleep(1)
        session.findById("wnd[1]/tbar[0]/btn[16]").press(); time.sleep(1)
        session.findById("wnd[0]/usr/btn%_PNPPERNR_%_APP_%-VALU_PUSH").press(); time.sleep(1)
        for i, matricula in enumerate(matriculas):
            session.findById("wnd[1]/usr/tabsTAB_STRIP/tabpSIVA/ssubSCREEN_HEADER:SAPLALDB:3010/tblSAPLALDBSINGLE/ctxtRSCSEL_255-SLOW_I[1,1]").text = matricula
            session.findById("wnd[1]/usr/tabsTAB_STRIP/tabpSIVA/ssubSCREEN_HEADER:SAPLALDB:3010/tblSAPLALDBSINGLE").verticalScrollbar.position = i + 1
        session.findById("wnd[1]/tbar[0]/btn[8]").press()
        return True
    except Exception as e:
        print(f"Erro ao inserir matrículas: {e}")
        try: session.findById("wnd[1]/tbar[0]/btn[12]").press()
        except: pass
        return False

def execute(session, matriculas, periodo, config, output_base_path, progress_queue=None):
    """Executa o processo de PLR 2022."""
    task_id = "PLR 2022"
    try:
        print(f"--- Iniciando processo '{task_id}' ---")
        if progress_queue:
            progress_queue.put({"type": "task_list", "tasks": [task_id]})
            progress_queue.put({"type": "status", "detalhe": f"Processando {len(matriculas)} matrículas para {task_id}"})
            progress_queue.put({"type": "task_update", "task_id": task_id, "status": "Executando..."})

        MES = "04"
        ANO = "2022"
        DATA_BONDT = "08.04.2022"
        
        session.startTransaction("PC00_M37_CEDT"); time.sleep(1)
        session.findById("wnd[0]/tbar[1]/btn[17]").press(); time.sleep(1)
        session.findById("wnd[1]/usr/txtENAME-LOW").text = ""
        session.findById("wnd[1]/tbar[0]/btn[8]").press(); time.sleep(1)
        shell = session.findById("wnd[1]/usr/cntlALV_CONTAINER_1/shellcont/shell")
        shell.setCurrentCell(9, "TEXT"); shell.selectedRows = "9"
        session.findById("wnd[1]/tbar[0]/btn[2]").press(); time.sleep(1)

        session.findById("wnd[0]/usr/txtPNPPABRP").text = MES
        session.findById("wnd[0]/usr/txtPNPPABRJ").text = ANO
        session.findById("wnd[0]/usr/ctxtBONDT").text = DATA_BONDT
        
        if not inserir_matriculas(session, matriculas):
            raise RuntimeError("Falha ao inserir matrículas no processo PLR 2022.")
        time.sleep(1)
        
        caminho_de_saida = get_save_path(output_base_path, "PLR_2022")
        session.findById("wnd[0]/usr/ctxtP_DIR").text = caminho_de_saida
        session.findById("wnd[0]/usr/chkP_BRANCH").selected = True
        session.findById("wnd[0]/usr/chkP_PDF").selected = True
        start_sapgui_security_watcher(timeout=10)
        session.findById("wnd[0]/tbar[1]/btn[8]").press()
        while session.Busy: time.sleep(1)
        session.findById("wnd[0]/tbar[0]/btn[3]").press(); time.sleep(1)
            
        if progress_queue:
            progress_queue.put({"type": "task_update", "task_id": task_id, "status": "✅ Concluído"})
        return True, "PLR 2022 concluído com sucesso."

    except Exception as e:
        if progress_queue:
            progress_queue.put({"type": "task_update", "task_id": task_id, "status": "❌ Erro"})
        print(f"ERRO no processo PLR 2022: {e}")
        return False, f"Erro no processo PLR 2022: {e}"
