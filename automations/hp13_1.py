import time, os, pyperclip
from datetime import datetime

# Tabela de datas interna APENAS para o HP13.1, fiel à imagem
TABELA_DATAS_HP13_1 = {
    2021: "12.11.2021", 2022: "14.11.2022", 2023: "14.11.2023",
    2024: "14.11.2024", 2025: "14.11.2025", 2026: "13.11.2026",
    2027: "12.11.2027", 2028: "14.11.2028",
}

def execute(session, matriculas, periodo, options, base_path):
    print("--- Iniciando etapa: HP 13.1 ---")
    try:
        ano_inicio, ano_fim = int(periodo['inicio'].split('/')[1]), int(periodo['fim'].split('/')[1])
    except: return False, "Erro: Período inválido."
    
    hoje = datetime.now().strftime("%d.%m")
    pasta_data = os.path.join(base_path, hoje)
    primeira_vez = True
    
    try:
        print("  Selecionando variante '13. Sal. 1ª Parc'...")
        session.findById("wnd[0]/tbar[1]/btn[17]").press(); time.sleep(1)
        popup_variante = session.findById("wnd[1]")
        popup_variante.findById("usr/txtENAME-LOW").text = ""
        popup_variante.findById("tbar[0]/btn[8]").press(); time.sleep(1)
        grid = popup_variante.findById("usr/cntlALV_CONTAINER_1/shellcont/shell")
        grid.setCurrentCell(0, "TEXT"); grid.selectedRows = "0"
        popup_variante.findById("tbar[0]/btn[2]").press(); time.sleep(1)

        for ano_atual in range(ano_inicio, ano_fim + 1):
            print(f"  Processando 1ª parcela do 13º para o ano: {ano_atual}")
            
            data_bondt = TABELA_DATAS_HP13_1.get(ano_atual)
            if not data_bondt:
                return False, f"Data BONDT não encontrada para HP13.1 no ano {ano_atual}."
            
            print(f"    Usando Data BONDT: {data_bondt}")
            session.findById("wnd[0]/usr/txtPNPPABRP").text = "11"
            session.findById("wnd[0]/usr/txtPNPPABRJ").text = str(ano_atual)
            session.findById("wnd[0]/usr/ctxtBONDT").text = data_bondt
            
            if primeira_vez:
                print("  Inserindo matrículas...")
                session.findById("wnd[0]/usr/btn%_PNPPERNR_%_APP_%-VALU_PUSH").press(); time.sleep(1)
                pyperclip.copy("\n".join(matriculas))
                session.findById("wnd[1]/tbar[0]/btn[24]").press(); time.sleep(0.5)
                session.findById("wnd[1]/tbar[0]/btn[8]").press(); time.sleep(1)
                primeira_vez = False
            
            diretorio_saida = os.path.join(pasta_data, f"HP 13 - 01 {ano_atual}")
            if not os.path.exists(diretorio_saida): os.makedirs(diretorio_saida)
            session.findById("wnd[0]/usr/ctxtP_DIR").text = diretorio_saida
            session.findById("wnd[0]/usr/chkP_BRANCH").selected = True
            session.findById("wnd[0]/usr/chkP_PDF").selected = True
            session.findById("wnd[0]/tbar[1]/btn[8]").press()
            print("    Aguardando processamento..."); time.sleep(5)
            session.findById("wnd[0]/tbar[0]/btn[3]").press(); time.sleep(1)

        return True, "Etapa HP 13.1 concluída."
    except Exception as e: return False, f"Erro em HP 13.1: {e}"