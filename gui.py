import io
from contextlib import redirect_stdout

from PySide6.QtGui import QFontDatabase
from PySide6.QtPrintSupport import QPrinter
from PySide6.QtWidgets import (
    QComboBox, QDoubleSpinBox, QFileDialog, QFormLayout, QGroupBox,
    QHBoxLayout, QMainWindow, QMessageBox, QPlainTextEdit, QPushButton,
    QScrollArea, QSplitter, QVBoxLayout, QWidget,
)

import calculo


def spin(minimo, maximo, valor, casas=2, sufixo=""):
    s = QDoubleSpinBox()
    s.setRange(minimo, maximo)
    s.setDecimals(casas)
    s.setValue(valor)
    if sufixo:
        s.setSuffix(f" {sufixo}")
    return s


def combo(itens):
    """itens: lista de (texto, valor)"""
    c = QComboBox()
    for texto, valor in itens:
        c.addItem(texto, valor)
    return c


class Janela(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cálculo de Lajes Maciças — NBR 6118")
        self.resize(1200, 750)

        # ---------- campos ----------
        self.lx = spin(0.5, 20, 4.0, 3, "m")
        self.ly = spin(0.5, 40, 5.0, 3, "m")
        self.tipo = combo([("Piso", "piso"), ("Cobertura", "cobertura")])
        self.caso = combo([(f"{k} — {calculo.DESCRICAO[k]}", k) for k in range(1, 7)])
        self.caa = combo([("I", "I"), ("II", "II"), ("III", "III"), ("IV", "IV")])
        self.caa.setCurrentIndex(1)
        self.cob = spin(0, 80, 0, 1, "mm")          # 0 = nominal da CAA
        self.fck = spin(20, 40, 25, 0, "MPa")
        self.fyk = spin(400, 600, 500, 0, "MPa")
        self.phi = spin(4, 20, 8, 1, "mm")
        self.agregado = combo([(n, k) for k, (n, _) in calculo.AGREGADOS.items()])
        self.agregado.setCurrentIndex(1)
        self.gc = spin(20, 30, 25, 1, "kN/m³")
        self.g_contrapiso = spin(0, 20, 0, 2, "kN/m²")
        self.g_revest_inf = spin(0, 20, 0, 2, "kN/m²")
        self.g_piso = spin(0, 20, 0, 2, "kN/m²")
        self.g_paredes = spin(0, 20, 0, 2, "kN/m²")
        self.g_outros = spin(0, 20, 0, 2, "kN/m²")
        self.q = spin(0, 50, 2.0, 2, "kN/m²")
        self.psi2 = spin(0, 1, 0.3, 2)
        self.h = spin(0, 0.6, 0, 3, "m")            # 0 = automático
        self.t0 = spin(0, 70, 0.47, 2, "meses")
        self.tinf = spin(0, 200, 70, 0, "meses")

        # ---------- layout do formulário ----------
        def grupo(titulo, linhas):
            g = QGroupBox(titulo)
            f = QFormLayout(g)
            for rotulo, w in linhas:
                f.addRow(rotulo, w)
            return g

        form = QVBoxLayout()
        form.addWidget(grupo("Geometria", [
            ("lx (menor vão)", self.lx), ("ly (maior vão)", self.ly),
            ("Tipo", self.tipo), ("Caso estrutural", self.caso),
            ("h (0 = automático)", self.h)]))
        form.addWidget(grupo("Materiais e durabilidade", [
            ("CAA", self.caa), ("Cobrimento (0 = nominal)", self.cob),
            ("fck", self.fck), ("fyk", self.fyk), ("Bitola φ", self.phi),
            ("Agregado", self.agregado)]))
        form.addWidget(grupo("Cargas", [
            ("Peso esp. concreto", self.gc), ("Contrapiso", self.g_contrapiso),
            ("Revest. inferior", self.g_revest_inf), ("Piso final", self.g_piso),
            ("Paredes", self.g_paredes), ("Outros permanentes", self.g_outros),
            ("Variável q", self.q), ("ψ2", self.psi2)]))
        form.addWidget(grupo("Fluência", [("t0", self.t0), ("t final", self.tinf)]))

        btn_calc = QPushButton("Calcular")
        btn_calc.clicked.connect(self.calcular)
        btn_pdf = QPushButton("Exportar PDF")
        btn_pdf.clicked.connect(self.exportar_pdf)
        linha = QHBoxLayout()
        linha.addWidget(btn_calc)
        linha.addWidget(btn_pdf)
        form.addLayout(linha)
        form.addStretch()

        painel = QWidget()
        painel.setLayout(form)
        rolagem = QScrollArea()
        rolagem.setWidgetResizable(True)
        rolagem.setWidget(painel)

        self.saida = QPlainTextEdit()
        self.saida.setReadOnly(True)
        self.saida.setFont(QFontDatabase.systemFont(QFontDatabase.FixedFont))

        divisor = QSplitter()
        divisor.addWidget(rolagem)
        divisor.addWidget(self.saida)
        divisor.setStretchFactor(1, 1)
        self.setCentralWidget(divisor)

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
            self.saida.setPlainText(buf.getvalue())
        except (ValueError, KeyError) as e:
            QMessageBox.warning(self, "Erro nos dados", str(e))

    def exportar_pdf(self):
        caminho, _ = QFileDialog.getSaveFileName(
            self, "Salvar memória de cálculo", "memoria_calculo.pdf", "PDF (*.pdf)")
        if not caminho:
            return
        impressora = QPrinter(QPrinter.HighResolution)
        impressora.setOutputFormat(QPrinter.PdfFormat)
        impressora.setOutputFileName(caminho)
        self.saida.print_(impressora)