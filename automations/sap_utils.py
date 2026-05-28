import win32com.client
import sys
import time

def allow_sapgui_security_prompt(timeout=5):
    """Autoriza o popup de seguranca do SAP GUI, marcando memorizar decisao."""
    try:
        import win32gui
        import win32con
        shell = win32com.client.Dispatch("WScript.Shell")
    except Exception as e:
        print(f"   AVISO: Nao foi possivel preparar popup SAPGUI: {e}")
        return False

    def find_sapgui_windows():
        windows = []

        def enum_handler(hwnd, _):
            try:
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    if "sapgui" in title.lower():
                        windows.append(hwnd)
            except Exception:
                pass
            return True

        win32gui.EnumWindows(enum_handler, None)
        return windows

    def click_child_by_text(hwnd, text_check, check_state=False):
        clicked = False

        def enum_child(child, _):
            nonlocal clicked
            try:
                text = win32gui.GetWindowText(child).strip().replace("&", "").lower()
                if text_check(text):
                    if check_state:
                        state = win32gui.SendMessage(child, win32con.BM_GETCHECK, 0, 0)
                        if state:
                            clicked = True
                            return False
                    win32gui.PostMessage(child, win32con.BM_CLICK, 0, 0)
                    clicked = True
                    return False
            except Exception:
                pass
            return True

        win32gui.EnumChildWindows(hwnd, enum_child, None)
        return clicked

    deadline = time.time() + timeout
    while time.time() < deadline:
        for hwnd in find_sapgui_windows():
            marcou_memorizar = click_child_by_text(
                hwnd,
                lambda text: "memorizar" in text or "remember" in text,
                check_state=True,
            )

            if not marcou_memorizar:
                try:
                    win32gui.SetForegroundWindow(hwnd)
                    time.sleep(0.2)
                    shell.SendKeys("%m")
                    time.sleep(0.2)
                except Exception:
                    pass

            if click_child_by_text(hwnd, lambda text: text in ("permitir", "allow")):
                print("   [LOG] Popup SAPGUI autorizado com memorizar decisao.")
                return True

            try:
                win32gui.SetForegroundWindow(hwnd)
                time.sleep(0.2)
                shell.SendKeys("%p")
                print("   [LOG] Popup SAPGUI autorizado por atalho Alt+P.")
                return True
            except Exception:
                pass

        time.sleep(0.2)

    return False

def start_sapgui_security_watcher(timeout=8):
    """Inicia uma thread para autorizar popup SAPGUI enquanto o SAP processa."""
    import threading

    watcher = threading.Thread(target=allow_sapgui_security_prompt, args=(timeout,), daemon=True)
    watcher.start()
    return watcher

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
