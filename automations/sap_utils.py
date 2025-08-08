import win32com.client
import sys

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

        # Tenta pegar a primeira conexão e a primeira sessão
        connection = application.Children(0)
        if not isinstance(connection, win32com.client.CDispatch):
            return None
            
        session = connection.Children(0)
        if not isinstance(session, win32com.client.CDispatch):
            return None
            
        print("Conexão com SAP estabelecida com sucesso.")
        return session

    except Exception as e:
        print(f"ERRO: Não foi possível conectar ao SAP. Verifique se o SAP Logon está aberto. Detalhes: {e}", file=sys.stderr)
        return None