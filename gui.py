import io
from contextlib import redirect_stdout

from PySide6.QtCore import QLocale, QMarginsF, Qt
from PySide6.QtGui import (
    QFontDatabase, QKeySequence, QPageLayout, QPageSize, QShortcut,
)
from PySide6.QtPrintSupport import QPrinter
from PySide6.QtWidgets import (
    QApplication, QComboBox, QDoubleSpinBox, QFileDialog, QFrame,
    QGridLayout, QGroupBox, QHBoxLayout, QLabel, QMainWindow, QMessageBox,
    QPlainTextEdit, QPushButton, QScrollArea, QSplitter, QStyle,
    QVBoxLayout, QWidget,
)

import calculo


ESTILO = """
QMainWindow, QWidget#raiz { background: #f4f6f8; }
QWidget { font-size: 13px; color: #1d2b3a; }

QFrame#cabecalho { background: #12304a; }
QLabel#titulo { color: #ffffff; font-size: 19px; font-weight: 600; }
QLabel#subtitulo { color: #a9c1d6; font-size: 12px; }

QScrollArea { border: none; background: transparent; }
QWidget#painel { background: transparent; }

QGroupBox {
    background: #ffffff;
    border: 1px solid #dde3ea;
    border-radius: 8px;
    margin-top: 14px;
    padding: 16px 10px 10px 10px;
    font-weight: 600;
    color: #12304a;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
}
QLabel#rotulo { color: #5b6b7b; font-size: 11px; font-weight: 400; }

QDoubleSpinBox, QComboBox {
    background: #fbfcfd;
    border: 1px solid #cfd8e1;
    border-radius: 5px;
    padding: 3px 6px;
    min-height: 24px;
    font-weight: 400;
}
QDoubleSpinBox:hover, QComboBox:hover { border-color: #9fb3c6; }
QDoubleSpinBox:focus, QComboBox:focus { border: 1px solid #1f6feb; background: #ffffff; }
QComboBox QAbstractItemView {
    background: #ffffff;
    border: 1px solid #cfd8e1;
    selection-background-color: #dbe9fd;
    selection-color: #12304a;
    outline: none;
}

QPushButton {
    background: #ffffff;
    border: 1px solid #cfd8e1;
    border-radius: 6px;
    padding: 7px 14px;
    font-weight: 500;
}
QPushButton:hover { background: #eef3f8; }
QPushButton:pressed { background: #e0e8f0; }
QPushButton:disabled { color: #9aa8b5; background: #f1f4f7; }
QPushButton#primario {
    background: #1f6feb;
    border: 1px solid #1a5fcc;
    color: #ffffff;
    font-weight: 600;
}
QPushButton#primario:hover { background: #3a82f0; }
QPushButton#primario:pressed { background: #1a5fcc; }

QPlainTextEdit {
    background: #ffffff;
    border: 1px solid #dde3ea;
    border-radius: 8px;
    padding: 12px;
    selection-background-color: #cfe1fb;
}
QSplitter::handle { background: transparent; }
QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }
QScrollBar::handle:vertical { background: #c5d0db; border-radius: 4px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: #a9b8c7; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; width: 0; }

QStatusBar { background: #ffffff; border-top: 1px solid #dde3ea; color: #5b6b7b; }
QToolTip { background: #12304a; color: #ffffff; border: none; padding: 4px 8px; }
"""

LOCAL = QLocale(QLocale.Portuguese, QLocale.Brazil)


class SpinSemRoda(QDoubleSpinBox):
    """Evita alterar valores sem querer ao rolar o painel com o mouse."""

    def __init__(self):
        super().__init__()
        self.setFocusPolicy(Qt.StrongFocus)
        self.setLocale(LOCAL)
        self.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

    def wheelEvent(self, e):
        if self.hasFocus():
            super().wheelEvent(e)
        else:
            e.ignore()


class ComboSemRoda(QComboBox):
    def __init__(self):
        super().__init__()
        self.setFocusPolicy(Qt.StrongFocus)

    def wheelEvent(self, e):
        if self.hasFocus():
            super().wheelEvent(e)
        else:
            e.ignore()


def spin(minimo, maximo, valor, casas=2, sufixo="", dica=""):
    s = SpinSemRoda()
    s.setRange(minimo, maximo)
    s.setDecimals(casas)
    s.setValue(valor)
    if sufixo:
        s.setSuffix(f" {sufixo}")
    if dica:
        s.setToolTip(dica)
    return s


