import os
import sys
from datetime import datetime
import time
from .path_utils import get_save_path
import pyautogui

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
try:
    from automations.sap_utils import connect_to_sap, keep_alive
except ImportError:
    try:
        from sap_utils import connect_to_sap, keep_alive
    except ImportError:
        def connect_to_sap(): return None
        def keep_alive(session): print("AVISO: Função keep_alive não encontrada.")

def handle_save_dialog(folder_path, file_name):
    """Usa pyautogui para encontrar o campo 'Nome:', clicar nele, e salvar."""
    try:
        print("   [LOG] Janela de 'Salvar como' detectada. Procurando pelo campo 'Nome:'...")
        time.sleep(2)

        # Tenta localizar a imagem do label "Nome:" na tela
        label_coords = pyautogui.locateCenterOnScreen('label_nome.png', confidence=0.9)
        
        if label_coords is None:
            raise RuntimeError("Não foi possível encontrar a imagem 'label_nome.png' na tela.")

        print("   [LOG] Label 'Nome:' encontrado. Clicando no campo de texto...")
        pyautogui.click(label_coords.x + 100, label_coords.y)
        time.sleep(0.5)
        
        pyautogui.hotkey('ctrl', 'a')
        pyautogui.press('delete')
        time.sleep(0.5)

        full_path = os.path.join(folder_path, file_name)
        pyautogui.write(full_path, interval=0.01)
        time.sleep(1)
        
        pyautogui.press('enter')
        print(f"   [LOG] Arquivo salvo com sucesso em: {full_path}")
        time.sleep(3)
        return True
    except Exception as e:
        print(f"   [ERRO] Falha ao interagir com a janela de 'Salvar como': {e}")
        pyautogui.press('esc')
        return False

def execute(session, matriculas, periodo, config, output_base_path, progress_queue=None):
    """
    Executa a geração do Termo de Rescisão (TRCT) e salva o arquivo localmente.
    """
    try:
        print("--- Iniciando processo 'Termo de Rescisão (TRCT)' ---")
        
        matriculas_validas = [m.strip() for m in matriculas if m.strip()]
        if progress_queue:
            progress_queue.put({"type": "task_list", "tasks": [f"TRCT - {m}" for m in matriculas_validas]})
        
        caminho_de_saida = get_save_path(output_base_path, "TRCT")
        arquivos_salvos = 0

        # Navegação inicial feita uma única vez
        print(f"   [LOG] Iniciando navegação para a transação...")
        session.findById("wnd[0]").maximize()
        session.findById("wnd[0]/usr/cntlIMAGE_CONTAINER/shellcont/shell/shellcont[0]/shell").doubleClickNode("0000000018")
        time.sleep(1)
        session.findById("wnd[0]/tbar[1]/btn[17]").press(); time.sleep(1)
        shell = session.findById("wnd[1]/usr/cntlALV_CONTAINER_1/shellcont/shell")
        shell.setCurrentCell(2, "TEXT")
        shell.selectedRows = "2"
        shell.doubleClickCurrentCell(); time.sleep(1)

        data_inicio = "01.01.2021"

        for i, matricula in enumerate(matriculas_validas):
            task_id = f"TRCT - {matricula}"
            
            if progress_queue:
                progress_queue.put({"type": "status", "detalhe": f"Processando Matrícula {i+1}/{len(matriculas_validas)}: {matricula}"})
                progress_queue.put({"type": "task_update", "task_id": task_id, "status": "Executando..."})
            
            # Preenche os campos de data e matrícula
            session.findById("wnd[0]/usr/ctxtPNPBEGDA").text = data_inicio
            session.findById("wnd[0]/usr/ctxtPNPPERNR-LOW").text = matricula
            
            keep_alive(session)
            session.findById("wnd[0]/tbar[1]/btn[8]").press(); time.sleep(1)
            
            session.findById("wnd[1]/usr/ctxtSFPOUTPAR-DEST").text = "ZPDF"
            session.findById("wnd[1]/tbar[0]/btn[8]").press(); time.sleep(3)
            
            # --- Bloco para Salvar o Arquivo ---
            print(f"   [LOG] Tentando salvar o arquivo para a matrícula {matricula}...")
            session.findById("wnd[0]/mbar/menu[0]/menu[1]").Select(); time.sleep(1.5)
            session.findById("wnd[1]/usr/subSUBSCREEN_STEPLOOP:SAPLSPO5:0150/sub:SAPLSPO5:0150/radSPOPLI-SELFLAG[3,0]").select()
            session.findById("wnd[1]/tbar[0]/btn[0]").press()
            
            nome_arquivo = f"TRCT - {matricula}.html"
            if not handle_save_dialog(caminho_de_saida, nome_arquivo):
                raise RuntimeError("Falha ao salvar o arquivo com pyautogui.")
            
            arquivos_salvos += 1
            
            # Volta para a tela de parâmetros para a próxima matrícula
            session.findById("wnd[0]/tbar[0]/btn[3]").press(); time.sleep(1)

            if progress_queue:
                progress_queue.put({"type": "task_update", "task_id": task_id, "status": "✅ Concluído"})

        # Volta para o menu principal no final de tudo
        session.findById("wnd[0]/tbar[0]/okcd").text = "/n"
        session.findById("wnd[0]").sendVKey(0); time.sleep(1)

        return True, f"{arquivos_salvos} Termo(s) de Rescisão gerado(s) com sucesso."
    except Exception as e:
        if progress_queue and 'task_id' in locals():
            progress_queue.put({"type": "task_update", "task_id": task_id, "status": "❌ Erro"})
        print(f"ERRO no processo Termo de Rescisão: {e}")
        return False, f"Erro ao gerar Termo de Rescisão: {e}"