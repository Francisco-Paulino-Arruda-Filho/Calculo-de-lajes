---
layout: default
title: Calculadora de Lajes Maciças
---

<script>
  MathJax = {
    tex: {
      inlineMath: [['$', '$'], ['\\(', '\\)']],
      displayMath: [['$$', '$$']]
    },
    options: {
      skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code']
    }
  };
</script>

<script async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>

# Calculadora de Lajes Maciças de Concreto Armado

Documentação do código de cálculo (`calculo.py`).

Referências citadas no código: Carvalho & Figueiredo Filho, *Cálculo e Detalhamento de Estruturas Usuais de Concreto Armado* (4ª ed.); Bastos (pré-dimensionamento); ABNT NBR 6118:2026; ABNT NBR 6120:2019.

> **Perfil acadêmico.** O código traz um perfil de ensaio: piso não em balanço, CA-50, agregado granito/gnaisse, carga permanente adicional de 1,28 kN/m², q = 1,50 kN/m² e ψ₂ = 0,30. Ele **não deve ser usado como dimensionamento final de obras**. As verificações de flecha e fissuração do módulo unidirecional são preliminares.

---

## 1. Visão geral

O módulo dimensiona **lajes maciças retangulares** em dois modelos, escolhidos automaticamente pela relação entre os vãos:

| Modelo | Condição | Método |
|---|---|---|
| **Bidirecional** (armada em duas direções) | $\lambda \leq 2{,}0$ | Coeficientes tabelados (casos 1 a 9) |
| **Unidirecional** (armada em uma direção) | $\lambda > 2{,}0$ | Faixa de 1 m, análise elástica linear (3 vinculações) |

Nos dois modelos, o programa cobre:

1. Pré-dimensionamento da espessura.
2. Levantamento de cargas (ELU e ELS).
3. Momentos fletores e reações de apoio.
4. Dimensionamento da armadura de flexão e armadura mínima.
5. Detalhamento: número de barras, espaçamento máximo e espaçamento livre.
6. Verificação de flecha, com fissuração (Branson) e fluência.
7. Verificação ao cisalhamento sem armadura transversal.
8. Auditoria dos limites normativos verificáveis e parecer final.

### 1.1 Escopo

| Item | Limite nesta versão |
|---|---|
| Geometria | Laje retangular, qualquer $\lambda = l_y/l_x \geq 1$ |
| Bidirecional | Casos 1 a 9 (Quadros 7.2 a 7.5 e 7.8 a 7.10) |
| Unidirecional | Apoiada-apoiada, engastada-apoiada, engastada-engastada |
| Concreto | C20 a C40 (parâmetros do bloco de tensões) |
| Tipo de laje | Piso ou cobertura, não em balanço |
| Ação variável | Uma única ação variável |
| Carga | Uniformemente distribuída |

Para entradas fisicamente inválidas ou fora do domínio tabelado, o código **lança `ValueError`** em vez de extrapolar silenciosamente.

---

## 2. Arquitetura e fluxo de dados

```text
Interface (gui.py)
   │  usuário informa os dois vãos
   ▼
classificar_laje(a, b)        → lx, ly, λ, modelo, casos disponíveis, imagem
   │  usuário escolhe a vinculação (a seleção é limpa ao trocar os vãos)
   ▼
executar_modelo(dados)        → ponto único de entrada do cálculo
   ├─ validar_entrada_modelo(d)
   ├─ classificar_laje(...)   → reordena lx/ly e define d['unidirecional']
   ├─ calcular(d)              (λ ≤ 2) ou calcular_unidirecional(d) (λ > 2)
   ├─ anexar_verificacoes_complementares(d, r) → padroniza campos de flecha
   ├─ avaliar_detalhamento(d, r)                 → triagem geométrica das barras
   └─ auditar_limites_normativos(d, r)           → checks + pendências
   ▼
devolve (d, r)
   ▼
Impressão (capturada com redirect_stdout):
   imprimir(d, r) ou imprimir_unidirecional(d, r)
   imprimir_detalhamento(r)
   imprimir_auditoria_normativa(r)
   imprimir_parecer_final(d, r)
```

