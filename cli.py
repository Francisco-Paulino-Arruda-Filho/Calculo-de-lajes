"""Versão de terminal (opcional). A aplicação desktop usa gui.py e não depende deste arquivo."""
import math

from calculo import (
    AGREGADOS, COB_NOMINAL, DESCRICAO, FCK_MIN_CAA, altura_minima, cab,
    classificar_laje, estimar_h_bastos, executar_modelo, imprimir,
    imprimir_auditoria_normativa, imprimir_detalhamento,
    imprimir_parecer_final, imprimir_unidirecional, sep,
)


def entrada():
    sep(); print("  CÁLCULO DE LAJES MACIÇAS — PERFIL ACADÊMICO AUTOMÁTICO")
    print("  Carvalho & Figueiredo + hipóteses de ensaio + NBR 6118:2026"); sep()
    
    print(">> GEOMETRIA")
    lx = float(input("   lx — menor vão de cálculo (m): "))
    ly = float(input("   ly — maior vão de cálculo (m): "))
    if lx <= 0 or ly <= 0:
        raise ValueError("Os vãos devem ser positivos.")
    classificacao = classificar_laje(lx, ly)
    if ly < lx:
        print("   [aviso] lx e ly foram trocados para manter lx <= ly.")
    lx, ly = classificacao['lx'], classificacao['ly']
    lam = classificacao['lambda']
    print(f"   λ = ly/lx = {lam:.2f}")
    unidirecional = classificacao['unidirecional']
    print(f"   CLASSIFICAÇÃO AUTOMÁTICA: {classificacao['titulo']}")
    if unidirecional:
        print("   [modelo] LAJE UNIDIRECIONAL: faixa de 1 m no menor vão.")
        print("   [atenção] O apoio na direção do menor vão será informado separadamente.")
    else:
        print("   [modelo] LAJE BIDIRECIONAL: coeficientes tabelados.")

    # Perfil acadêmico padronizado: laje de PISO, não em balanço.
    # A identificação de piso/cobertura depende do uso e NÃO pode ser inferida dos vãos.
    tipo = "piso"
    print("\n>> USO: piso não em balanço (perfil acadêmico fixo; h mínimo = 8 cm)")

    if unidirecional:
        print("\n>> APOIOS NA DIREÇÃO DO MENOR VÃO (MODELO DE FAIXA)")
        print("   1: duas extremidades simplesmente apoiadas")
        print("   2: uma extremidade engastada e outra apoiada")
        print("   3: duas extremidades engastadas")
        apoio_1d = int(input("   Condição (1–3): "))
        if apoio_1d not in (1, 2, 3):
            raise ValueError("Condição de apoio unidirecional inválida.")
        caso = 1  # marcador apenas para estimativa de h; não usa tabelas 2D
    else:
        print("\n>> CASO ESTRUTURAL (tabelas de Carvalho & Figueiredo)")
        for k in range(1, 10):
            print(f"   {k}: {DESCRICAO[k]}")
        caso = int(input("   Caso (1–9): "))
        if caso not in range(1, 10):
            raise ValueError("Caso inválido: escolha de 1 a 9.")
        apoio_1d = None

    print("\n>> CLASSE DE AGRESSIVIDADE AMBIENTAL")
    print("   I=Rural  II=Urbano  III=Marinho/Industrial  IV=Muito agressivo")
    caa = input("   CAA (I/II/III/IV): ").strip().upper()
    if caa not in COB_NOMINAL:
        raise ValueError("CAA inválida.")
    cob_nbr = COB_NOMINAL[caa]
    cob = float(cob_nbr)
    print(f"   Cobrimento nominal automático para CAA {caa}: {cob:.0f} mm")

    print("\n>> MATERIAIS")
    # Seleção automática da classe mínima de resistência conforme a CAA.
    # O usuário não precisa digitar fck; esta versão adota o mínimo normativo.
    fck = FCK_MIN_CAA[caa]
    print(f"   fck definido automaticamente: C{fck} ({fck} MPa) para CAA {caa}.")
    fyk = 500.0  # aço CA-50: resistência característica, NÃO de cálculo
    print(f"   Aço CA-50: fyk = {fyk:.0f} MPa; fyd = fyk/1,15 = {fyk/1.15:.2f} MPa")
    phi = float(input("   Diâmetro das barras principais φ (mm): "))
    if phi <= 0:
        raise ValueError("Diâmetro deve ser positivo.")
    if cob < phi:
        raise ValueError(f"O cobrimento nominal ({cob:.1f} mm) não pode ser inferior ao diâmetro da barra ({phi:.1f} mm).")

    # Hipótese de agregado, não uma propriedade universal do concreto.
    agregado, alpha_E = AGREGADOS["2"]
    print(f"   Agregado adotado no perfil: {agregado} (alpha_E={alpha_E:.2f})")

    # Perfil de ensaio inspirado nos valores globais da laje L2 de Bastos:
    # g=4,28 kN/m² PARA h=0,12 m e q=1,50 kN/m². O valor 1,28 é
    # somente a diferença 4,28 - 25*0,12, NÃO uma composição
    # documentalmente verificada de contrapiso/piso/parede.
    # Em outras espessuras, g total muda; não equivale ao mesmo exemplo.
    gc = 25.0
    g_contrapiso = 0.0
    g_revest_inf = 0.0
    g_piso = 0.0
    g_paredes = 0.0
    g_outros = 1.28
    print("\n>> CARGA VARIÁVEL")
    print("   Informe a carga variável característica de acordo com o uso da laje.")
    q = float(input("   Carga variável característica qₖ (kN/m²): ").replace(",", "."))
    if not math.isfinite(q) or q < 0:
        raise ValueError("A carga variável qₖ deve ser finita e não negativa.")
    # A adequação da sobrecarga ao uso deve ser conferida na NBR 6120:2019.
    # Não é solicitada uma segunda carga no terminal.
    psi2 = 0.30
    print("\n>> CARREGAMENTO AUTOMÁTICO — PERFIL DE ENSAIO, NÃO PROJETO REAL")
    print("   Peso específico concreto: 25,00 kN/m³")
    print("   Carga permanente adicional global: 1,28 kN/m² (sem decomposição por camadas)")
    print(f"   Carga variável INFORMADA: {q:.2f} kN/m²; psi2: {psi2:.2f} (hipótese de ensaio)")
    print("   ATENÇÃO: revestimentos, paredes, uso e cargas reais NÃO são constantes.")
    print("   A carga informada não é automaticamente conferida contra a tabela de usos da NBR 6120.")

    print("\n>> ESPESSURA")
    _, h_est, l_star, n_eng = estimar_h_bastos(lx, ly, caso, cob/1000, phi/1000)
    h_min = altura_minima(tipo)
    h_sug = max(h_est, h_min)
    print(f"   Estimativa Bastos: l*={l_star:.3f} m; n={n_eng}; h≈{h_est*100:.1f} cm")
    print(f"   Limite mínimo normativo desta categoria: {h_min*100:.1f} cm")
    # Entrada amigável em centímetros; os cálculos continuam em metros.
    h_cm = float(input("   h adotado (cm): ").replace(",", "."))
    if not math.isfinite(h_cm) or h_cm <= 0:
        raise ValueError("A espessura h deve ser positiva e finita (em cm).")
    h = h_cm / 100.0
    if h < h_min:
        raise ValueError(f"h={h*100:.1f} cm menor que o mínimo de {h_min*100:.1f} cm.")
    if phi/1000 > h/8:
        raise ValueError(
            "\nVERIFICAÇÃO DA BITOLA DA ARMADURA\n"
            f"Espessura da laje: {h*100:.2f} cm\n"
            f"Bitola escolhida: {phi/10:.2f} cm\n"
            f"Bitola máxima adotada: {h*100/8:.2f} cm\n"
            "RESULTADO: NÃO ATENDE\n"
            "Escolha uma bitola menor ou aumente a espessura da laje."
        )

    # Parâmetros de ensaio fixos, não valores universais de fluência.
    t0, tinf = 14.0/30.0, 70.0
    print(f"\n>> FLUÊNCIA: t0={t0:.3f} mês (~14 dias), t={tinf:.0f} meses [perfil de ensaio]")
    print("   NOTA: idade de carregamento e horizonte de análise variam no projeto real.")

    return dict(
        lx=lx, ly=ly, caso=caso, unidirecional=unidirecional, apoio_1d=apoio_1d, tipo=tipo, caa=caa, cob=cob, cob_nbr=cob_nbr,
        fck=fck, fyk=fyk, phi=phi, agregado=agregado, alpha_E=alpha_E,
        gc=gc, g_contrapiso=g_contrapiso, g_revest_inf=g_revest_inf,
        g_piso=g_piso, g_paredes=g_paredes, g_outros=g_outros,
        q=q, psi2=psi2, h=h, h_min=h_min, h_est=h_est, t0=t0, tinf=tinf,
    )


if __name__ == "__main__":
    try:
        dados = entrada()
        dados, resultados = executar_modelo(dados)
        if dados["unidirecional"]:
            imprimir_unidirecional(dados, resultados)
        else:
            imprimir(dados, resultados)
        imprimir_detalhamento(resultados)
        imprimir_parecer_final(dados, resultados)
        imprimir_auditoria_normativa(resultados)
    except (ValueError, KeyError) as e:
        print(f"\n[ERRO DE ENTRADA/MODELO] {e}")