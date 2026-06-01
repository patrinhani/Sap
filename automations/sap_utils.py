import os
import win32com.client
import sys
import time
import threading

NOME_CONEXAO_SAP = "15. VIA ECP PRD Viavarejo"
SAP_CLIENTE = "100"
SAP_IDIOMA = "PT"
SAP_LOGON_PATHS = (
    r"C:\Program Files\SAP\FrontEnd\SAPgui\saplogon.exe",
    r"C:\Program Files (x86)\SAP\FrontEnd\SAPgui\saplogon.exe",
)

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
                    title_lower = title.lower()
                    title_compacto = title_lower.replace(" ", "")
                    if "sapgui" in title_compacto or ("sap" in title_lower and ("security" in title_lower or "segurança" in title_lower)):
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
    watcher = threading.Thread(target=allow_sapgui_security_prompt, args=(timeout,), daemon=True)
    watcher.start()
    return watcher


def monitorar_seguranca_sapgui(stop_event, intervalo=0.5):
    try:
        import pythoncom
        pythoncom.CoInitialize()
    except Exception:
        pythoncom = None

    try:
        while not stop_event.is_set():
            allow_sapgui_security_prompt(timeout=1)
            stop_event.wait(intervalo)
    finally:
        if pythoncom is not None:
            try:
                pythoncom.CoUninitialize()
            except Exception:
                pass


def iniciar_monitor_seguranca_sapgui(intervalo=0.5):
    """Mantem um monitor ativo para autorizar popups SAPGUI durante toda a automacao."""
    stop_event = threading.Event()
    monitor = threading.Thread(
        target=monitorar_seguranca_sapgui,
        args=(stop_event, intervalo),
        daemon=True,
    )
    monitor.start()
    return stop_event, monitor


def parar_monitor_seguranca_sapgui(stop_event, monitor):
    if stop_event is not None:
        stop_event.set()
    if monitor is not None:
        monitor.join(timeout=3)

def _obter_sap_gui():
    try:
        return win32com.client.GetObject("SAPGUI")
    except Exception:
        return None


def _obter_application_sap(timeout=15):
    limite = time.time() + timeout

    while time.time() < limite:
        SapGuiAuto = _obter_sap_gui()
        if SapGuiAuto is not None:
            try:
                return SapGuiAuto.GetScriptingEngine
            except Exception:
                pass

        time.sleep(1)

    return None


def _colecao(objeto, nome):
    try:
        return getattr(objeto, nome)
    except Exception:
        return None


def _quantidade(colecao):
    try:
        return int(colecao.Count)
    except Exception:
        return 0


def _item(colecao, indice):
    try:
        return colecao(indice)
    except Exception:
        return None


def _iterar_colecoes(objeto, nomes):
    for nome in nomes:
        colecao = _colecao(objeto, nome)
        if colecao is None:
            continue

        for indice in range(_quantidade(colecao)):
            item = _item(colecao, indice)
            if item is not None:
                yield item


def _obter_primeira_sessao(connection):
    return next(_iterar_colecoes(connection, ("Children", "Sessions")), None)


def _sessao_pronta(session):
    try:
        return not session.Busy
    except Exception:
        return False


def _sessao_acessivel(session):
    try:
        session.findById("wnd[0]")
        return True
    except Exception:
        return False


def _aguardar_sessao(connection, timeout=30):
    limite = time.time() + timeout
    ultimo_erro = None

    while time.time() < limite:
        try:
            session = _obter_primeira_sessao(connection)
            if session is not None and _sessao_pronta(session):
                return session
        except Exception as e:
            ultimo_erro = e

        time.sleep(1)

    raise RuntimeError(f"Nenhuma sessão SAP ficou pronta em {timeout} segundos. Último erro: {ultimo_erro}")


def _buscar_sessao_aberta(application):
    primeira_sessao = None
    sessao_login = None

    for connection in _iterar_colecoes(application, ("Children", "Connections")):
        for session in _iterar_colecoes(connection, ("Children", "Sessions")):
            if not _sessao_acessivel(session):
                continue
            if primeira_sessao is None:
                primeira_sessao = session
            if _tela_login_disponivel(session):
                if sessao_login is None:
                    sessao_login = session
                continue
            if _sessao_pronta(session):
                return session

    return sessao_login or primeira_sessao


