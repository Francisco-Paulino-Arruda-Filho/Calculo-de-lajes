import io
import os
import sys
from contextlib import redirect_stdout
from math import ceil

from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtPrintSupport import QPrinter
from PySide6.QtWidgets import (
    QAbstractItemView, QComboBox, QDoubleSpinBox, QFileDialog, QFormLayout,
    QGroupBox, QHBoxLayout, QHeaderView, QLabel, QMainWindow, QMessageBox,
    QPlainTextEdit, QPushButton, QTabWidget, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget,
)

import calculo


# ---------------------------------------------------------------------------
# Núcleo sem interface (usado pela janela e pelo teste de paridade)
# ---------------------------------------------------------------------------

def caminho_recurso(nome):
    bases = []
    if getattr(sys, "frozen", False):
        bases.append(getattr(sys, "_MEIPASS", os.path.dirname(sys.executable)))
    bases.append(os.path.dirname(os.path.abspath(__file__)))
    for base in bases:
        for sub in ("assets", ""):
            p = os.path.join(base, sub, nome)
            if os.path.isfile(p):
                return p
    return None


def montar_dados_padrao(lx, ly, vinculacao, caa, phi, q, h_cm):
    """Reproduz exatamente o dicionário que calculo.entrada() devolve."""
    info = calculo.classificar_laje(lx, ly)
    uni = info["unidirecional"]
    if vinculacao not in info["casos"]:
        raise ValueError("Selecione a vinculação da laje.")
    tipo = "piso"
    cob_nbr = calculo.COB_NOMINAL[caa]
    cob = float(cob_nbr)
    fck = calculo.FCK_MIN_CAA[caa]
    agregado, alpha_E = calculo.AGREGADOS["2"]
    caso = 1 if uni else vinculacao
    apoio_1d = vinculacao if uni else None
    h = h_cm / 100.0
    h_min = calculo.altura_minima(tipo)
    _, h_est, _, _ = calculo.estimar_h_bastos(
        info["lx"], info["ly"], caso, cob / 1000, phi / 1000)
    return dict(
        lx=info["lx"], ly=info["ly"], caso=caso, unidirecional=uni,
        apoio_1d=apoio_1d, tipo=tipo, caa=caa, cob=cob, cob_nbr=cob_nbr,
        fck=fck, fyk=500.0, phi=phi, agregado=agregado, alpha_E=alpha_E,
        gc=25.0, g_contrapiso=0.0, g_revest_inf=0.0, g_piso=0.0,
        g_paredes=0.0, g_outros=1.28, q=q, psi2=0.30, h=h, h_min=h_min,
        h_est=h_est, t0=14.0 / 30.0, tinf=70.0,
    )


def gerar_memoria(dados):
    """Executa o modelo e captura a mesma saída do fluxo de terminal."""
    d, r = calculo.executar_modelo(dados)
    partes = {}

    def capturar(chave, func, *args):
        buf = io.StringIO()
        with redirect_stdout(buf):
            func(*args)
        partes[chave] = buf.getvalue()

    if d["unidirecional"]:
        capturar("memoria", calculo.imprimir_unidirecional, d, r)
    else:
        capturar("memoria", calculo.imprimir, d, r)
    capturar("detalhamento", calculo.imprimir_detalhamento, r)
    capturar("parecer", calculo.imprimir_parecer_final, d, r)
    capturar("auditoria", calculo.imprimir_auditoria_normativa, r)
    partes["completo"] = (partes["memoria"] + partes["detalhamento"]
                          + partes["parecer"] + partes["auditoria"])
    return d, r, partes


# ---------------------------------------------------------------------------
# Linhas das tabelas de resultados (apenas leitura dos resultados prontos)
# ---------------------------------------------------------------------------

def f2(v, nd=2):
    return f"{v:.{nd}f}".replace(".", ",")


def situacao(ok):
    return "ATENDE" if ok else "NÃO ATENDE"


