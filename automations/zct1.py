# automations/zct1.py
import time
from .path_utils import get_save_path
from .sap_utils import start_sapgui_security_watcher

def execute(session, matriculas, periodo, mes, ano, output_base_path, progress_queue):
    if not matriculas: return True, "Nenhuma matrícula para processar."
    try:
        task_id = f"ZCT1 - {mes}/{ano}"
        if progress_queue:
            if hasattr(progress_queue, "should_skip") and progress_queue.should_skip(task_id):
                progress_queue.put({"type": "task_update", "task_id": task_id, "status": "✅ Concluído (checkpoint)"})
                return True, f"{task_id} já concluído no checkpoint."
            progress_queue.put({"type": "status", "detalhe": f"Processando {len(matriculas)} matrículas para {task_id}"})
            progress_queue.put({"type": "task_update", "task_id": task_id, "status": "Executando..."})

        # Navega para a transação pelo menu
        session.findById("wnd[0]/usr/cntlIMAGE_CONTAINER/shellcont/shell/shellcont[0]/shell").doubleClickNode("0000000015")
        session.findById("wnd[0]/tbar[1]/btn[17]").press(); time.sleep(1)
        session.findById("wnd[1]/usr/txtENAME-LOW").text = ""
        session.findById("wnd[1]/tbar[0]/btn[8]").press(); time.sleep(1)
        
        # Seleciona a variante ZCT1 (linha 19)
        shell = session.findById("wnd[1]/usr/cntlALV_CONTAINER_1/shellcont/shell")
        shell.setCurrentCell(19, "TEXT"); shell.selectedRows = "19"
        shell.doubleClickCurrentCell(); time.sleep(1)
        
        # Preenche os dados (exemplo, você pode precisar ajustar)
        session.findById("wnd[0]/usr/radPNPTIMRA").select()
        session.findById("wnd[0]/usr/chkP_PDF").selected = True
        session.findById("wnd[0]/usr/txtPNPPABRP").text = mes
        session.findById("wnd[0]/usr/txtPNPPABRJ").text = ano
        # session.findById("wnd[0]/usr/ctxtPNPPERNR-LOW").text = "matricula" # ZCT1 parece ser individual
        
        caminho_de_saida = get_save_path(output_base_path, "ZDP1", ano=ano, mes=mes)
        session.findById("wnd[0]/usr/ctxtP_DIR").text = caminho_de_saida
        
        # ... (lógica para inserir a lista de matrículas) ...

        start_sapgui_security_watcher(timeout=10)
        session.findById("wnd[0]/tbar[1]/btn[8]").press(); time.sleep(2)
        session.findById("wnd[0]/tbar[0]/btn[3]").press(); time.sleep(1) # Volta

        if progress_queue:
            progress_queue.put({"type": "task_update", "task_id": task_id, "status": "✅ Concluído"})

        return True, "ZCT1 processado com sucesso."
    except Exception as e:
        if progress_queue and 'task_id' in locals():
            progress_queue.put({"type": "task_update", "task_id": task_id, "status": "❌ Erro"})
        return False, f"Erro no processo ZCT1: {e}"