- As funções de cálculo **não imprimem nada**: recebem `d` e devolvem `r`. Isso permite testar o núcleo sem interface.
- As funções `imprimir*` só formatam `d` e `r`.
- Erros de entrada ou de modelo são `ValueError` ou `KeyError`, tratados na interface com `QMessageBox`.

### 2.1 `classificar_laje(lado_a, lado_b)`

Ordena os lados ($l_x$ = menor, $l_y$ = maior) e devolve um dicionário pronto para a GUI. A classificação **não depende** do caso de vinculação.

| Chave | $\lambda \leq 2{,}0$ | $\lambda > 2{,}0$ |
|---|---|---|
| `modelo` | `"bidirecional"` | `"unidirecional"` |
| `casos` | `DESCRICAO` (1 a 9) | `CASOS_UNIDIRECIONAIS` (1 a 3) |
| `imagem` | `vinculacoes_bidirecionais_precisas.jpeg` | `vinculacoes_unidirecionais_precisas.jpeg` |

Convenção para montar `d`:

| Modelo | `unidirecional` | `caso` | `apoio_1d` |
|---|---|---|---|
| Bidirecional | `False` | 1 a 9 | `None` |
| Unidirecional | `True` | `1` (marcador apenas para a estimativa de espessura) | 1, 2 ou 3 |

> Os três casos unidirecionais se referem a uma faixa de 1 m **na direção do menor vão**. Eles **não** equivalem numericamente aos casos 1, 3 e 5 do modelo bidirecional.

---

## 3. Convenções

### 3.1 Eixos e vãos

- `lx` é o **menor vão** e `ly` o maior. Se o usuário os inverter, o código troca.

$$
\lambda = \frac{l_y}{l_x}
$$

- **Bidirecional:** armadura x paralela a `lx` (camada inferior); armadura y paralela a `ly`, uma bitola acima.
- **Unidirecional:** armadura principal paralela a `lx` (vão de cálculo $L = l_x$); armadura de distribuição paralela a `ly`.

### 3.2 Unidades

| Grandeza | Unidade |
|---|---|
| Vãos e alturas (internamente) | m |
| Cobrimento e bitola na entrada | mm |
| Cargas distribuídas | kN/m² |
| Momentos | kNm/m |
| Reações e cortantes | kN/m |
| Resistências e módulos | MPa (convertidos para kN/m² nas contas) |
| Armadura | cm²/m |
| Espaçamento | cm |

### 3.3 Sufixos de variáveis (modelo bidirecional)

| Sufixo | Significado |
|---|---|
| `_xp`, `_yp` | momento/armadura **positivo** em x e em y |
| `_xn`, `_yn` | momento/armadura **negativo** (engaste) em x e em y |
| `_elu`, `_rare`, `_qp` | combinação última, rara e quase permanente |

---

## 4. Tabelas de coeficientes (modelo bidirecional)

Todas são listas de linhas com $\lambda$ de 1,00 a 2,00, em passos de 0,05.

### 4.1 `MOMENTOS` (Quadros 7.3 a 7.5), casos 1 a 9

Cada linha: `[λ, µx+, µy+, µx−, µy−]`. Zero significa que **não há engaste** naquela direção.

$$
M = \mu \cdot \frac{p \, l_x^2}{100}
$$

### 4.2 `REACOES` (Quadros 7.8 a 7.10), casos 1 a 9

$$
R = k \cdot \frac{p \, l_x}{10}
$$

`coef_reacoes(caso, lam)` monta o dicionário de coeficientes:

| Caso | Coeficientes devolvidos |
|---|---|
| 1 | `kx`, `ky` |
| 2 | `kx`, `ky`, `kyp` (tabela extra `_KYP_CASO2`) |
| 3 | `kx`, `kxp`, `ky` (fixo 1,83) |
| 4 | `kx`, `kxp`, `ky` (fixo 1,83), `kyp` (fixo 3,17) |
| 5 | `kxp`, `ky` |
| 6 | `kx`, `kyp` |
| 7 | `kx`, `kxp`, `kyp` |
| 8 | `kxp`, `ky`, `kyp` |
| 9 | `kxp`, `kyp` |

