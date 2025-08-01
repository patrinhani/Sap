import time, os
from datetime import datetime
def execute(session, matriculas, periodo, options, base_path):
    print("--- Iniciando execução de CTPS Digital ---")
    hoje = datetime.now().strftime("%d.%m")
    pasta_data = os.path.join(base_path, hoje)
    caminho_vba = os.path.join(pasta_data, "CTPS")
    if not os.path.exists(caminho_vba): os.makedirs(caminho_vba)
    empresas_para_testar = ["0021", "0029", "0004", "0049"]
    processados_com_sucesso = 0; erros = 0
    try:
        for matricula in matriculas:
            matricula = matricula.strip()
            if not matricula: continue
            print(f"Processando matrícula: {matricula}")
            caminho_salvar_completo = os.path.join(caminho_vba, f" ctps sap - {matricula}")
            encontrou_empresa = False
            for codigo_empresa in empresas_para_testar:
                print(f"  Tentando com empresa: {codigo_empresa}...")
                session.StartTransaction("ZHCMTR0074"); time.sleep(1)
                session.findById("wnd[0]/tbar[1]/btn[17]").press(); time.sleep(1)
                try:
                    grid = session.findById("wnd[1]/usr/cntlALV_CONTAINER_1/shellcont/shell")
                    grid.currentCellRow = 2; grid.selectedRows = "2"
                    session.findById("wnd[1]/tbar[0]/btn[2]").press(); time.sleep(1)
                except: session.findById("wnd[1]").close(); time.sleep(1)
                session.findById("wnd[0]/usr/ctxtPNPPERNR-LOW").text = matricula
                session.findById("wnd[0]/usr/ctxtPNPBUKRS-LOW").text = codigo_empresa
                session.findById("wnd[0]/usr/ctxtP_CARR").text = caminho_salvar_completo
                session.findById("wnd[0]/tbar[1]/btn[8]").press(); time.sleep(0.5)
                if session.Children.Count > 1:
                    try:
                        popup = session.findById("wnd[1]")
                        popup.findById("usr/chkSSFPP-TDIMMED").selected = True
                        popup.findById("usr/ctxtSSFPP-TDDEST").text = "lp01"
                        popup.findById("wnd[1]/tbar[0]/btn[8]").press()
                        encontrou_empresa = True; processados_com_sucesso += 1
                    except: session.findById("wnd[1]").close()
                if encontrou_empresa: break
            if not encontrou_empresa: erros += 1
        mensagem_final = f"Concluído: {processados_com_sucesso} processadas, {erros} com erro."
        return True, mensagem_final
    except Exception as e: return False, f"Erro em CTPS Digital: {e}"