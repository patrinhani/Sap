import time, os, pyperclip
from datetime import datetime

# Tabela de datas interna, contendo apenas os dados relevantes para HQ, ZDP1 e ZDP2
TABELA_DATAS_INTERNA = {
    (6, 2021): "15.06.2021", (7, 2021): "15.07.2021", (8, 2021): "13.08.2021",
    (9, 2021): "15.09.2021", (10, 2021): "15.10.2021", (11, 2021): "12.11.2021",
    # ... cole o restante da mesma tabela do HQ.py aqui ...
    (12, 2025): "15.12.2025",
}

def execute(session, matriculas, periodo, options, base_path):
    print("--- Iniciando execução de ZDP2 ---")
    try:
        mes_inicio, ano_inicio = 8, 2024
        mes_fim, ano_fim = int(periodo['fim'].split('/')[0]), int(periodo['fim'].split('/')[1])
        if (ano_fim < 2024) or (ano_fim == 2024 and mes_fim < 8): return False, "Erro: Período final deve ser a partir de Agosto/2024."
    except: return False, "Erro: Período inválido."
    
    hoje = datetime.now().strftime("%d.%m")
    pasta_data = os.path.join(base_path, hoje)
    caminho_vba = os.path.join(pasta_data, "HPQ")
    primeira_vez_matriculas, primeira_vez_variante = True, True
    
    try:
        mes_atual, ano_atual = mes_inicio, ano_inicio
        while (ano_atual, mes_atual) <= (ano_fim, mes_fim):
            periodo_str = f"{str(mes_atual).zfill(2)}/{ano_atual}"
            print(f"  Processando período: {periodo_str}")
            
            if primeira_vez_variante:
                session.StartTransaction("PC00_M37_CEDT"); time.sleep(1)
                print("  Selecionando variante 'ZDP2' via busca...")
                session.findById("wnd[0]/tbar[1]/btn[17]").press(); time.sleep(1)
                session.findById("wnd[1]/usr/cntlALV_CONTAINER_1/shellcont/shell").pressToolbarButton("&FIND"); time.sleep(1)
                session.findById("wnd[2]/usr/txtGS_SEARCH-VALUE").text = "zdp2"
                session.findById("wnd[2]").sendVKey(0)
                session.findById("wnd[2]/tbar[0]/btn[12]").press(); time.sleep(0.5)
                session.findById("wnd[1]/usr/cntlALV_CONTAINER_1/shellcont/shell").doubleClickCurrentCell(); time.sleep(1)
                primeira_vez_variante = False

            # Busca a data na tabela interna
            data_bondt = TABELA_DATAS_INTERNA.get((mes_atual, ano_atual))
            if not data_bondt:
                return False, f"Erro: Data BONDT não encontrada para o período {periodo_str}. Verifique a tabela interna."
            
            print(f"    Usando Data BONDT: {data_bondt}")
            session.findById("wnd[0]/usr/radPNPTIMRA").select()
            session.findById("wnd[0]/usr/ctxtBONDT").text = data_bondt
            session.findById("wnd[0]/usr/ctxtPAYTY").text = "A"
            session.findById("wnd[0]/usr/txtPAYID").text = "A"
            session.findById("wnd[0]/usr/txtPNPPABRP").text = str(mes_atual)
            session.findById("wnd[0]/usr/txtPNPPABRJ").text = str(ano_atual)

            if primeira_vez_matriculas:
                print("  Inserindo matrículas...")
                session.findById("wnd[0]/usr/btn%_PNPPERNR_%_APP_%-VALU_PUSH").press(); time.sleep(1)
                pyperclip.copy("\n".join(matriculas))
                session.findById("wnd[1]/tbar[0]/btn[24]").press(); time.sleep(0.5)
                session.findById("wnd[1]/tbar[0]/btn[8]").press(); time.sleep(1)
                primeira_vez_matriculas = False

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
        
        return True, "Processo ZDP2 concluído."
    except Exception as e: return False, f"Erro em ZDP2: {e}"