Chaves com `p` (`kxp`, `kyp`) são de **borda engastada**. As demais, de borda apoiada.

### 4.3 `ALPHA_FLECHA` (Quadro 7.2)

Cada linha: `[λ, α_caso1, ..., α_caso9]`. A coluna usada é `caso − 1`.

$$
f = \alpha \cdot \frac{p \, l_x^4}{E_{cs} \, h^3 \cdot 100}
$$

### 4.4 Tabelas normativas

**Cobrimento nominal mínimo e fck mínimo por CAA** (`COB_NOMINAL`, `FCK_MIN_CAA`):

| CAA | Cobrimento (mm) | fck mínimo (MPa) |
|---|---:|---:|
| I | 20 | 20 |
| II | 25 | 25 |
| III | 35 | 30 |
| IV | 45 | 40 |

**Taxa mínima $\rho_{min}$ (%) para seção retangular** (`RHO_MIN_TAB`):

| fck (MPa) | 20 a 30 | 35 | 40 |
|---|---:|---:|---:|
| $\rho_{min}$ (%) | 0,150 | 0,164 | 0,179 |

A tabela completa vai até C90. `rho_min(fck)` interpola linearmente.

### 4.5 `AGREGADOS`

| Código | Agregado | $\alpha_E$ |
|---|---|---:|
| 1 | basalto/diabásio | 1,20 |
| 2 | granito/gnaisse | 1,00 |
| 3 | calcário | 0,90 |
| 4 | arenito | 0,70 |

---

## 5. Funções auxiliares (comuns aos dois modelos)

### 5.1 `interpolar(tabela, lam, col=None)`

$$
v = v_0 + t \,(v_1 - v_0), \qquad
t = \frac{\lambda - \lambda_0}{\lambda_1 - \lambda_0}
$$

Fora do intervalo tabelado, lança `ValueError` (**sem extrapolação**).

### 5.2 `xi(t_meses)`: coeficiente de fluência

$$
\xi(t) =
\begin{cases}
0 & t \leq 0 \\
0{,}68 \cdot 0{,}996^{\,t} \cdot t^{0{,}32} & 0 < t \leq 70 \text{ meses} \\
2{,}0 & t > 70 \text{ meses}
\end{cases}
$$

### 5.3 `fctm_nbr(fck)`

$$
f_{ctm} =
\begin{cases}
0{,}3 \, f_{ck}^{2/3} & f_{ck} \leq 50 \text{ MPa} \\
2{,}12 \ln\!\big(1 + 0{,}1\,(f_{ck} + 8)\big) & f_{ck} > 50 \text{ MPa}
\end{cases}
$$

### 5.4 `modulos_concreto(fck, alpha_E)`

$$
E_{ci} = \alpha_E \cdot 5600 \sqrt{f_{ck}} \quad (f_{ck} \leq 50)
$$

$$
\alpha_i = \min\!\left(0{,}8 + 0{,}2\,\frac{f_{ck}}{80},\; 1{,}0\right)
$$

$$
E_{cs} = \alpha_i \, E_{ci}
$$

### 5.5 `altura_minima(tipo)`

| Tipo | h mínimo |
|---|---|
| Piso não em balanço | 8 cm |
| Cobertura não em balanço | 7 cm |

### 5.6 `estimar_h_bastos(lx, ly, caso, cob, phi)`

Com $n$ = número de bordas engastadas (`N_BORDAS_ENGASTADAS`, de 0 a 4):

$$
l^* = \min(l_x,\; 0{,}7\,l_y)
$$

$$
d \,[\text{cm}] = (2{,}5 - 0{,}1\,n)\; l^* \,[\text{m}]
$$

$$
h = d + c + \frac{\phi}{2}
$$

No modelo unidirecional, usa-se `caso = 1` ($n = 0$) apenas como marcador.

---

## 6. Validação de entrada: `validar_entrada_modelo(d)`

