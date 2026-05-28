import os
import sys
import time
from datetime import datetime
from .path_utils import get_save_path

# Adiciona o diretório pai ao path para importar módulos irmãos se necessário
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from automations.sap_utils import connect_to_sap, keep_alive, start_sapgui_security_watcher
except ImportError:
    try:
        from sap_utils import connect_to_sap, keep_alive, start_sapgui_security_watcher
    except ImportError:
        # Fallback para testes locais sem a biblioteca completa
        def connect_to_sap(): return None
        def keep_alive(session): print("AVISO: Função keep_alive não encontrada.")

def execute(session, matriculas, periodo, config, output_base_path, progress_queue=None):
    """
    Gera o relatório da CTPS Digital (ZHCMTR0074).
    Refatorado para seguir a lógica da macro VBA 'Sub Ctps_'.
    """
    try:
        print("--- Iniciando execução de CTPS Digital (Lógica VBA Atualizada) ---")
        
        # Lista de empresas definida no VBA
        empresas_para_testar = ["0021", "0029", "0004", "0049"]
        
        processados_com_sucesso = 0
        erros = 0
        
        # Limpeza e preparação da lista de matrículas
        matriculas_validas = [m.strip() for m in matriculas if m.strip()]
        total_matriculas = len(matriculas_validas)
        
        if progress_queue:
            progress_queue.put({"type": "task_list", "tasks": matriculas_validas})

        # --- CONTROLE DE KEEP-ALIVE ---
        KEEP_ALIVE_INTERVAL = 180
        last_ping_time = time.time()
        # -----------------------------

        for i, matricula in enumerate(matriculas_validas):
            # --- VERIFICAÇÃO DE KEEP-ALIVE ---
            current_time = time.time()
            if current_time - last_ping_time > KEEP_ALIVE_INTERVAL:
                keep_alive(session)
                last_ping_time = current_time
            # ---------------------------------
            
            task_id = matricula
            if progress_queue:
                progress_queue.put({"type": "status", "detalhe": f"Processando Matrícula {i+1}/{total_matriculas}: {matricula}"})
                progress_queue.put({"type": "task_update", "task_id": task_id, "status": "Executando..."})
            
            # Definição do caminho de salvamento (Equivalente ao caminhoSalvar do VBA)
            # O VBA usa: ...\CTPS\ ctps sap - {matricula}
            # O get_save_path gerencia a pasta base, aqui criamos a subpasta e nome
            pasta_ctps = get_save_path(output_base_path, "CTPS")
            
            # Nota: O VBA tem um espaço antes de "ctps" (" ctps sap - "), mantido aqui se for intencional,
            # mas geralmente recomenda-se trim. Vou manter o padrão do nome do arquivo lógico.
            caminho_salvar_completo = os.path.join(pasta_ctps, f"ctps sap - {matricula}")
            
            encontrou_empresa = False
            
            # Loop pelas empresas (Lógica do VBA: Tenta cada empresa até achar ou acabar)
            for codigo_empresa in empresas_para_testar:
                try:
                    # VBA: StartTransaction dentro do loop de empresas
                    session.StartTransaction("ZHCMTR0074")
                    time.sleep(1) 

                    # VBA: Selecionar Variante
                    session.findById("wnd[0]/tbar[1]/btn[17]").press()
                    time.sleep(1)
                    
                    try:
                        # Tenta selecionar a linha 2 da variante
                        session.findById("wnd[1]/usr/cntlALV_CONTAINER_1/shellcont/shell").currentCellRow = 2
                        session.findById("wnd[1]/usr/cntlALV_CONTAINER_1/shellcont/shell").selectedRows = "2"
                        session.findById("wnd[1]/tbar[0]/btn[2]").press()
                    except Exception:
                        # Se falhar a seleção da variante (janela não abriu ou erro), tenta fechar popup se existir
                        if session.Children.Count > 1:
                            session.findById("wnd[1]").close()
                    
                    time.sleep(0.5)

                    # --- PREENCHIMENTO DOS CAMPOS (Sequência exata do VBA) ---
                    
                    # 1. Matrícula e Empresa
                    session.findById("wnd[0]/usr/ctxtPNPPERNR-LOW").text = matricula
                    session.findById("wnd[0]/usr/ctxtPNPBUKRS-LOW").text = codigo_empresa
                    
                    # Foco cosmético do VBA (mantido para garantir comportamento)
                    session.findById("wnd[0]/usr/ctxtPNPBUKRS-LOW").setFocus()
                    session.findById("wnd[0]/usr/ctxtPNPBUKRS-LOW").caretPosition = 4
                    
                    # 2. Checkboxes (Antes do Enter, conforme VBA atual)
                    session.findById("wnd[0]/usr/chkC_SF").selected = False
                    session.findById("wnd[0]/usr/chkC_CARR").selected = True
                    
                    # 3. Pressionar Enter (sendVKey 0)
                    session.findById("wnd[0]").sendVKey(0)
                    time.sleep(1) # Aguarda validação do SAP
                    
                    # 4. Inserir Caminho
                    session.findById("wnd[0]/usr/ctxtP_CARR").text = caminho_salvar_completo
                    session.findById("wnd[0]/usr/ctxtP_CARR").setFocus()
                    session.findById("wnd[0]/usr/ctxtP_CARR").caretPosition = len(caminho_salvar_completo)
                    
                    # 5. Executar (F8)
                    start_sapgui_security_watcher(timeout=10)
                    session.findById("wnd[0]/tbar[1]/btn[8]").press()
                    
                    # Espera processamento
                    time.sleep(1)
                    
                    # --- VERIFICAÇÃO DE POPUP DE IMPRESSÃO (Sucesso) ---
                    # VBA: If .Children.Count > 1 Then ...
                    if session.Children.Count > 1:
                        # Verifica se é a janela de impressão correta procurando o checkbox TDIMMED
                        try:
                            chk_imediata = session.findById("wnd[1]/usr/chkSSFPP-TDIMMED")
                            
                            # Se não deu erro acima, o campo existe. Prossegue.
                            chk_imediata.selected = True
                            session.findById("wnd[1]/usr/ctxtSSFPP-TDDEST").text = "lp01"
                            session.findById("wnd[1]/usr/chkSSFPP-TDIMMED").setFocus()
                            
                            # Confirmar impressão
                            session.findById("wnd[1]/tbar[0]/btn[8]").press()
                            
                            encontrou_empresa = True
                            processados_com_sucesso += 1
                            break # Sai do loop de empresas (Exit For)
                            
                        except Exception:
                            # VBA: "Se a janela abriu mas não tem o campo, assume que deu erro e fecha"
                            # Pode ser mensagem de erro "Nenhum dado selecionado"
                            session.findById("wnd[1]").close()
                
                except Exception as e_sap:
                    # Captura erros de script SAP e tenta continuar para a próxima empresa
                    print(f"Erro ao tentar empresa {codigo_empresa} para matrícula {matricula}: {e_sap}")
                    # Garante que volta para a tela inicial ou fecha popups antes da próxima iteração
                    try:
                        session.findById("wnd[0]/tbar[0]/btn[15]").press() # Tenta voltar (F3)
                    except:
                        pass
                    continue

            # Atualização de status final da matrícula
            if encontrou_empresa:
                if progress_queue: progress_queue.put({"type": "task_update", "task_id": task_id, "status": "✅ Concluído"})
            else:
                erros += 1
                if progress_queue: progress_queue.put({"type": "task_update", "task_id": task_id, "status": "❌ Erro/Não encontrado"})
        
        mensagem_final = f"Processo concluído. Sucesso: {processados_com_sucesso}, Erros: {erros}."
        print(mensagem_final)
        return True, mensagem_final

    except Exception as e:
        erro_msg = f"Erro crítico na execução CTPS: {e}"
        print(erro_msg)
        if progress_queue and 'task_id' in locals():
             progress_queue.put({"type": "task_update", "task_id": task_id, "status": "❌ Erro Fatal"})
        return False, erro_msg
