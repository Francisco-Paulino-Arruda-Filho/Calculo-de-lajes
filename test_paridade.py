"""Compara o fluxo da interface com o fluxo original de terminal (cli.entrada()).

Uso:  python test_paridade.py
Não abre janela: usa as mesmas funções que a interface chama.
"""
import builtins
import io
import sys
from contextlib import redirect_stdout

import calculo
import cli
import gui

CASOS = []
for caso in range(1, 10):
    CASOS.append(dict(lx=4.0, ly=5.0, vinc=caso, caa="II", phi=8.0, q=2.0, h=12.0))
for apoio in (1, 2, 3):
    CASOS.append(dict(lx=3.0, ly=7.0, vinc=apoio, caa="II", phi=8.0, q=2.0, h=12.0))
CASOS.append(dict(lx=5.0, ly=4.0, vinc=4, caa="III", phi=10.0, q=3.0, h=14.0))
CASOS.append(dict(lx=4.5, ly=6.0, vinc=7, caa="I", phi=8.0, q=1.5, h=12.0))


def dados_terminal(c):
    respostas = iter([str(c["lx"]), str(c["ly"]), str(c["vinc"]),
                      c["caa"], str(c["phi"]), str(c["q"]), str(c["h"])])
    original = builtins.input
    builtins.input = lambda *_: next(respostas)
    try:
        with redirect_stdout(io.StringIO()):
            return cli.entrada()
    finally:
        builtins.input = original


def memoria_terminal(dados):
    d, r = calculo.executar_modelo(dados)
    buf = io.StringIO()
    with redirect_stdout(buf):
        if d["unidirecional"]:
            calculo.imprimir_unidirecional(d, r)
        else:
            calculo.imprimir(d, r)
        calculo.imprimir_detalhamento(r)
        calculo.imprimir_parecer_final(d, r)
        calculo.imprimir_auditoria_normativa(r)
    return buf.getvalue()


def executar(func):
    try:
        return func(), None
    except (ValueError, KeyError) as e:
        return None, str(e)


falhas = 0
for c in CASOS:
    rotulo = f"lx={c['lx']} ly={c['ly']} vinc={c['vinc']} CAA={c['caa']} phi={c['phi']} q={c['q']} h={c['h']}"
    dt, err_t = executar(lambda: dados_terminal(c))
    dg, err_g = executar(lambda: gui.montar_dados_padrao(
        c["lx"], c["ly"], c["vinc"], c["caa"], c["phi"], c["q"], c["h"]))
    if err_t or err_g:
        ok = err_t is not None and err_t == err_g or (err_t is None and err_g is None)
        print(("OK   " if ok else "FALHA"), rotulo, "| erro na entrada:", err_t, "|", err_g)
        falhas += 0 if ok else 1
        continue
    if dt != dg:
        dif = [k for k in dt if dt[k] != dg.get(k)]
        print("FALHA", rotulo, "| dicionários diferentes em:", dif)
        falhas += 1
        continue
    txt_t, e1 = executar(lambda: memoria_terminal(dt))
    res_g, e2 = executar(lambda: gui.gerar_memoria(dg))
    txt_g = res_g[2]["completo"] if res_g else None
    ok = (txt_t == txt_g) and (e1 == e2)
    print(("OK   " if ok else "FALHA"), rotulo, "" if not (e1 or e2) else f"| erro de cálculo igual nos dois: {e1}")
    falhas += 0 if ok else 1

print("\nTodos os casos idênticos." if falhas == 0 else f"\n{falhas} caso(s) com diferença.")
sys.exit(1 if falhas else 0)