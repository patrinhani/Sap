import os
import sys
from datetime import datetime
import time
from .path_utils import get_save_path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
try:
    from automations.sap_utils import connect_to_sap
except ImportError:
    try:
        from sap_utils import connect_to_sap
    except ImportError:
        def connect_to_sap(): return None

def inserir_matriculas(session, matriculas):
    """Função padrão para inserir matrículas."""
    try:
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
    """Executa a 2ª Parcela do 13º Salário para os anos de 2021 a 2024."""
    try:
        print("--- Iniciando processo '13º Salário - 2ª Parcela' ---")
        bondt_lookup = {
            ('2021', '12'): '15.12.2021', ('2022', '12'): '15.12.2022', ('2023', '12'): '15.12.2023', ('2024', '12'): '13.12.2024',
            ('2025', '12'): '15.12.2025', ('2026', '12'): '15.12.2026', ('2027', '12'): '15.12.2027', ('2028', '12'): '15.12.2028'
        }

        session.startTransaction("PC00_M37_CEDT"); time.sleep(1)
        session.findById("wnd[0]/tbar[1]/btn[17]").press(); time.sleep(1)
        session.findById("wnd[1]/usr/txtENAME-LOW").text = ""
        session.findById("wnd[1]/tbar[0]/btn[8]").press(); time.sleep(1)
        shell = session.findById("wnd[1]/usr/cntlALV_CONTAINER_1/shellcont/shell")
        shell.setCurrentCell(1, "TEXT"); shell.selectedRows = "1"
        session.findById("wnd[1]/tbar[0]/btn[2]").press(); time.sleep(1)

        anos_a_processar = list(range(2021, 2025))
        if progress_queue:
            progress_queue.put({"type": "task_list", "tasks": [f"13º (2ª) - {ano}" for ano in anos_a_processar]})

        if not inserir_matriculas(session, matriculas):
            return False, "Falha ao inserir matrículas."
        time.sleep(1)

        for i, ano_atual in enumerate(anos_a_processar):
            task_id = f"13º (2ª) - {ano_atual}"
            if progress_queue:
                progress_queue.put({"type": "status", "detalhe": f"Processando {len(matriculas)} matrículas para {task_id}"})
                progress_queue.put({"type": "task_update", "task_id": task_id, "status": "Executando..."})

            data_bondt = bondt_lookup.get((str(ano_atual), '12'), "")
            
            session.findById("wnd[0]/usr/txtPNPPABRP").text = "12"
            session.findById("wnd[0]/usr/txtPNPPABRJ").text = str(ano_atual)
            session.findById("wnd[0]/usr/ctxtBONDT").text = data_bondt
            caminho_de_saida = get_save_path(output_base_path, "HP13_2", ano=ano_atual)
            session.findById("wnd[0]/usr/ctxtP_DIR").text = caminho_de_saida
            session.findById("wnd[0]/usr/chkP_BRANCH").selected = True
            session.findById("wnd[0]/usr/chkP_PDF").selected = True
            session.findById("wnd[0]/tbar[1]/btn[8]").press()
            while session.Busy: time.sleep(1)
            session.findById("wnd[0]/tbar[0]/btn[3]").press(); time.sleep(1)

            if progress_queue:
                progress_queue.put({"type": "task_update", "task_id": task_id, "status": "✅ Concluído"})
            
        return True, "2ª Parcela do 13º Salário concluída com sucesso."
    except Exception as e:
        if progress_queue and 'task_id' in locals():
            progress_queue.put({"type": "task_update", "task_id": task_id, "status": "❌ Erro"})
        return False, f"Erro no processo 13º Salário - 2ª Parcela: {e}"