def linhas_cargas_momentos(d, r):
    if d["unidirecional"]:
        linhas = [
            ("Carga permanente total gk", f2(r["g"]), "kN/m²"),
            ("Carga variável qk", f2(r["q"]), "kN/m²"),
            ("Carga de cálculo (ELU)", f2(r["pd"]), "kN/m²"),
            ("Carga quase permanente (ELS)", f2(r["pqp"]), "kN/m²"),
            ("Momento positivo de cálculo", f2(r["Mpos"]), "kN·m/m"),
        ]
        if r["Mneg"] > 0:
            linhas.append(("Momento negativo de cálculo (módulo)", f2(r["Mneg"]), "kN·m/m"))
        return linhas
    linhas = [
        ("Carga permanente total g", f2(r["g"]), "kN/m²"),
        ("Carga variável q", f2(d["q"]), "kN/m²"),
        ("Carga de cálculo (ELU)", f2(r["p_elu"]), "kN/m²"),
        ("Carga quase permanente (ELS)", f2(r["p_qp"]), "kN/m²"),
        ("Coeficiente μx⁺", f2(r["mu_xp"]), ""),
        ("Coeficiente μy⁺", f2(r["mu_yp"]), ""),
    ]
    if r["mu_xn"]:
        linhas.append(("Coeficiente μx⁻", f2(r["mu_xn"]), ""))
    if r["mu_yn"]:
        linhas.append(("Coeficiente μy⁻", f2(r["mu_yn"]), ""))
    linhas += [
        ("Momento Mx⁺ (ELU)", f2(r["Mx_pos"]), "kN·m/m"),
        ("Momento My⁺ (ELU)", f2(r["My_pos"]), "kN·m/m"),
    ]
    if r["Mx_neg"]:
        linhas.append(("Momento Mx⁻ (ELU)", f2(r["Mx_neg"]), "kN·m/m"))
    if r["My_neg"]:
        linhas.append(("Momento My⁻ (ELU)", f2(r["My_neg"]), "kN·m/m"))
    return linhas


def linhas_reacoes(d, r):
    if d["unidirecional"]:
        return [("Reação no apoio A", f2(r["Ra"]), "kN/m"),
                ("Reação no apoio B", f2(r["Rb"]), "kN/m")]
    linhas = []
    for chave, nome in (("Rx_ap", "Rx em borda apoiada"),
                        ("Rx_eng", "Rx' em borda engastada"),
                        ("Ry_ap", "Ry em borda apoiada"),
                        ("Ry_eng", "Ry' em borda engastada")):
        if r[chave] is not None:
            linhas.append((nome, f2(r[chave]), "kN/m"))
    linhas.append(("Rx crítico", f2(r["Rx"]), "kN/m"))
    linhas.append(("Ry crítico", f2(r["Ry"]), "kN/m"))
    return linhas


def linhas_armaduras(d, r):
    if d["unidirecional"]:
        mapa = [("principal_positiva", "Principal — momento positivo", "Aspos_calc", "Aspos"),
                ("principal_negativa", "Principal — momento negativo", "Asneg_calc", "Asneg"),
                ("distribuicao", "Distribuição", None, "Asdist")]
    else:
        mapa = [("x_positiva", "Direção X — positiva", "As_xp_calc", "As_xp"),
                ("y_positiva", "Direção Y — positiva", "As_yp_calc", "As_yp"),
                ("x_negativa", "Direção X — negativa", "As_xn_calc", "As_xn"),
                ("y_negativa", "Direção Y — negativa", "As_yn_calc", "As_yn")]
    linhas = []
    for chave, nome, calc, req in mapa:
        v = r["detalhamento"][chave]
        if v["n"] <= 0:
            continue
        linhas.append((
            nome,
            f2(r[calc]) if calc else "—",
            f2(r[req]),
            f"{v['n']} φ {d['phi']:g} mm",
            f2(v["s_cm"]),
            f2(v["As_fornecida"]),
            f2(v["livre_mm"] / 10),
            v["status"],
        ))
    return linhas


def linhas_flechas(d, r):
    ok250 = r["f_total"] <= r["lim_250"]
    ok350 = r["f_q"] <= r["lim_350"]
    return [
        ("Momento de fissuração Mr", f2(r["Mr"]), "kN·m/m", ""),
        ("Momento característico Ma", f2(r["Ma"]), "kN·m/m", ""),
        ("Estádio", r["estadio"], "", ""),
        ("Flecha imediata", f2(r["f_imediata"] * 100), "cm", ""),
        ("Flecha diferida", f2(r["f_diferida"] * 100), "cm", ""),
        ("Flecha final", f2(r["f_total"] * 100), "cm", situacao(ok250)),
        ("Limite lx/250", f2(r["lim_250"] * 100), "cm", ""),
        ("Flecha da parcela variável", f2(r["f_q"] * 100), "cm", situacao(ok350)),
        ("Referência lx/350", f2(r["lim_350"] * 100), "cm", ""),
    ]


