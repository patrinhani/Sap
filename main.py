import contextlib
import importlib
import json
import os
import re
import sys
import time
from datetime import datetime

from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QFont, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QStyle,
    QTabWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from icon_utils import ensure_app_icon


def app_base_path():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = app_base_path()
    return os.path.join(base_path, relative_path)


def app_config_path(filename):
    base_path = app_base_path()
    if os.access(base_path, os.W_OK):
        return os.path.join(base_path, filename)

    return app_data_path(filename)


def app_data_path(filename):
    appdata = os.environ.get("APPDATA") or os.path.expanduser("~")
    return os.path.join(appdata, "SapAutomacao", filename)


def app_icon_path():
    icon_path = resource_path(os.path.join("assets", "gcb_icone.ico"))
    if os.path.exists(icon_path):
        return icon_path
    return ensure_app_icon(app_base_path())


MOCK_MODE = False


def sap_util(function_name):
    module = importlib.import_module("automations.sap_utils")
    return getattr(module, function_name)


def connect_to_sap(*args, **kwargs):
    return sap_util("connect_to_sap")(*args, **kwargs)


def keep_alive(*args, **kwargs):
    return sap_util("keep_alive")(*args, **kwargs)


def iniciar_monitor_seguranca_sapgui(*args, **kwargs):
    return sap_util("iniciar_monitor_seguranca_sapgui")(*args, **kwargs)


def parar_monitor_seguranca_sapgui(*args, **kwargs):
    return sap_util("parar_monitor_seguranca_sapgui")(*args, **kwargs)


def lazy_execute(module_name):
    def execute(*args, **kwargs):
        module = importlib.import_module(f"automations.{module_name}")
        return module.execute(*args, **kwargs)

    return execute


PROCESS_MAP = {
    "HP Holerite": lazy_execute("hp"),
    "HQ Holerite": lazy_execute("hq"),
    "ZDP1 Holerite": lazy_execute("zdp1_worker"),
    "13º Salário": lazy_execute("decimo_terceiro"),
    "PLRs": lazy_execute("plrs"),
    "CTPS Digital": lazy_execute("ctps_digital"),
    "Ficha Financeira": lazy_execute("ficha_financeira"),
    "HP Individual (Off-Cycle)": lazy_execute("hp_individual"),
    "1ª Parcela 13º": lazy_execute("hp13_1"),
    "2ª Parcela 13º": lazy_execute("hp13_2"),
    "HP-COM": lazy_execute("hp_com"),
    "ZDP1": lazy_execute("zdp1"),
    "ZDP2": lazy_execute("zdp2"),
}

SEQUENCES = {
    "HP": ["HP Completo"],
    "HQ": ["HQ Completo"],
    "HP Completo": ["HP Holerite", "ZDP1 Holerite", "HP-COM"],
    "HQ Completo": ["HQ Holerite", "ZDP2"],
    "HP+HQ": ["HP Completo", "HQ Completo"],
    "13º Salário Completo": ["13º Salário"],
    "PLRs Normal": ["PLRs"],
    "Ficha Financeira": ["Ficha Financeira"],
    "CTPS Digital": ["CTPS Digital"],
    "HP Individual": ["HP Individual (Off-Cycle)"],
    "1ª Parcela 13º": ["1ª Parcela 13º"],
    "2ª Parcela 13º": ["2ª Parcela 13º"],
    "HP-COM": ["HP-COM"],
    "ZDP1": ["ZDP1"],
    "ZDP2": ["ZDP2"],
    "Massa Completa de Holerites": ["HP Completo", "HQ Completo", "13º Salário", "PLRs"],
    "Ficha + CTPS": ["Ficha Financeira", "CTPS Digital"],
    "EXECUTAR TUDO": [
        "Massa Completa de Holerites",
        "Ficha Financeira",
        "CTPS Digital",
        "HP Individual (Off-Cycle)",
    ],
}

PROCESS_GROUPS = [
    (
        "Holerites",
        [
            ("HP Completo", "HP"),
            ("HQ Completo", "HQ"),
            ("HP + HQ", "HP+HQ"),
            ("HP-COM", "HP-COM"),
            ("Massa Completa", "Massa Completa de Holerites"),
        ],
    ),
    (
        "Anuais",
        [
            ("13º Salário", "13º Salário Completo"),
            ("1ª Parcela 13º", "1ª Parcela 13º"),
            ("2ª Parcela 13º", "2ª Parcela 13º"),
            ("PLRs", "PLRs Normal"),
        ],
    ),
    (
        "Documentos",
        [
            ("Ficha Financeira", "Ficha Financeira"),
            ("CTPS Digital", "CTPS Digital"),
            ("Ficha + CTPS", "Ficha + CTPS"),
            ("HP Individual", "HP Individual"),
            ("ZDP1", "ZDP1"),
            ("ZDP2", "ZDP2"),
        ],
    ),
]

MAX_TENTATIVAS_PROCESSO = 4
RETRY_DELAY_SECONDS = 60
CHECKPOINT_FILE_NAME = ".sap_automacao_checkpoint.json"
PROCESSOS_RETOMADA_POR_MATRICULA = {
    "CTPS Digital",
    "Ficha Financeira",
    "HP Individual (Off-Cycle)",
    "HP-COM",
    "1ª Parcela 13º",
    "2ª Parcela 13º",
}

CONFIG_FILE = app_config_path("config.json")


def checkpoint_path(output_base_path):
    return os.path.join(output_base_path, CHECKPOINT_FILE_NAME)


def global_checkpoint_path():
    return app_data_path(CHECKPOINT_FILE_NAME)


def read_checkpoint_file(path):
    if not path or not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
        if isinstance(data, dict):
            data["_checkpoint_file"] = path
            return data
    except Exception:
        return None
    return None


def checkpoint_updated_at(checkpoint):
    try:
        return datetime.fromisoformat(checkpoint.get("updated_at", ""))
    except Exception:
        return datetime.min


def load_checkpoint(output_base_path=None):
    candidates = []

    global_checkpoint = read_checkpoint_file(global_checkpoint_path())
    if global_checkpoint:
        candidates.append(global_checkpoint)

    if output_base_path:
        local_checkpoint = read_checkpoint_file(checkpoint_path(output_base_path))
        if local_checkpoint:
            candidates.append(local_checkpoint)

    if not candidates:
        return None

    return max(candidates, key=checkpoint_updated_at)


def save_checkpoint(output_base_path, data):
    data = dict(data)
    data["output_base_path"] = output_base_path

    targets = [global_checkpoint_path()]
    if output_base_path:
        targets.append(checkpoint_path(output_base_path))

    for path in dict.fromkeys(targets):
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
        except Exception:
            pass


def clear_checkpoint(output_base_path=None):
    global_checkpoint = read_checkpoint_file(global_checkpoint_path())
    checkpoint_output_path = output_base_path
    if global_checkpoint and global_checkpoint.get("output_base_path"):
        checkpoint_output_path = global_checkpoint.get("output_base_path")

    paths = [global_checkpoint_path()]
    if checkpoint_output_path:
        paths.append(checkpoint_path(checkpoint_output_path))
    if output_base_path and output_base_path != checkpoint_output_path:
        paths.append(checkpoint_path(output_base_path))

    for path in dict.fromkeys(paths):
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass


def expandir_sequencia(sequence_name):
    pendentes = list(SEQUENCES.get(sequence_name, []))
    finais = []

    while pendentes:
        tarefa = pendentes.pop(0)
        if tarefa in SEQUENCES and tarefa not in PROCESS_MAP:
            pendentes[0:0] = SEQUENCES.get(tarefa, [])
        else:
            finais.append(tarefa)

    return list(dict.fromkeys(finais))


class ProgressBridge:
    def __init__(self, signal):
        self.signal = signal

    def put(self, msg):
        self.signal.emit(msg)

    def log(self, text):
        text = text.rstrip()
        if text:
            self.put({"type": "log", "msg": text})


class LogWriter:
    def __init__(self, bridge):
        self.bridge = bridge

    def write(self, text):
        for line in text.splitlines():
            if line.strip():
                self.bridge.log(line)

    def flush(self):
        pass


class ResumeProgressTracker:
    def __init__(self, queue_destino, matriculas, state=None, on_update=None):
        state = state or {}
        self.queue_destino = queue_destino
        self.matriculas_originais = list(matriculas)
        self.matriculas_set = set(self.matriculas_originais)
        self.completed_task_ids = set(state.get("completed_task_ids", []))
        self.current_task_id = state.get("current_task_id")
        self.on_update = on_update

    def put(self, msg):
        changed = False
        if isinstance(msg, dict):
            tipo = msg.get("type")
            if tipo == "task_update":
                task_id = str(msg.get("task_id", "")).strip()
                status = str(msg.get("status", "")).lower()
                if task_id:
                    self.current_task_id = task_id
                    changed = True
                    if "concluido" in status or "concluído" in status:
                        self.completed_task_ids.add(task_id)
                        changed = True
            elif tipo == "task_list":
                self.current_task_id = None
                changed = True

        self.queue_destino.put(msg)
        if changed and self.on_update is not None:
            self.on_update(self.snapshot())

    def snapshot(self):
        return {
            "completed_task_ids": sorted(self.completed_task_ids),
            "current_task_id": self.current_task_id,
        }

    def should_skip(self, task_id):
        return str(task_id).strip() in self.completed_task_ids

    def matriculas_pendentes(self):
        concluidas = self.completed_task_ids & self.matriculas_set
        if not concluidas:
            return list(self.matriculas_originais)
        return [matricula for matricula in self.matriculas_originais if matricula not in concluidas]

    def resumo_retomada(self):
        concluidas = len(self.completed_task_ids & self.matriculas_set)
        total = len(self.matriculas_originais)
        if self.current_task_id:
            return f"último item detectado: {self.current_task_id}; matrículas concluídas: {concluidas}/{total}"
        return f"matrículas concluídas: {concluidas}/{total}"


class AutomationWorker(QThread):
    progress = pyqtSignal(dict)
    done = pyqtSignal(bool, str)

    def __init__(self, sequence_name, matriculas, periodo, config, output_base_path, sap_password, resume_checkpoint=None):
        super().__init__()
        self.sequence_name = sequence_name
        self.matriculas = list(matriculas)
        self.periodo = dict(periodo)
        self.config = dict(config)
        self.output_base_path = output_base_path
        self.sap_password = sap_password
        self.resume_checkpoint = resume_checkpoint or {}
        self.completed_processes = set(self.resume_checkpoint.get("completed_processes", []))
        self.current_process_state = self.resume_checkpoint.get("current_process_state", {})
        self.current_process = self.resume_checkpoint.get("current_process")
        self.tarefas = []
        self.bridge = ProgressBridge(self.progress)

    def run(self):
        pythoncom = None
        stop_event = None
        monitor = None

        try:
            try:
                import pythoncom as pythoncom_mod
                pythoncom = pythoncom_mod
                pythoncom.CoInitialize()
            except Exception:
                pythoncom = None

            stop_event, monitor = iniciar_monitor_seguranca_sapgui()
            writer = LogWriter(self.bridge)

            with contextlib.redirect_stdout(writer), contextlib.redirect_stderr(writer):
                if not self.sap_password:
                    raise ValueError("Senha SAP não informada. Ela é necessária para login e reconexão automática.")
                self.bridge.put({"type": "status", "geral": "Conectando ao SAP", "detalhe": ""})
                session = connect_to_sap(self.sap_password, levantar_erros=True)

                if session is None and not MOCK_MODE:
                    raise ConnectionError("Falha na conexão com o SAP. Verifique se o SAP GUI está aberto e logado.")

                self.tarefas = expandir_sequencia(self.sequence_name)
                if not self.tarefas:
                    raise ValueError(f"Sequência desconhecida: {self.sequence_name}")

                total = len(self.tarefas)
                self._save_checkpoint()
                for indice, processo_nome in enumerate(self.tarefas, start=1):
                    if processo_nome in self.completed_processes:
                        self.bridge.put({
                            "type": "status",
                            "geral": f"Etapa {indice}/{total}: {processo_nome}",
                            "detalhe": "Já concluída no checkpoint. Pulando.",
                            "progresso_geral": ((indice - 1) / total) * 100,
                        })
                        continue

                    self.current_process = processo_nome
                    self.current_process_state = {}
                    self._save_checkpoint()
                    progresso = ((indice - 1) / total) * 100
                    self.bridge.put({
                        "type": "status",
                        "geral": f"Etapa {indice}/{total}: {processo_nome}",
                        "detalhe": "Iniciando",
                        "progresso_geral": progresso,
                    })

                    funcao = PROCESS_MAP.get(processo_nome)
                    if not funcao:
                        self.bridge.log(f"AVISO: Processo '{processo_nome}' não encontrado.")
                        continue

                    session = self._executar_processo_com_retomada(processo_nome, funcao, session)
                    self.completed_processes.add(processo_nome)
                    self.current_process_state = {}
                    self._save_checkpoint()
                    try:
                        keep_alive(session)
                    except Exception:
                        pass

                self.bridge.put({"type": "status", "geral": "Concluído", "detalhe": ""})
                self.bridge.put({"type": "success", "msg": f"Sequência '{self.sequence_name}' concluída."})
                clear_checkpoint(self.output_base_path)
                self.done.emit(True, f"Sequência '{self.sequence_name}' concluída.")
        except Exception as e:
            self.bridge.put({"type": "error", "msg": str(e)})
            self.done.emit(False, str(e))
        finally:
            parar_monitor_seguranca_sapgui(stop_event, monitor)
            if pythoncom is not None:
                try:
                    pythoncom.CoUninitialize()
                except Exception:
                    pass

    def _executar_processo_com_retomada(self, processo_nome, funcao, session):
        tracker_state = self.current_process_state if self.current_process == processo_nome else {}
        tracker = ResumeProgressTracker(
            self.bridge,
            self.matriculas,
            state=tracker_state,
            on_update=self._update_current_process_state,
        )
        ultima_mensagem = ""

        for tentativa in range(1, MAX_TENTATIVAS_PROCESSO + 1):
            try:
                if tentativa > 1:
                    self._wait_before_retry(processo_nome, tentativa, tracker)
                    self.bridge.put({
                        "type": "status",
                        "geral": f"Reconectando SAP para {processo_nome}",
                        "detalhe": f"Tentativa {tentativa}/{MAX_TENTATIVAS_PROCESSO}: abrindo nova sessão e refazendo login.",
                    })
                    session = connect_to_sap(
                        self.sap_password,
                        levantar_erros=True,
                        forcar_nova_sessao=True,
                    )

                if processo_nome in PROCESSOS_RETOMADA_POR_MATRICULA:
                    matriculas_tentativa = tracker.matriculas_pendentes()
                    if not matriculas_tentativa:
                        self.bridge.put({
                            "type": "status",
                            "detalhe": f"{processo_nome}: itens concluídos detectados. Avançando.",
                        })
                        return session
                else:
                    matriculas_tentativa = list(self.matriculas)

                sucesso, mensagem = funcao(
                    session,
                    matriculas_tentativa,
                    self.periodo,
                    self.config,
                    self.output_base_path,
                    progress_queue=tracker,
                )
                if sucesso:
                    return session

                ultima_mensagem = mensagem
                raise RuntimeError(mensagem)
            except Exception as e:
                ultima_mensagem = str(e)
                self._update_current_process_state(tracker.snapshot())
                if tentativa >= MAX_TENTATIVAS_PROCESSO:
                    raise RuntimeError(f"Erro em '{processo_nome}' após retomada automática: {ultima_mensagem}") from e

                self.bridge.put({
                    "type": "status",
                    "geral": f"Falha em {processo_nome}",
                    "detalhe": f"Retomada automática preparada: {tracker.resumo_retomada()}",
                })

        return session

    def _wait_before_retry(self, processo_nome, tentativa, tracker):
        remaining = RETRY_DELAY_SECONDS
        while remaining > 0:
            self.bridge.put({
                "type": "status",
                "geral": f"Aguardando retomada de {processo_nome}",
                "detalhe": (
                    f"Nova tentativa {tentativa}/{MAX_TENTATIVAS_PROCESSO} em {remaining}s. "
                    f"{tracker.resumo_retomada()}"
                ),
            })
            sleep_for = min(5, remaining)
            time.sleep(sleep_for)
            remaining -= sleep_for

    def _update_current_process_state(self, state):
        self.current_process_state = dict(state)
        self._save_checkpoint()

    def _save_checkpoint(self):
        data = {
            "version": 1,
            "updated_at": datetime.now().isoformat(timespec="seconds"),
            "sequence_name": self.sequence_name,
            "periodo": self.periodo,
            "config": self.config,
            "matriculas": self.matriculas,
            "tarefas": self.tarefas,
            "completed_processes": sorted(self.completed_processes),
            "current_process": self.current_process,
            "current_process_state": self.current_process_state,
        }
        save_checkpoint(self.output_base_path, data)


class SapAutomationWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.worker = None
        self.output_base_path = ""
        self.progress_items = {}
        self.action_buttons = []
        self.form_buttons = []
        self.nav_buttons = []
        self.resume_nav_button = None
        self.resume_pulse_on = False
        self.resume_attention_timer = QTimer(self)
        self.resume_attention_timer.setInterval(700)
        self.resume_attention_timer.timeout.connect(self.toggle_resume_attention)

        now = datetime.now()
        self.years = [str(i) for i in range(now.year - 5, now.year + 5)]
        self.months = [f"{i:02d}" for i in range(1, 13)]

        self.setWindowTitle("Painel de Automação SAP")
        self.setMinimumSize(1180, 720)
        icon_path = app_icon_path()
        if icon_path:
            self.setWindowIcon(QIcon(icon_path))

        self._build_ui()
        self._apply_style()
        self.load_config()
        self.update_matricula_count()
        self.update_resume_status()

    def standard_icon(self, name):
        pixmap = getattr(QStyle.StandardPixmap, name, None)
        if pixmap is None:
            return QIcon()
        return self.style().standardIcon(pixmap)

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)

        main_layout = QHBoxLayout(root)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        sidebar = self._build_sidebar()
        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_execution_page())
        self.stack.addWidget(self._build_progress_page())
        self.stack.addWidget(self._build_resume_page())
        self.stack.addWidget(self._build_settings_page())

        main_layout.addWidget(sidebar)
        main_layout.addWidget(self.stack, 1)

    def _build_sidebar(self):
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(238)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(18, 22, 18, 18)
        layout.setSpacing(10)

        title = QLabel("SAP Automação")
        title.setObjectName("sidebarTitle")
        subtitle = QLabel("Operações de folha")
        subtitle.setObjectName("sidebarSubtitle")

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(18)

        nav_items = [
            ("Execução", "SP_MediaPlay", 0),
            ("Progresso", "SP_FileDialogDetailedView", 1),
            ("Retomada", "SP_BrowserReload", 2),
            ("Ajustes", "SP_FileDialogInfoView", 3),
        ]

        for label, icon_name, index in nav_items:
            button = QPushButton(label)
            button.setObjectName("navButton")
            button.setCheckable(True)
            button.setIcon(self.standard_icon(icon_name))
            button.clicked.connect(lambda checked=False, idx=index: self.show_page(idx))
            layout.addWidget(button)
            self.nav_buttons.append(button)
            if label == "Retomada":
                self.resume_nav_button = button

        layout.addStretch()

        self.status_badge = QLabel("Pronto")
        self.status_badge.setObjectName("statusBadge")
        self.status_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_badge)

        self.nav_buttons[0].setChecked(True)
        return sidebar

    def _build_execution_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(16)

        header = self._section_header("Controle de Execução", "Parâmetros e rotinas")
        layout.addWidget(header)

        top_grid = QGridLayout()
        top_grid.setHorizontalSpacing(14)
        top_grid.setVerticalSpacing(14)

        output_panel = self._panel("Saída")
        output_layout = QHBoxLayout(output_panel)
        output_layout.setContentsMargins(14, 16, 14, 14)
        output_layout.setSpacing(10)
        self.output_input = QLineEdit()
        self.output_input.setReadOnly(True)
        self.output_input.setPlaceholderText("Nenhuma pasta selecionada")
        choose_folder = QPushButton("Selecionar")
        choose_folder.setIcon(self.standard_icon("SP_DirOpenIcon"))
        choose_folder.clicked.connect(self.select_output_folder)
        open_folder = QPushButton("Abrir")
        open_folder.setObjectName("secondaryButton")
        open_folder.setIcon(self.standard_icon("SP_DialogOpenButton"))
        open_folder.clicked.connect(self.open_output_folder)
        self.form_buttons.extend([choose_folder, open_folder])
        output_layout.addWidget(self.output_input, 1)
        output_layout.addWidget(choose_folder)
        output_layout.addWidget(open_folder)

        login_panel = self._panel("Login SAP")
        login_layout = QHBoxLayout(login_panel)
        login_layout.setContentsMargins(14, 16, 14, 14)
        login_layout.setSpacing(10)
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Senha SAP")
        self.show_password_check = QCheckBox("Mostrar")
        self.show_password_check.toggled.connect(self.toggle_password_visibility)
        login_layout.addWidget(self.password_input, 1)
        login_layout.addWidget(self.show_password_check)

        period_panel = self._panel("Período")
        period_layout = QGridLayout(period_panel)
        period_layout.setContentsMargins(14, 16, 14, 14)
        period_layout.setHorizontalSpacing(8)
        period_layout.setVerticalSpacing(8)
        self.start_month_combo = QComboBox()
        self.start_year_combo = QComboBox()
        self.end_month_combo = QComboBox()
        self.end_year_combo = QComboBox()
        for combo in (self.start_month_combo, self.end_month_combo):
            combo.addItems(self.months)
        for combo in (self.start_year_combo, self.end_year_combo):
            combo.addItems(self.years)
        period_layout.addWidget(QLabel("Início"), 0, 0)
        period_layout.addWidget(self.start_month_combo, 0, 1)
        period_layout.addWidget(self.start_year_combo, 0, 2)
        period_layout.addWidget(QLabel("Fim"), 1, 0)
        period_layout.addWidget(self.end_month_combo, 1, 1)
        period_layout.addWidget(self.end_year_combo, 1, 2)

        ficha_panel = self._panel("Ficha Financeira")
        ficha_layout = QVBoxLayout(ficha_panel)
        ficha_layout.setContentsMargins(14, 16, 14, 14)
        self.ficha_type_combo = QComboBox()
        self.ficha_type_combo.addItems(["HTML (Layout Padrão)", "PDF (Exportação Direta)"])
        ficha_layout.addWidget(self.ficha_type_combo)

        top_grid.addWidget(output_panel, 0, 0, 1, 2)
        top_grid.addWidget(login_panel, 0, 2)
        top_grid.addWidget(period_panel, 1, 0)
        top_grid.addWidget(ficha_panel, 1, 1, 1, 2)
        top_grid.setColumnStretch(0, 1)
        top_grid.setColumnStretch(1, 1)
        top_grid.setColumnStretch(2, 1)
        layout.addLayout(top_grid)

        content_grid = QGridLayout()
        content_grid.setHorizontalSpacing(16)
        content_grid.setColumnStretch(0, 3)
        content_grid.setColumnStretch(1, 2)

        matriculas_panel = self._panel("Matrículas")
        matriculas_layout = QVBoxLayout(matriculas_panel)
        matriculas_layout.setContentsMargins(14, 16, 14, 14)
        matriculas_layout.setSpacing(10)
        self.matriculas_text = QPlainTextEdit()
        self.matriculas_text.setPlaceholderText("Matrículas")
        self.matriculas_text.setMinimumHeight(220)
        self.matriculas_text.textChanged.connect(self.update_matricula_count)
        matriculas_actions = QHBoxLayout()
        self.matricula_count_label = QLabel("0 matrículas")
        paste_button = QPushButton("Colar")
        paste_button.setObjectName("secondaryButton")
        paste_button.setIcon(self.standard_icon("SP_FileDialogContentsView"))
        paste_button.clicked.connect(self.paste_matriculas)
        normalize_button = QPushButton("Organizar")
        normalize_button.setObjectName("secondaryButton")
        normalize_button.setIcon(self.standard_icon("SP_BrowserReload"))
        normalize_button.clicked.connect(self.normalize_matriculas)
        clear_button = QPushButton("Limpar")
        clear_button.setObjectName("secondaryButton")
        clear_button.setIcon(self.standard_icon("SP_DialogResetButton"))
        clear_button.clicked.connect(self.matriculas_text.clear)
        self.form_buttons.extend([paste_button, normalize_button, clear_button])
        matriculas_actions.addWidget(self.matricula_count_label)
        matriculas_actions.addStretch()
        matriculas_actions.addWidget(paste_button)
        matriculas_actions.addWidget(normalize_button)
        matriculas_actions.addWidget(clear_button)
        matriculas_layout.addWidget(self.matriculas_text, 1)
        matriculas_layout.addLayout(matriculas_actions)

        processes_panel = self._panel("Rotinas")
        processes_layout = QVBoxLayout(processes_panel)
        processes_layout.setContentsMargins(14, 16, 14, 14)
        processes_layout.setSpacing(10)
        self.process_tabs = QTabWidget()
        self.process_tabs.setDocumentMode(True)

        for group_name, actions in PROCESS_GROUPS:
            tab = QWidget()
            tab_layout = QVBoxLayout(tab)
            tab_layout.setContentsMargins(0, 12, 0, 0)
            tab_layout.setSpacing(8)
            for label, sequence in actions:
                button = QPushButton(label)
                button.setMinimumHeight(42)
                button.setIcon(self.standard_icon("SP_MediaPlay"))
                button.clicked.connect(lambda checked=False, seq=sequence: self.start_automation(seq))
                tab_layout.addWidget(button)
                self.action_buttons.append(button)
            tab_layout.addStretch()
            self.process_tabs.addTab(tab, group_name)

        self.run_all_button = QPushButton("EXECUTAR TUDO")
        self.run_all_button.setObjectName("dangerButton")
        self.run_all_button.setMinimumHeight(46)
        self.run_all_button.setIcon(self.standard_icon("SP_MediaPlay"))
        self.run_all_button.clicked.connect(lambda: self.start_automation("EXECUTAR TUDO"))
        self.action_buttons.append(self.run_all_button)

        processes_layout.addWidget(self.process_tabs, 1)
        processes_layout.addWidget(self.run_all_button)

        content_grid.addWidget(matriculas_panel, 0, 0)
        content_grid.addWidget(processes_panel, 0, 1)
        layout.addLayout(content_grid, 1)

        return page

    def _build_progress_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(14)

        layout.addWidget(self._section_header("Progresso", "Execução e histórico"))

        status_panel = self._panel("Execução Atual")
        status_layout = QGridLayout(status_panel)
        status_layout.setContentsMargins(14, 16, 14, 14)
        status_layout.setHorizontalSpacing(12)
        self.general_status_label = QLabel("Pronto")
        self.general_status_label.setObjectName("largeStatus")
        self.detail_status_label = QLabel("")
        self.detail_status_label.setWordWrap(True)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        status_layout.addWidget(self.general_status_label, 0, 0)
        status_layout.addWidget(self.progress_bar, 0, 1)
        status_layout.addWidget(self.detail_status_label, 1, 0, 1, 2)
        status_layout.setColumnStretch(0, 2)
        status_layout.setColumnStretch(1, 3)
        layout.addWidget(status_panel)

        split = QGridLayout()
        split.setColumnStretch(0, 3)
        split.setColumnStretch(1, 2)
        split.setHorizontalSpacing(14)

        tasks_panel = self._panel("Itens")
        tasks_layout = QVBoxLayout(tasks_panel)
        tasks_layout.setContentsMargins(14, 16, 14, 14)
        tasks_layout.setSpacing(10)
        filter_layout = QHBoxLayout()
        self.progress_filter = QLineEdit()
        self.progress_filter.setPlaceholderText("Filtrar progresso")
        self.progress_filter.textChanged.connect(self.filter_progress_items)
        filter_layout.addWidget(self.progress_filter)
        tasks_layout.addLayout(filter_layout)
        self.progress_tree = QTreeWidget()
        self.progress_tree.setHeaderLabels(["Item", "Status"])
        self.progress_tree.setRootIsDecorated(False)
        self.progress_tree.setAlternatingRowColors(True)
        self.progress_tree.header().setStretchLastSection(False)
        self.progress_tree.setColumnWidth(0, 340)
        tasks_layout.addWidget(self.progress_tree, 1)

        log_panel = self._panel("Log")
        log_layout = QVBoxLayout(log_panel)
        log_layout.setContentsMargins(14, 16, 14, 14)
        log_layout.setSpacing(10)
        self.log_box = QPlainTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.log_box.setFont(QFont("Consolas", 10))

        log_buttons = QHBoxLayout()
        copy_log = QPushButton("Copiar")
        copy_log.setObjectName("secondaryButton")
        copy_log.setIcon(self.standard_icon("SP_DialogSaveButton"))
        copy_log.clicked.connect(self.copy_log)
        clear_log = QPushButton("Limpar")
        clear_log.setObjectName("secondaryButton")
        clear_log.setIcon(self.standard_icon("SP_DialogResetButton"))
        clear_log.clicked.connect(self.log_box.clear)
        log_buttons.addStretch()
        log_buttons.addWidget(copy_log)
        log_buttons.addWidget(clear_log)
        log_layout.addLayout(log_buttons)
        log_layout.addWidget(self.log_box, 1)

        split.addWidget(tasks_panel, 0, 0)
        split.addWidget(log_panel, 0, 1)
        layout.addLayout(split, 1)

        return page

    def _build_resume_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(14)

        layout.addWidget(self._section_header("Retomada", "Checkpoint e continuidade"))

        panel = self._panel("Execução Interrompida")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(14, 16, 14, 14)
        panel_layout.setSpacing(12)

        self.resume_alert_label = QLabel("Nenhum checkpoint global ou local encontrado.")
        self.resume_alert_label.setObjectName("resumeAlert")
        self.resume_alert_label.setWordWrap(True)
        panel_layout.addWidget(self.resume_alert_label)

        self.resume_details_box = QPlainTextEdit()
        self.resume_details_box.setReadOnly(True)
        self.resume_details_box.setMinimumHeight(260)
        self.resume_details_box.setPlaceholderText("A retomada aparece aqui quando existir checkpoint global ou local.")
        panel_layout.addWidget(self.resume_details_box, 1)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        refresh_button = QPushButton("Recarregar")
        refresh_button.setObjectName("secondaryButton")
        refresh_button.setIcon(self.standard_icon("SP_BrowserReload"))
        refresh_button.clicked.connect(self.update_resume_status)

        discard_button = QPushButton("Descartar checkpoint")
        discard_button.setObjectName("dangerButton")
        discard_button.setIcon(self.standard_icon("SP_DialogDiscardButton"))
        discard_button.clicked.connect(self.discard_checkpoint)

        self.resume_now_button = QPushButton("Retomar agora")
        self.resume_now_button.setIcon(self.standard_icon("SP_MediaPlay"))
        self.resume_now_button.clicked.connect(self.start_resume_from_checkpoint)

        self.form_buttons.extend([refresh_button, discard_button, self.resume_now_button])
        button_layout.addWidget(refresh_button)
        button_layout.addWidget(discard_button)
        button_layout.addWidget(self.resume_now_button)
        panel_layout.addLayout(button_layout)

        layout.addWidget(panel, 1)
        return page

    def _build_settings_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(14)

        layout.addWidget(self._section_header("Ajustes", "Configuração local"))

        panel = self._panel("Preferências")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(14, 16, 14, 14)
        panel_layout.setSpacing(10)

        self.save_output_check = QCheckBox("Salvar pasta selecionada")
        self.save_output_check.setChecked(True)
        self.clear_after_success_check = QCheckBox("Limpar senha ao finalizar")
        self.clear_after_success_check.setChecked(True)

        panel_layout.addWidget(self.save_output_check)
        panel_layout.addWidget(self.clear_after_success_check)

        manual_button = QPushButton("Abrir guia da interface")
        manual_button.setObjectName("secondaryButton")
        manual_button.setIcon(self.standard_icon("SP_DialogHelpButton"))
        manual_button.clicked.connect(self.open_manual)
        self.form_buttons.append(manual_button)
        panel_layout.addWidget(manual_button)
        panel_layout.addStretch()

        layout.addWidget(panel)
        layout.addStretch()
        return page

    def _section_header(self, title, subtitle):
        frame = QFrame()
        frame.setObjectName("header")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)
        title_label = QLabel(title)
        title_label.setObjectName("pageTitle")
        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("pageSubtitle")
        layout.addWidget(title_label)
        layout.addWidget(subtitle_label)
        return frame

    def _panel(self, title):
        group = QGroupBox(title)
        group.setObjectName("panel")
        group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        return group

    def show_page(self, index):
        self.stack.setCurrentIndex(index)
        for i, button in enumerate(self.nav_buttons):
            button.setChecked(i == index)
        if index == 2:
            self.update_resume_status()

    def refresh_widget_style(self, widget):
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.update()

    def toggle_resume_attention(self):
        self.resume_pulse_on = not self.resume_pulse_on
        self.apply_resume_nav_state(load_checkpoint(self.output_base_path) is not None)

    def apply_resume_nav_state(self, has_checkpoint):
        if self.resume_nav_button is None:
            return
        self.resume_nav_button.setText("Retomada !" if has_checkpoint else "Retomada")
        self.resume_nav_button.setProperty("checkpoint", "true" if has_checkpoint else "false")
        self.resume_nav_button.setProperty(
            "pulse",
            "true" if has_checkpoint and self.resume_pulse_on else "false",
        )
        self.refresh_widget_style(self.resume_nav_button)

        if has_checkpoint and not self.resume_attention_timer.isActive():
            self.resume_attention_timer.start()
        elif not has_checkpoint and self.resume_attention_timer.isActive():
            self.resume_attention_timer.stop()
            self.resume_pulse_on = False

    def current_screen_params(self, sequence_name=None):
        tipo_ficha = "PDF" if "PDF" in self.ficha_type_combo.currentText() else "HTML"
        return {
            "sequence_name": sequence_name,
            "matriculas": self.get_matriculas(),
            "periodo": {
                "inicio": f"{self.start_month_combo.currentText()}/{self.start_year_combo.currentText()}",
                "fim": f"{self.end_month_combo.currentText()}/{self.end_year_combo.currentText()}",
            },
            "config": {"tipo_saida": tipo_ficha},
        }

    def checkpoint_matches_current_screen(self, checkpoint, sequence_name=None):
        params = self.current_screen_params(sequence_name)
        sequence_matches = (
            sequence_name is None
            or checkpoint.get("sequence_name") == params["sequence_name"]
        )
        return (
            sequence_matches
            and checkpoint.get("matriculas") == params["matriculas"]
            and checkpoint.get("periodo") == params["periodo"]
            and checkpoint.get("config") == params["config"]
        )

    def format_checkpoint_details(self, checkpoint):
        if not checkpoint:
            return "Nenhum checkpoint encontrado."

        periodo = checkpoint.get("periodo") or {}
        config = checkpoint.get("config") or {}
        matriculas = checkpoint.get("matriculas") or []
        current_state = checkpoint.get("current_process_state") or {}
        completed_processes = checkpoint.get("completed_processes") or []
        completed_tasks = current_state.get("completed_task_ids") or []
        tarefas = checkpoint.get("tarefas") or []
        preview_matriculas = ", ".join(str(matricula) for matricula in matriculas[:12])
        if len(matriculas) > 12:
            preview_matriculas += f" ... (+{len(matriculas) - 12})"

        same_screen = self.checkpoint_matches_current_screen(checkpoint)
        lines = [
            f"Status: {'mesmos parâmetros da tela atual' if same_screen else 'parâmetros salvos no checkpoint serão usados'}",
            f"Última atualização: {checkpoint.get('updated_at', '')}",
            f"Rotina original: {checkpoint.get('sequence_name', '')}",
            f"Período original: {periodo.get('inicio', '')} até {periodo.get('fim', '')}",
            f"Tipo de saída: {config.get('tipo_saida', '')}",
            f"Etapa atual: {checkpoint.get('current_process') or 'não identificada'}",
            f"Item atual: {current_state.get('current_task_id') or 'não identificado'}",
            f"Etapas concluídas: {len(completed_processes)}",
            f"Itens concluídos na etapa atual: {len(completed_tasks)}",
            f"Total de matrículas: {len(matriculas)}",
            f"Matrículas: {preview_matriculas}",
            "",
            "Sequência expandida:",
            ", ".join(tarefas) if tarefas else "Ainda não registrada.",
            "",
            f"Checkpoint global: {global_checkpoint_path()}",
            f"Cópia na saída: {checkpoint_path(checkpoint.get('output_base_path')) if checkpoint.get('output_base_path') else 'não registrada'}",
        ]
        return "\n".join(lines)

    def update_resume_status(self):
        checkpoint = load_checkpoint(self.output_base_path)
        has_checkpoint = checkpoint is not None
        self.apply_resume_nav_state(has_checkpoint)

        if not hasattr(self, "resume_alert_label"):
            return

        self.resume_now_button.setEnabled(has_checkpoint and not (self.worker and self.worker.isRunning()))
        if has_checkpoint:
            current = checkpoint.get("current_process") or "etapa não identificada"
            updated_at = checkpoint.get("updated_at", "")
            self.resume_alert_label.setText(
                f"Checkpoint encontrado. Retomada disponível a partir de '{current}' ({updated_at})."
            )
            self.resume_alert_label.setProperty("state", "warning")
            self.resume_details_box.setPlainText(self.format_checkpoint_details(checkpoint))
        else:
            self.resume_alert_label.setText("Nenhum checkpoint global ou local encontrado.")
            self.resume_alert_label.setProperty("state", "empty")
            self.resume_details_box.setPlainText("Quando uma execução cair, o checkpoint aparecerá aqui.")
        self.refresh_widget_style(self.resume_alert_label)

    def load_config(self):
        now = datetime.now()
        config = {}
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, "r", encoding="utf-8") as file:
                    config = json.load(file)
        except Exception as e:
            self.append_log(f"Erro ao carregar configuração: {e}")

        self.start_month_combo.setCurrentText(config.get("mes_inicio", f"{now.month:02d}"))
        self.start_year_combo.setCurrentText(config.get("ano_inicio", str(now.year)))
        self.end_month_combo.setCurrentText(config.get("mes_fim", f"{now.month:02d}"))
        self.end_year_combo.setCurrentText(config.get("ano_fim", str(now.year)))
        self.ficha_type_combo.setCurrentText(config.get("tipo_ficha", "HTML (Layout Padrão)"))

        output_path = config.get("output_base_path", "")
        if output_path:
            self.output_base_path = output_path
            self.output_input.setText(output_path)

    def save_config(self):
        config = {
            "mes_inicio": self.start_month_combo.currentText(),
            "ano_inicio": self.start_year_combo.currentText(),
            "mes_fim": self.end_month_combo.currentText(),
            "ano_fim": self.end_year_combo.currentText(),
            "tipo_ficha": self.ficha_type_combo.currentText(),
        }
        if self.save_output_check.isChecked() and self.output_base_path:
            config["output_base_path"] = self.output_base_path

        try:
            os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
            with open(CONFIG_FILE, "w", encoding="utf-8") as file:
                json.dump(config, file, ensure_ascii=False, indent=2)
        except Exception as e:
            self.append_log(f"Erro ao salvar configuração: {e}")

    def select_output_folder(self):
        path = QFileDialog.getExistingDirectory(
            self,
            "Selecione a pasta de destino",
            self.output_base_path or os.path.expanduser("~"),
        )
        if not path:
            return
        self.output_base_path = path
        self.output_input.setText(path)
        self.save_config()
        self.update_resume_status()

    def open_output_folder(self):
        if not self.output_base_path:
            QMessageBox.warning(self, "Pasta de destino", "Selecione uma pasta de destino.")
            return
        os.makedirs(self.output_base_path, exist_ok=True)
        os.startfile(self.output_base_path)

    def open_manual(self):
        manual_path = resource_path("GUIA_INTERFACE.html")
        if not os.path.exists(manual_path):
            manual_path = os.path.join(app_base_path(), "GUIA_INTERFACE.html")
        if not os.path.exists(manual_path):
            manual_path = resource_path("MANUAL_DE_USO.html")
        if not os.path.exists(manual_path):
            manual_path = os.path.join(app_base_path(), "MANUAL_DE_USO.html")
        if not os.path.exists(manual_path):
            QMessageBox.warning(self, "Manual", "Manual de uso não encontrado.")
            return
        os.startfile(manual_path)

    def toggle_password_visibility(self, checked):
        mode = QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
        self.password_input.setEchoMode(mode)

    def get_matriculas(self):
        text = self.matriculas_text.toPlainText()
        return [line.strip() for line in text.splitlines() if line.strip()]

    def update_matricula_count(self):
        total = len(self.get_matriculas())
        label = "1 matrícula" if total == 1 else f"{total} matrículas"
        self.matricula_count_label.setText(label)

    def paste_matriculas(self):
        text = QApplication.clipboard().text()
        if not text:
            return
        current = self.matriculas_text.toPlainText().rstrip()
        joined = f"{current}\n{text}" if current else text
        self.matriculas_text.setPlainText(joined)
        self.normalize_matriculas()

    def normalize_matriculas(self):
        text = self.matriculas_text.toPlainText()
        partes = [p.strip() for p in re.split(r"[\s,;]+", text) if p.strip()]
        unicas = list(dict.fromkeys(partes))
        self.matriculas_text.setPlainText("\n".join(unicas))

    def start_automation(self, sequence_name):
        if self.worker and self.worker.isRunning():
            QMessageBox.information(self, "Automação em andamento", "Aguarde a execução atual terminar.")
            return

        resume_checkpoint = self.resolve_resume_checkpoint(sequence_name)
        if resume_checkpoint:
            checkpoint_output_path = resume_checkpoint.get("output_base_path") or self.output_base_path
            if not checkpoint_output_path:
                QMessageBox.warning(
                    self,
                    "Checkpoint inválido",
                    "A retomada não tem pasta de saída salva. Selecione uma pasta antes de continuar.",
                )
                return
            self.output_base_path = checkpoint_output_path
            self.output_input.setText(checkpoint_output_path)
            sequence_name = resume_checkpoint.get("sequence_name") or sequence_name
            matriculas = list(resume_checkpoint.get("matriculas") or [])
            periodo = dict(resume_checkpoint.get("periodo") or {})
            config = dict(resume_checkpoint.get("config") or {})
        else:
            if not self.output_base_path:
                QMessageBox.warning(self, "Pasta de destino", "Selecione uma pasta de destino.")
                return
            params = self.current_screen_params(sequence_name)
            matriculas = params["matriculas"]
            if not matriculas:
                QMessageBox.warning(self, "Matrículas", "Informe ao menos uma matrícula.")
                return
            periodo = params["periodo"]
            config = params["config"]

        sap_password = self.ensure_sap_password()
        if not sap_password:
            return

        self.reset_progress()
        self.set_busy(True)
        self.show_page(1)
        self.save_config()

        self.worker = AutomationWorker(
            sequence_name,
            matriculas,
            periodo,
            config,
            self.output_base_path,
            sap_password,
            resume_checkpoint=resume_checkpoint,
        )
        self.worker.progress.connect(self.handle_progress)
        self.worker.done.connect(self.finish_automation)
        self.worker.start()

    def ensure_sap_password(self):
        sap_password = self.password_input.text()
        if sap_password.strip():
            return sap_password

        sap_password, ok = QInputDialog.getText(
            self,
            "Senha SAP obrigatória",
            "Informe a senha do SAP para login e reconexão automática:",
            QLineEdit.EchoMode.Password,
        )
        if not ok or not sap_password.strip():
            QMessageBox.warning(
                self,
                "Senha SAP",
                "A senha do SAP é obrigatória para iniciar, reconectar e retomar a automação.",
            )
            self.password_input.setFocus()
            return None

        self.password_input.setText(sap_password)
        return sap_password

    def resolve_resume_checkpoint(self, sequence_name=None):
        checkpoint = load_checkpoint(self.output_base_path)
        if not checkpoint:
            return None

        completed_processes = len(checkpoint.get("completed_processes", []))
        current = checkpoint.get("current_process") or "etapa não identificada"
        current_state = checkpoint.get("current_process_state") or {}
        current_task = current_state.get("current_task_id") or "item ainda não identificado"
        completed_tasks = len(current_state.get("completed_task_ids", []))
        checkpoint_sequence = checkpoint.get("sequence_name") or "rotina não identificada"
        periodo = checkpoint.get("periodo") or {}
        updated_at = checkpoint.get("updated_at", "")
        same_screen = self.checkpoint_matches_current_screen(checkpoint, sequence_name)
        status_parametros = (
            "A tela atual está com os mesmos parâmetros."
            if same_screen
            else "A retomada usará os parâmetros salvos no checkpoint, não os campos atuais da tela."
        )
        answer = QMessageBox.question(
            self,
            "Retomar execução",
            (
                "Foi encontrada uma execução interrompida.\n\n"
                f"Última atualização: {updated_at}\n"
                f"Rotina original: {checkpoint_sequence}\n"
                f"Período original: {periodo.get('inicio', '')} até {periodo.get('fim', '')}\n"
                f"Etapa atual: {current}\n"
                f"Item atual: {current_task}\n"
                f"Etapas concluídas: {completed_processes}\n"
                f"Itens concluídos na etapa atual: {completed_tasks}\n"
                f"{status_parametros}\n\n"
                "Deseja retomar desse ponto?"
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )

        if answer == QMessageBox.StandardButton.Yes:
            return checkpoint

        return None

    def start_resume_from_checkpoint(self):
        if self.worker and self.worker.isRunning():
            QMessageBox.information(self, "Automação em andamento", "Aguarde a execução atual terminar.")
            return

        checkpoint = load_checkpoint(self.output_base_path)
        if not checkpoint:
            QMessageBox.information(self, "Retomada", "Nenhum checkpoint encontrado.")
            self.update_resume_status()
            return

        sequence_name = checkpoint.get("sequence_name")
        matriculas = list(checkpoint.get("matriculas") or [])
        periodo = dict(checkpoint.get("periodo") or {})
        config = dict(checkpoint.get("config") or {})
        checkpoint_output_path = checkpoint.get("output_base_path") or self.output_base_path
        if not sequence_name or not matriculas or not periodo or not checkpoint_output_path:
            QMessageBox.warning(
                self,
                "Checkpoint inválido",
                "O arquivo de retomada está incompleto. Não é seguro continuar automaticamente.",
            )
            return

        self.output_base_path = checkpoint_output_path
        self.output_input.setText(checkpoint_output_path)

        sap_password = self.ensure_sap_password()
        if not sap_password:
            return

        self.reset_progress()
        self.set_busy(True)
        self.show_page(1)
        self.save_config()

        self.worker = AutomationWorker(
            sequence_name,
            matriculas,
            periodo,
            config,
            checkpoint_output_path,
            sap_password,
            resume_checkpoint=checkpoint,
        )
        self.worker.progress.connect(self.handle_progress)
        self.worker.done.connect(self.finish_automation)
        self.worker.start()

    def discard_checkpoint(self):
        checkpoint = load_checkpoint(self.output_base_path)
        if not checkpoint:
            self.update_resume_status()
            return

        answer = QMessageBox.question(
            self,
            "Descartar checkpoint",
            "Deseja descartar a retomada salva?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        clear_checkpoint(checkpoint.get("output_base_path") or self.output_base_path)
        self.update_resume_status()

    def reset_progress(self):
        self.progress_tree.clear()
        self.progress_items.clear()
        self.log_box.clear()
        self.progress_filter.clear()
        self.progress_bar.setValue(0)
        self.general_status_label.setText("Preparando")
        self.detail_status_label.setText("")

    def set_busy(self, busy):
        for button in self.action_buttons:
            button.setEnabled(not busy)
        for button in self.form_buttons:
            button.setEnabled(not busy)
        self.status_badge.setText("Executando" if busy else "Pronto")
        self.output_input.setEnabled(not busy)
        self.password_input.setEnabled(not busy)
        self.show_password_check.setEnabled(not busy)
        self.start_month_combo.setEnabled(not busy)
        self.start_year_combo.setEnabled(not busy)
        self.end_month_combo.setEnabled(not busy)
        self.end_year_combo.setEnabled(not busy)
        self.ficha_type_combo.setEnabled(not busy)
        self.matriculas_text.setEnabled(not busy)

    def handle_progress(self, msg):
        tipo = msg.get("type")

        if tipo == "status":
            if "geral" in msg:
                self.general_status_label.setText(msg["geral"])
            if "detalhe" in msg:
                self.detail_status_label.setText(msg["detalhe"])
            if "progresso_geral" in msg:
                self.progress_bar.setValue(round(msg["progresso_geral"]))
        elif tipo == "task_list":
            for task_id in msg.get("tasks", []):
                self.ensure_progress_item(str(task_id), "Pendente")
        elif tipo == "task_update":
            self.update_progress_item(str(msg.get("task_id", "")), str(msg.get("status", "")))
        elif tipo == "log":
            self.append_log(msg.get("msg", ""))
        elif tipo == "success":
            self.append_log(msg.get("msg", ""))
            self.progress_bar.setValue(100)
        elif tipo == "error":
            self.append_log(msg.get("msg", ""))
            self.general_status_label.setText("Erro")
            self.detail_status_label.setText(msg.get("msg", ""))

    def ensure_progress_item(self, task_id, status):
        if not task_id:
            return None
        item = self.progress_items.get(task_id)
        if item is None:
            item = QTreeWidgetItem([task_id, status])
            self.progress_tree.addTopLevelItem(item)
            self.progress_items[task_id] = item
        else:
            item.setText(1, status)
        self.apply_item_color(item, status)
        self.filter_progress_items(self.progress_filter.text())
        return item

    def update_progress_item(self, task_id, status):
        item = self.ensure_progress_item(task_id, status)
        if item is not None:
            self.progress_tree.setCurrentItem(item)
            self.progress_tree.scrollToItem(item)

    def apply_item_color(self, item, status):
        status_lower = status.lower()
        if "conclu" in status_lower:
            color = QColor("#4CA3FF")
        elif "erro" in status_lower or "não encontrado" in status_lower:
            color = QColor("#FF5A6A")
        elif "executando" in status_lower:
            color = QColor("#DCEBFF")
        else:
            color = QColor("#8EA0B6")
        item.setForeground(1, QBrush(color))

    def filter_progress_items(self, text):
        text = text.lower().strip()
        for i in range(self.progress_tree.topLevelItemCount()):
            item = self.progress_tree.topLevelItem(i)
            haystack = f"{item.text(0)} {item.text(1)}".lower()
            item.setHidden(bool(text and text not in haystack))

    def append_log(self, text):
        if not text:
            return
        self.log_box.appendPlainText(text)
        bar = self.log_box.verticalScrollBar()
        bar.setValue(bar.maximum())

    def copy_log(self):
        QApplication.clipboard().setText(self.log_box.toPlainText())

    def finish_automation(self, success, message):
        self.set_busy(False)
        self.status_badge.setText("Finalizado" if success else "Falhou")
        self.general_status_label.setText("Concluído" if success else "Falhou")
        self.detail_status_label.setText(message)
        if success:
            self.progress_bar.setValue(100)
            if self.clear_after_success_check.isChecked():
                self.password_input.clear()
            self.save_config()
            QMessageBox.information(self, "Concluído", message)
        else:
            QMessageBox.critical(self, "Erro na Execução", message)
        self.update_resume_status()

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            resposta = QMessageBox.question(
                self,
                "Automação em andamento",
                "Uma automação está em andamento. Deseja fechar mesmo assim?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if resposta != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
        self.save_config()
        event.accept()

    def _apply_style(self):
        self.setStyleSheet("""
            QMainWindow {
                background: #101419;
                color: #E6EDF5;
            }
            QFrame#sidebar {
                background: #0B0F14;
                border: 0;
            }
            QLabel#sidebarTitle {
                color: #F4F8FF;
                font-size: 20px;
                font-weight: 700;
            }
            QLabel#sidebarSubtitle {
                color: #8EA0B6;
                font-size: 12px;
            }
            QPushButton#navButton {
                background: transparent;
                color: #B9C7D8;
                border: 0;
                border-radius: 6px;
                padding: 11px 12px;
                text-align: left;
                font-weight: 600;
            }
            QPushButton#navButton:hover {
                background: #18202A;
            }
            QPushButton#navButton:checked {
                background: #12365F;
                color: #FFFFFF;
                border-left: 3px solid #E5485A;
            }
            QPushButton#navButton[checkpoint="true"] {
                background: #351620;
                color: #FFFFFF;
                border-left: 3px solid #D63D4F;
            }
            QPushButton#navButton[checkpoint="true"][pulse="true"] {
                background: #D63D4F;
                color: #FFFFFF;
            }
            QLabel#statusBadge {
                background: #102A47;
                color: #DCEBFF;
                border: 1px solid #2F80D8;
                border-radius: 6px;
                padding: 8px 10px;
                font-weight: 700;
            }
            QLabel#pageTitle {
                color: #F4F8FF;
                font-size: 24px;
                font-weight: 750;
            }
            QLabel#pageSubtitle {
                color: #8EA0B6;
                font-size: 12px;
            }
            QGroupBox#panel {
                background: #171D24;
                border: 1px solid #2A3441;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 8px;
                font-weight: 700;
                color: #DCEBFF;
            }
            QGroupBox#panel::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                background: #171D24;
                color: #DCEBFF;
                font-weight: 700;
                left: 12px;
                padding: 0 6px;
            }
            QLabel#largeStatus {
                color: #F4F8FF;
                font-size: 17px;
                font-weight: 700;
            }
            QLabel {
                color: #D5DFEA;
            }
            QLabel#resumeAlert {
                border-radius: 6px;
                padding: 12px 14px;
                font-weight: 700;
            }
            QLabel#resumeAlert[state="warning"] {
                background: #351620;
                color: #FFE8ED;
                border: 1px solid #D63D4F;
            }
            QLabel#resumeAlert[state="empty"] {
                background: #102A47;
                color: #DCEBFF;
                border: 1px solid #2F80D8;
            }
            QLineEdit, QComboBox, QPlainTextEdit, QTreeWidget {
                background: #0F151C;
                border: 1px solid #2A3441;
                border-radius: 6px;
                padding: 7px 9px;
                color: #E6EDF5;
                selection-background-color: #2F80D8;
                selection-color: #FFFFFF;
            }
            QLineEdit:focus, QComboBox:focus, QPlainTextEdit:focus, QTreeWidget:focus {
                border: 1px solid #2F80D8;
            }
            QLineEdit:disabled, QComboBox:disabled, QPlainTextEdit:disabled {
                background: #151B22;
                color: #718196;
                border: 1px solid #252E39;
            }
            QPlainTextEdit {
                font-family: Consolas;
            }
            QComboBox::drop-down {
                border: 0;
                width: 28px;
            }
            QComboBox QAbstractItemView {
                background: #111821;
                color: #E6EDF5;
                border: 1px solid #2A3441;
                selection-background-color: #2F80D8;
                selection-color: #FFFFFF;
                outline: 0;
            }
            QTabWidget::pane {
                border: 1px solid #2A3441;
                border-radius: 6px;
                top: -1px;
            }
            QTabBar::tab {
                background: #111821;
                color: #9DAEC1;
                padding: 8px 14px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 4px;
                font-weight: 600;
            }
            QTabBar::tab:selected {
                background: #172231;
                color: #FFFFFF;
                border: 1px solid #2F80D8;
                border-bottom: 1px solid #172231;
            }
            QPushButton {
                background: #2F80D8;
                color: white;
                border: 0;
                border-radius: 6px;
                padding: 9px 14px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: #1E6EC1;
            }
            QPushButton:disabled {
                background: #2A3441;
                color: #75859A;
            }
            QPushButton#secondaryButton {
                background: #121922;
                color: #DCEBFF;
                border: 1px solid #2A3441;
            }
            QPushButton#secondaryButton:hover {
                background: #172231;
                border: 1px solid #2F80D8;
            }
            QPushButton#dangerButton {
                background: #D63D4F;
            }
            QPushButton#dangerButton:hover {
                background: #B92E3F;
            }
            QCheckBox {
                color: #D5DFEA;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 4px;
                border: 1px solid #46566A;
                background: #0F151C;
            }
            QCheckBox::indicator:checked {
                background: #D63D4F;
                border: 1px solid #D63D4F;
            }
            QProgressBar {
                background: #0F151C;
                border: 1px solid #2A3441;
                border-radius: 6px;
                height: 20px;
                text-align: center;
                color: #E6EDF5;
                font-weight: 700;
            }
            QProgressBar::chunk {
                background: #2F80D8;
                border-radius: 5px;
            }
            QTreeWidget {
                alternate-background-color: #121922;
                gridline-color: #2A3441;
            }
            QHeaderView::section {
                background: #172231;
                color: #DCEBFF;
                border: 0;
                border-bottom: 1px solid #2A3441;
                padding: 8px;
                font-weight: 700;
            }
            QScrollBar:vertical {
                background: #0F151C;
                width: 12px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #334155;
                min-height: 28px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #2F80D8;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
        """)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    icon_path = app_icon_path()
    if icon_path:
        app.setWindowIcon(QIcon(icon_path))
    window = SapAutomationWindow()
    window.showMaximized()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
