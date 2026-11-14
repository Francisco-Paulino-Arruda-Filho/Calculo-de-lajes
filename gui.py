import io
import os
import sys
from contextlib import redirect_stdout
from math import ceil

from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QPixmap
from PySide6.QtPrintSupport import QPrinter
from PySide6.QtWidgets import (
    QApplication, QAbstractItemView, QComboBox, QDoubleSpinBox,
    QFileDialog, QFormLayout, QFrame, QGroupBox, QHBoxLayout,
    QHeaderView, QLabel, QMainWindow, QMessageBox, QPlainTextEdit,
    QPushButton, QScrollArea, QSizePolicy, QSplitter, QTabWidget,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget
)

import calculo


# ---------------------------------------------------------------------------
# Núcleo sem interface
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


def montar_dados_padrao(
    lx, ly, vinculacao, caa, phi, q, h_cm,
    g2k=0.0, fck=None, cob=None, tipo="piso",
    fyk=500.0, agregado_id="2", aco="CA-50"
):
    """Monta os dados da GUI sem impor cargas adicionais fixas."""
    info = calculo.classificar_laje(lx, ly)
    uni = info["unidirecional"]

    if vinculacao not in info["casos"]:
        raise ValueError("Selecione a vinculação da laje.")
    if tipo == "balanco":
        raise ValueError("O modelo de lajes em balanço ainda não está implementado.")

    cob_min = calculo.COB_NOMINAL[caa]
    fck_min = calculo.FCK_MIN_CAA[caa]
    cob = float(cob_min if cob is None else cob)
    fck = float(fck_min if fck is None else fck)
    if fck < fck_min:
        raise ValueError(f"Para CAA {caa}, o fck mínimo é {fck_min} MPa.")
    if cob < cob_min:
        raise ValueError(f"Para CAA {caa}, o cobrimento mínimo é {cob_min} mm.")

    try:
        agregado, alpha_E = calculo.AGREGADOS[str(agregado_id)]
    except KeyError as exc:
        raise ValueError("Tipo de agregado inválido.") from exc

    caso = 1 if uni else vinculacao
    apoio_1d = vinculacao if uni else None
    h = float(h_cm) / 100.0
    h_min = calculo.altura_minima(tipo)
    if h < h_min:
        raise ValueError(
            f"A espessura mínima para {tipo} sem balanço é {h_min * 100:.0f} cm."
        )

    _, h_est, _, _ = calculo.estimar_h_bastos(
        info["lx"], info["ly"], caso, cob / 1000, phi / 1000
    )

    return dict(
        lx=info["lx"], ly=info["ly"], caso=caso,
        unidirecional=uni, apoio_1d=apoio_1d, tipo=tipo,
        caa=caa, cob=cob, cob_nbr=cob_min, fck=fck,
        fyk=float(fyk), aco=aco, phi=float(phi),
        agregado=agregado, alpha_E=alpha_E, gc=25.0,
        g_contrapiso=0.0, g_revest_inf=0.0, g_piso=0.0,
        g_paredes=0.0, g_outros=float(g2k), q=float(q),
        psi2=0.30, h=h, h_min=h_min, h_est=h_est,
        t0=14.0 / 30.0, tinf=70.0,
    )


def gerar_memoria(dados):
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

    partes["completo"] = (
        partes["memoria"]
        + partes["detalhamento"]
        + partes["parecer"]
        + partes["auditoria"]
    )

    return d, r, partes


# ---------------------------------------------------------------------------
# Linhas das tabelas de resultados
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
            linhas.append((
                "Momento negativo de cálculo (módulo)",
                f2(r["Mneg"]),
                "kN·m/m"
            ))

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
        return [
            ("Reação no apoio A", f2(r["Ra"]), "kN/m"),
            ("Reação no apoio B", f2(r["Rb"]), "kN/m")
        ]

    linhas = []

    for chave, nome in (
        ("Rx_ap", "Rx em borda apoiada"),
        ("Rx_eng", "Rx' em borda engastada"),
        ("Ry_ap", "Ry em borda apoiada"),
        ("Ry_eng", "Ry' em borda engastada")
    ):
        if r[chave] is not None:
            linhas.append((nome, f2(r[chave]), "kN/m"))

    linhas.append(("Rx crítico", f2(r["Rx"]), "kN/m"))
    linhas.append(("Ry crítico", f2(r["Ry"]), "kN/m"))

    return linhas


def linhas_armaduras(d, r):
    if d["unidirecional"]:
        mapa = [
            ("principal_positiva", "Principal — momento positivo", "Aspos_calc", "Aspos"),
            ("principal_negativa", "Principal — momento negativo", "Asneg_calc", "Asneg"),
            ("distribuicao", "Distribuição", None, "Asdist")
        ]
    else:
        mapa = [
            ("x_positiva", "Direção X — positiva", "As_xp_calc", "As_xp"),
            ("y_positiva", "Direção Y — positiva", "As_yp_calc", "As_yp"),
            ("x_negativa", "Direção X — negativa", "As_xn_calc", "As_xn"),
            ("y_negativa", "Direção Y — negativa", "As_yn_calc", "As_yn")
        ]

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
# Desenho das vinculações
# ---------------------------------------------------------------------------

F, T = False, True

BORDAS_UNI = {
    1: (F, F, F, F),
    2: (T, F, F, F),
    3: (T, T, F, F),
}

BORDAS_BI = {
    1: (F, F, F, F),
    2: (F, F, F, T),
    3: (T, F, F, F),
    4: (T, F, F, T),
    5: (F, F, T, T),
    6: (T, T, F, F),
    7: (T, T, F, T),
    8: (T, F, T, T),
    9: (T, T, T, T),
}


