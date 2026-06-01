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

def inserir_matriculas_com_limpeza(session, matriculas):
    """Versão da função que limpa a seleção anterior."""
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
        print(f"Erro ao inserir matrículas com limpeza: {e}")
        try: session.findById("wnd[1]/tbar[0]/btn[12]").press()
        except: pass
        return False

def execute(session, matriculas, periodo, config, output_base_path, progress_queue=None):
    """Executa a 1ª Parcela do 13º Salário para os anos de 2021 a 2025."""
    try:
        print("--- Iniciando processo '13º Salário - 1ª Parcela' ---")
        bondt_lookup = {
            ('2021', '11'): '12.11.2021', ('2022', '11'): '14.11.2022', ('2023', '11'): '14.11.2023', ('2024', '11'): '14.11.2024',
            ('2025', '11'): '14.11.2025', ('2026', '11'): '13.11.2026', ('2027', '11'): '15.11.2027', ('2028', '11'): '14.11.2028'
        }
        
        session.startTransaction("PC00_M37_CEDT"); time.sleep(1)
        session.findById("wnd[0]/tbar[1]/btn[17]").press(); time.sleep(1)
        session.findById("wnd[1]/usr/txtENAME-LOW").text = ""
        session.findById("wnd[1]/tbar[0]/btn[8]").press(); time.sleep(1)
        shell = session.findById("wnd[1]/usr/cntlALV_CONTAINER_1/shellcont/shell")
        shell.setCurrentCell(0, "TEXT"); shell.selectedRows = "0"
        session.findById("wnd[1]/tbar[0]/btn[2]").press(); time.sleep(1)

        anos_a_processar = list(range(2021, 2026))
        if progress_queue:
            progress_queue.put({"type": "task_list", "tasks": [f"13º (1ª) - {ano}" for ano in anos_a_processar]})

        if not inserir_matriculas_com_limpeza(session, matriculas):
            return False, "Falha ao inserir matrículas."
        time.sleep(1)
        
        for i, ano_atual in enumerate(anos_a_processar):
            task_id = f"13º (1ª) - {ano_atual}"
            if progress_queue and hasattr(progress_queue, "should_skip") and progress_queue.should_skip(task_id):
                progress_queue.put({"type": "task_update", "task_id": task_id, "status": "✅ Concluído (checkpoint)"})
                continue
            if progress_queue:
                progress_queue.put({"type": "status", "detalhe": f"Processando {len(matriculas)} matrículas para {task_id}"})
                progress_queue.put({"type": "task_update", "task_id": task_id, "status": "Executando..."})

            data_bondt = bondt_lookup.get((str(ano_atual), '11'))
            if data_bondt is None:
                if ano_atual == 2021: data_bondt = "12.11.2021"
                else: data_bondt = f"14.11.{ano_atual}"
            
            session.findById("wnd[0]/usr/txtPNPPABRP").text = "11"
            session.findById("wnd[0]/usr/txtPNPPABRJ").text = str(ano_atual)
            session.findById("wnd[0]/usr/ctxtBONDT").text = data_bondt
            caminho_de_saida = get_save_path(output_base_path, "HP13_1", ano=ano_atual)
            session.findById("wnd[0]/usr/ctxtP_DIR").text = caminho_de_saida
            session.findById("wnd[0]/usr/chkP_BRANCH").selected = True
            session.findById("wnd[0]/usr/chkP_PDF").selected = True
            start_sapgui_security_watcher(timeout=10)
            session.findById("wnd[0]/tbar[1]/btn[8]").press()
            while session.Busy: time.sleep(1)
            session.findById("wnd[0]/tbar[0]/btn[3]").press(); time.sleep(1)
            
            if progress_queue:
                progress_queue.put({"type": "task_update", "task_id": task_id, "status": "✅ Concluído"})
            
        return True, "1ª Parcela do 13º Salário concluída com sucesso."
    except Exception as e:
        if progress_queue and 'task_id' in locals():
            progress_queue.put({"type": "task_update", "task_id": task_id, "status": "❌ Erro"})
        return False, f"Erro no processo 13º Salário - 1ª Parcela: {e}"
