import win32com.client
def connect_to_sap():
    try:
        SapGuiAuto = win32com.client.GetObject("SAPGUI")
        application = SapGuiAuto.GetScriptingEngine
        connection = application.Children(0)
        session = connection.Children(0)
        print("Conexão com SAP estabelecida com sucesso.")
        return session
    except Exception as e:
        print(f"Erro ao conectar com o SAP: {e}")
        return None