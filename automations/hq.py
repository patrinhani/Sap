import os
import sys
from datetime import datetime
import time

# Bloco para ajudar na importação do 'sap_utils' durante o teste
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

def inserir_matriculas(session, matriculas):
    """Função para preencher a lista de matrículas no pop-up do SAP."""
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
    """Executa a automação para Holerite Quinzenal (HQ)."""
    try:
        print("--- Iniciando processo 'HQ (Holerite Quinzenal)' ---")

        # Tabela de consulta para a data BONDT.
        bondt_lookup = {
            ('2021', '06'): '15.06.2021', ('2021', '08'): '13.08.2021', ('2021', '09'): '15.09.2021', ('2021', '10'): '15.10.2021', ('2021', '11'): '12.11.2021', ('2021', '12'): '15.12.2021',
            ('2022', '01'): '14.01.2022', ('2022', '03'): '15.03.2022', ('2022', '04'): '14.04.2022', ('2022', '05'): '13.05.2022', ('2022', '07'): '15.07.2022', ('2022', '08'): '15.08.2022', ('2022', '10'): '14.10.2022', ('2022', '11'): '14.11.2022', ('2022', '12'): '15.12.2022',
            ('2023', '02'): '15.02.2023', ('2023', '04'): '14.04.2023', ('2023', '05'): '15.05.2023', ('2023', '06'): '15.06.2023', ('2023', '08'): '15.08.2023', ('2023', '09'): '15.09.2023', ('2023', '10'): '13.10.2023', ('2023', '11'): '14.11.2023', ('2023', '12'): '15.12.2023',
            ('2024', '01'): '15.01.2024', ('2024', '03'): '15.03.2024', ('2024', '05'): '15.05.2024', ('2024', '06'): '14.06.2024', ('2024', '07'): '15.07.2024', ('2024', '08'): '15.08.2024', ('2024', '09'): '13.09.2024', ('2024', '11'): '14.11.2024', ('2024', '12'): '13.12.2024',
            ('2025', '01'): '15.01.2025', ('2025', '02'): '14.02.2025', ('2025', '04'): '15.04.2025', ('2025', '05'): '15.05.2025', ('2025', '06'): '13.06.2025', ('2025', '08'): '15.08.2025', ('2025', '09'): '15.09.2025', ('2025', '10'): '15.10.2025', ('2025', '11'): '14.11.2025', ('2025', '12'): '15.12.2025',
            ('2026', '02'): '13.02.2026', ('2026', '03'): '13.03.2026', ('2026', '05'): '15.05.2026', ('2026', '06'): '15.06.2026', ('2026', '07'): '15.07.2026', ('2026', '09'): '15.09.2026', ('2026', '10'): '15.10.2026', ('2026', '11'): '13.11.2026', ('2026', '12'): '15.12.2026',
            ('2027', '01'): '15.01.2027', ('2027', '03'): '15.03.2027', ('2027', '04'): '15.04.2027', ('2027', '05'): '14.05.2027', ('2027', '06'): '15.06.2027', ('2027', '08'): '13.08.2027', ('2027', '09'): '15.09.2027', ('2027', '10'): '15.10.2027', ('2027', '11'): '15.11.2027', ('2027', '12'): '15.12.2027',
            ('2028', '02'): '15.02.2028', ('2028', '03'): '15.03.2028', ('2028', '04'): '14.04.2028', ('2028', '06'): '15.06.2028', ('2028', '07'): '14.07.2028', ('2028', '09'): '15.09.2028', ('2028', '10'): '13.10.2028', ('2028', '11'): '14.11.2028', ('2028', '12'): '15.12.2028'
        }
        
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
        shell.setCurrentCell(2, "TEXT")
        shell.selectedRows = "2"
        session.findById("wnd[1]/tbar[0]/btn[2]").press()
        time.sleep(1)

        if not inserir_matriculas(session, matriculas):
            return False, "Falha ao inserir matrículas no processo HQ."
        time.sleep(1)

        for mes, ano in iterar_meses(periodo['inicio'], periodo['fim']):
            data_bondt = bondt_lookup.get((ano, mes))
            
            if data_bondt is None:
                print(f"AVISO: Data BONDT não encontrada para {mes}/{ano}. Pulando este mês.")
                continue

            print(f"Processando HQ para {mes}/{ano} com BONDT {data_bondt}...")
            
            session.findById("wnd[0]/usr/txtPNPPABRP").text = mes
            session.findById("wnd[0]/usr/txtPNPPABRJ").text = ano
            session.findById("wnd[0]/usr/ctxtBONDT").text = data_bondt
            
            pasta_saida_periodo = os.path.join(pasta_saida_principal, "HPQ", f"HPQ - {int(mes)}.{ano}")
            os.makedirs(pasta_saida_periodo, exist_ok=True)
            session.findById("wnd[0]/usr/ctxtP_DIR").text = pasta_saida_periodo
            
            session.findById("wnd[0]/usr/chkP_BRANCH").selected = True
            session.findById("wnd[0]/usr/chkP_PDF").selected = True
            
            session.findById("wnd[0]/tbar[1]/btn[8]").press()
            time.sleep(2)
            
            session.findById("wnd[0]/tbar[0]/btn[3]").press()
            time.sleep(1)
            
        print("--- Processo 'HQ (Holerite Quinzenal)' finalizado. ---")
        return True, "Processo HQ concluído com sucesso."

    except Exception as e:
        print(f"ERRO no processo HQ: {e}")
        return False, f"Erro no processo HQ: {e}"

# --- Bloco de Teste ---
if __name__ == "__main__":
    # ... (bloco de teste para rodar de forma isolada) ...
    pass