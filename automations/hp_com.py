import time, os, pyperclip
from datetime import datetime
def execute(session, matriculas, periodo, options, base_path):
    print("--- Iniciando execução de HP-COM ---")
    try:
        mes_inicio, ano_inicio = int(periodo['inicio'].split('/')[0]), int(periodo['inicio'].split('/')[1])
        mes_fim, ano_fim = int(periodo['fim'].split('/')[0]), int(periodo['fim'].split('/')[1])
    except: return False, "Erro: Período inválido."
    hoje = datetime.now().strftime("%d.%m")
    pasta_data = os.path.join(base_path, hoje)
    caminho_vba = os.path.join(pasta_data, "HP")
    primeira_vez = True
    try:
        session.StartTransaction("PC00_M37_CEDT"); time.sleep(1)
        session.findById("wnd[0]/tbar[1]/btn[17]").press(); time.sleep(1)
        grid = session.findById("wnd[1]/usr/cntlALV_CONTAINER_1/shellcont/shell")
        grid.setCurrentCell(6, "TEXT"); grid.selectedRows = "6"
        session.findById("wnd[1]/tbar[0]/btn[2]").press(); time.sleep(1)
        mes_atual, ano_atual = mes_inicio, ano_inicio
        while (ano_atual, mes_atual) <= (ano_fim, mes_fim):
            if (ano_atual > 2022 and ano_atual < 2024) or (ano_atual == 2022 and mes_atual == 12) or (ano_atual == 2024 and mes_atual <= 7):
                print(f"  Processando período: {mes_atual}/{ano_atual}")
                session.findById("wnd[0]/usr/txtPNPPABRP").text = str(mes_atual)
                session.findById("wnd[0]/usr/txtPNPPABRJ").text = str(ano_atual)
                if primeira_vez:
                    print("  Inserindo matrículas...")
                    session.findById("wnd[0]/usr/btn%_PNPPERNR_%_APP_%-VALU_PUSH").press(); time.sleep(1)
                    pyperclip.copy("\n".join(matriculas))
                    session.findById("wnd[1]/tbar[0]/btn[24]").press(); time.sleep(0.5)
                    session.findById("wnd[1]/tbar[0]/btn[8]").press(); time.sleep(1)
                    primeira_vez = False
                diretorio_saida = os.path.join(caminho_vba, f"HP - {mes_atual}.{ano_atual}")
                if not os.path.exists(diretorio_saida): os.makedirs(diretorio_saida)
                session.findById("wnd[0]/usr/ctxtP_DIR").text = diretorio_saida
                session.findById("wnd[0]/usr/chkP_BRANCH").selected = True
                session.findById("wnd[0]/usr/chkP_PDF").selected = True
                session.findById("wnd[0]/tbar[1]/btn[8]").press()
                print("    Aguardando processamento..."); time.sleep(5)
                session.findById("wnd[0]/tbar[0]/btn[3]").press(); time.sleep(1)
            else: print(f"  Pulando período: {mes_atual}/{ano_atual}")
            if mes_atual == 12: mes_atual, ano_atual = 1, ano_atual + 1
            else: mes_atual += 1
        return True, "Processo HP-COM concluído."
    except Exception as e: return False, f"Erro em HP-COM: {e}"