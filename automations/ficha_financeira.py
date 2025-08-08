import os
import sys
from datetime import datetime
import time
from .path_utils import get_save_path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
try:
    from automations.sap_utils import connect_to_sap
except ImportError:
    pass

def execute(session, matriculas, periodo, config, output_base_path, progress_queue=None):
    """Gera a Ficha Financeira, reportando o progresso por matrícula e ano."""
    try:
        print("--- Iniciando execução da Ficha Financeira ---")
        empresas_para_testar = ["0021", "0029", "0004", "0049"]
        
        try:
            ano_inicio = int(periodo['inicio'].split('/')[1])
            ano_fim = int(periodo['fim'].split('/')[1])
        except (ValueError, IndexError):
            return False, "Erro: Período inválido."

        tarefas = []
        matriculas_validas = [m.strip() for m in matriculas if m.strip()]
        for matricula in matriculas_validas:
            for ano in range(ano_inicio, ano_fim + 1):
                tarefas.append(f"FF {matricula} - {ano}")
        
        if progress_queue:
            progress_queue.put({"type": "task_list", "tasks": tarefas})

        arquivos_gerados = 0
        for i, task_id in enumerate(tarefas):
            matricula, ano_str = task_id.replace("FF ", "").split(" - ")
            ano = int(ano_str)
            
            if progress_queue:
                progress_queue.put({"type": "status", "detalhe": f"Processando Tarefa {i+1}/{len(tarefas)}: {task_id}"})
                progress_queue.put({"type": "task_update", "task_id": task_id, "status": "Executando..."})
            
            caminho_de_saida = get_save_path(output_base_path, "FichaFinanceira")
            encontrou_empresa_valida = False
            for empresa in empresas_para_testar:
                if encontrou_empresa_valida: break
                
                session.StartTransaction("ZHCMTR0084"); time.sleep(1)
                session.findById("wnd[0]/tbar[1]/btn[17]").press(); time.sleep(1)
                session.findById("wnd[1]/usr/cntlALV_CONTAINER_1/shellcont/shell").selectedRows = "0"
                session.findById("wnd[1]/tbar[0]/btn[2]").press(); time.sleep(1)
                
                session.findById("wnd[0]/usr/ctxtPNPBEGDA").text = f"01.01.{ano}"
                session.findById("wnd[0]/usr/ctxtPNPENDDA").text = f"31.12.{ano}"
                session.findById("wnd[0]/usr/txtP_COMPE").text = str(ano)
                session.findById("wnd[0]/usr/ctxtPNPBUKRS-LOW").text = empresa
                session.findById("wnd[0]/usr/ctxtPNPPERNR-LOW").text = matricula
                session.findById("wnd[0]/tbar[1]/btn[8]").press(); time.sleep(3)
                
                try:
                    session.findById("wnd[0]/tbar[1]/btn[46]").press()
                    session.findById("wnd[0]/tbar[1]/btn[45]").press(); time.sleep(1)
                    session.findById("wnd[1]/usr/subSUBSCREEN_STEPLOOP:SAPLSPO5:0150/sub:SAPLSPO5:0150/radSPOPLI-SELFLAG[3,0]").select()
                    session.findById("wnd[1]/tbar[0]/btn[0]").press(); time.sleep(1)
                    nome_arquivo = f"{matricula} - ff {str(ano)[-2:]}.html"
                    session.findById("wnd[1]/usr/ctxtDY_PATH").text = caminho_de_saida
                    session.findById("wnd[1]/usr/ctxtDY_FILENAME").text = nome_arquivo
                    session.findById("wnd[1]/tbar[0]/btn[0]").press()
                    arquivos_gerados += 1
                    encontrou_empresa_valida = True
                except:
                    session.findById("wnd[0]").sendVKey(3)

            if progress_queue:
                status_final = "✅ Concluído" if encontrou_empresa_valida else "❌ Erro"
                progress_queue.put({"type": "task_update", "task_id": task_id, "status": status_final})

        mensagem_final = f"Processo concluído! {arquivos_gerados} arquivo(s) gerado(s)."
        return True, mensagem_final

    except Exception as e:
        if progress_queue and 'task_id' in locals():
            progress_queue.put({"type": "task_update", "task_id": task_id, "status": "❌ Erro"})
        return False, f"Erro em Ficha Financeira: {e}"