import os
import sys
from datetime import datetime
import time

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

# --- Funções de Ajuda ---
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
    """Executa a automação para a variante HP-COM, com filtro de data específico."""
    try:
        print("--- Iniciando processo 'HP-COM' ---")
        
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
        shell.setCurrentCell(6, "TEXT")
        shell.selectedRows = "6"
        session.findById("wnd[1]/tbar[0]/btn[2]").press()
        time.sleep(1)

        if not inserir_matriculas(session, matriculas):
            return False, "Falha ao inserir matrículas no processo HP-COM."
        time.sleep(1)

        for mes, ano in iterar_meses(periodo['inicio'], periodo['fim']):
            mes_int, ano_int = int(mes), int(ano)
            
            if (ano_int > 2022 and ano_int < 2024) or \
               (ano_int == 2022 and mes_int == 12) or \
               (ano_int == 2024 and mes_int <= 7):
                
                print(f"Processando HP-COM para data válida: {mes}/{ano}...")
                
                session.findById("wnd[0]/usr/txtPNPPABRP").text = mes
                session.findById("wnd[0]/usr/txtPNPPABRJ").text = ano
                
                pasta_saida_periodo = os.path.join(pasta_saida_principal, "HP", f"HP - {mes_int}.{ano}")
                os.makedirs(pasta_saida_periodo, exist_ok=True)
                session.findById("wnd[0]/usr/ctxtP_DIR").text = pasta_saida_periodo
                
                session.findById("wnd[0]/usr/chkP_BRANCH").selected = True
                session.findById("wnd[0]/usr/chkP_PDF").selected = True
                
                session.findById("wnd[0]/tbar[1]/btn[8]").press()
                
                while session.Busy:
                    time.sleep(1)
                
                session.findById("wnd[0]/tbar[0]/btn[3]").press()
                time.sleep(1)
            else:
                print(f"Ignorando data {mes}/{ano} para HP-COM (fora do filtro).")

        print("--- Processo 'HP-COM' finalizado. ---")
        return True, "Processo HP-COM concluído com sucesso."

    except Exception as e:
        print(f"ERRO no processo HP-COM: {e}")
        return False, f"Erro no processo HP-COM: {e}"

# --- Bloco de Teste ---
if __name__ == "__main__":
    # ... (bloco de teste para rodar de forma isolada) ...
    pass