| Verificação | Erro lançado |
|---|---|
| `lx`, `ly`, `h`, `phi`, `fck`, `fyk`, `gc`, `alpha_E` numéricos, finitos e maiores que zero | Parâmetro deve ser positivo |
| `q`, `cob`, cargas permanentes, `t0`, `tinf` maiores ou iguais a zero | Parâmetro não pode ser negativo |
| $0 \leq \psi_2 \leq 1$ | psi2 inválido |
| $t_{\infty} \geq t_0$ | Idade final antecede a inicial |
| CAA em I a IV | Classe de agressividade inválida |
| $h \geq h_{min}$ | Espessura abaixo do mínimo |
| $\phi \leq h/8$ | Bitola superior a h/8 |
| $c \geq \phi$ | Cobrimento inferior ao diâmetro |
| $h > 2c + \phi$ | Espessura insuficiente |

Em `executar_modelo`, também se verifica a escolha da vinculação: caso 1 a 9 (bidirecional) ou apoio 1 a 3 (unidirecional).

> A faixa C20–C40 e o fck mínimo da CAA não são checados em `validar_entrada_modelo`. O cobrimento nominal da CAA aparece na auditoria (seção 10), não como erro.

---

## 7. Modelo bidirecional: `calcular(d)`

### 7.1 Materiais

$$
\gamma_c = 1{,}4, \quad \gamma_s = 1{,}15, \quad
f_{cd} = \frac{f_{ck}}{\gamma_c}, \quad f_{yd} = \frac{f_{yk}}{\gamma_s}
$$

$$
f_{ctk,inf} = 0{,}7\, f_{ctm}
$$

### 7.2 Alturas úteis

$$
d_x = h - c - \frac{\phi}{2}, \qquad
d_y = h - c - \frac{3\phi}{2}
$$

As mesmas expressões valem para a armadura negativa.

### 7.3 Cargas

$$
g_1 = \gamma_{conc}\, h
$$

$$
g_2 = g_{contrapiso} + g_{revest.inf} + g_{piso} + g_{paredes} + g_{outros}
$$

$$
g = g_1 + g_2
$$

| Combinação | Expressão | Uso |
|---|---|---|
| ELU | $p_{ELU} = 1{,}4\,(g + q)$ | momentos, reações, armadura, cortante |
| ELS rara | $p_{rare} = g + q$ | estádio |
| ELS quase permanente | $p_{qp} = g + \psi_2\, q$ | flecha de longa duração |
| Parcela variável | $p_q = q$ | flecha da carga variável |

### 7.4 Momentos e reações

$$
M_i = \mu_i\,\frac{p_{ELU}\, l_x^2}{100}
$$

$$
R = k\,\frac{p_{ELU}\, l_x}{10}
$$

$$
R_x = \max(R_{x,ap},\, R_{x,eng}), \qquad
R_y = \max(R_{y,ap},\, R_{y,eng})
$$

### 7.5 Flexão

Faixa $b_w = 1{,}0$ m; $\alpha_c = 0{,}85$, $\eta_c = 1{,}0$, $\lambda_{bloco} = 0{,}8$.

$$
A = \alpha_c \eta_c f_{cd}\, b_w\, \lambda_{bloco}
$$

$$
x = \frac{A\,d - \sqrt{(A\,d)^2 - 2\,A\,\lambda_{bloco}\, M_d}}{A\,\lambda_{bloco}}
$$

$$
z = d - \frac{\lambda_{bloco}\, x}{2}, \qquad
A_s = \frac{M_d}{f_{yd}\, z}
$$

- Discriminante $\leq 0$: seção insuficiente.
- **Dutilidade:** $x/d \leq 0{,}45$, senão o código lança erro.

### 7.6 Armadura mínima e barras

$$
A_{s,min} = \frac{\rho_{min}}{100}\, b_w\, h
$$

| Armadura | Mínimo |
|---|---|
| Positiva (duas direções) | $0{,}67\, A_{s,min}$ |
| Negativa | $A_{s,min}$ |

$$
s_{max} = \min(2h,\; 20 \text{ cm})
$$

$$
n = \max\!\left(
\left\lceil \frac{A_s}{A_b} \right\rceil,\;
\left\lceil \frac{100}{s_{max}} \right\rceil
\right)
$$

$$
s = \frac{100}{n}
$$

### 7.7 Flecha

$$
I_c = \frac{b_w h^3}{12}, \qquad
M_r = \frac{1{,}5\, f_{ctm}\, I_c}{h/2}
$$

