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

def iterar_meses(data_inicio_str, data_fim_str):
    """Gera um iterador de (mês, ano) entre duas datas no formato 'MM/AAAA'."""
    try:
        mes_inicio, ano_inicio = map(int, data_inicio_str.split('/'))
        mes_fim, ano_fim = map(int, data_fim_str.split('/'))
    except (ValueError, TypeError): return
    ano_atual, mes_atual = ano_inicio, mes_inicio
    while (ano_atual < ano_fim) or (ano_atual == ano_fim and mes_atual <= mes_fim):
        yield f"{mes_atual:02d}", str(ano_atual)
        mes_atual += 1
        if mes_atual > 12: mes_atual = 1; ano_atual += 1

# --- FUNÇÃO DE INSERÇÃO DE MATRÍCULAS 100% ESPELHADA DO VBA ---
def inserir_matriculas_espelhado_vba(session, matriculas):
    """
    Insere matrículas replicando a lógica de dupla interação do VBA
    (escrever + mover scrollbar) para máxima compatibilidade e robustez.
    """
    try:
        print("   [LOG] Abrindo janela de seleção múltipla...")
        session.findById("wnd[0]/usr/btn%_PNPPERNR_%_APP_%-VALU_PUSH").press(); time.sleep(1)
        
        print("   [LOG] Clicando no botão 'Limpar Seleção' (btn[16])...")
        session.findById("wnd[1]/tbar[0]/btn[16]").press(); time.sleep(1)
        
        print("   [LOG] Reabrindo janela de inserção...")
        session.findById("wnd[0]/usr/btn%_PNPPERNR_%_APP_%-VALU_PUSH").press(); time.sleep(1)

        for i, matricula in enumerate(matriculas):
            # Ação 1: Escreve a matrícula no campo de texto
            print(f"   [LOG] Ação 1/2: Escrevendo matrícula '{matricula.strip()}'...")
            session.findById("wnd[1]/usr/tabsTAB_STRIP/tabpSIVA/ssubSCREEN_HEADER:SAPLALDB:3010/tblSAPLALDBSINGLE/ctxtRSCSEL_255-SLOW_I[1,1]").text = matricula.strip()
            
            # Ação 2: Move a barra de rolagem para forçar a atualização da UI do SAP
            print(f"   [LOG] Ação 2/2: Movendo scrollbar para a posição {i + 1}...")
            session.findById("wnd[1]/usr/tabsTAB_STRIP/tabpSIVA/ssubSCREEN_HEADER:SAPLALDB:3010/tblSAPLALDBSINGLE").verticalScrollbar.position = i + 1
        
        print("   [LOG] Clicando em 'Executar' (btn[8]) para confirmar as matrículas...")
        session.findById("wnd[1]/tbar[0]/btn[8]").press()
        print("   [LOG] Matrículas inseridas com sucesso.")
        return True
    except Exception as e:
        print(f"   [ERRO NO LOG] Falha durante a inserção de matrículas: {e}")
        try: session.findById("wnd[1]/tbar[0]/btn[12]").press()
        except: pass
        return False

def execute(session, matriculas, periodo, config, output_base_path, progress_queue=None):
    """Executa a automação para Holerite Padrão (HP), reportando o progresso."""
    try:
        print("\n--- [LOG] Iniciando processo 'HP (Holerite Padrão)' ---")
        
        print("   [LOG] Iniciando transação 'PC00_M37_CEDT'...")
        session.startTransaction("PC00_M37_CEDT"); time.sleep(1)
        
        print("   [LOG] Pressionando 'Obter Variante' (btn[17])...")
        session.findById("wnd[0]/tbar[1]/btn[17]").press(); time.sleep(1)
        
        print("   [LOG] Limpando campo de busca de variante...")
        session.findById("wnd[1]/usr/txtENAME-LOW").text = ""
        
        print("   [LOG] Clicando em 'Executar' na busca de variante (btn[8])...")
        session.findById("wnd[1]/tbar[0]/btn[8]").press(); time.sleep(1)
        
        print("   [LOG] Acessando a tabela de variantes (shell)...")
        shell = session.findById("wnd[1]/usr/cntlALV_CONTAINER_1/shellcont/shell")
        
        print("   [LOG] Selecionando a linha 7...")
        shell.setCurrentCell(7, "TEXT"); shell.selectedRows = "7"
        
        print("   [LOG] Clicando em 'Escolher' (btn[2]) para confirmar a variante...")
        session.findById("wnd[1]/tbar[0]/btn[2]").press(); time.sleep(1)

        meses_a_processar = list(iterar_meses(periodo['inicio'], periodo['fim']))
        if progress_queue:
            progress_queue.put({"type": "task_list", "tasks": [f"HP - {mes}/{ano}" for mes, ano in meses_a_processar]})
        
        # Chama a nova função de inserção espelhada
        if not inserir_matriculas_espelhado_vba(session, matriculas):
            return False, "Falha ao inserir matrículas."
        time.sleep(1)

        for i, (mes, ano) in enumerate(meses_a_processar):
            task_id = f"HP - {mes}/{ano}"
            if progress_queue and hasattr(progress_queue, "should_skip") and progress_queue.should_skip(task_id):
                progress_queue.put({"type": "task_update", "task_id": task_id, "status": "✅ Concluído (checkpoint)"})
                continue
            if progress_queue:
                progress_queue.put({"type": "status", "detalhe": f"Processando {len(matriculas)} matrículas para {task_id}"})
                progress_queue.put({"type": "task_update", "task_id": task_id, "status": "Executando..."})
            
            print(f"\n   [LOG] Preenchendo dados para {task_id}...")
            session.findById("wnd[0]/usr/txtPNPPABRP").text = mes
            session.findById("wnd[0]/usr/txtPNPPABRJ").text = ano
            caminho_de_saida = get_save_path(output_base_path, "HP", ano=ano, mes=mes)
            session.findById("wnd[0]/usr/ctxtP_DIR").text = caminho_de_saida
            session.findById("wnd[0]/usr/chkP_BRANCH").selected = True
            session.findById("wnd[0]/usr/chkP_PDF").selected = True
            
            print("   [LOG] Clicando em 'Executar' (F8) para gerar o relatório...")
            start_sapgui_security_watcher(timeout=10)
            session.findById("wnd[0]/tbar[1]/btn[8]").press(); time.sleep(2)
            
            print("   [LOG] Clicando em 'Voltar' (F3) para a tela de parâmetros...")
            session.findById("wnd[0]/tbar[0]/btn[3]").press(); time.sleep(1)
            
            if progress_queue:
                progress_queue.put({"type": "task_update", "task_id": task_id, "status": "✅ Concluído"})

        return True, "Processo HP concluído com sucesso."
    except Exception as e:
        print(f"\n!!! [ERRO NO LOG] O SCRIPT FALHOU APÓS O ÚLTIMO PASSO LOGADO ACIMA !!!\n   Detalhes do Erro: {e}\n")
        if progress_queue and 'task_id' in locals():
            progress_queue.put({"type": "task_update", "task_id": task_id, "status": "❌ Erro"})
        return False, f"Erro no processo HP: {e}"
