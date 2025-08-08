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

def execute(session, matriculas, periodo, config, output_base_path, progress_queue=None):
    """Gera o relatório da CTPS Digital, reportando o progresso por matrícula."""
    try:
        print("--- Iniciando execução de CTPS Digital ---")
        empresas_para_testar = ["0021", "0029", "0004", "0049"]
        processados_com_sucesso = 0
        erros = 0
        
        matriculas_validas = [m.strip() for m in matriculas if m.strip()]
        total_matriculas = len(matriculas_validas)
        if progress_queue:
            progress_queue.put({"type": "task_list", "tasks": matriculas_validas})

        for i, matricula in enumerate(matriculas_validas):
            task_id = matricula
            
            if progress_queue:
                progress_queue.put({"type": "status", "detalhe": f"Processando Matrícula {i+1}/{total_matriculas}: {matricula}"})
                progress_queue.put({"type": "task_update", "task_id": task_id, "status": "Executando..."})
            
            caminho_base = get_save_path(output_base_path, "CTPS")
            caminho_salvar_completo = os.path.join(caminho_base, f"ctps sap - {matricula}")
            encontrou_empresa = False
            
            for codigo_empresa in empresas_para_testar:
                print(f"  Tentando com empresa: {codigo_empresa}...")
                
                session.StartTransaction("ZHCMTR0074"); time.sleep(1)
                session.findById("wnd[0]/tbar[1]/btn[17]").press(); time.sleep(1)
                
                try:
                    grid = session.findById("wnd[1]/usr/cntlALV_CONTAINER_1/shellcont/shell")
                    grid.currentCellRow = 2; grid.selectedRows = "2"
                    session.findById("wnd[1]/tbar[0]/btn[2]").press(); time.sleep(1)
                except Exception:
                    session.findById("wnd[1]").close(); time.sleep(1)
                    
                session.findById("wnd[0]/usr/ctxtPNPPERNR-LOW").text = matricula
                session.findById("wnd[0]/usr/ctxtPNPBUKRS-LOW").text = codigo_empresa
                session.findById("wnd[0]/usr/ctxtP_CARR").text = caminho_salvar_completo
                session.findById("wnd[0]/tbar[1]/btn[8]").press(); time.sleep(0.5)
                
                if session.Children.Count > 1:
                    try:
                        popup = session.findById("wnd[1]")
                        popup.findById("usr/chkSSFPP-TDIMMED").selected = True
                        popup.findById("usr/ctxtSSFPP-TDDEST").text = "lp01"
                        popup.findById("wnd[1]/tbar[0]/btn[8]").press()
                        encontrou_empresa = True
                        processados_com_sucesso += 1
                    except Exception:
                        session.findById("wnd[1]").close()
                        
                if encontrou_empresa:
                    break
            
            if encontrou_empresa:
                if progress_queue: progress_queue.put({"type": "task_update", "task_id": task_id, "status": "✅ Concluído"})
            else:
                erros += 1
                if progress_queue: progress_queue.put({"type": "task_update", "task_id": task_id, "status": "❌ Erro"})
        
        mensagem_final = f"Concluído: {processados_com_sucesso} processadas, {erros} com erro."
        return True, mensagem_final

    except Exception as e:
        if progress_queue and 'task_id' in locals():
            progress_queue.put({"type": "task_update", "task_id": task_id, "status": "❌ Erro"})
        return False, f"Erro em CTPS Digital: {e}"