$M_a = \max(M_{x,rare}, M_{y,rare})$, com a armadura fornecida e a altura útil dessa direção.

Se $M_a > M_r$ (estádio II), com $\alpha_e = 210\,000 / E_{cs}$:

$$
\frac{b_w}{2}\, x_{II}^2 + \alpha_e A_s x_{II} - \alpha_e A_s d = 0
$$

$$
I_{II} = \frac{b_w x_{II}^3}{3} + \alpha_e A_s (d - x_{II})^2
$$

$$
I_{eq} = \min\!\left\{
\left(\frac{M_r}{M_a}\right)^3 I_c +
\left[1 - \left(\frac{M_r}{M_a}\right)^3\right] I_{II},
\; I_c
\right\}
$$

$$
f = \alpha\,\frac{p\, l_x^4}{E_{cs}\, h^3 \cdot 100}\cdot\frac{I_c}{I_{eq}}
$$

$$
\alpha_f = \xi(t) - \xi(t_0), \qquad
f_{total} = f_{qp}\,(1 + \alpha_f)
$$

Padrões: $t_0 = 0{,}47$ mês (14 dias) e $t = 70$ meses.

| Verificação | Condição |
|---|---|
| Flecha total | $f_{total} \leq l_x/250$ |
| Parcela variável | $f_q \leq l_x/350$ |

Não se aplica um limite genérico de $l/500$, porque ele depende do efeito específico.

### 7.8 Cisalhamento (x e y)

$$
\tau_{Rd} = 0{,}25\,\frac{f_{ctk,inf}}{\gamma_c}
$$

$$
\rho_1 = \min\!\left(\frac{A_{s1}}{b_w d}, 0{,}02\right), \qquad k = 1{,}0
$$

$$
V_{Rd1} = \tau_{Rd}\, k\,(1{,}2 + 40\rho_1)\, b_w d
$$

$$
V_{Sd} = \max(R_{crit} - p_{ELU}\, d,\; 0)
$$

---

## 8. Modelo unidirecional: `calcular_unidirecional(d)`

Faixa de 1 m na direção do menor vão ($L = l_x$), carga uniforme, viga prismática elástica linear. Não representa balanços, torção de canto ou cargas concentradas.

### 8.1 Geometria, materiais e cargas

$$
d = h - c - \frac{\phi}{2}
$$

Materiais, $g$, $p_d = 1{,}4(g+q)$ e $p_{qp} = g + \psi_2 q$ seguem as mesmas expressões do modelo bidirecional.

### 8.2 Esforços

| Vinculação (`apoio_1d`) | $M^+$ | $M^-$ | $R_A$ | $R_B$ | $k_f$ |
|---|---|---|---|---|---|
| 1. Apoiada-apoiada (A-A) | $p L^2/8$ | 0 | $pL/2$ | $pL/2$ | $5/384$ |
| 2. Engastada-apoiada (E-A) | $9pL^2/128$ | $pL^2/8$ | $5pL/8$ | $3pL/8$ | $0{,}00542$ |
| 3. Engastada-engastada (E-E) | $pL^2/24$ | $pL^2/12$ | $pL/2$ | $pL/2$ | $1/384$ |

### 8.3 Armaduras

A flexão usa o mesmo bloco retangular e o mesmo limite $x/d \leq 0{,}45$ do modelo bidirecional.

| Armadura | Valor adotado |
|---|---|
| Principal positiva | $\max(A_{s,calc}, A_{s,min})$, com o **mínimo integral** |
| Principal negativa | $\max(A_{s,calc}, A_{s,min})$, se $M^- > 0$ |
| Distribuição | $\max(0{,}20\,A_{s,pos};\; 0{,}90 \text{ cm²/m};\; 0{,}50\,A_{s,min})$ |

O critério da distribuição segue a NBR 6118:2026, Tabela 19.1 (armadura secundária).

### 8.4 Flecha

$M_a$ usa a combinação rara $p_k = g + q$:

| Vinculação | $M_a$ |
|---|---|
| A-A | $p_k L^2/8$ |
| E-A | $\max(p_k L^2/8,\; 9 p_k L^2/128)$ |
| E-E | $p_k L^2/12$ |

