import win32com.client
import sys
import time

def connect_to_sap():
    """
    Tenta se conectar a uma sessão SAP GUI aberta.
    Retorna o objeto da sessão se for bem-sucedido, ou None se falhar.
    """
    try:
        print("Conectando ao SAP GUI...")
        SapGuiAuto = win32com.client.GetObject("SAPGUI")
        if not isinstance(SapGuiAuto, win32com.client.CDispatch):
            return None

        application = SapGuiAuto.GetScriptingEngine
        if not isinstance(application, win32com.client.CDispatch):
            return None

        connection = application.Children(0)
        if not isinstance(connection, win32com.client.CDispatch):
            return None
            
        session = connection.Children(0)
        if not isinstance(session, win32com.client.CDispatch):
            return None
            
        print("Conexão com SAP estabelecida com sucesso.")
        return session

    except Exception as e:
        print(f"ERRO: Não foi possível conectar ao SAP. Detalhes: {e}", file=sys.stderr)
        return None

# NOVO: Função centralizada para manter a conexão ativa
def keep_alive(session):
    """Envia um comando inofensivo para o SAP para evitar timeout por inatividade."""
    try:
        print("   Enviando sinal 'keep-alive' para manter a conexão SAP ativa...")
        # Lê o texto da barra de status, uma ação que não altera nada
        _ = session.findById("wnd[0]/sbar").text 
        print("   Sinal enviado com sucesso.")
        time.sleep(1) # Pequena pausa após o ping
    except Exception as e:
        print(f"   AVISO: Não foi possível enviar o sinal de keep-alive. A conexão pode ter caído. Erro: {e}")