# ---------------------------------------------------------------------------
# Desenho das vinculações (QPainter)
# ---------------------------------------------------------------------------

# Bordas engastadas de cada caso: (esquerda, direita, superior, inferior)
# Convenção do desenho: lx = horizontal (bordas superior/inferior têm comprimento lx),
#                       ly = vertical   (bordas esquerda/direita têm comprimento ly).
F, T = False, True
BORDAS_UNI = {
    1: (F, F, F, F),   # apoiada - apoiada
    2: (T, F, F, F),   # engastada - apoiada
    3: (T, T, F, F),   # engastada - engastada
}
# ATENÇÃO: confira esta tabela com a numeração usada no seu calculo.py
BORDAS_BI = {
    1: (F, F, F, F),   # 4 bordas apoiadas
    2: (F, F, F, T),   # 1 borda menor engastada
    3: (T, F, F, F),   # 1 borda maior engastada
    4: (T, F, F, T),   # 2 bordas adjacentes engastadas
    5: (F, F, T, T),   # 2 bordas menores engastadas
    6: (T, T, F, F),   # 2 bordas maiores engastadas
    7: (T, T, F, T),   # 3 bordas engastadas (1 menor apoiada)
    8: (T, F, T, T),   # 3 bordas engastadas (1 maior apoiada)
    9: (T, T, T, T),   # 4 bordas engastadas
}


