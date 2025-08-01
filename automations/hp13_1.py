import time
import os
import pyperclip
from datetime import datetime

def execute(session, matriculas, periodo, options, base_path):
    """
    Executa a 1ª parcela do 13º. Usa o período de anos da interface
    e calcula a Data BONDT internamente.
    """
    print("--- Iniciando execução de HP 13.1 ---")
    try:
        ano_inicio, ano_fim = int(periodo['inicio'].split('/')[1]), int(periodo['fim'].split('/')[1])
    except:
        return False, "Erro: Período inválido."

    hoje = datetime.now().strftime("%d.%m")
    pasta_data = os.path.join(base_path, hoje)
    primeira_vez = True

    try:
        session.StartTransaction("PC00_M37_CEDT")
        time.sleep(1)
        session.findById("wnd[0]/tbar[1]/btn[17]").press()
        time.sleep(1)
        grid = session.findById("wnd[1]/usr/cntlALV_CONTAINER_1/shellcont/shell")
        grid.setCurrentCell(0, "TEXT")  # Variante 13. Sal. 1ª Parc
        grid.selectedRows = "0"
        session.findById("wnd[1]/tbar[0]/btn[2]").press()
        time.sleep(1)

        for ano_atual in range(ano_inicio, ano_fim + 1):
            print(f"  Processando 1ª parcela do 13º para o ano: {ano_atual}")
            
            # Lógica de data interna, idêntica ao VBA
            data_bondt_final = f"14.11.{ano_atual}"
            print(f"    Usando Data BONDT fixa: {data_bondt_final}")

            session.findById("wnd[0]/usr/txtPNPPABRP").text = "11" # Mês fixo
            session.findById("wnd[0]/usr/txtPNPPABRJ").text = str(ano_atual)
            session.findById("wnd[0]/usr/ctxtBONDT").text = data_bondt_final
            
            if primeira_vez:
                print("  Inserindo matrículas...")
                session.findById("wnd[0]/usr/btn%_PNPPERNR_%_APP_%-VALU_PUSH").press()
                time.sleep(1)
                pyperclip.copy("\n".join(matriculas))
                session.findById("wnd[1]/tbar[0]/btn[24]").press()
                time.sleep(0.5)
                session.findById("wnd[1]/tbar[0]/btn[8]").press()
                time.sleep(1)
                primeira_vez = False
            
            diretorio_saida = os.path.join(pasta_data, f"HP 13 - 01 {ano_atual}")
            if not os.path.exists(diretorio_saida):
                os.makedirs(diretorio_saida)
            session.findById("wnd[0]/usr/ctxtP_DIR").text = diretorio_saida
            session.findById("wnd[0]/usr/chkP_BRANCH").selected = True
            session.findById("wnd[0]/usr/chkP_PDF").selected = True
            session.findById("wnd[0]/tbar[1]/btn[8]").press()
            print("    Aguardando processamento...")
            time.sleep(5)
            session.findById("wnd[0]/tbar[0]/btn[3]").press()
            time.sleep(1)

        return True, "Processo HP 13.1 concluído."
    except Exception as e:
        return False, f"Erro em HP 13.1: {e}"