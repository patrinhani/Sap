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
    """Executa a automação para a variante ZDP1, com verificação de data."""
    try:
        print("--- Iniciando processo 'ZDP1' ---")
        datas_validas_zdp1 = {
            ("06", "2021"), ("08", "2021"), ("09", "2021"), ("10", "2021"), ("11", "2021"), ("12", "2021"),("01", "2022"), ("03", "2022"), ("04", "2022"), ("05", "2022"), ("07", "2022"), ("08", "2022"), ("10", "2022"), ("11", "2022"), ("12", "2022"),("02", "2023"), ("04", "2023"), ("05", "2023"), ("06", "2023"), ("08", "2023"), ("09", "2023"), ("10", "2023"), ("11", "2023"), ("12", "2023"),("01", "2024"), ("03", "2024"), ("05", "2024"), ("06", "2024"), ("07", "2024"), ("08", "2024"), ("09", "2024"), ("11", "2024"), ("12", "2024"),("01", "2025"), ("02", "2025"), ("04", "2025"), ("05", "2025"), ("06", "2025"), ("08", "2025"), ("09", "2025"), ("10", "2025"), ("11", "2025"), ("12", "2025"),("02", "2026"), ("03", "2026"), ("05", "2026"), ("06", "2026"), ("07", "2026"), ("09", "2026"), ("10", "2026"), ("11", "2026"), ("12", "2026"),("01", "2027"), ("03", "2027"), ("04", "2027"), ("05", "2027"), ("06", "2027"), ("08", "2027"), ("09", "2027"), ("10", "2027"), ("11", "2027"), ("12", "2027"),("02", "2028"), ("03", "2028"), ("04", "2028"), ("06", "2028"), ("07", "2028"), ("09", "2028"), ("10", "2028"), ("11", "2028"), ("12", "2028"),
        }
        
        hoje = datetime.now().strftime("%d.%m")
        pasta_saida_principal = os.path.join(output_base_path, f"HP SAP - {hoje}")
        os.makedirs(pasta_saida_principal, exist_ok=True)

        session.startTransaction("PC00_M37_CEDT")
        time.sleep(1)
        session.findById("wnd[0]/tbar[1]/btn[17]").press()
        time.sleep(1)
        
        session.findById("wnd[1]/usr/txtENAME-LOW").text = ""
        session.findById("wnd[1]/usr/txtENAME-LOW").setFocus()
        session.findById("wnd[1]/tbar[0]/btn[8]").press()
        time.sleep(1)
        
        session.findById("wnd[1]/usr/cntlALV_CONTAINER_1/shellcont/shell").pressToolbarButton("&FIND")
        time.sleep(1)
        session.findById("wnd[2]/usr/txtGS_SEARCH-VALUE").text = "zdp1"
        session.findById("wnd[2]").sendVKey(0)
        time.sleep(1)
        session.findById("wnd[2]/tbar[0]/btn[12]").press()
        time.sleep(1)
        
        focused_row = session.findById("wnd[1]/usr/cntlALV_CONTAINER_1/shellcont/shell").currentCellRow
        session.findById("wnd[1]/usr/cntlALV_CONTAINER_1/shellcont/shell").selectedRows = focused_row
        session.findById("wnd[1]/usr/cntlALV_CONTAINER_1/shellcont/shell").doubleClickCurrentCell()
        time.sleep(1)

        if not inserir_matriculas(session, matriculas):
            return False, "Falha ao inserir matrículas no processo ZDP1."
        time.sleep(1)

        for mes, ano in iterar_meses(periodo['inicio'], periodo['fim']):
            if (mes, ano) in datas_validas_zdp1:
                print(f"Processando ZDP1 para data válida: {mes}/{ano}...")
                
                session.findById("wnd[0]/usr/radPNPTIMRA").select()
                session.findById("wnd[0]/usr/txtPNPPABRP").text = mes
                session.findById("wnd[0]/usr/txtPNPPABRJ").text = ano
                
                pasta_saida_periodo = os.path.join(pasta_saida_principal, "HP", f"HP - {int(mes)}.{ano}")
                os.makedirs(pasta_saida_periodo, exist_ok=True)
                session.findById("wnd[0]/usr/ctxtP_DIR").text = pasta_saida_periodo
                
                session.findById("wnd[0]/usr/chkP_BRANCH").selected = True
                session.findById("wnd[0]/usr/chkP_PDF").selected = True
                
                session.findById("wnd[0]/tbar[1]/btn[8]").press()
                time.sleep(2)
                
                session.findById("wnd[0]/tbar[0]/btn[3]").press()
                time.sleep(1)
            else:
                print(f"Ignorando data {mes}/{ano} para ZDP1 (não está na lista).")

        print("--- Processo 'ZDP1' finalizado. ---")
        return True, "Processo ZDP1 concluído com sucesso."

    except Exception as e:
        print(f"ERRO no processo ZDP1: {e}")
        return False, f"Erro no processo ZDP1: {e}"

# --- Bloco de Teste ---
if __name__ == "__main__":
    # ... (bloco de teste para rodar de forma isolada) ...
    pass