class VinculacaoWidget(QWidget):
    """Desenha os casos de vinculação da laje e destaca o selecionado."""
    clicado = Signal(object)          # emite a chave do caso clicado

    COLUNAS = 3
    ALTURA_LEGENDA = 64

    def __init__(self):
        super().__init__()
        self._casos = {}              # chave -> descrição
        self._uni = True
        self._sel = None
        self._rects = {}
        self.setMinimumSize(520, 360)

    # ---------- API ----------
    def configurar(self, casos, unidirecional):
        self._casos = dict(casos)
        self._uni = unidirecional
        self._sel = None
        self.update()

    def selecionar(self, chave):
        self._sel = chave
        self.update()

    # ---------- interação ----------
    def mousePressEvent(self, ev):
        pos = ev.position()
        for k, r in self._rects.items():
            if r.contains(pos):
                self.clicado.emit(k)
                return

    # ---------- desenho ----------
    def _bordas(self, chave):
        tabela = BORDAS_UNI if self._uni else BORDAS_BI
        try:
            return tabela.get(int(chave), (F, F, F, F))
        except (TypeError, ValueError):
            return (F, F, F, F)

    def paintEvent(self, _ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._rects = {}
        n = len(self._casos)
        if n == 0:
            p.end()
            return

        pal = self.palette()
        txt = pal.color(pal.ColorRole.WindowText)
        destaque = pal.color(pal.ColorRole.Highlight)
        fundo = pal.color(pal.ColorRole.Base)
        suave = QColor(txt)
        suave.setAlpha(60)

        linhas = ceil(n / self.COLUNAS)
        area_h = self.height() - self.ALTURA_LEGENDA
        cw = self.width() / self.COLUNAS
        ch = area_h / linhas

        for i, (chave, desc) in enumerate(self._casos.items()):
            r, c = divmod(i, self.COLUNAS)
            cel = QRectF(c * cw, r * ch, cw, ch).adjusted(6, 6, -6, -6)
            self._rects[chave] = cel
            sel = (chave == self._sel)

            # cartão
            p.setPen(QPen(destaque if sel else suave, 3 if sel else 1))
            p.setBrush(fundo)
            p.drawRoundedRect(cel, 8, 8)

            # legenda do caso (embaixo do cartão)
            fonte = QFont(self.font())
            fonte.setPointSizeF(max(8.0, fonte.pointSizeF() - 1))
            fonte.setBold(sel)
            p.setFont(fonte)
            p.setPen(txt)
            alt_txt = 34
            rtxt = QRectF(cel.left() + 6, cel.bottom() - alt_txt,
                          cel.width() - 12, alt_txt - 4)
            p.drawText(rtxt, int(Qt.AlignmentFlag.AlignHCenter
                                 | Qt.AlignmentFlag.AlignVCenter
                                 | Qt.TextFlag.TextWordWrap), str(desc))

            # laje: retângulo proporcional, centralizado no espaço restante
            livre = QRectF(cel.left() + 18, cel.top() + 16,
                           cel.width() - 36, cel.height() - alt_txt - 30)
            prop = 0.75                                  # largura / altura
            h = min(livre.height(), livre.width() / prop)
            w = h * prop
            laje = QRectF(livre.center().x() - w / 2,
                          livre.center().y() - h / 2, w, h)
            self._desenhar_laje(p, laje, self._bordas(chave), chave,
                                txt, destaque if sel else txt)

        self._desenhar_legenda(p, txt)
        p.end()

    def _desenhar_laje(self, p, laje, bordas, chave, cor_txt, cor_laje):
        esq, dire, sup, inf = bordas
        esp = 8.0
        # hachuras das bordas engastadas (fora da laje)
        faixas = (
            (esq,  QRectF(laje.left() - esp, laje.top(), esp, laje.height())),
            (dire, QRectF(laje.right(), laje.top(), esp, laje.height())),
            (sup,  QRectF(laje.left(), laje.top() - esp, laje.width(), esp)),
            (inf,  QRectF(laje.left(), laje.bottom(), laje.width(), esp)),
        )
        for engastada, faixa in faixas:
            if engastada:
                self._hachurar(p, faixa, cor_txt)

        # contorno da laje
        p.setPen(QPen(cor_laje, 2.2))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRect(laje)

        # linha grossa nas bordas engastadas
        p.setPen(QPen(cor_txt, 3))
        if esq:
            p.drawLine(laje.topLeft(), laje.bottomLeft())
        if dire:
            p.drawLine(laje.topRight(), laje.bottomRight())
        if sup:
            p.drawLine(laje.topLeft(), laje.topRight())
        if inf:
            p.drawLine(laje.bottomLeft(), laje.bottomRight())

        # número do caso num círculo
        raio = max(min(laje.width(), laje.height()) * 0.17, 11)
        c = laje.center()
        p.setPen(QPen(cor_laje, 1.8))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(c, raio, raio)
        f = QFont(self.font())
        f.setBold(True)
        f.setPointSizeF(f.pointSizeF() + 1)
        p.setFont(f)
        p.setPen(cor_laje)
        p.drawText(QRectF(c.x() - raio, c.y() - raio, 2 * raio, 2 * raio),
                   int(Qt.AlignmentFlag.AlignCenter), str(chave))

    @staticmethod
    def _hachurar(p, faixa, cor):
        p.save()
        p.setClipRect(faixa)
        p.setPen(QPen(cor, 1.2))
        passo = 4
        h = faixa.height()
        x = int(-h)
        while x < faixa.width():
            p.drawLine(faixa.left() + x, faixa.bottom(),
                       faixa.left() + x + h, faixa.top())
            x += passo
        p.restore()

    def _desenhar_legenda(self, p, cor):
        y = self.height() - self.ALTURA_LEGENDA + 8
        f = QFont(self.font())
        f.setPointSizeF(max(8.0, f.pointSizeF() - 1))
        p.setFont(f)
        p.setPen(cor)
        # amostra: borda hachurada
        amostra = QRectF(14, y + 10, 26, 16)
        self._hachurar(p, QRectF(amostra.left(), amostra.top() - 7, amostra.width(), 7), cor)
        p.setPen(QPen(cor, 3))
        p.drawLine(amostra.topLeft(), amostra.topRight())
        p.setPen(cor)
        p.drawText(QRectF(50, y, self.width() - 60, 26),
                   int(Qt.AlignmentFlag.AlignVCenter),
                   "Borda hachurada: engastada   |   borda sem hachura: simplesmente apoiada")
        p.drawText(QRectF(14, y + 28, self.width() - 28, 24),
                   int(Qt.AlignmentFlag.AlignVCenter),
                   "lx = menor vão (horizontal)   |   ly = maior vão (vertical)   |   "
                   "clique em um desenho para selecionar o caso")


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------

def spin(minimo, maximo, valor, casas=2, sufixo="", passo=None):
    s = QDoubleSpinBox()
    s.setRange(minimo, maximo)
    s.setDecimals(casas)
    s.setValue(valor)
    if sufixo:
        s.setSuffix(f" {sufixo}")
    if passo:
        s.setSingleStep(passo)
    return s


def nova_tabela(colunas):
    t = QTableWidget(0, len(colunas))
    t.setHorizontalHeaderLabels(colunas)
    t.verticalHeader().setVisible(False)
    t.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    t.setAlternatingRowColors(True)
    t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
    t.horizontalHeader().setStretchLastSection(True)
    return t


def preencher(tabela, linhas):
    tabela.setRowCount(len(linhas))
    for i, linha in enumerate(linhas):
        for j, v in enumerate(linha):
            tabela.setItem(i, j, QTableWidgetItem(str(v)))
    tabela.resizeColumnsToContents()


def texto_mono():
    e = QPlainTextEdit()
    e.setReadOnly(True)
    e.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
    e.setFont(QFont("Consolas", 10))
    return e


class Janela(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Calculadora de Lajes Maciças — NBR 6118")
        self.resize(1280, 800)
        self.info = None

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        self.tabs.addTab(self._aba_tipo(), "1. Tipo de laje")
        self.tabs.addTab(self._aba_dados(), "2. Dados de entrada")
        self.tabs.addTab(self._aba_resultados(), "3. Resultados")
        self.tabs.setTabEnabled(1, False)
        self.tabs.setTabEnabled(2, False)

        self.atualizar_classificacao()

    # ---------------- aba 1 ----------------
    def _aba_tipo(self):
        self.vao_a = spin(0.1, 40, 4.0, 3, "m", 0.1)
        self.vao_b = spin(0.1, 40, 5.0, 3, "m", 0.1)
        self.vao_a.setKeyboardTracking(False)
        self.vao_b.setKeyboardTracking(False)
        self.vao_a.valueChanged.connect(self.atualizar_classificacao)
        self.vao_b.valueChanged.connect(self.atualizar_classificacao)

        g_vaos = QGroupBox("Dimensões da laje")
        f = QFormLayout(g_vaos)
        f.addRow("Vão A", self.vao_a)
        f.addRow("Vão B", self.vao_b)
        f.addRow(QLabel("A ordem não importa: o menor vão vira lx."))

        self.lbl_titulo = QLabel()
        self.lbl_titulo.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.lbl_lx = QLabel()
        self.lbl_ly = QLabel()
        self.lbl_lam = QLabel()
        self.lbl_nota = QLabel()
        self.lbl_nota.setWordWrap(True)
        g_class = QGroupBox("Classificação automática")
        c = QFormLayout(g_class)
        c.addRow(self.lbl_titulo)
        c.addRow("lx (menor vão)", self.lbl_lx)
        c.addRow("ly (maior vão)", self.lbl_ly)
        c.addRow("λ = ly/lx", self.lbl_lam)
        c.addRow(self.lbl_nota)

        self.cmb_vinc = QComboBox()
        self.cmb_vinc.currentIndexChanged.connect(self.vinculacao_mudou)
        g_vinc = QGroupBox("Vinculação")
        v = QVBoxLayout(g_vinc)
        v.addWidget(QLabel("Escolha o caso no combo ou clicando no desenho:"))
        v.addWidget(self.cmb_vinc)

        esquerda = QVBoxLayout()
        esquerda.addWidget(g_vaos)
        esquerda.addWidget(g_class)
        esquerda.addWidget(g_vinc)
        esquerda.addStretch()
        w_esq = QWidget()
        w_esq.setLayout(esquerda)
        w_esq.setMaximumWidth(430)

        self.img = VinculacaoWidget()
        self.img.clicado.connect(self.selecionar_caso_clicado)

        aba = QWidget()
        lay = QHBoxLayout(aba)
        lay.addWidget(w_esq)
        lay.addWidget(self.img, 1)
        return aba

    def atualizar_classificacao(self):
        try:
            self.info = calculo.classificar_laje(self.vao_a.value(), self.vao_b.value())
        except ValueError as e:
            QMessageBox.warning(self, "Dimensões inválidas", str(e))
            return
        i = self.info
        self.lbl_titulo.setText(i["titulo"])
        self.lbl_lx.setText(f"{f2(i['lx'], 3)} m")
        self.lbl_ly.setText(f"{f2(i['ly'], 3)} m")
        self.lbl_lam.setText(f2(i["lambda"], 3))
        self.lbl_nota.setText(i["nota"])

        # Ao trocar as dimensões, a vinculação anterior é descartada.
        self.cmb_vinc.blockSignals(True)
        self.cmb_vinc.clear()
        self.cmb_vinc.addItem("— selecione a vinculação —", None)
        for k, txt in i["casos"].items():
            self.cmb_vinc.addItem(f"{k} — {txt}", k)
        self.cmb_vinc.blockSignals(False)
        self.tabs.setTabEnabled(1, False)
        self.tabs.setTabEnabled(2, False)
        self.img.configurar(i["casos"], i["unidirecional"])
        self.atualizar_estimativa()

    def vinculacao_mudou(self):
        self.tabs.setTabEnabled(1, self.cmb_vinc.currentData() is not None)
        self.tabs.setTabEnabled(2, False)
        self.img.selecionar(self.cmb_vinc.currentData())
        self.atualizar_estimativa()

    def selecionar_caso_clicado(self, chave):
        idx = self.cmb_vinc.findData(chave)
        if idx >= 0:
            self.cmb_vinc.setCurrentIndex(idx)

    # ---------------- aba 2 ----------------
    def _aba_dados(self):
        self.cmb_caa = QComboBox()
        for txt, k in (("I — Rural", "I"), ("II — Urbana", "II"),
                       ("III — Marinha/Industrial", "III"), ("IV — Muito agressiva", "IV")):
            self.cmb_caa.addItem(txt, k)
        self.cmb_caa.setCurrentIndex(1)
        self.phi = spin(4, 25, 8.0, 1, "mm", 0.5)
        self.q = spin(0, 50, 2.0, 2, "kN/m²", 0.5)
        self.h = spin(1, 100, 12.0, 1, "cm", 0.5)
        self.cmb_caa.currentIndexChanged.connect(self.atualizar_fixos)
        self.phi.valueChanged.connect(self.atualizar_estimativa)

        g_in = QGroupBox("Dados informados")
        f = QFormLayout(g_in)
        f.addRow("Classe de agressividade (CAA)", self.cmb_caa)
        f.addRow("Bitola das barras principais φ", self.phi)
        f.addRow("Carga variável característica qk", self.q)
        f.addRow("Espessura adotada h", self.h)
        self.lbl_est = QLabel()
        self.lbl_est.setWordWrap(True)
        f.addRow(self.lbl_est)

        self.lbl_fck = QLabel()
        self.lbl_cob = QLabel()
        g_fix = QGroupBox("Hipóteses fixas do perfil acadêmico (não editáveis)")
        x = QFormLayout(g_fix)
        x.addRow("Tipo de laje", QLabel("Piso não em balanço (h mínimo = 8 cm)"))
        x.addRow("fck (mínimo da CAA)", self.lbl_fck)
        x.addRow("Cobrimento nominal", self.lbl_cob)
        x.addRow("Aço", QLabel("CA-50 (fyk = 500 MPa)"))
        x.addRow("Agregado", QLabel("granito/gnaisse (αE = 1,00)"))
        x.addRow("Peso específico do concreto", QLabel("25,00 kN/m³"))
        x.addRow("Carga permanente adicional global", QLabel("1,28 kN/m²"))
        x.addRow("ψ2", QLabel("0,30"))
        x.addRow("Fluência", QLabel("t0 = 14 dias; t = 70 meses"))

        btn = QPushButton("Calcular")
        btn.setMinimumHeight(40)
        btn.clicked.connect(self.calcular)

        col = QVBoxLayout()
        col.addWidget(g_in)
        col.addWidget(g_fix)
        col.addWidget(btn)
        col.addStretch()
        aba = QWidget()
        aba.setLayout(col)
        self.atualizar_fixos()
        return aba

    def atualizar_fixos(self):
        caa = self.cmb_caa.currentData()
        self.lbl_fck.setText(f"C{calculo.FCK_MIN_CAA[caa]} ({calculo.FCK_MIN_CAA[caa]} MPa)")
        self.lbl_cob.setText(f"{calculo.COB_NOMINAL[caa]} mm")
        self.atualizar_estimativa()

    def atualizar_estimativa(self):
        if self.info is None or not hasattr(self, "lbl_est"):
            return
        try:
            vinc = self.cmb_vinc.currentData()
            caso = 1 if self.info["unidirecional"] else (vinc or 1)
            cob = calculo.COB_NOMINAL[self.cmb_caa.currentData()]
            _, h_est, l_star, n = calculo.estimar_h_bastos(
                self.info["lx"], self.info["ly"], caso, cob / 1000, self.phi.value() / 1000)
            self.lbl_est.setText(
                f"Estimativa (Bastos): l* = {f2(l_star, 3)} m; n = {n}; "
                f"h ≈ {f2(h_est * 100, 1)} cm. Mínimo normativo: 8,0 cm.")
        except (ValueError, KeyError):
            self.lbl_est.setText("")

    # ---------------- aba 3 ----------------
    def _aba_resultados(self):
        self.txt_parecer = texto_mono()
        self.tab_cargas = nova_tabela(["Item", "Valor", "Unidade"])
        self.tab_reacoes = nova_tabela(["Item", "Valor", "Unidade"])
        self.tab_arm = nova_tabela(["Armadura", "As calculada (cm²/m)", "As adotada (cm²/m)",
                                    "Barras/m", "Espaçamento (cm)", "As fornecida (cm²/m)",
                                    "Espaç. livre (cm)", "Verificação geométrica"])
        self.tab_flecha = nova_tabela(["Item", "Valor", "Unidade", "Situação"])
        self.txt_memoria = texto_mono()

        self.res_tabs = QTabWidget()
        self.res_tabs.addTab(self.txt_parecer, "Parecer final")
        self.res_tabs.addTab(self.tab_cargas, "Cargas e momentos")
        self.res_tabs.addTab(self.tab_reacoes, "Reações")
        self.res_tabs.addTab(self.tab_arm, "Armaduras")
        self.res_tabs.addTab(self.tab_flecha, "Flechas")
        self.res_tabs.addTab(self.txt_memoria, "Memória completa")

        btn_pdf = QPushButton("Exportar memória em PDF")
        btn_pdf.clicked.connect(self.exportar_pdf)
        lay = QVBoxLayout()
        lay.addWidget(self.res_tabs)
        lay.addWidget(btn_pdf)
        aba = QWidget()
        aba.setLayout(lay)
        return aba

    def calcular(self):
        try:
            dados = montar_dados_padrao(
                self.vao_a.value(), self.vao_b.value(),
                self.cmb_vinc.currentData(), self.cmb_caa.currentData(),
                self.phi.value(), self.q.value(), self.h.value())
            d, r, partes = gerar_memoria(dados)
        except (ValueError, KeyError) as e:
            QMessageBox.warning(self, "Erro nos dados", str(e))
            return
        self.txt_parecer.setPlainText(partes["parecer"])
        self.txt_memoria.setPlainText(partes["completo"])
        preencher(self.tab_cargas, linhas_cargas_momentos(d, r))
        preencher(self.tab_reacoes, linhas_reacoes(d, r))
        preencher(self.tab_arm, linhas_armaduras(d, r))
        preencher(self.tab_flecha, linhas_flechas(d, r))
        self.tabs.setTabEnabled(2, True)
        self.tabs.setCurrentIndex(2)
        self.res_tabs.setCurrentIndex(0)

    def exportar_pdf(self):
        caminho, _ = QFileDialog.getSaveFileName(
            self, "Salvar memória de cálculo", "memoria_calculo.pdf", "PDF (*.pdf)")
        if not caminho:
            return
        impressora = QPrinter(QPrinter.PrinterMode.HighResolution)
        impressora.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        impressora.setOutputFileName(caminho)
        self.txt_memoria.print_(impressora)