Estádio e $I_{eq}$ seguem a mesma formulação de Branson, com a armadura principal positiva fornecida.

$$
f_{el} = k_f\,\frac{p_{qp} L^4}{E_{cs} I_c}
$$

$$
f_{imediata} = f_{el}\,\frac{I_c}{I_{eq}}, \qquad
f_q = k_f\,\frac{q L^4}{E_{cs} I_{eq}}
$$

$$
f_{diferida} = \alpha_f\, f_{imediata}, \qquad
f_{total} = f_{imediata} + f_{diferida}
$$

Limites: $L/250$ (total) e $L/350$ (parcela variável).

### 8.5 Cisalhamento

$$
V_{Rd} = 0{,}25\, f_{ctd}\,(1{,}2 + 40\rho)\, d
$$

$$
V_{Sd} = \max(R_A, R_B) - p_d\, d
$$

---

## 9. Detalhamento geométrico: `selecionar_barras` e `avaliar_detalhamento`

As barras são verificadas em todas as armaduras do modelo:

- Bidirecional: x/y positivas e x/y negativas.
- Unidirecional: principal positiva, principal negativa e distribuição.

$$
s_{livre} = s - \phi \;\geq\;
\max(20 \text{ mm},\; \phi,\; 1{,}2\, d_{max,agr})
$$

com $d_{max,agr} = 19$ mm por padrão (`agregado_max_mm`).

Quando o espaçamento livre não atende, o código sugere até três bitolas maiores (6,3 a 25 mm) compatíveis com $h/8$ e com o cobrimento. Também há alerta para mais de 100 barras/m.

Resultado: `r['detalhamento']`, `r['detalhamento_ok']` e `r['detalhamento_alertas']`.

---

## 10. Auditoria normativa: `auditar_limites_normativos`

Triagem explícita (NBR 6118:2026, 7.4.7, 13.2.4, 19.3.3, 20.1–20.2):

| Check | Critério |
|---|---|
| Cobrimento da CAA | $c \geq c_{nom}$ (Tabela 7.2) |
| Cobrimento × bitola | $c \geq \phi$ |
| Agregado | $d_{max} \leq 1{,}2\,c$ |
| Bitola máxima | $\phi \leq h/8$ |
| Espessura mínima | $h \geq h_{min}$ |
| Uma camada cabe | $h > 2c + \phi$ |
| Espaçamento máximo | $\min(2h, 20)$ cm; **33 cm** na distribuição |
| Espaçamento livre | conforme a seção 9 |
| Área fornecida | $A_{s,forn} \geq A_{s,req}$ |
| Armadura secundária (só 1D) | critério da seção 8.3 |

O status é `NAO ATENDE` ou `TRIAGEM ATENDE; VALIDACAO DE PROJETO PENDENTE`.

A lista `pendencias` registra o que não é verificável com os dados de entrada: armadura de borda sem continuidade, bordas livres e aberturas, ancoragem e emendas, momentos volventes, compatibilização entre lajes, punção e cargas concentradas, refinamento de ELS e as hipóteses do perfil acadêmico.

---

## 11. Saídas impressas

| Função | Conteúdo |
|---|---|
| `imprimir(d, r)` | Memória bidirecional em 10 seções (dados, materiais, alturas úteis, cargas, momentos, reações, armaduras, flecha, cisalhamento, resumo) |
| `imprimir_unidirecional(d, r)` | Memória unidirecional em 8 seções (geometria, materiais, ações, esforços, armaduras, cisalhamento, flechas, resumo) |
| `imprimir_detalhamento(r)` | Acomodação das barras por armadura e resultado geral |
| `imprimir_auditoria_normativa(r)` | Checks `[OK]`/`[FALHA]` e total atendido |
| `imprimir_parecer_final(d, r)` | Parecer com flechas, cisalhamento, detalhamento e limites: ATENDE / NÃO ATENDE / NÃO VERIFICADO |

### 11.1 Principais chaves de `r`

