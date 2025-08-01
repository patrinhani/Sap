import time
import os
import pyperclip
from datetime import datetime

# Tabela de datas interna, contendo apenas os dados relevantes para HQ, ZDP1 e ZDP2
TABELA_DATAS_INTERNA = {
    (6, 2021): "15.06.2021", (7, 2021): "15.07.2021", (8, 2021): "13.08.2021",
    (9, 2021): "15.09.2021", (10, 2021): "15.10.2021", (11, 2021): "12.11.2021",
    (12, 2021): "15.12.2021", (1, 2022): "14.01.2022", (2, 2022): "15.02.2022",
    (3, 2022): "15.03.2022", (4, 2022): "14.04.2022", (5, 2022): "13.05.2022",
    (6, 2022): "15.06.2022", (7, 2022): "15.07.2022", (8, 2022): "15.08.2022",
    (9, 2022): "15.09.2022", (10, 2022): "14.10.2022", (11, 2022): "14.11.2022",
    (12, 2022): "15.12.2022", (1, 2023): "13.01.2023", (2, 2023): "15.02.2023",
    (3, 2023): "15.03.2023", (4, 2023): "14.04.2023", (5, 2023): "15.05.2023",
    (6, 2023): "15.06.2023", (7, 2023): "15.07.2023", (8, 2023): "15.08.2023",
    (9, 2023): "15.09.2023", (10, 2023): "13.10.2023", (11, 2023): "14.11.2023",
    (12, 2023): "15.12.2023", (1, 2024): "15.01.2024", (2, 2024): "15.02.2024",
    (3, 2024): "15.03.2024", (4, 2024): "15.04.2024", (5, 2024): "15.05.2024",
    (6, 2024): "14.06.2024", (7, 2024): "15.07.2024", (8, 2024): "15.08.2024",
    (9, 2024): "13.09.2024", (10, 2024): "15.10.2024", (11, 2024): "14.11.2024",
    (12, 2024): "15.12.2024", (1, 2025): "15.01.2025", (2, 2025): "14.02.2025",
    (3, 2025): "14.03.2025", (4, 2025): "15.04.2025", (5, 2025): "15.05.2025",
    (6, 2025): "13.06.2025", (7, 2025): "15.07.2025", (8, 2025): "15.08.2025",
    (9, 2025): "15.09.2025", (10, 2025): "15.10.2025", (11, 2025): "14.11.2025",
    (12, 2025): "15.12.2025",
    # ... adicione mais datas aqui se necessário
}

def execute(session, matriculas, periodo, options, base_path):
    print("--- Iniciando execução de HQ ---")
    try:
        mes_inicio, ano_inicio = int(periodo['inicio'].split('/')[0]), int(periodo['inicio'].split('/')[1])
        mes_fim, ano_fim = int(periodo['fim'].split('/')[0]), int(periodo['fim'].split('/')[1])
    except: return False, "Erro: Período inválido."
    
    hoje = datetime.now().strftime("%d.%m")
    pasta_data = os.path.join(base_path, hoje)
    caminho_vba = os.path.join(pasta_data, "HPQ")
    primeira_vez = True
    
    try:
        session.StartTransaction("PC00_M37_CEDT"); time.sleep(1)
        session.findById("wnd[0]/tbar[1]/btn[17]").press(); time.sleep(1)
        grid = session.findById("wnd[1]/usr/cntlALV_CONTAINER_1/shellcont/shell")
        grid.setCurrentCell(2, "TEXT"); grid.selectedRows = "2"
        session.findById("wnd[1]/tbar[0]/btn[2]").press(); time.sleep(1)
        
        mes_atual, ano_atual = mes_inicio, ano_inicio
        while (ano_atual, mes_atual) <= (ano_fim, mes_fim):
            periodo_str = f"{str(mes_atual).zfill(2)}/{ano_atual}"
            print(f"  Processando período: {periodo_str}")

            # Busca a data na tabela interna
            data_bondt = TABELA_DATAS_INTERNA.get((mes_atual, ano_atual))
            if not data_bondt:
                print(f"    AVISO: Data BONDT não encontrada para {periodo_str}. Campo ficará vazio.")
            else:
                print(f"    Usando Data BONDT: {data_bondt}")
                session.findById("wnd[0]/usr/ctxtBONDT").text = data_bondt

            session.findById("wnd[0]/usr/txtPNPPABRP").text = str(mes_atual)
            session.findById("wnd[0]/usr/txtPNPPABRJ").text = str(ano_atual)
            
            if primeira_vez:
                print("  Inserindo matrículas...")
                session.findById("wnd[0]/usr/btn%_PNPPERNR_%_APP_%-VALU_PUSH").press(); time.sleep(1)
                pyperclip.copy("\n".join(matriculas))
                session.findById("wnd[1]/tbar[0]/btn[24]").press(); time.sleep(0.5)
                session.findById("wnd[1]/tbar[0]/btn[8]").press(); time.sleep(1)
                primeira_vez = False

            diretorio_saida = os.path.join(caminho_vba, f"HPQ - {mes_atual}.{ano_atual}")
            if not os.path.exists(diretorio_saida): os.makedirs(diretorio_saida)
            session.findById("wnd[0]/usr/ctxtP_DIR").text = diretorio_saida
            session.findById("wnd[0]/usr/chkP_BRANCH").selected = True
            session.findById("wnd[0]/usr/chkP_PDF").selected = True
            session.findById("wnd[0]/tbar[1]/btn[8]").press()
            print("    Aguardando processamento..."); time.sleep(5)
            session.findById("wnd[0]/tbar[0]/btn[3]").press(); time.sleep(1)

            if mes_atual == 12: mes_atual, ano_atual = 1, ano_atual + 1
            else: mes_atual += 1
        
        return True, "Processo HQ concluído."
    except Exception as e: return False, f"Erro em HQ: {e}"