def combo(itens, dica=""):
    """itens: lista de (texto, valor)"""
    c = ComboSemRoda()
    for texto, valor in itens:
        c.addItem(texto, valor)
    if dica:
        c.setToolTip(dica)
    return c


def campo(rotulo, widget):
    """Rótulo pequeno acima do campo."""
    w = QWidget()
    lay = QVBoxLayout(w)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(3)
    lb = QLabel(rotulo)
    lb.setObjectName("rotulo")
    lay.addWidget(lb)
    lay.addWidget(widget)
    return w


def grupo(titulo, itens, colunas=2):
    """itens: (rótulo, widget) ou (rótulo, widget, largura_em_colunas)."""
    g = QGroupBox(titulo)
    grade = QGridLayout(g)
    grade.setHorizontalSpacing(12)
    grade.setVerticalSpacing(10)
    for c in range(colunas):
        grade.setColumnStretch(c, 1)
    linha = coluna = 0
    for item in itens:
        rotulo, w = item[0], item[1]
        largura = item[2] if len(item) > 2 else 1
        if coluna + largura > colunas:
            linha += 1
            coluna = 0
        grade.addWidget(campo(rotulo, w), linha, coluna, 1, largura)
        coluna += largura
        if coluna >= colunas:
            linha += 1
            coluna = 0
    return g


