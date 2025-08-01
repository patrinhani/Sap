import time, os
from datetime import datetime
def execute(session, matriculas, periodo, options, base_path):
    print("--- Iniciando execução da Ficha Financeira ---")
    hoje = datetime.now().strftime("%d.%m")
    caminho_vba = os.path.join(base_path, hoje) # Salva na raiz da pasta da data
    if not os.path.exists(caminho_vba): os.makedirs(caminho_vba)
    empresas_para_testar = ["0021", "0029", "0004", "0049"]
    try:
        ano_inicio, ano_fim = int(periodo['inicio'].split('/')[1]), int(periodo['fim'].split('/')[1])
    except: return False, "Erro: Período inválido."
    arquivos_gerados = 0
    try:
        for matricula in matriculas:
            matricula = matricula.strip()
            if not matricula: continue
            print(f"Processando Matrícula: {matricula}")
            for ano in range(ano_inicio, ano_fim + 1):
                print(f"  Analisando Ano: {ano}")
                encontrou_empresa_valida = False
                for empresa in empresas_para_testar:
                    if encontrou_empresa_valida: break
                    print(f"    Tentando Empresa: {empresa}...")
                    session.StartTransaction("ZHCMTR0084"); time.sleep(1)
                    session.findById("wnd[0]/tbar[1]/btn[17]").press(); time.sleep(1)
                    session.findById("wnd[1]/usr/cntlALV_CONTAINER_1/shellcont/shell").selectedRows = "0"
                    session.findById("wnd[1]/tbar[0]/btn[2]").press(); time.sleep(1)
                    session.findById("wnd[0]/usr/ctxtPNPBEGDA").text = f"01.01.{ano}"
                    session.findById("wnd[0]/usr/ctxtPNPENDDA").text = f"31.12.{ano}"
                    session.findById("wnd[0]/usr/txtP_COMPE").text = str(ano)
                    session.findById("wnd[0]/usr/ctxtPNPBUKRS-LOW").text = empresa
                    session.findById("wnd[0]/usr/ctxtPNPPERNR-LOW").text = matricula
                    session.findById("wnd[0]/tbar[1]/btn[8]").press()
                    print("    Aguardando relatório..."); time.sleep(3)  
                    try:
                        session.findById("wnd[0]/tbar[1]/btn[46]")
                        print("    Exportando...")
                        session.findById("wnd[0]/tbar[1]/btn[46]").press()
                        session.findById("wnd[0]/tbar[1]/btn[45]").press(); time.sleep(1)
                        session.findById("wnd[1]/usr/subSUBSCREEN_STEPLOOP:SAPLSPO5:0150/sub:SAPLSPO5:0150/radSPOPLI-SELFLAG[3,0]").select()
                        session.findById("wnd[1]/tbar[0]/btn[0]").press(); time.sleep(1)
                        nome_arquivo = f"{matricula} - ff {str(ano)[-2:]}.html"
                        session.findById("wnd[1]/usr/ctxtDY_PATH").text = caminho_vba
                        session.findById("wnd[1]/usr/ctxtDY_FILENAME").text = nome_arquivo
                        session.findById("wnd[1]/tbar[0]/btn[0]").press()
                        arquivos_gerados += 1; encontrou_empresa_valida = True
                    except:
                        print(f"    Nenhum dado para {matricula}, Ano {ano}, Empresa {empresa}")
                        session.findById("wnd[0]").sendVKey(3)
        return True, f"Processo concluído! {arquivos_gerados} arquivo(s) gerado(s)."
    except Exception as e: return False, f"Erro em Ficha Financeira: {e}"