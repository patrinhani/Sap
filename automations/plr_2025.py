import os
import sys
from datetime import datetime
import time

# pyperclip foi REMOVIDO

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
try:
    from automations.sap_utils import connect_to_sap
except ImportError:
    try:
        from sap_utils import connect_to_sap
    except ImportError:
        def connect_to_sap():
            print("AVISO: A função 'connect_to_sap' não foi encontrada.")
            return None

# --- FUNÇÃO DE INSERÇÃO PADRÃO (SEM CLIPBOARD) ---
def inserir_matriculas(session, matriculas):
    """Insere as matrículas uma a uma, de forma segura."""
    try:
        session.findById("wnd[0]/usr/btn%_PNPPERNR_%_APP_%-VALU_PUSH").press()
        time.sleep(1)

        # Limpa o campo antes de inserir
        session.findById("wnd[1]/tbar[0]/btn[16]").press()
        time.sleep(1)
        
        # Reabre a janela para inserção
        session.findById("wnd[0]/usr/btn%_PNPPERNR_%_APP_%-VALU_PUSH").press()
        time.sleep(1)
        
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

# --- Função Principal de Execução ---
def execute(session, matriculas, periodo, config, output_base_path):
    """Executa o processo de PLR 2025."""
    try:
        print("--- Iniciando processo 'PLR 2025' ---")
        
        MES = "04"
        ANO = "2025"
        DATA_BONDT = "15.04.2025"
        
        hoje = datetime.now().strftime("%d.%m")
        pasta_saida_principal = os.path.join(output_base_path, f"HP SAP - {hoje}")
        os.makedirs(pasta_saida_principal, exist_ok=True)
        
        session.startTransaction("PC00_M37_CEDT")
        time.sleep(1)
        
        session.findById("wnd[0]/tbar[1]/btn[17]").press()
        time.sleep(1)

        session.findById("wnd[1]/usr/txtENAME-LOW").text = ""
        session.findById("wnd[1]/tbar[0]/btn[8]").press()
        time.sleep(1)
        
        shell = session.findById("wnd[1]/usr/cntlALV_CONTAINER_1/shellcont/shell")
        shell.setCurrentCell(9, "TEXT")
        shell.selectedRows = "9"
        session.findById("wnd[1]/tbar[0]/btn[2]").press()
        time.sleep(1)

        session.findById("wnd[0]/usr/txtPNPPABRP").text = MES
        session.findById("wnd[0]/usr/txtPNPPABRJ").text = ANO
        session.findById("wnd[0]/usr/ctxtBONDT").text = DATA_BONDT
        
        # ALTERADO: Chama a função de inserção segura
        if not inserir_matriculas(session, matriculas):
            return False, "Falha ao inserir matrículas no processo PLR 2025."
        time.sleep(1)
        
        pasta_saida_ano = os.path.join(pasta_saida_principal, "HPL 2025")
        os.makedirs(pasta_saida_ano, exist_ok=True)
        session.findById("wnd[0]/usr/ctxtP_DIR").text = pasta_saida_ano
        
        session.findById("wnd[0]/usr/chkP_BRANCH").selected = True
        session.findById("wnd[0]/usr/chkP_PDF").selected = True
        
        session.findById("wnd[0]/tbar[1]/btn[8]").press()
        
        while session.Busy:
            time.sleep(1)
        
        session.findById("wnd[0]/tbar[0]/btn[3]").press()
        time.sleep(1)
            
        print("--- Processo 'PLR 2025' finalizado. ---")
        return True, "PLR 2025 concluído com sucesso."

    except Exception as e:
        print(f"ERRO no processo PLR 2025: {e}")
        return False, f"Erro no processo PLR 2025: {e}"