| Grupo | Bidirecional | Unidirecional |
|---|---|---|
| Esforços | `Mx_pos`, `My_pos`, `Mx_neg`, `My_neg`, `Rx`, `Ry` | `Mpos`, `Mneg`, `Ra`, `Rb` |
| Armaduras | `As_*_calc`, `As_*`, `Asf_*`, `n_*`, `s_*` | `Aspos_calc`, `Asneg_calc`, `Aspos`, `Asneg`, `Asdist`, `barras` |
| Dutilidade | `xid_xp`, `xid_yp`, `xid_xn`, `xid_yn` | `xip`, `xin` |
| Flecha | `f_qp`, `f_q`, `f_total`, `f_imediata`, `f_diferida` | `f_el`, `f_imediata`, `f_diferida`, `f_total`, `f_q`, `els_total_ok`, `els_q_ok` |
| Cisalhamento | `Vsd_x`, `VRd1_x`, `Vsd_y`, `VRd1_y`, `cis_ok_x`, `cis_ok_y` | `Vsd`, `VRd`, `cis_ok` |
| Comuns | `Mr`, `Ma`, `Ic`, `III`, `Ieq`, `estadio`, `alpha_f`, `lim_250`, `lim_350`, `detalhamento`, `auditoria_normativa` | idem |

\* As chaves `f_imediata` e `f_diferida` são acrescentadas por `anexar_verificacoes_complementares`.

---

## 12. Limitações e pontos de atenção

1. **Descrição dos casos 2D.** Confira a numeração e a orientação das bordas engastadas (`DESCRICAO` e `coef_reacoes`) com os quadros do livro, sobretudo nos casos 2, 3, 5, 6 e 8.
2. **Valores suspeitos nas tabelas.** Revise `MOMENTOS[1]` em λ = 1,60 (µy⁺ = 3,14 destoa da vizinhança) e `ALPHA_FLECHA` caso 8 em λ = 1,55 (2,53). No caso 8, `coef_reacoes` usa `vals[1..3]` e ignora `vals[0]`.
3. **Combinação última simplificada:** $1{,}4(g+q)$ vale para uma única ação variável.
4. **Concreto limitado a C40** no bloco de tensões e na ductilidade.
5. **Cisalhamento conservador:** $k = 1{,}0$ e $V_{Sd} = R - p\,d$, sem largura de apoio.
6. **Flecha 2D:** a rigidez equivalente vem da direção de maior momento raro e é aplicada às duas parcelas; $\rho' = 0$.
7. **Flecha 1D (E-A):** $M_a$ resulta no momento de engaste, mas a inércia fissurada usa a armadura positiva. É uma estimativa preliminar.
8. **Compatibilização de momentos** entre lajes adjacentes não é feita.
9. Balanços, lajes nervuradas, lisas/cogumelo, cargas concentradas e geometrias não retangulares não são cobertos.
10. As referências à NBR 6118:2026 nos comentários devem ser conferidas contra o texto vigente.
11. **Ferramenta de apoio acadêmico.** Os resultados devem ser revisados por engenheiro responsável antes de qualquer uso em projeto.

---

## 13. Como validar o código

1. Resolva à mão um exemplo do livro em cada modelo e compare $M$, $A_s$ e a flecha.
2. Teste a fronteira: λ = 2,00 deve cair no bidirecional e λ = 2,01 no unidirecional.
3. Para cada vinculação 1D, confira as reações por equilíbrio: $R_A + R_B = pL$.
4. Teste entradas inválidas: $\phi > h/8$, $c < \phi$, $\psi_2 > 1$, $t < t_0$, caso ou apoio fora da lista.
5. Verifique a coerência: aumentar $h$ reduz $A_s$ e a flecha; aumentar $q$ aumenta $M$, $A_s$ e a flecha.
6. Escreva testes `pytest` chamando `executar_modelo()` com dicionários fixos e valores de referência.

---

## 14. Referências

- CARVALHO, R. C.; FIGUEIREDO FILHO, J. R. *Cálculo e Detalhamento de Estruturas Usuais de Concreto Armado*. 4ª ed.
- BASTOS, P. S. dos S. *Lajes de concreto*. Notas de aula (pré-dimensionamento).
- ABNT NBR 6118:2026 — Projeto de estruturas de concreto.
- ABNT NBR 6120:2019 — Ações para o cálculo de estruturas de edificações.