def _tela_login_disponivel(session):
    try:
        session.findById("wnd[0]/usr/txtRSYST-MANDT")
        return True
    except Exception:
        return False


def _usuario_windows():
    try:
        return os.getlogin()
    except Exception:
        return os.environ.get("USERNAME", "")


def _texto_barra_status(session):
    try:
        return session.findById("wnd[0]/sbar").text
    except Exception:
        return ""


def _preencher_login(session, senha):
    if not senha:
        raise ValueError("Informe a senha do SAP para abrir uma nova sessão.")

    print("Preenchendo login do SAP...")
    session.findById("wnd[0]/usr/txtRSYST-MANDT").text = SAP_CLIENTE
    session.findById("wnd[0]/usr/txtRSYST-BNAME").text = _usuario_windows()
    session.findById("wnd[0]/usr/pwdRSYST-BCODE").text = senha
    session.findById("wnd[0]/usr/txtRSYST-LANGU").text = SAP_IDIOMA
    session.findById("wnd[0]").sendVKey(0)


def _aguardar_login_concluido(session, timeout=25):
    limite = time.time() + timeout

    while time.time() < limite:
        if _sessao_pronta(session) and not _tela_login_disponivel(session):
            return True
        time.sleep(1)

    detalhe = _texto_barra_status(session)
    if detalhe:
        raise RuntimeError(f"Login SAP não concluído: {detalhe}")
    raise RuntimeError("Login SAP não concluído dentro do tempo esperado.")


def _abrir_sap_logon():
    for caminho in SAP_LOGON_PATHS:
        if os.path.exists(caminho):
            os.startfile(caminho)
            print("Abrindo SAP Logon, aguarde...")
            return True

    try:
        os.startfile("saplogon.exe")
        print("Abrindo SAP Logon, aguarde...")
        return True
    except Exception:
        print("Caminho do SAP Logon não encontrado. Verifique a instalação.")
        return False


def verificar_sap_logado():
    try:
        application = _obter_application_sap(timeout=2)
        if application is None:
            return False

        for connection in _iterar_colecoes(application, ("Children", "Connections")):
            for session in _iterar_colecoes(connection, ("Children", "Sessions")):
                if not _tela_login_disponivel(session):
                    return True

        return False
    except Exception:
        return False


def iniciar_sap(senha=None, forcar_nova_sessao=False):
    application = _obter_application_sap(timeout=3)

    if application is not None:
        if not forcar_nova_sessao:
            session = _buscar_sessao_aberta(application)
            if session is not None:
                if _tela_login_disponivel(session):
                    print("SAP já está aberto aguardando login.")
                    _preencher_login(session, senha)
                    _aguardar_login_concluido(session)
                else:
                    print("SAP já está aberto. Usando a sessão existente.")
                return session

            print("SAP GUI já está aberto, mas sem sessão ativa. Abrindo conexão...")
        else:
            print("Reiniciando conexão SAP em uma nova sessão...")
    else:
        if not _abrir_sap_logon():
            return None

        application = _obter_application_sap(timeout=15)
        if application is None:
            raise RuntimeError("Não foi possível acessar o SAPGUI. Verifique se o SAP GUI Scripting está habilitado.")

    try:
        print(f"Iniciando a conexão com '{NOME_CONEXAO_SAP}'...")
        start_sapgui_security_watcher(timeout=10)
        connection = application.OpenConnection(NOME_CONEXAO_SAP, True)
        session = _aguardar_sessao(connection, timeout=30)

        if _tela_login_disponivel(session):
            _preencher_login(session, senha)
            _aguardar_login_concluido(session)

        return session
    except Exception:
        raise


def connect_to_sap(senha=None, levantar_erros=False, forcar_nova_sessao=False):
    """
    Conecta a uma sessão SAP já aberta ou abre o SAP Logon e faz login quando necessário.
    Retorna o objeto da sessão se for bem-sucedido, ou None se falhar.
    """
    try:
        print("Conectando ao SAP GUI...")
        session = iniciar_sap(senha, forcar_nova_sessao=forcar_nova_sessao)
        if session is None:
            return None

        print("Conexão com SAP estabelecida com sucesso.")
        return session

    except Exception as e:
        print(f"ERRO: Não foi possível conectar ao SAP. Detalhes: {e}", file=sys.stderr)
        if levantar_erros:
            raise
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
