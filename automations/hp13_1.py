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
    """Função auxiliar padrão. Não será usada diretamente pela lógica principal deste script."""
    pass

def inserir_matriculas_com_limpeza(session, matriculas):
    """Versão especial da função que limpa a seleção anterior, como no VBA."""
    try:
        session.findById("wnd[0]/usr/btn%_PNPPERNR_%_APP_%-VALU_PUSH").press()
        time.sleep(1)
        
        # NOVO PASSO: Clica no botão para limpar seleções anteriores
        session.findById("wnd[1]/tbar[0]/btn[16]").press() 
        time.sleep(1)

        # Reabre a janela para inserção
        session.findById("wnd[0]/usr/btn%_PNPPERNR_%_APP_%-VALU_PUSH").press()
        time.sleep(1)
        
        for i, matricula in enumerate(matriculas):
            session.findById("wnd[1]/usr/tabsTAB_STRIP/tabpSIVA/ssubSCREEN_HEADER:SAPLALDB:3010/tblSAPLALDBSINGLE/ctxtRSCSEL_255-SLOW_I[1,1]").text = matricula
            session.findById("wnd[1]/usr/tabsTAB_STRIP/tabpSIVA/ssubSCREEN_HEADER:SAPLALDB:3010/tblSAPLALDBSINGLE").verticalScrollbar.position = i + 1
            
        session.findById("wnd[1]/tbar[0]/btn[8]").press()
        return True
    except Exception as e:
        print(f"Erro ao inserir matrículas com limpeza: {e}")
        try: session.findById("wnd[1]/tbar[0]/btn[12]").press()
        except: pass
        return False

# --- Função Principal de Execução ---

def execute(session, matriculas, periodo, config, output_base_path):
    """Executa a 1ª Parcela do 13º Salário para os anos de 2021 a 2024."""
    try:
        print("--- Iniciando processo '13º Salário - 1ª Parcela' ---")
        
        # Tabela de consulta para a data BONDT. Usaremos a mesma que já temos.
        # O VBA original parece consultar uma lista diferente (colunas W,X,Y), mas a lógica de fallback é forte.
        # Manteremos a mesma lista para consistência, e o fallback será acionado se a data não estiver aqui.
        bondt_lookup = {
            ('2021', '11'): '12.11.2021', ('2022', '11'): '14.11.2022', ('2023', '11'): '14.11.2023', ('2024', '11'): '14.11.2024',
            # Adicionando outras datas da lista principal para o caso de existirem
            ('2025', '11'): '14.11.2025', ('2026', '11'): '13.11.2026', ('2027', '11'): '15.11.2027', ('2028', '11'): '14.11.2028'
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
        
        # Seleciona a variante da 1ª Parcela do 13º (linha 0)
        shell = session.findById("wnd[1]/usr/cntlALV_CONTAINER_1/shellcont/shell")
        shell.setCurrentCell(0, "TEXT")
        shell.selectedRows = "0"
        session.findById("wnd[1]/tbar[0]/btn[2]").press()
        time.sleep(1)

        # Insere as matrículas uma única vez, com a função que limpa o campo
        if not inserir_matriculas_com_limpeza(session, matriculas):
            return False, "Falha ao inserir matrículas no processo 13º Salário - 1ª Parcela."
        time.sleep(1)

        # ATENÇÃO: Loop fixo de anos, ignora o 'periodo' selecionado na interface
        for ano_atual in range(2021, 2025):
            print(f"Processando 1ª Parcela do 13º para o ano de {ano_atual}...")
            
            # Lógica para definir a data BONDT
            data_bondt = bondt_lookup.get((str(ano_atual), '11'))
            if data_bondt is None:
                # Lógica de fallback, como no VBA
                if ano_atual == 2021:
                    data_bondt = "12.11.2021"
                else: # 2022, 2023, 2024
                    data_bondt = f"14.11.{ano_atual}"
                print(f"AVISO: Data BONDT não encontrada na lista, usando valor padrão: {data_bondt}")
            
            # Preenche os campos fixos e variáveis
            session.findById("wnd[0]/usr/txtPNPPABRP").text = "11" # Mês é sempre 11
            session.findById("wnd[0]/usr/txtPNPPABRJ").text = str(ano_atual)
            session.findById("wnd[0]/usr/ctxtBONDT").text = data_bondt
            
            # Define o diretório de saída
            pasta_saida_ano = os.path.join(pasta_saida_principal, f"HP 13 - 01 {ano_atual}")
            os.makedirs(pasta_saida_ano, exist_ok=True)
            session.findById("wnd[0]/usr/ctxtP_DIR").text = pasta_saida_ano
            
            session.findById("wnd[0]/usr/chkP_BRANCH").selected = True
            session.findById("wnd[0]/usr/chkP_PDF").selected = True
            
            session.findById("wnd[0]/tbar[1]/btn[8]").press()
            
            while session.Busy:
                time.sleep(1)
            
            session.findById("wnd[0]/tbar[0]/btn[3]").press()
            time.sleep(1)
            
        print("--- Processo '13º Salário - 1ª Parcela' finalizado. ---")
        return True, "1ª Parcela do 13º Salário concluída com sucesso."

    except Exception as e:
        print(f"ERRO no processo 13º Salário - 1ª Parcela: {e}")
        return False, f"Erro no processo 13º Salário - 1ª Parcela: {e}"

# --- Bloco de Teste ---
if __name__ == "__main__":
    print(">>> MODO DE TESTE INDIVIDUAL DO SCRIPT 'hp13_1.py' <<<")
    
    matriculas_teste = ["00123456", "00654321"]
    # A variável 'periodo' é ignorada pela lógica principal, mas a mantemos por padrão
    periodo_teste = {"inicio": "01/2024", "fim": "12/2024"} 
    pasta_saida_teste = "C:/Temp/Testes_Automacao_SAP"
    
    print(f"Matrículas de teste: {matriculas_teste}")
    print(f"Período de teste: {periodo_teste} (será ignorado pelo script)")
    print(f"Pasta de saída: {pasta_saida_teste}")
    
    print("\nTentando conectar ao SAP...")
    sap_session = connect_to_sap()
    
    if sap_session:
        print("Conexão com SAP bem-sucedida. Iniciando a automação...")
        sucesso, mensagem = execute(
            session=sap_session,
            matriculas=matriculas_teste,
            periodo=periodo_teste,
            config={},
            output_base_path=pasta_saida_teste
        )
        print("\n--- RESULTADO DO TESTE ---")
        print(f"Status: {'SUCESSO' if sucesso else 'FALHA'}")
        print(f"Mensagem: {mensagem}")
        print("--------------------------")
    else:
        print("\nNão foi possível conectar ao SAP. Verifique se o SAP GUI está aberto.")