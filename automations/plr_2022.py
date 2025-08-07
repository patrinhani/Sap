import time
import os
import pyperclip
from datetime import datetime

def execute(session, matriculas, periodo, options, base_path):
    print("--- Iniciando execução de PLR 2022 ---")
    
    # --- DADOS FIXOS PARA ESTE PROCESSO ---
    MES_FIXO = "04"
    ANO_FIXO = "2022"
    DATA_BONDT_FIXA = "08.04.2022"
    
    hoje = datetime.now().strftime("%d.%m")
    pasta_data = os.path.join(base_path, hoje)
    
    try:
        # A transação é iniciada pelo main_interface.py
        print("  Selecionando variante 'PLR'...")
        session.findById("wnd[0]/tbar[1]/btn[17]").press(); time.sleep(1)
        popup_variante = session.findById("wnd[1]")
        popup_variante.findById("usr/txtENAME-LOW").text = ""
        popup_variante.findById("tbar[0]/btn[8]").press()
        time.sleep(1)
        grid = popup_variante.findById("usr/cntlALV_CONTAINER_1/shellcont/shell")
        grid.setCurrentCell(9, "TEXT"); grid.selectedRows = "9"
        popup_variante.findById("tbar[0]/btn[2]").press(); time.sleep(1)
        
        session.findById("wnd[0]/usr/txtPNPPABRP").text = MES_FIXO
        session.findById("wnd[0]/usr/txtPNPPABRJ").text = ANO_FIXO
        session.findById("wnd[0]/usr/ctxtBONDT").text = DATA_BONDT_FIXA
        
        print(f"  Processando com data fixa: {MES_FIXO}/{ANO_FIXO}")
        print("  Inserindo matrículas...")
        session.findById("wnd[0]/usr/btn%_PNPPERNR_%_APP_%-VALU_PUSH").press(); time.sleep(1)
        pyperclip.copy("\n".join(matriculas))
        session.findById("wnd[1]/tbar[0]/btn[24]").press(); time.sleep(0.5)
        session.findById("wnd[1]/tbar[0]/btn[8]").press(); time.sleep(1)

        diretorio_saida = os.path.join(pasta_data, "HPL 2022")
        if not os.path.exists(diretorio_saida): os.makedirs(diretorio_saida)
        session.findById("wnd[0]/usr/ctxtP_DIR").text = diretorio_saida
        session.findById("wnd[0]/usr/chkP_BRANCH").selected = True
        session.findById("wnd[0]/usr/chkP_PDF").selected = True
        
        session.findById("wnd[0]/tbar[1]/btn[8]").press()
        print("    Aguardando processamento...")
        time.sleep(5)
        
        return True, "Processo PLR 2022 concluído."
    except Exception as e: return False, f"Erro em PLR 2022: {e}"