class VinculacaoWidget(QWidget):

    clicado = Signal(object)

    COLUNAS = 3
    ALTURA_LEGENDA = 64

    def __init__(self):
        super().__init__()

        self._casos = {}
        self._uni = True
        self._sel = None
        self._rects = {}

        self.setMinimumWidth(340)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )
        self._altura_cartao = 158
        self._atualizar_altura()

    def _atualizar_altura(self):
        linhas = max(1, ceil(len(self._casos) / self.COLUNAS))
        self.setMinimumHeight(linhas * self._altura_cartao + self.ALTURA_LEGENDA)
        self.resize(self.width(), self.minimumHeight())

    def configurar(self, casos, unidirecional):
        self._casos = dict(casos)
        self._uni = unidirecional
        self._sel = None
        self._atualizar_altura()
        self.updateGeometry()
        self.update()

    def selecionar(self, chave):
        self._sel = chave
        self.update()

    def mousePressEvent(self, ev):
        pos = ev.position()

        for k, r in self._rects.items():
            if r.contains(pos):
                self.clicado.emit(k)
                return

        super().mousePressEvent(ev)

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
        area_h = max(1, self.height() - self.ALTURA_LEGENDA)

        cw = self.width() / self.COLUNAS
        ch = area_h / linhas

        for i, (chave, desc) in enumerate(self._casos.items()):
            r, c = divmod(i, self.COLUNAS)

            cel = QRectF(
                c * cw,
                r * ch,
                cw,
                ch
            ).adjusted(6, 6, -6, -6)

            self._rects[chave] = cel
            sel = chave == self._sel

            p.setPen(QPen(destaque if sel else suave, 3 if sel else 1))
            p.setBrush(fundo)
            p.drawRoundedRect(cel, 8, 8)

            fonte = QFont(self.font())
            fonte.setPointSizeF(max(8.0, fonte.pointSizeF() - 1))
            fonte.setBold(sel)

            p.setFont(fonte)
            p.setPen(txt)

            alt_txt = 34

            rtxt = QRectF(
                cel.left() + 6,
                cel.bottom() - alt_txt,
                cel.width() - 12,
                alt_txt - 4
            )

            p.drawText(
                rtxt,
                int(
                    Qt.AlignmentFlag.AlignHCenter
                    | Qt.AlignmentFlag.AlignVCenter
                    | Qt.TextFlag.TextWordWrap
                ),
                str(desc)
            )

            livre = QRectF(
                cel.left() + 18,
                cel.top() + 16,
                cel.width() - 36,
                cel.height() - alt_txt - 30
            )

            prop = 0.75

            h = min(livre.height(), livre.width() / prop)
            w = h * prop

            laje = QRectF(
                livre.center().x() - w / 2,
                livre.center().y() - h / 2,
                w,
                h
            )

            self._desenhar_laje(
                p,
                laje,
                self._bordas(chave),
                chave,
                txt,
                destaque if sel else txt
            )

        self._desenhar_legenda(p, txt)
        p.end()

    def _desenhar_laje(self, p, laje, bordas, chave, cor_txt, cor_laje):
        esq, dire, sup, inf = bordas
        esp = 8.0

        faixas = (
            (esq, QRectF(laje.left() - esp, laje.top(), esp, laje.height())),
            (dire, QRectF(laje.right(), laje.top(), esp, laje.height())),
            (sup, QRectF(laje.left(), laje.top() - esp, laje.width(), esp)),
            (inf, QRectF(laje.left(), laje.bottom(), laje.width(), esp)),
        )

        for engastada, faixa in faixas:
            if engastada:
                self._hachurar(p, faixa, cor_txt)

        p.setPen(QPen(cor_laje, 2.2))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRect(laje)

        p.setPen(QPen(cor_txt, 3))

        if esq:
            p.drawLine(laje.topLeft(), laje.bottomLeft())

        if dire:
            p.drawLine(laje.topRight(), laje.bottomRight())

        if sup:
            p.drawLine(laje.topLeft(), laje.topRight())

        if inf:
            p.drawLine(laje.bottomLeft(), laje.bottomRight())

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

        p.drawText(
            QRectF(c.x() - raio, c.y() - raio, 2 * raio, 2 * raio),
            int(Qt.AlignmentFlag.AlignCenter),
            str(chave)
        )

    @staticmethod
    def _hachurar(p, faixa, cor):
        p.save()
        p.setClipRect(faixa)
        p.setPen(QPen(cor, 1.2))

        passo = 4
        h = faixa.height()
        x = int(-h)

        while x < faixa.width():
            p.drawLine(
                faixa.left() + x,
                faixa.bottom(),
                faixa.left() + x + h,
                faixa.top()
            )
            x += passo

        p.restore()

    def _desenhar_legenda(self, p, cor):
        y = self.height() - self.ALTURA_LEGENDA + 8

        f = QFont(self.font())
        f.setPointSizeF(max(8.0, f.pointSizeF() - 1))

        p.setFont(f)
        p.setPen(cor)

        amostra = QRectF(14, y + 10, 26, 16)

        self._hachurar(
            p,
            QRectF(
                amostra.left(),
                amostra.top() - 7,
                amostra.width(),
                7
            ),
            cor
        )

        p.setPen(QPen(cor, 3))
        p.drawLine(amostra.topLeft(), amostra.topRight())

        p.setPen(cor)

        p.drawText(
            QRectF(50, y, self.width() - 60, 26),
            int(Qt.AlignmentFlag.AlignVCenter),
            "Borda hachurada: engastada | borda sem hachura: simplesmente apoiada"
        )

        p.drawText(
            QRectF(14, y + 28, self.width() - 28, 24),
            int(Qt.AlignmentFlag.AlignVCenter),
            "lx = menor vão (horizontal) | ly = maior vão (vertical)"
        )