class Janela(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cálculo de Lajes Maciças — NBR 6118")
        self.resize(1280, 800)
        self.setMinimumSize(980, 600)
        self.setStyleSheet(ESTILO)

        self._criar_campos()
        self._montar_interface()
        self._atalhos()
        self._salvar_padroes()
        self._mostrar_vazio()

    # ------------------------------------------------------------------
    # campos
    # ------------------------------------------------------------------
    def _criar_campos(self):
        self.lx = spin(0.5, 20, 4.0, 3, "m", "Menor vão da laje")
        self.ly = spin(0.5, 40, 5.0, 3, "m", "Maior vão da laje")
        self.tipo = combo([("Piso", "piso"), ("Cobertura", "cobertura")])
        self.caso = combo(
            [(f"{k} — {calculo.DESCRICAO[k]}", k) for k in range(1, 7)],
            "Condição de apoio da laje")
        self.caa = combo([("I", "I"), ("II", "II"), ("III", "III"), ("IV", "IV")],
                         "Classe de agressividade ambiental")
        self.caa.setCurrentIndex(1)
        self.cob = spin(0, 80, 0, 1, "mm", "0 = cobrimento nominal da CAA")
        self.fck = spin(20, 40, 25, 0, "MPa")
        self.fyk = spin(400, 600, 500, 0, "MPa")
        self.phi = spin(4, 20, 8, 1, "mm", "Bitola da armadura")
        self.agregado = combo([(n, k) for k, (n, _) in calculo.AGREGADOS.items()])
        self.agregado.setCurrentIndex(1)
        self.gc = spin(20, 30, 25, 1, "kN/m³")
        self.g_contrapiso = spin(0, 20, 0, 2, "kN/m²")
        self.g_revest_inf = spin(0, 20, 0, 2, "kN/m²")
        self.g_piso = spin(0, 20, 0, 2, "kN/m²")
        self.g_paredes = spin(0, 20, 0, 2, "kN/m²")
        self.g_outros = spin(0, 20, 0, 2, "kN/m²")
        self.q = spin(0, 50, 2.0, 2, "kN/m²", "Carga variável")
        self.psi2 = spin(0, 1, 0.3, 2, "", "Fator de combinação quase permanente")
        self.h = spin(0, 0.6, 0, 3, "m", "0 = altura calculada automaticamente")
        self.t0 = spin(0, 70, 0.47, 2, "meses", "Idade do concreto no carregamento")
        self.tinf = spin(0, 200, 70, 0, "meses", "Tempo final para fluência")

    # ------------------------------------------------------------------
    # interface
    # ------------------------------------------------------------------
    def _montar_interface(self):
        raiz = QWidget()
        raiz.setObjectName("raiz")
        coluna = QVBoxLayout(raiz)
        coluna.setContentsMargins(0, 0, 0, 0)
        coluna.setSpacing(0)
        coluna.addWidget(self._cabecalho())

        # --- painel de entrada (rolável) ---
        form = QVBoxLayout()
        form.setSpacing(4)
        form.addWidget(grupo("Geometria", [
            ("lx (menor vão)", self.lx), ("ly (maior vão)", self.ly),
            ("Tipo", self.tipo), ("h (0 = automático)", self.h),
            ("Caso estrutural", self.caso, 2)]))
        form.addWidget(grupo("Materiais e durabilidade", [
            ("CAA", self.caa), ("Cobrimento (0 = nominal)", self.cob),
            ("fck", self.fck), ("fyk", self.fyk),
            ("Bitola φ", self.phi), ("Agregado", self.agregado)]))
        form.addWidget(grupo("Cargas", [
            ("Peso esp. concreto", self.gc), ("Variável q", self.q),
            ("Contrapiso", self.g_contrapiso), ("Revest. inferior", self.g_revest_inf),
            ("Piso final", self.g_piso), ("Paredes", self.g_paredes),
            ("Outros permanentes", self.g_outros), ("ψ2", self.psi2)]))
        form.addWidget(grupo("Fluência", [
            ("t0", self.t0), ("t final", self.tinf)]))
        form.addStretch()

        painel = QWidget()
        painel.setObjectName("painel")
        painel.setLayout(form)
        rolagem = QScrollArea()
        rolagem.setWidgetResizable(True)
        rolagem.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        rolagem.setWidget(painel)

        esquerda = QWidget()
        lay_esq = QVBoxLayout(esquerda)
        lay_esq.setContentsMargins(0, 0, 0, 0)
        lay_esq.setSpacing(10)
        lay_esq.addWidget(rolagem, 1)
        lay_esq.addLayout(self._barra_acoes())
        esquerda.setMinimumWidth(400)

        # --- saída ---
        self.saida = QPlainTextEdit()
        self.saida.setReadOnly(True)
        self.saida.setLineWrapMode(QPlainTextEdit.NoWrap)
        fonte = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        fonte.setPointSize(10)
        self.saida.setFont(fonte)

        divisor = QSplitter()
        divisor.setHandleWidth(10)
        divisor.setChildrenCollapsible(False)
        divisor.addWidget(esquerda)
        divisor.addWidget(self.saida)
        divisor.setStretchFactor(0, 0)
        divisor.setStretchFactor(1, 1)
        divisor.setSizes([440, 840])

        corpo = QWidget()
        lay_corpo = QVBoxLayout(corpo)
        lay_corpo.setContentsMargins(16, 14, 16, 12)
        lay_corpo.addWidget(divisor)
        coluna.addWidget(corpo, 1)

        self.setCentralWidget(raiz)
        self.statusBar().showMessage("Pronto")

    def _cabecalho(self):
        quadro = QFrame()
        quadro.setObjectName("cabecalho")
        lay = QVBoxLayout(quadro)
        lay.setContentsMargins(20, 14, 20, 14)
        lay.setSpacing(2)
        titulo = QLabel("Cálculo de Lajes Maciças")
        titulo.setObjectName("titulo")
        sub = QLabel("Dimensionamento e verificações segundo a NBR 6118")
        sub.setObjectName("subtitulo")
        lay.addWidget(titulo)
        lay.addWidget(sub)
        return quadro

    def _barra_acoes(self):
        st = self.style()
        self.btn_calc = QPushButton(st.standardIcon(QStyle.SP_MediaPlay), " Calcular")
        self.btn_calc.setObjectName("primario")
        self.btn_calc.setToolTip("Ctrl+Enter")
        self.btn_calc.setCursor(Qt.PointingHandCursor)
        self.btn_calc.clicked.connect(self.calcular)

        self.btn_pdf = QPushButton(st.standardIcon(QStyle.SP_DialogSaveButton), " PDF")
        self.btn_pdf.setToolTip("Exportar memória de cálculo (Ctrl+P)")
        self.btn_pdf.clicked.connect(self.exportar_pdf)

        self.btn_copiar = QPushButton("Copiar")
        self.btn_copiar.setToolTip("Copiar resultado para a área de transferência")
        self.btn_copiar.clicked.connect(self.copiar)

        btn_reset = QPushButton(st.standardIcon(QStyle.SP_BrowserReload), "")
        btn_reset.setToolTip("Restaurar valores padrão")
        btn_reset.clicked.connect(self.restaurar)

        for b in (self.btn_pdf, self.btn_copiar):
            b.setEnabled(False)
            b.setCursor(Qt.PointingHandCursor)
        btn_reset.setCursor(Qt.PointingHandCursor)

        linha = QHBoxLayout()
        linha.setSpacing(8)
        linha.addWidget(self.btn_calc, 1)
        linha.addWidget(self.btn_pdf)
        linha.addWidget(self.btn_copiar)
        linha.addWidget(btn_reset)
        return linha

    def _atalhos(self):
        for seq in ("Ctrl+Return", "Ctrl+Enter"):
            QShortcut(QKeySequence(seq), self, self.calcular)
        QShortcut(QKeySequence("Ctrl+P"), self, self.exportar_pdf)

    # ------------------------------------------------------------------
    # estado
    # ------------------------------------------------------------------
    def _widgets(self):
        return [w for w in vars(self).values()
                if isinstance(w, (QDoubleSpinBox, QComboBox))]

    def _salvar_padroes(self):
        self._padroes = {
            w: (w.currentIndex() if isinstance(w, QComboBox) else w.value())
            for w in self._widgets()}

    def restaurar(self):
        for w, v in self._padroes.items():
            if isinstance(w, QComboBox):
                w.setCurrentIndex(v)
            else:
                w.setValue(v)
        self._mostrar_vazio()
        self.statusBar().showMessage("Valores padrão restaurados")

    def _mostrar_vazio(self):
        self.saida.clear()
        self.saida.setPlaceholderText(
            "Preencha os dados ao lado e clique em Calcular (Ctrl+Enter).\n\n"
            "A memória de cálculo aparecerá aqui.")
        self.btn_pdf.setEnabled(False)
        self.btn_copiar.setEnabled(False)

    # ------------------------------------------------------------------
    # ações
    # ------------------------------------------------------------------
    def coletar(self):
        return dict(
            lx=self.lx.value(), ly=self.ly.value(),
            tipo=self.tipo.currentData(), caso=self.caso.currentData(),
            caa=self.caa.currentData(), cob=self.cob.value(),
            fck=self.fck.value(), fyk=self.fyk.value(), phi=self.phi.value(),
            agregado=self.agregado.currentData(), gc=self.gc.value(),
            g_contrapiso=self.g_contrapiso.value(),
            g_revest_inf=self.g_revest_inf.value(), g_piso=self.g_piso.value(),
            g_paredes=self.g_paredes.value(), g_outros=self.g_outros.value(),
            q=self.q.value(), psi2=self.psi2.value(), h=self.h.value(),
            t0=self.t0.value(), tinf=self.tinf.value(),
        )

    def calcular(self):
        try:
            d = calculo.montar_dados(self.coletar())
            r = calculo.calcular(d)
            buf = io.StringIO()
            with redirect_stdout(buf):
                calculo.imprimir(d, r)
        except (ValueError, KeyError) as e:
            self.statusBar().showMessage(f"Erro nos dados: {e}")
            QMessageBox.warning(self, "Erro nos dados", str(e))
            return
        self.saida.setPlainText(buf.getvalue())
        self.btn_pdf.setEnabled(True)
        self.btn_copiar.setEnabled(True)
        self.statusBar().showMessage("Cálculo concluído")

    def copiar(self):
        QApplication.clipboard().setText(self.saida.toPlainText())
        self.statusBar().showMessage("Resultado copiado", 3000)

    def exportar_pdf(self):
        if not self.saida.toPlainText():
            return
        caminho, _ = QFileDialog.getSaveFileName(
            self, "Salvar memória de cálculo", "memoria_calculo.pdf", "PDF (*.pdf)")
        if not caminho:
            return
        impressora = QPrinter(QPrinter.HighResolution)
        impressora.setOutputFormat(QPrinter.PdfFormat)
        impressora.setOutputFileName(caminho)
        impressora.setPageLayout(QPageLayout(
            QPageSize(QPageSize.A4), QPageLayout.Portrait,
            QMarginsF(15, 15, 15, 15), QPageLayout.Millimeter))
        self.saida.print_(impressora)
        self.statusBar().showMessage(f"PDF salvo em {caminho}", 5000)