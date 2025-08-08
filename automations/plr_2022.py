import os
import sys
from datetime import datetime
import time
import pyperclip # Importa a biblioteca para a área de transferência

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

# --- Função de Ajuda Especial para Colar Matrículas ---
# --- Função de Ajuda Especial para Colar Matrículas ---
def inserir_matriculas_colando(session, matriculas):
    """Copia a lista de matrículas para a área de transferência e cola no SAP."""
    try:
        # Junta a lista de matrículas em uma única string, separada por quebra de linha
        matriculas_str = "\n".join(matriculas)
        pyperclip.copy(matriculas_str)

        session.findById("wnd[0]/usr/btn%_PNPPERNR_%_APP_%-VALU_PUSH").press()
        time.sleep(1)
        
        # Limpa o campo antes de colar
        session.findById("wnd[1]/tbar[0]/btn[16]").press()
        time.sleep(1)
        
        # CORRIGIDO: Clica no botão "Importar da área de transferência" (btn[24])
        session.findById("wnd[1]/tbar[0]/btn[24]").press()
        time.sleep(1)
        
        # Confirma a importação
        session.findById("wnd[1]/tbar[0]/btn[8]").press()
        return True
    except Exception as e:
        print(f"Erro ao colar matrículas: {e}")
        pyperclip.copy("") # Limpa a área de transferência
        try: session.findById("wnd[1]/tbar[0]/btn[12]").press()
        except: pass
        return False

# --- Função Principal de Execução ---
def execute(session, matriculas, periodo, config, output_base_path):
    """Executa o processo de PLR 2022."""
    try:
        print("--- Iniciando processo 'PLR 2022' ---")
        
        # Valores fixos para este processo
        MES = "04"
        ANO = "2022"
        DATA_BONDT = "08.04.2022"
        
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
        
        if not inserir_matriculas_colando(session, matriculas):
            return False, "Falha ao inserir matrículas no processo PLR 2022."
        time.sleep(1)
        
        pasta_saida_ano = os.path.join(pasta_saida_principal, "HPL 2022")
        os.makedirs(pasta_saida_ano, exist_ok=True)
        session.findById("wnd[0]/usr/ctxtP_DIR").text = pasta_saida_ano
        
        session.findById("wnd[0]/usr/chkP_BRANCH").selected = True
        session.findById("wnd[0]/usr/chkP_PDF").selected = True
        
        session.findById("wnd[0]/tbar[1]/btn[8]").press()
        
        while session.Busy:
            time.sleep(1)
        
        session.findById("wnd[0]/tbar[0]/btn[3]").press()
        time.sleep(1)
            
        print("--- Processo 'PLR 2022' finalizado. ---")
        return True, "PLR 2022 concluído com sucesso."

    except Exception as e:
        pyperclip.copy("") # Garante que a área de transferência seja limpa em caso de erro
        print(f"ERRO no processo PLR 2022: {e}")
        return False, f"Erro no processo PLR 2022: {e}"

# --- Bloco de Teste ---
if __name__ == "__main__":
    # ... (bloco de teste padrão) ...
    pass