class DesenhosGeometria(QWidget):
    """Planta proporcional e vista esquemática da laje."""

    def __init__(self):
        super().__init__()
        self.lx = 3.0
        self.ly = 5.0
        self.setMinimumHeight(170)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def configurar(self, lx, ly):
        self.lx, self.ly = float(lx), float(ly)
        self.update()

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QColor("#FFFFFF"))
        w, h = self.width(), self.height()
        p.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        p.setPen(QColor("#243B53"))
        p.drawText(12, 20, "PLANTA DA LAJE")

        # Reserva espaço para os dois rótulos, evitando que o texto vertical
        # seja cortado pela margem esquerda do widget.
        area = QRectF(72, 34, max(70, w - 100), h - 78)
        lx = max(self.lx, 0.001)
        ly = max(self.ly, 0.001)
        escala = min(area.width() / lx, area.height() / ly)
        rw, rh = lx * escala, ly * escala
        x = area.center().x() - rw / 2
        y = area.center().y() - rh / 2

        p.setPen(QPen(QColor("#243B53"), 1.8))
        p.setBrush(QColor("#DCEBFA"))
        p.drawRect(QRectF(x, y, rw, rh))

        # lx é sempre o menor vão e aparece na dimensão horizontal;
        # ly é o maior vão e aparece na dimensão vertical.
        p.setPen(QPen(QColor("#2563D9"), 1.2))
        y_dim = min(h - 8, y + rh + 17)
        p.drawLine(int(x), int(y_dim), int(x + rw), int(y_dim))
        p.drawText(
            QRectF(x - 28, y_dim + 2, rw + 56, 20),
            int(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop),
            f"Lx = {self.lx:g} m"
        )
        # Dimensão vertical Ly
        p.setPen(QPen(QColor("#2563D9"), 1.2))

        # Linha vertical próxima ao retângulo
        x_dim = x - 12
        p.drawLine(
            int(x_dim), int(y),
            int(x_dim), int(y + rh)
        )

        # Pequenos traços nas extremidades
        p.drawLine(int(x_dim), int(y), int(x - 5), int(y))
        p.drawLine(int(x_dim), int(y + rh), int(x - 5), int(y + rh))

        # Texto vertical
        p.save()
        p.translate(x - 27, y + rh / 2)
        p.rotate(-90)
        p.drawText(
            QRectF(-rh / 2, -10, rh, 20),
            int(Qt.AlignmentFlag.AlignCenter),
            f"Ly = {self.ly:g} m"
        )
        p.restore()

        # A vista esquemática lateral foi removida para simplificar a área
        # de geometria e priorizar o espaço dos casos de vinculação.
        p.end()


# ---------------------------------------------------------------------------
# Componentes auxiliares
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

    s.setMinimumHeight(38)
    return s


def nova_tabela(colunas):
    t = QTableWidget(0, len(colunas))
    t.setHorizontalHeaderLabels(colunas)
    t.verticalHeader().setVisible(False)

    t.setEditTriggers(
        QAbstractItemView.EditTrigger.NoEditTriggers
    )

    t.setAlternatingRowColors(True)

    t.horizontalHeader().setSectionResizeMode(
        QHeaderView.ResizeMode.ResizeToContents
    )

    t.horizontalHeader().setStretchLastSection(True)

    return t


def preencher(tabela, linhas):
    tabela.setRowCount(len(linhas))

    for i, linha in enumerate(linhas):
        for j, v in enumerate(linha):
            item = QTableWidgetItem(str(v))

            if str(v) == "ATENDE":
                item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                item.setForeground(QColor("#16834A"))

            elif str(v) == "NÃO ATENDE":
                item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                item.setForeground(QColor("#C0392B"))

            tabela.setItem(i, j, item)

    tabela.resizeColumnsToContents()


def texto_mono():
    e = QPlainTextEdit()
    e.setReadOnly(True)
    e.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
    e.setFont(QFont("Consolas", 10))
    return e


# ---------------------------------------------------------------------------
# Interface principal
# ---------------------------------------------------------------------------

