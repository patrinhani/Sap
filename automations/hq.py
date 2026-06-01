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

def iterar_meses(data_inicio_str, data_fim_str):
    try:
        mes_inicio, ano_inicio = map(int, data_inicio_str.split('/'))
        mes_fim, ano_fim = map(int, data_fim_str.split('/'))
    except (ValueError, TypeError): return
    ano_atual, mes_atual = ano_inicio, mes_inicio
    while (ano_atual < ano_fim) or (ano_atual == ano_fim and mes_atual <= mes_fim):
        yield f"{mes_atual:02d}", str(ano_atual)
        mes_atual += 1
        if mes_atual > 12: mes_atual = 1; ano_atual += 1

def inserir_matriculas(session, matriculas):
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
    try:
        print("--- Iniciando processo 'HQ (Holerite Quinzenal)' ---")
        bondt_lookup = {
    # --- 2021 ---
    ('2021', '06'): '15.06.2021',
    ('2021', '07'): '15.07.2021',
    ('2021', '08'): '13.08.2021',
    ('2021', '09'): '15.09.2021',
    ('2021', '10'): '15.10.2021',
    ('2021', '11'): '12.11.2021',
    ('2021', '12'): '15.12.2021',

    # --- 2022 ---
    ('2022', '01'): '14.01.2022',
    ('2022', '02'): '15.02.2022',
    ('2022', '03'): '15.03.2022',
    ('2022', '04'): '14.04.2022',
    ('2022', '05'): '13.05.2022',
    ('2022', '06'): '15.06.2022',
    ('2022', '07'): '15.07.2022',
    ('2022', '08'): '15.08.2022',
    ('2022', '09'): '15.09.2022',
    ('2022', '10'): '14.10.2022',
    ('2022', '11'): '14.11.2022',
    ('2022', '12'): '15.12.2022',

    # --- 2023 ---
    ('2023', '01'): '13.01.2023',
    ('2023', '02'): '15.02.2023',
    ('2023', '03'): '15.03.2023',
    ('2023', '04'): '14.04.2023',
    ('2023', '05'): '15.05.2023',
    ('2023', '06'): '15.06.2023',
    ('2023', '07'): '14.07.2023',
    ('2023', '08'): '15.08.2023',
    ('2023', '09'): '15.09.2023',
    ('2023', '10'): '13.10.2023',
    ('2023', '11'): '14.11.2023',
    ('2023', '12'): '15.12.2023',

    # --- 2024 ---
    ('2024', '01'): '15.01.2024',
    ('2024', '02'): '15.02.2024',
    ('2024', '03'): '15.03.2024',
    ('2024', '04'): '15.04.2024',
    ('2024', '05'): '15.05.2024',
    ('2024', '06'): '14.06.2024',
    ('2024', '07'): '15.07.2024',
    ('2024', '08'): '15.08.2024',
    ('2024', '09'): '13.09.2024',
    ('2024', '10'): '15.10.2024',
    ('2024', '11'): '14.11.2024',
    ('2024', '12'): '13.12.2024',

    # --- 2025 ---
    ('2025', '01'): '15.01.2025',
    ('2025', '02'): '14.02.2025',
    ('2025', '03'): '14.03.2025',
    ('2025', '04'): '15.04.2025',
    ('2025', '05'): '15.05.2025',
    ('2025', '06'): '13.06.2025',
    ('2025', '07'): '15.07.2025',
    ('2025', '08'): '15.08.2025',
    ('2025', '09'): '15.09.2025',
    ('2025', '10'): '15.10.2025',
    ('2025', '11'): '14.11.2025',
    ('2025', '12'): '15.12.2025',

    # --- 2026 ---
    ('2026', '01'): '15.01.2026',
    ('2026', '02'): '13.02.2026',
    ('2026', '03'): '13.03.2026',
    ('2026', '04'): '15.04.2026',
    ('2026', '05'): '15.05.2026',
    ('2026', '06'): '15.06.2026',
    ('2026', '07'): '15.07.2026',
    ('2026', '08'): '14.08.2026',
    ('2026', '09'): '15.09.2026',
    ('2026', '10'): '15.10.2026',
    ('2026', '11'): '13.11.2026',
    ('2026', '12'): '15.12.2026',

    # --- 2027 ---
 
    ('2027', '02'): '15.02.2027',
    ('2027', '03'): '15.03.2027',
    ('2027', '04'): '15.04.2027',
    ('2027', '05'): '14.05.2027',
    ('2027', '06'): '15.06.2027',
    ('2027', '07'): '15.07.2027',
    ('2027', '08'): '13.08.2027',
    ('2027', '09'): '15.09.2027',
    ('2027', '10'): '15.10.2027',
    ('2027', '11'): '12.11.2027',
    ('2027', '12'): '15.12.2027',

 
}
        
        session.startTransaction("PC00_M37_CEDT"); time.sleep(1)
        session.findById("wnd[0]/tbar[1]/btn[17]").press(); time.sleep(1)
        session.findById("wnd[1]/usr/txtENAME-LOW").text = ""
        session.findById("wnd[1]/tbar[0]/btn[8]").press(); time.sleep(1)
        shell = session.findById("wnd[1]/usr/cntlALV_CONTAINER_1/shellcont/shell")
        shell.setCurrentCell(2, "TEXT"); shell.selectedRows = "2"
        session.findById("wnd[1]/tbar[0]/btn[2]").press(); time.sleep(1)

        meses_a_processar = [m for m in iterar_meses(periodo['inicio'], periodo['fim']) if (m[1], m[0]) in bondt_lookup]
        if progress_queue:
            progress_queue.put({"type": "task_list", "tasks": [f"HQ - {mes}/{ano}" for mes, ano in meses_a_processar]})
        
        if not inserir_matriculas(session, matriculas): return False, "Falha ao inserir matrículas."
        time.sleep(1)

        for i, (mes, ano) in enumerate(meses_a_processar):
            task_id = f"HQ - {mes}/{ano}"
            data_bondt = bondt_lookup.get((ano, mes))
            if progress_queue and hasattr(progress_queue, "should_skip") and progress_queue.should_skip(task_id):
                progress_queue.put({"type": "task_update", "task_id": task_id, "status": "✅ Concluído (checkpoint)"})
                continue
            if progress_queue:
                progress_queue.put({"type": "status", "detalhe": f"Processando {len(matriculas)} matrículas para {task_id}"})
                progress_queue.put({"type": "task_update", "task_id": task_id, "status": "Executando..."})
            
            session.findById("wnd[0]/usr/txtPNPPABRP").text = mes
            session.findById("wnd[0]/usr/txtPNPPABRJ").text = ano
            session.findById("wnd[0]/usr/ctxtBONDT").text = data_bondt
            caminho_de_saida = get_save_path(output_base_path, "HQ", ano=ano, mes=mes)
            session.findById("wnd[0]/usr/ctxtP_DIR").text = caminho_de_saida
            session.findById("wnd[0]/usr/chkP_BRANCH").selected = True
            session.findById("wnd[0]/usr/chkP_PDF").selected = True
            start_sapgui_security_watcher(timeout=10)
            session.findById("wnd[0]/tbar[1]/btn[8]").press(); time.sleep(2)
            session.findById("wnd[0]/tbar[0]/btn[3]").press(); time.sleep(1)
            
            if progress_queue:
                progress_queue.put({"type": "task_update", "task_id": task_id, "status": "✅ Concluído"})
            
        return True, "Processo HQ concluído com sucesso."
    except Exception as e:
        if progress_queue and 'task_id' in locals():
            progress_queue.put({"type": "task_update", "task_id": task_id, "status": "❌ Erro"})
        return False, f"Erro no processo HQ: {e}"
