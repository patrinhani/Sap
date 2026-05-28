# automations/zct2_worker.py
import time
from .path_utils import get_save_path
from .sap_utils import keep_alive, start_sapgui_security_watcher

def execute(session, matriculas, mes, ano, output_base_path, progress_queue=None):
    if not matriculas: return True, "Nenhuma matrícula para ZCT2."
    task_id = f"ZCT2 - {mes}/{ano}"
    try:
        print(f"--- Iniciando processo '{task_id}' para {len(matriculas)} matrículas ---")
        if progress_queue:
            progress_queue.put({"type": "task_list", "tasks": [task_id]})
            progress_queue.put({"type": "status", "detalhe": f"Processando {len(matriculas)} matrículas para {task_id}"})
            progress_queue.put({"type": "task_update", "task_id": task_id, "status": "Executando..."})

        session.findById("wnd[0]/usr/cntlIMAGE_CONTAINER/shellcont/shell/shellcont[0]/shell").doubleClickNode("0000000015")
        time.sleep(1)
        session.findById("wnd[0]/tbar[1]/btn[17]").press(); time.sleep(1)
        session.findById("wnd[1]/usr/txtENAME-LOW").text = ""
        session.findById("wnd[1]/tbar[0]/btn[8]").press(); time.sleep(1)
        
        shell = session.findById("wnd[1]/usr/cntlALV_CONTAINER_1/shellcont/shell")
        shell.setCurrentCell(20, "TEXT"); shell.selectedRows = "20"
        shell.doubleClickCurrentCell(); time.sleep(1)
        
        session.findById("wnd[0]/usr/radPNPTIMRA").select()
        session.findById("wnd[0]/usr/chkP_PDF").selected = True
        session.findById("wnd[0]/usr/txtPNPPABRP").text = mes
        session.findById("wnd[0]/usr/txtPNPPABRJ").text = ano
        
        caminho_de_saida = get_save_path(output_base_path, "ZDP1", ano=ano, mes=mes)
        session.findById("wnd[0]/usr/ctxtP_DIR").text = caminho_de_saida
        
        from .hp import inserir_matriculas
        if not inserir_matriculas(session, matriculas):
            raise RuntimeError("Falha ao inserir matrículas no processo ZCT2.")
        
        keep_alive(session)
        start_sapgui_security_watcher(timeout=10)
        session.findById("wnd[0]/tbar[1]/btn[8]").press(); time.sleep(2)
        session.findById("wnd[0]/tbar[0]/btn[15]").press(); time.sleep(1)

        if progress_queue:
            progress_queue.put({"type": "task_update", "task_id": task_id, "status": "✅ Concluído"})

        return True, "ZCT2 processado com sucesso."
    except Exception as e:
        if progress_queue: progress_queue.put({"type": "task_update", "task_id": task_id, "status": "❌ Erro"})
        return False, f"Erro no processo ZCT2: {e}"