class Janela(QMainWindow):

    ESTILO = """
        QMainWindow, QWidget#appBody {
            background: #F3F6FB;
            color: #182638;
            font-family: "Segoe UI", "Arial", sans-serif;
            font-size: 10pt;
        }

        QFrame#appHeader {
            background: #132B45;
            border: 1px solid #1B3B5D;
            border-radius: 16px;
        }

        QLabel#brandMark {
            background: #2F6FED;
            color: #FFFFFF;
            border-radius: 12px;
            font-size: 17pt;
            font-weight: 800;
            min-width: 48px;
            max-width: 48px;
            min-height: 48px;
            max-height: 48px;
        }

        QLabel#headerTitle {
            color: #FFFFFF;
            font-size: 19pt;
            font-weight: 700;
        }

        QLabel#headerSubtitle {
            color: #B8C9DA;
            font-size: 9.5pt;
        }

        QLabel#headerBadge {
            background: #203F60;
            color: #DCEBFA;
            border: 1px solid #355B7E;
            border-radius: 9px;
            padding: 8px 13px;
            font-weight: 700;
        }

        QLabel#pageTitle {
            color: #172B43;
            font-size: 17pt;
            font-weight: 700;
        }

        QLabel#pageSubtitle {
            color: #66778B;
            font-size: 9.5pt;
        }

        QLabel#footerText {
            color: #718096;
            font-size: 8.5pt;
        }

        QTabWidget::pane {
            border: 0;
            background: transparent;
            top: 0px;
        }

        QTabBar::tab {
            background: #E7EDF5;
            color: #53657A;
            border: 1px solid #E0E7F0;
            border-radius: 9px;
            padding: 11px 19px;
            margin: 0 7px 8px 0;
            min-width: 100px;
            font-weight: 600;
        }

        QTabBar::tab:selected {
            background: #2563D9;
            color: #FFFFFF;
            border-color: #2563D9;
        }

        QTabBar::tab:disabled {
            color: #A5B1BF;
            background: #EEF2F7;
        }

        QGroupBox {
            background: #FFFFFF;
            border: 1px solid #E0E7F0;
            border-radius: 13px;
            margin-top: 15px;
            padding: 14px 14px 10px 14px;
            font-weight: 650;
            color: #243B53;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            left: 13px;
            top: 2px;
            padding: 0 6px;
            color: #314B67;
        }

        QLabel {
            color: #34465B;
        }

        QLabel#classificationBadge {
            background: #EAF2FF;
            color: #1E56B5;
            border: 1px solid #D4E4FF;
            border-radius: 8px;
            padding: 9px 11px;
            font-size: 11pt;
            font-weight: 700;
        }

        QLabel#helperText {
            color: #6C7D90;
            font-size: 9pt;
        }

        QLabel#estimateCallout {
            background: #F0F6FF;
            color: #315A8E;
            border: 1px solid #DCEAFF;
            border-radius: 9px;
            padding: 10px;
            font-size: 9pt;
        }

        QComboBox, QDoubleSpinBox {
            background: #FFFFFF;
            color: #1D2D40;
            border: 1px solid #D6E0EB;
            border-radius: 8px;
            padding: 7px 9px;
            min-height: 25px;
        }

        QComboBox QAbstractItemView {
            background-color: #FFFFFF;
            color: #1D2D40;
            border: 1px solid #D6E0EB;
            selection-background-color: #E8F1FF;
            selection-color: #183B70;
            outline: none;
        }

        QComboBox QAbstractItemView::item {
            color: #1D2D40;
            background-color: #FFFFFF;
            padding: 8px 10px;
            min-height: 24px;
        }

        QComboBox QAbstractItemView::item:hover {
            background-color: #F0F6FF;
            color: #1D2D40;
        }

        QComboBox QAbstractItemView::item:selected {
            background-color: #E8F1FF;
            color: #183B70;
        }

        QComboBox:hover, QDoubleSpinBox:hover {
            border-color: #A9BED8;
        }

        QComboBox:focus, QDoubleSpinBox:focus {
            border: 1px solid #3778E5;
            background: #FFFFFF;
        }

        QPushButton {
            border-radius: 9px;
            padding: 10px 17px;
            font-weight: 700;
            min-height: 20px;
        }

        QPushButton#primaryButton {
            background: #2563D9;
            color: #FFFFFF;
            border: 1px solid #2563D9;
        }

        QPushButton#primaryButton:hover {
            background: #1D55BF;
        }

        QPushButton#primaryButton:pressed {
            background: #17469F;
        }

        QPushButton#secondaryButton {
            background: #FFFFFF;
            color: #285A9E;
            border: 1px solid #C9D8EA;
        }

        QPushButton#secondaryButton:hover {
            background: #F0F6FF;
            border-color: #8FB2E0;
        }

        QTableWidget {
            background: #FFFFFF;
            alternate-background-color: #F7F9FC;
            color: #26384B;
            border: 1px solid #E0E7F0;
            border-radius: 9px;
            gridline-color: transparent;
            selection-background-color: #E8F1FF;
            selection-color: #183B70;
        }

        QTableWidget::item {
            padding: 8px 7px;
            border: 0;
            border-bottom: 1px solid #EDF1F6;
        }

        QHeaderView::section {
            background: #EDF2F8;
            color: #42566D;
            padding: 10px 8px;
            border: 0;
            border-bottom: 1px solid #DCE5EF;
            font-weight: 700;
        }

        QPlainTextEdit {
            background: #FFFFFF;
            color: #26384B;
            border: 1px solid #E0E7F0;
            border-radius: 9px;
            padding: 12px;
            selection-background-color: #DCEAFF;
        }

        QScrollBar:vertical {
            background: transparent;
            width: 10px;
            margin: 2px;
        }

        QScrollBar::handle:vertical {
            background: #C7D3E0;
            min-height: 28px;
            border-radius: 5px;
        }

        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {
            height: 0px;
        }

        QScrollBar:horizontal {
            background: transparent;
            height: 10px;
            margin: 2px;
        }

        QScrollBar::handle:horizontal {
            background: #C7D3E0;
            min-width: 28px;
            border-radius: 5px;
        }

        QScrollBar::add-line:horizontal,
        QScrollBar::sub-line:horizontal {
            width: 0px;
        }

        QFrame#metricCard {
            background: #FFFFFF;
            border: 1px solid #E0E7F0;
            border-radius: 12px;
        }

        QLabel#metricTitle {
            color: #75859A;
            font-size: 8pt;
            font-weight: 800;
        }

        QLabel#metricValue {
            color: #193B61;
            font-size: 17pt;
            font-weight: 750;
        }

        QLabel#metricHint {
            color: #8290A1;
            font-size: 8pt;
        }

        QSplitter::handle {
            background: #E0E7F0;
            width: 5px;
        }

        QSplitter::handle:hover {
            background: #9BB9DF;
        }
    """

    def __init__(self):
        super().__init__()

        self.setWindowTitle(
            "SlabCalc"
        )

        self.resize(1360, 900)
        self.setMinimumSize(900, 650)
        self.setStyleSheet(self.ESTILO)

        self.info = None
        self.metric_values = {}

        central = QWidget()
        central.setObjectName("appBody")

        root = QVBoxLayout(central)
        root.setContentsMargins(20, 16, 20, 12)
        root.setSpacing(12)

        root.addWidget(self._criar_cabecalho())

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setMovable(False)

        root.addWidget(self.tabs, 1)

        rodape = QLabel(
            "FERRAMENTA DE APOIO ACADÊMICO"
        )

        rodape.setObjectName("footerText")
        rodape.setAlignment(
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignVCenter
        )

        root.addWidget(rodape)

        self.setCentralWidget(central)

        self.tabs.addTab(self._aba_tipo(), "01  Geometria")
        self.tabs.addTab(self._aba_dados(), "02  Parâmetros")
        self.tabs.addTab(self._aba_resultados(), "03  Resultados")

        self.tabs.setTabEnabled(1, False)
        self.tabs.setTabEnabled(2, False)

        self.atualizar_classificacao()

    def _criar_cabecalho(self):
        header = QFrame()
        header.setObjectName("appHeader")

        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(15)

        marca = QLabel("SC")
        marca.setObjectName("brandMark")
        marca.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(marca)

        textos = QVBoxLayout()
        textos.setSpacing(3)

        titulo = QLabel("SlabCalc")
        titulo.setObjectName("headerTitle")

        subtitulo = QLabel(
            "Dimensionamento, verificações e memória de cálculo\nDo cálculo à compreensão estrutural."
        )
        subtitulo.setObjectName("headerSubtitle")

        textos.addWidget(titulo)
        textos.addWidget(subtitulo)

        layout.addLayout(textos)
        layout.addStretch(1)

        logo = QLabel()
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        caminho = caminho_recurso("ifce_logo.png")
        pm = QPixmap(caminho) if caminho else QPixmap()

        if not pm.isNull():
            dpr = self.devicePixelRatioF()
            pm = pm.scaledToHeight(
                int(60 * dpr),
                Qt.TransformationMode.SmoothTransformation
            )
            pm.setDevicePixelRatio(dpr)

            logo.setObjectName("headerLogo")
            logo.setPixmap(pm)
        else:
            logo.setObjectName("headerBadge")
            logo.setText("NBR 6118")

        layout.addWidget(
            logo,
            0,
            Qt.AlignmentFlag.AlignVCenter
        )

        return header

    @staticmethod
    def _intro(titulo, subtitulo):
        bloco = QWidget()

        layout = QVBoxLayout(bloco)
        layout.setContentsMargins(0, 0, 0, 2)
        layout.setSpacing(4)

        h = QLabel(titulo)
        h.setObjectName("pageTitle")

        s = QLabel(subtitulo)
        s.setObjectName("pageSubtitle")
        s.setWordWrap(True)

        layout.addWidget(h)
        layout.addWidget(s)

        return bloco

    @staticmethod
    def _criar_metrica(titulo, valor, dica):
        card = QFrame()
        card.setObjectName("metricCard")

        card.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )

        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(4)

        lbl_titulo = QLabel(titulo.upper())
        lbl_titulo.setObjectName("metricTitle")

        lbl_valor = QLabel(valor)
        lbl_valor.setObjectName("metricValue")

        lbl_dica = QLabel(dica)
        lbl_dica.setObjectName("metricHint")
        lbl_dica.setWordWrap(True)

        layout.addWidget(lbl_titulo)
        layout.addWidget(lbl_valor)
        layout.addWidget(lbl_dica)

        return card, lbl_valor, lbl_dica

    # -----------------------------------------------------------------------
    # ETAPA 1 — GEOMETRIA
    # -----------------------------------------------------------------------

    def _aba_tipo(self):
        pagina = QWidget()

        lay = QVBoxLayout(pagina)
        lay.setContentsMargins(18, 12, 18, 14)
        lay.setSpacing(12)

        lay.addWidget(
            self._intro(
                "Geometria e condições de apoio",
                "Informe os vãos da laje. A classificação é feita automaticamente; "
                "em seguida, selecione a vinculação correspondente."
            )
        )

        self.vao_a = spin(0.1, 40, 4.0, 3, "m", 0.1)
        self.vao_b = spin(0.1, 40, 5.0, 3, "m", 0.1)

        self.vao_a.setKeyboardTracking(False)
        self.vao_b.setKeyboardTracking(False)

        self.vao_a.valueChanged.connect(
            self.atualizar_classificacao
        )

        self.vao_b.valueChanged.connect(
            self.atualizar_classificacao
        )

        # Painel de dimensões
        g_vaos = QGroupBox("Dimensões da laje")

        f = QFormLayout(g_vaos)
        f.setLabelAlignment(
            Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignVCenter
        )

        f.setHorizontalSpacing(12)
        f.setVerticalSpacing(10)

        f.addRow("Vão A", self.vao_a)
        f.addRow("Vão B", self.vao_b)

        ordem = QLabel(
            "A ordem não importa: o menor vão será considerado lx."
        )

        ordem.setObjectName("helperText")
        ordem.setWordWrap(True)

        f.addRow(ordem)

        # Classificação
        self.lbl_titulo = QLabel()
        self.lbl_titulo.setObjectName("classificationBadge")
        self.lbl_titulo.setMinimumHeight(42)
        self.lbl_titulo.setWordWrap(True)

        self.lbl_lx = QLabel()
        self.lbl_ly = QLabel()
        self.lbl_lam = QLabel()

        self.lbl_nota = QLabel()
        self.lbl_nota.setWordWrap(True)
        self.lbl_nota.setObjectName("helperText")

        g_class = QGroupBox("Classificação automática")

        c = QFormLayout(g_class)
        c.setHorizontalSpacing(12)
        c.setVerticalSpacing(9)

        c.addRow(self.lbl_titulo)
        c.addRow("lx · menor vão", self.lbl_lx)
        c.addRow("ly · maior vão", self.lbl_ly)
        c.addRow("λ = ly/lx", self.lbl_lam)
        c.addRow(self.lbl_nota)

        # Vinculação
        self.cmb_vinc = QComboBox()
        self.cmb_vinc.setMinimumHeight(40)

        self.cmb_vinc.currentIndexChanged.connect(
            self.vinculacao_mudou
        )

        g_vinc = QGroupBox("Vinculação")

        v = QVBoxLayout(g_vinc)
        v.setSpacing(9)

        texto_vinc = QLabel(
            "Selecione pelo menu ou clique diretamente em um dos diagramas ao lado."
        )

        texto_vinc.setWordWrap(True)
        texto_vinc.setObjectName("helperText")

        v.addWidget(texto_vinc)
        v.addWidget(self.cmb_vinc)

        # Planta no painel esquerdo, acima dos campos de geometria.
        # Assim, os casos de vinculação podem ocupar toda a altura do painel direito.
        self.desenhos_geometria = DesenhosGeometria()
        self.desenhos_geometria.setMinimumHeight(190)
        self.desenhos_geometria.setMaximumHeight(210)

        # Painel esquerdo com rolagem
        esquerda = QVBoxLayout()
        esquerda.setSpacing(10)
        esquerda.setContentsMargins(0, 0, 8, 0)

        esquerda.addWidget(self.desenhos_geometria)
        esquerda.addWidget(g_vaos)
        esquerda.addWidget(g_class)
        esquerda.addWidget(g_vinc)
        esquerda.addStretch(1)

        w_esq = QWidget()
        w_esq.setObjectName("painelEsquerdo")
        w_esq.setLayout(esquerda)

        rolagem_esq = QScrollArea()
        rolagem_esq.setWidgetResizable(True)
        rolagem_esq.setFrameShape(QFrame.Shape.NoFrame)

        rolagem_esq.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        rolagem_esq.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        rolagem_esq.setMinimumWidth(300)
        rolagem_esq.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )

        rolagem_esq.setWidget(w_esq)

        # Canvas dos diagramas
        self.img = VinculacaoWidget()
        self.img.setObjectName("vinculacaoCanvas")
        self.img.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )

        self.img.clicado.connect(
            self.selecionar_caso_clicado
        )

        g_canvas = QGroupBox(
            "Casos de vinculação disponíveis"
        )

        canvas_lay = QVBoxLayout(g_canvas)
        canvas_lay.setContentsMargins(12, 15, 12, 12)
        canvas_lay.setSpacing(8)

        dica_canvas = QLabel(
            "As bordas hachuradas representam engastamento. "
            "Clique em um cartão para selecionar o caso."
        )

        dica_canvas.setObjectName("helperText")
        dica_canvas.setWordWrap(True)

        canvas_lay.addWidget(dica_canvas)

        # A área de cartões tem rolagem própria. O widget interno mantém
        # altura suficiente para desenhar todas as linhas sem comprimi-las.
        rolagem_casos = QScrollArea()
        rolagem_casos.setWidgetResizable(True)
        rolagem_casos.setFrameShape(QFrame.Shape.NoFrame)
        rolagem_casos.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        rolagem_casos.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        rolagem_casos.setWidget(self.img)
        canvas_lay.addWidget(rolagem_casos, 1)

        g_canvas.setMinimumWidth(340)
        g_canvas.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )

        # QSplitter: distribui o espaço entre os dois painéis.
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(6)

        splitter.addWidget(rolagem_esq)
        splitter.addWidget(g_canvas)

        # Prioriza a área dos casos de vinculação no lado direito.
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 7)

        splitter.setSizes([350, 820])

        self.splitter_geometria = splitter

        # O painel de vinculações fica à direita e ocupa toda a altura
        # disponível; a planta permanece no painel esquerdo.
        lay.addWidget(splitter, 1)

        return pagina

    def atualizar_classificacao(self):
        try:
            self.info = calculo.classificar_laje(
                self.vao_a.value(),
                self.vao_b.value()
            )

        except ValueError as e:
            QMessageBox.warning(
                self,
                "Dimensões inválidas",
                str(e)
            )
            return

        i = self.info

        self.lbl_titulo.setText(i["titulo"])
        self.lbl_lx.setText(f"{f2(i['lx'], 3)} m")
        self.lbl_ly.setText(f"{f2(i['ly'], 3)} m")
        self.lbl_lam.setText(f2(i["lambda"], 3))
        self.lbl_nota.setText(i["nota"])
        if hasattr(self, "desenhos_geometria"):
            self.desenhos_geometria.configurar(i["lx"], i["ly"])

        self.cmb_vinc.blockSignals(True)

        self.cmb_vinc.clear()
        self.cmb_vinc.addItem(
            "— Selecione a vinculação —",
            None
        )

        for k, txt in i["casos"].items():
            self.cmb_vinc.addItem(
                f"{k} — {txt}",
                k
            )

        self.cmb_vinc.blockSignals(False)

        self.tabs.setTabEnabled(1, False)
        self.tabs.setTabEnabled(2, False)

        self.img.configurar(
            i["casos"],
            i["unidirecional"]
        )

        self.atualizar_estimativa()

    def vinculacao_mudou(self):
        selecionada = (
            self.cmb_vinc.currentData() is not None
        )

        self.tabs.setTabEnabled(1, selecionada)
        self.tabs.setTabEnabled(2, False)

        self.img.selecionar(
            self.cmb_vinc.currentData()
        )

        self.atualizar_estimativa()

    def selecionar_caso_clicado(self, chave):
        idx = self.cmb_vinc.findData(chave)

        if idx >= 0:
            self.cmb_vinc.setCurrentIndex(idx)

    # -----------------------------------------------------------------------
    # ETAPA 2 — PARÂMETROS
    # -----------------------------------------------------------------------

    def _aba_dados(self):
        pagina = QWidget()
        lay = QVBoxLayout(pagina)
        lay.setContentsMargins(22, 18, 22, 20)
        lay.setSpacing(12)
        lay.addWidget(self._intro(
            "Parâmetros de dimensionamento",
            "Informe os materiais, a espessura e as ações características. "
            "Os valores sugeridos pela CAA podem ser editados, respeitando os mínimos."
        ))

        self.cmb_caa = QComboBox()
        for txt, key in (("I — Rural", "I"), ("II — Urbana", "II"),
                         ("III — Marinha/Industrial", "III"),
                         ("IV — Muito agressiva", "IV")):
            self.cmb_caa.addItem(txt, key)
        self.cmb_caa.setCurrentIndex(1)

        self.fck = spin(10, 40, 25, 0, "MPa", 5)
        self.cob = spin(0, 80, 25, 0, "mm", 1)
        self.h = spin(1, 100, 12, 1, "cm", 0.5)
        self.g2k = spin(0, 100, 0, 2, "kN/m²", 0.1)
        self.q = spin(0, 100, 0, 2, "kN/m²", 0.1)

        self.cmb_tipo = QComboBox()
        self.cmb_tipo.addItem("Piso", "piso")
        self.cmb_tipo.addItem("Cobertura", "cobertura")

        self.cmb_aco = QComboBox()
        self.cmb_aco.addItem("CA-50 (fyk = 500 MPa)", ("CA-50", 500.0))
        self.cmb_aco.addItem("CA-60 (fyk = 600 MPa)", ("CA-60", 600.0))
        self.phi = QComboBox()
        self._atualizar_bitolas()

        self.cmb_agregado = QComboBox()
        for key, (nome, alpha) in calculo.AGREGADOS.items():
            self.cmb_agregado.addItem(f"{nome} (αE = {alpha:.2f})", key)
        idx_ag = self.cmb_agregado.findData("2")
        if idx_ag >= 0:
            self.cmb_agregado.setCurrentIndex(idx_ag)

        self.cmb_caa.currentIndexChanged.connect(self.atualizar_fixos)
        self.cmb_tipo.currentIndexChanged.connect(self.atualizar_validacao)
        self.cmb_aco.currentIndexChanged.connect(self._atualizar_bitolas)
        for campo in (self.fck, self.cob, self.h, self.g2k, self.q):
            campo.valueChanged.connect(self.atualizar_validacao)
        self.phi.currentIndexChanged.connect(self.atualizar_estimativa)

        g_in = QGroupBox("Dados informados")
        f = QFormLayout(g_in)
        f.setHorizontalSpacing(16)
        f.setVerticalSpacing(9)
        f.addRow("Classe de agressividade (CAA)", self.cmb_caa)
        f.addRow("fck do concreto", self.fck)
        f.addRow("Cobrimento nominal", self.cob)
        f.addRow("Tipo de utilização", self.cmb_tipo)
        f.addRow("Espessura da laje h", self.h)
        f.addRow("Carga permanente adicional g₂,k", self.g2k)
        f.addRow("Carga variável característica qk", self.q)
        f.addRow("Categoria do aço", self.cmb_aco)
        f.addRow("Bitola das barras principais φ", self.phi)
        f.addRow("Tipo de agregado", self.cmb_agregado)

        g_info = QGroupBox("Referências e validação")
        x = QFormLayout(g_info)
        self.lbl_fck_min = QLabel()
        self.lbl_cob_min = QLabel()
        self.lbl_h_min = QLabel()
        self.lbl_peso = QLabel("25,00 kN/m³ — concreto armado")
        self.lbl_alerta = QLabel()
        self.lbl_alerta.setWordWrap(True)
        self.lbl_alerta.setStyleSheet("color: #B42318; font-weight: 700;")
        x.addRow("fck mínimo sugerido", self.lbl_fck_min)
        x.addRow("Cobrimento mínimo sugerido", self.lbl_cob_min)
        x.addRow("Espessura mínima", self.lbl_h_min)
        x.addRow("Peso específico", self.lbl_peso)
        x.addRow(self.lbl_alerta)

        self.lbl_est = QLabel()
        self.lbl_est.setObjectName("estimateCallout")
        self.lbl_est.setWordWrap(True)
        x.addRow(self.lbl_est)

        conteudo = QHBoxLayout()
        conteudo.setSpacing(14)
        conteudo.addWidget(g_in, 3)
        conteudo.addWidget(g_info, 2)
        lay.addLayout(conteudo)

        acoes = QHBoxLayout()
        acoes.addStretch(1)
        self.btn_calcular = QPushButton("✓   Calcular dimensionamento")
        self.btn_calcular.setObjectName("primaryButton")
        self.btn_calcular.setMinimumWidth(245)
        self.btn_calcular.setMinimumHeight(46)
        self.btn_calcular.clicked.connect(self.calcular)
        acoes.addWidget(self.btn_calcular)
        lay.addLayout(acoes)
        lay.addStretch(1)
        self.atualizar_fixos()
        return pagina

    def _atualizar_bitolas(self):
        if not hasattr(self, "phi"):
            return
        atual = self.phi.currentData() if self.phi.count() else 8.0
        self.phi.blockSignals(True)
        self.phi.clear()
        # Bitolas usuais em ordem crescente.
        for diametro in (5.0, 6.3, 8.0, 10.0, 12.5, 16.0, 20.0, 25.0):
            self.phi.addItem(f"{diametro:g} mm", diametro)
        idx = self.phi.findData(atual)
        self.phi.setCurrentIndex(idx if idx >= 0 else self.phi.findData(8.0))
        self.phi.blockSignals(False)
        self.atualizar_estimativa()

    def atualizar_fixos(self):
        caa = self.cmb_caa.currentData()
        fmin = calculo.FCK_MIN_CAA[caa]
        cmin = calculo.COB_NOMINAL[caa]
        self.lbl_fck_min.setText(f"C{fmin} ({fmin} MPa)")
        self.lbl_cob_min.setText(f"{cmin} mm")
        self.fck.setValue(max(self.fck.value(), fmin))
        self.cob.setValue(max(self.cob.value(), cmin))
        self.atualizar_validacao()
        self.atualizar_estimativa()

    def atualizar_validacao(self, *_args):
        if not hasattr(self, "lbl_alerta"):
            return
        caa = self.cmb_caa.currentData()
        tipo = self.cmb_tipo.currentData()
        hmin = calculo.altura_minima(tipo) if tipo != "balanco" else None
        erros = []
        campos = ((self.fck, self.fck.value() >= calculo.FCK_MIN_CAA[caa]),
                  (self.cob, self.cob.value() >= calculo.COB_NOMINAL[caa]),
                  (self.h, hmin is not None and self.h.value()/100 >= hmin))
        for campo, ok in campos:
            campo.setStyleSheet("" if ok else "QDoubleSpinBox { border: 2px solid #D92D20; background: #FEF3F2; }")
        if self.fck.value() < calculo.FCK_MIN_CAA[caa]:
            erros.append(f"fck mínimo para CAA {caa}: {calculo.FCK_MIN_CAA[caa]} MPa.")
        if self.cob.value() < calculo.COB_NOMINAL[caa]:
            erros.append(f"Cobrimento mínimo para CAA {caa}: {calculo.COB_NOMINAL[caa]} mm.")
        if tipo == "balanco":
            erros.append("Lajes em balanço não podem ser calculadas nesta versão: o modelo estrutural não está implementado.")
        elif self.h.value()/100 < hmin:
            erros.append(f"Espessura mínima para {tipo}: {hmin*100:.0f} cm.")
        self.lbl_h_min.setText("Não disponível para balanço" if hmin is None else f"{hmin*100:.0f} cm")
        self.lbl_alerta.setText("\n".join(erros))
        self.btn_calcular.setEnabled(not erros)
        self.atualizar_estimativa()

    def atualizar_estimativa(self):
        if self.info is None or not hasattr(self, "lbl_est"):
            return
        try:
            vinc = self.cmb_vinc.currentData()
            caso = 1 if self.info["unidirecional"] else (vinc or 1)
            cob = self.cob.value()
            phi = float(self.phi.currentData() or 8.0)
            _, h_est, l_star, n = calculo.estimar_h_bastos(
                self.info["lx"], self.info["ly"], caso, cob/1000, phi/1000
            )
            hmin = calculo.altura_minima(self.cmb_tipo.currentData()) if self.cmb_tipo.currentData() != "balanco" else 0.10
            self.lbl_est.setText(
                f"Pré-dimensionamento (Bastos): l* = {f2(l_star,3)} m; n = {n}; "
                f"h estimado ≈ {f2(h_est*100,1)} cm. Mínimo aplicável: {hmin*100:.0f} cm."
            )
        except (ValueError, KeyError, TypeError):
            self.lbl_est.setText("A estimativa será apresentada após a seleção da vinculação.")

    # -----------------------------------------------------------------------
    # ETAPA 3 — RESULTADOS
    # -----------------------------------------------------------------------

    def _aba_resultados(self):
        pagina = QWidget()

        lay = QVBoxLayout(pagina)
        lay.setContentsMargins(22, 18, 22, 20)
        lay.setSpacing(13)

        lay.addWidget(
            self._intro(
                "Resultados do dimensionamento",
                "Consulte os indicadores gerais, as verificações "
                "e a memória de cálculo gerada pelo modelo."
            )
        )

        faixa_metricas = QHBoxLayout()
        faixa_metricas.setSpacing(12)

        metricas = (
            ("tipo", "Classificação", "Comportamento da laje"),
            ("lx", "Menor vão · lx", "Dimensão considerada"),
            ("ly", "Maior vão · ly", "Dimensão considerada"),
            ("h", "Espessura · h", "Espessura adotada"),
        )

        for chave, titulo, dica in metricas:
            card, valor, descricao = self._criar_metrica(
                titulo,
                "—",
                dica
            )

            self.metric_values[chave] = (
                valor,
                descricao
            )

            faixa_metricas.addWidget(card, 1)

        lay.addLayout(faixa_metricas)

        self.txt_parecer = texto_mono()
        self.txt_parecer.setLineWrapMode(
            QPlainTextEdit.LineWrapMode.WidgetWidth
        )

        self.tab_cargas = nova_tabela(
            ["Item", "Valor", "Unidade"]
        )

        self.tab_reacoes = nova_tabela(
            ["Item", "Valor", "Unidade"]
        )

        self.tab_arm = nova_tabela([
            "Armadura",
            "As calculada (cm²/m)",
            "As adotada (cm²/m)",
            "Barras/m",
            "Espaçamento (cm)",
            "As fornecida (cm²/m)",
            "Espaç. livre (cm)",
            "Verificação geométrica",
        ])

        self.tab_flecha = nova_tabela([
            "Item",
            "Valor",
            "Unidade",
            "Situação"
        ])

        self.txt_memoria = texto_mono()

        self.res_tabs = QTabWidget()
        self.res_tabs.setDocumentMode(True)

        self.res_tabs.addTab(
            self.txt_parecer,
            "Parecer final"
        )

        self.res_tabs.addTab(
            self.tab_cargas,
            "Cargas e momentos"
        )

        self.res_tabs.addTab(
            self.tab_reacoes,
            "Reações"
        )

        self.res_tabs.addTab(
            self.tab_arm,
            "Armaduras"
        )

        self.res_tabs.addTab(
            self.tab_flecha,
            "Flechas"
        )

        self.res_tabs.addTab(
            self.txt_memoria,
            "Memória completa"
        )

        lay.addWidget(self.res_tabs, 1)

        rodape = QHBoxLayout()

        observacao = QLabel(
            "Os resultados são apresentados conforme as premissas informadas."
        )

        observacao.setObjectName("helperText")

        rodape.addWidget(observacao)
        rodape.addStretch(1)

        btn_pdf = QPushButton(
            "Exportar memória em PDF"
        )

        btn_pdf.setObjectName("secondaryButton")
        btn_pdf.clicked.connect(self.exportar_pdf)

        rodape.addWidget(btn_pdf)

        lay.addLayout(rodape)

        return pagina

    def _atualizar_indicadores(self, dados):
        tipo = (
            "Unidirecional"
            if dados["unidirecional"]
            else "Bidirecional"
        )

        valores = {
            "tipo": (
                tipo,
                "Classificação automática"
            ),

            "lx": (
                f"{f2(dados['lx'], 3)} m",
                "Menor vão da laje"
            ),

            "ly": (
                f"{f2(dados['ly'], 3)} m",
                "Maior vão da laje"
            ),

            "h": (
                f"{f2(dados['h'] * 100, 1)} cm",
                "Espessura adotada no cálculo"
            ),
        }

        for chave, (valor, detalhe) in valores.items():
            self.metric_values[chave][0].setText(valor)
            self.metric_values[chave][1].setText(detalhe)

    def calcular(self):
        try:
            dados = montar_dados_padrao(
                self.vao_a.value(),
                self.vao_b.value(),
                self.cmb_vinc.currentData(),
                self.cmb_caa.currentData(),
                float(self.phi.currentData()),
                self.q.value(),
                self.h.value(),
                g2k=self.g2k.value(),
                fck=self.fck.value(),
                cob=self.cob.value(),
                tipo=self.cmb_tipo.currentData(),
                fyk=self.cmb_aco.currentData()[1],
                agregado_id=self.cmb_agregado.currentData(),
                aco=self.cmb_aco.currentData()[0]
            )

            d, r, partes = gerar_memoria(dados)

        except (ValueError, KeyError) as e:
            QMessageBox.warning(
                self,
                "Erro nos dados",
                str(e)
            )
            return

        except Exception as e:
            QMessageBox.critical(
                self,
                "Erro no dimensionamento",
                f"Não foi possível realizar o cálculo:\n\n{e}"
            )
            return

        self.txt_parecer.setPlainText(
            partes["parecer"]
        )

        self.txt_memoria.setPlainText(
            partes["completo"]
        )

        preencher(
            self.tab_cargas,
            linhas_cargas_momentos(d, r)
        )

        preencher(
            self.tab_reacoes,
            linhas_reacoes(d, r)
        )

        preencher(
            self.tab_arm,
            linhas_armaduras(d, r)
        )

        preencher(
            self.tab_flecha,
            linhas_flechas(d, r)
        )

        self._atualizar_indicadores(d)

        self.tabs.setTabEnabled(2, True)
        self.tabs.setCurrentIndex(2)

        self.res_tabs.setCurrentIndex(0)

    def exportar_pdf(self):
        caminho, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar memória de cálculo",
            "memoria_calculo.pdf",
            "PDF (*.pdf)"
        )

        if not caminho:
            return

        if not caminho.lower().endswith(".pdf"):
            caminho += ".pdf"

        impressora = QPrinter(
            QPrinter.PrinterMode.HighResolution
        )

        impressora.setOutputFormat(
            QPrinter.OutputFormat.PdfFormat
        )

        impressora.setOutputFileName(caminho)

        self.txt_memoria.print_(impressora)

        QMessageBox.information(
            self,
            "PDF exportado",
            "A memória de cálculo foi exportada com sucesso."
        )


# ---------------------------------------------------------------------------
# Inicialização
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app = QApplication(sys.argv)

    app.setApplicationName(
        "SlabCalc"
    )

    app.setFont(
        QFont("Segoe UI", 10)
    )

    janela = Janela()
    janela.showMaximized()

    sys.exit(app.exec())