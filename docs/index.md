---
layout: default
title: Calculadora de Lajes Maciças
---

<script async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>

# Calculadora de Lajes Maciças de Concreto Armado

Documentação do código de cálculo (`calculo.py`) e de sua integração com a interface (`gui.py`)

Referências citadas no código: Carvalho & Figueiredo, *Cálculo e Detalhamento de Estruturas Usuais de Concreto Armado* (4ª ed.); Bastos (pré-dimensionamento); ABNT NBR 6118:2026; ABNT NBR 6120:2019.

---

## 1. Visão geral

O módulo dimensiona **lajes maciças retangulares** e produz uma memória de cálculo completa. A laje é classificada automaticamente pela relação entre os vãos, e o código escolhe um entre dois modelos:

| Modelo | Quando | Método |
|---|---|---|
| **Bidirecional** (armada em duas direções) | $$\lambda \le 2{,}0$$ | Coeficientes tabelados de Carvalho & Figueiredo (momentos, reações e flechas), casos de vinculação 1 a 9 |
| **Unidirecional** (armada em uma direção) | $$\lambda > 2{,}0$$ | Faixa de 1 m no menor vão, análise elástica linear de viga, três condições de apoio |

Em ambos os modelos o programa cobre:

1. Pré-dimensionamento da espessura (estimativa de Bastos).
2. Levantamento de cargas (ELU e ELS).
3. Esforços: momentos fletores e reações de apoio.
4. Dimensionamento da armadura de flexão.
5. Armadura mínima e espaçamento máximo.
6. Triagem geométrica do espaçamento das barras.
7. Verificação de flecha, com fissuração (Branson) e fluência.
8. Verificação simplificada ao cisalhamento.
9. Auditoria de limites normativos e parecer final.

### 1.1 Escopo

| Item | Limite nesta versão |
|---|---|
| Geometria | Laje retangular com vãos positivos e finitos |
| Modelo bidirecional | $$\lambda = l_y/l_x \le 2{,}0$$, casos de vinculação 1 a 9 |
| Modelo unidirecional | $$\lambda > 2{,}0$$, apoios A-A, E-A e E-E na direção do menor vão |
| Concreto | Escopo de C20 a C40 (o limite de dutilidade $$x/d \le 0{,}45$$ foi adotado para essa faixa) |
| Tipo de laje | Piso ou cobertura, não em balanço |
| Ação variável | Uma única ação variável |

O código **lança `ValueError`** em vez de extrapolar silenciosamente (por exemplo, $$\lambda$$ fora do intervalo tabelado, seção insuficiente à flexão ou dutilidade não atendida).

> A interface fixa o concreto em C20 a C40 ao usar o $$f_{ck}$$ mínimo da classe de agressividade (C20, C25, C30 e C40). O módulo `calculo.py` em si **não bloqueia** valores de $$f_{ck}$$ fora dessa faixa; quem o chama diretamente deve respeitar o escopo.

---

## 2. Arquitetura e fluxo de dados

```
Interface (gui.py)
   │  classificar_laje(vão A, vão B)     → modelo, casos disponíveis, λ
   │  usuário escolhe a vinculação
   ▼
montar_dados_padrao(...)                 → dicionário de entrada
   ▼
executar_modelo(dados)                   → (d, r)
   │   ├─ validar_entrada_modelo(d)
   │   ├─ classificar_laje(lx, ly)
   │   ├─ calcular(d)  ou  calcular_unidirecional(d)
   │   ├─ anexar_verificacoes_complementares(d, r)
   │   ├─ avaliar_detalhamento(d, r)
   │   └─ auditar_limites_normativos(d, r)
   ▼
gerar_memoria(dados)                     → textos capturados com redirect_stdout
   ├─ imprimir(d, r)  ou  imprimir_unidirecional(d, r)
   ├─ imprimir_detalhamento(r)
   ├─ imprimir_parecer_final(d, r)
   └─ imprimir_auditoria_normativa(r)
```

Organização dos arquivos:

| Arquivo | Papel |
|---|---|
| `calculo.py` | Tabelas, fórmulas, classificação, cálculo e impressão da memória. Não tem entrada de dados por terminal |
| `gui.py` | Interface PySide6; monta o dicionário de entrada, chama `executar_modelo` e exibe os resultados |
| `cli.py` | Versão opcional de terminal, com a função `entrada()` que faz as perguntas |
| `test_paridade.py` | Compara o fluxo da interface com o fluxo de terminal em 14 casos |

Pontos importantes:

- `calcular()` e `calcular_unidirecional()` **não imprimem nada**: recebem `d` e devolvem `r`. Isso permite testar o núcleo sem interface.
- `imprimir*()` só formatam `d` e `r`. Não calculam nada novo.
- `executar_modelo()` é o **ponto único de entrada** do cálculo. Ele escolhe o módulo adequado a partir de $$\lambda$$ e devolve `(d, r)`.
- Erros de entrada ou de modelo são `ValueError` ou `KeyError`, tratados na interface com `QMessageBox`.

---

## 3. Convenções

### 3.1 Eixos e vãos

- `lx` é o **menor vão** e `ly` o maior. Os lados informados são ordenados automaticamente por `classificar_laje()`.
- O parâmetro de forma é:

$$
\lambda = \frac{l_y}{l_x}
$$

**Bidirecional:**

- Direção **x**: armadura paralela a `lx`, na camada inferior.
- Direção **y**: armadura paralela a `ly`, uma bitola acima (segunda camada).

**Unidirecional:**

- O vão de cálculo é `lx` (menor vão); a armadura principal fica nessa direção.
- A armadura de distribuição é perpendicular a ela.
- `ly` só entra no cálculo de $$\lambda$$ e na estimativa de espessura.

### 3.2 Unidades

| Grandeza | Unidade |
|---|---|
| Vãos, alturas, cobrimentos (internamente) | m |
| Cobrimento e bitola no dicionário de entrada | mm |
| Espessura `h` na interface | cm (convertida para m internamente) |
| Cargas distribuídas | kN/m² |
| Momentos | kN·m/m |
| Reações e cortantes | kN/m |
| Resistências e módulos | MPa (convertidos para kN/m² nas contas) |
| Armadura | cm²/m |
| Espaçamento | cm |

### 3.3 Sufixos de variáveis (bidirecional)

| Sufixo | Significado |
|---|---|
| `_xp`, `_yp` | momento/armadura **positivo** em x e em y |
| `_xn`, `_yn` | momento/armadura **negativo** (engaste) em x e em y |
| `_elu`, `_rare`, `_qp` | combinação última, rara e quase permanente |

### 3.4 Marcadores do dicionário de entrada

| Chave | Bidirecional | Unidirecional |
|---|---|---|
| `unidirecional` | `False` | `True` |
| `caso` | caso de vinculação (1 a 9) | sempre `1` (apenas marcador para a estimativa de espessura) |
| `apoio_1d` | `None` | 1 (A-A), 2 (E-A) ou 3 (E-E) |

Os três apoios unidirecionais **não** equivalem numericamente aos casos 1, 3 e 5 do modelo bidirecional.

---

## 4. Classificação da laje (`classificar_laje`)

```python
info = classificar_laje(lado_a, lado_b)
```

A função **não dimensiona nada**; apenas devolve o que a interface precisa. Se algum lado não for positivo e finito, lança `ValueError`.

| Chave | Conteúdo |
|---|---|
| `lx`, `ly` | vãos ordenados (menor e maior) |
| `lambda` | $$\lambda = l_y/l_x$$ |
| `unidirecional` | `True` se $$\lambda > 2{,}0$$ |
| `modelo` | `"bidirecional"` ou `"unidirecional"` |
| `titulo` | `"LAJE BIDIRECIONAL"` ou `"LAJE UNIDIRECIONAL"` |
| `casos` | dicionário de vinculações disponíveis (9 casos ou 3 apoios) |
| `nota` | texto de apoio para a interface |

A regra é aplicada sobre os vãos, sem depender da vinculação escolhida. Ao mudar as dimensões, a interface descarta a vinculação anterior.

### 4.1 Casos bidirecionais (`DESCRICAO`)

| Caso | Descrição |
|---|---|
| 1 | 4 bordas simplesmente apoiadas |
| 2 | 1 borda engastada paralela a $$l_y$$; demais apoiadas |
| 3 | 1 borda engastada paralela a $$l_x$$; demais apoiadas |
| 4 | 2 bordas adjacentes engastadas; demais apoiadas |
| 5 | 2 bordas opostas engastadas paralelas a $$l_y$$; demais apoiadas |
| 6 | 2 bordas opostas engastadas paralelas a $$l_x$$; demais apoiadas |
| 7 | 3 bordas engastadas; borda apoiada paralela a $$l_y$$ |
| 8 | 3 bordas engastadas; borda apoiada paralela a $$l_x$$ |
| 9 | 4 bordas engastadas |

### 4.2 Casos unidirecionais (`CASOS_UNIDIRECIONAIS`)

| Apoio | Descrição |
|---|---|
| 1 | Apoiada nas duas extremidades da faixa (A-A) |
| 2 | Engastada em uma extremidade e apoiada na outra (E-A) |
| 3 | Engastada nas duas extremidades da faixa (E-E) |

---

## 5. Tabelas de coeficientes (modelo bidirecional)

`MOMENTOS`, `REACOES` e `ALPHA_FLECHA` são listas de linhas com $$\lambda$$ de 1,00 a 2,00, em passos de 0,05.

### 5.1 `MOMENTOS` (Quadros 7.3 a 7.5)

Dicionário por caso (1 a 9). Cada linha: `[λ, µx+, µy+, µx−, µy−]`. Zero significa que **não há engaste** naquela direção.

$$
M = \mu \cdot \frac{p \, l_x^2}{100}
$$

### 5.2 `REACOES` (Quadros 7.8 a 7.10)

Cada linha traz os coeficientes tabelados do caso; os coeficientes de borda engastada e alguns valores constantes são completados em `coef_reacoes()`.

$$
R = k \cdot \frac{p \, l_x}{10}
$$

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

### 5.3 `ALPHA_FLECHA` (Quadro 7.2)

Cada linha: `[λ, α_caso1, ..., α_caso9]`. A coluna usada é `caso − 1`.

$$
f = \alpha \cdot \frac{p \, l_x^4}{E_{cs} \, h^3 \cdot 100}
$$

### 5.4 Tabelas normativas

**Cobrimento nominal mínimo e $$f_{ck}$$ mínimo por classe de agressividade (CAA):**

| CAA | Cobrimento (mm) | fck mínimo (MPa) |
|---|---|---|
| I | 20 | 20 |
| II | 25 | 25 |
| III | 35 | 30 |
| IV | 45 | 40 |

**Taxa mínima de armadura $$\rho_{min}$$ (%) para seção retangular** (`RHO_MIN_TAB`):

| fck (MPa) | 20 a 30 | 35 | 40 |
|---|---|---|---|
| $$\rho_{min}$$ (%) | 0,150 | 0,164 | 0,179 |

A tabela completa vai até C90. `rho_min(fck)` interpola linearmente entre os valores e satura nos extremos.

**Agregados (`AGREGADOS`):** fator $$\alpha_E$$ para o módulo de elasticidade.

| Código | Agregado | $$\alpha_E$$ |
|---|---|---|
| 1 | basalto/diabásio | 1,20 |
| 2 | granito/gnaisse | 1,00 |
| 3 | calcário | 0,90 |
| 4 | arenito | 0,70 |

**Bordas engastadas por caso (`N_BORDAS_ENGASTADAS`)**, usado na estimativa de espessura:

| Caso | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|---|---|
| $$n$$ | 0 | 1 | 1 | 2 | 2 | 2 | 3 | 3 | 4 |

---

## 6. Funções auxiliares

### 6.1 `interpolar(tabela, lam, col=None)`

Interpolação linear entre duas linhas consecutivas da tabela:

$$
v = v_0 + t \,(v_1 - v_0), \qquad t = \frac{\lambda - \lambda_0}{\lambda_1 - \lambda_0}
$$

- Se $$\lambda$$ estiver fora do intervalo tabelado, lança `ValueError` (**sem extrapolação**).
- Com `col=None`, devolve a lista de coeficientes da linha. Com `col=i`, devolve só o i-ésimo.

### 6.2 `coef_reacoes(caso, lam)` e `reacoes_kNm(caso, lam, p, lx)`

A primeira devolve o dicionário de coeficientes $$k$$ do caso (tabela da seção 5.2). A segunda multiplica cada $$k$$ por $$p\,l_x/10$$. Caso fora de 1 a 9 lança `ValueError`.

### 6.3 `xi(t_meses)`: coeficiente $$\xi(t)$$ de fluência

$$
\xi(t) =
\begin{cases}
0 & t \le 0 \\
0{,}68 \cdot 0{,}996^{\,t} \cdot t^{0{,}32} & 0 < t \le 70 \text{ meses} \\
2{,}0 & t > 70 \text{ meses}
\end{cases}
$$

### 6.4 `fctm_nbr(fck)`: resistência média à tração

$$
f_{ctm} =
\begin{cases}
0{,}3 \, f_{ck}^{2/3} & f_{ck} \le 50 \text{ MPa} \\
2{,}12 \ln\!\big(1 + 0{,}1\,(f_{ck} + 8)\big) & f_{ck} > 50 \text{ MPa}
\end{cases}
$$

### 6.5 `modulos_concreto(fck, alpha_E)`: módulos de elasticidade

$$
E_{ci} = \alpha_E \cdot 5600 \sqrt{f_{ck}} \quad (f_{ck} \le 50 \text{ MPa})
$$

$$
\alpha_i = \min\!\left(0{,}8 + 0{,}2\,\frac{f_{ck}}{80},\; 1{,}0\right)
$$

$$
E_{cs} = \alpha_i \, E_{ci}
$$

O módulo $$E_{cs}$$ (secante) é o usado nas flechas.

### 6.6 `altura_minima(tipo)`

| Tipo | h mínimo |
|---|---|
| Piso não em balanço | 8 cm |
| Cobertura não em balanço | 7 cm |

### 6.7 `estimar_h_bastos(lx, ly, caso, cob, phi)`

Estimativa da espessura pelo pré-dimensionamento de Bastos, com $$n$$ = número de bordas engastadas (`N_BORDAS_ENGASTADAS`):

$$
l^* = \min(l_x,\; 0{,}7\,l_y)
$$

$$
d \,[\text{cm}] = (2{,}5 - 0{,}1\,n)\; l^* \,[\text{m}]
$$

$$
h = d + c + \frac{\phi}{2}
$$

Devolve `(d, h_est, l*, n)`. No modelo unidirecional usa-se `caso = 1` ($$n = 0$$). A interface mostra essa estimativa como orientação; a espessura adotada é a informada pelo usuário.

### 6.8 `selecionar_barras(As, phi, h, cob, agregado_max_mm=19, s_max_cm=None)`

Escolhe o número de barras por metro e faz a triagem geométrica do espaçamento.

$$
A_b = \frac{\pi \phi^2}{4} \qquad \text{(cm² por barra, com } \phi \text{ em cm)}
$$

$$
s_{max} = \min(2h,\; 20 \text{ cm})
$$

$$
n = \max\!\left(\left\lceil \frac{A_s}{A_b} \right\rceil,\; \left\lceil \frac{100}{s_{max}} \right\rceil\right)
$$

$$
s = \frac{100}{n}, \qquad A_{s,forn} = n\, A_b
$$

O espaçamento livre entre faces de barras vizinhas e o mínimo geométrico adotado são:

$$
e_{livre} = s - \phi, \qquad e_{livre,min} = \max\!\left(20 \text{ mm},\; \phi,\; 1{,}2\, d_{max}\right)
$$

com $$d_{max} = 19$$ mm por padrão. A função devolve `n`, `s_cm`, `As_fornecida`, `livre_mm`, `livre_min_mm`, `status` e `avisos`. Gera aviso quando:

- o espaçamento livre é menor que o mínimo (com alternativas de bitola, quando existirem);
- há mais de 100 barras por metro;
- $$\phi > h/8$$;
- o cobrimento é menor que a bitola.

O `status` é `NÃO ATENDE` se houver aviso, e `ATENDE (triagem geométrica)` caso contrário. Para $$A_s \le 0$$ devolve `NÃO APLICÁVEL`.

### 6.9 `validar_entrada_modelo(d)`

Ver seção 11.

---

## 7. Modelo bidirecional: `calcular(d)`

### 7.1 Materiais

$$
\gamma_c = 1{,}4, \qquad \gamma_s = 1{,}15
$$

$$
f_{cd} = \frac{f_{ck}}{\gamma_c}, \qquad f_{yd} = \frac{f_{yk}}{\gamma_s}
$$

$$
f_{ctk,inf} = 0{,}7\, f_{ctm}
$$

Os módulos $$E_{ci}$$, $$\alpha_i$$ e $$E_{cs}$$ vêm de `modulos_concreto()`. Para as contas, $$E_{cs}$$ é convertido de MPa para kN/m² (× 1000).

### 7.2 Alturas úteis

$$
d_{x} = h - c - \frac{\phi}{2}
$$

$$
d_{y} = h - c - \frac{3\phi}{2}
$$

A armadura em x fica na camada mais externa. A de y fica uma bitola acima, por isso perde $$\phi$$ de altura útil. As mesmas expressões valem para a armadura negativa. Se alguma altura útil for $$\le 0$$, o código lança erro.

### 7.3 Cargas

$$
g_1 = \gamma_{conc} \cdot h \qquad \text{(peso próprio)}
$$

$$
g_2 = g_{contrapiso} + g_{revest.inf} + g_{piso} + g_{paredes} + g_{outros}
$$

$$
g = g_1 + g_2
$$

| Combinação | Expressão | Uso |
|---|---|---|
| ELU (normal simplificada) | $$p_{ELU} = 1{,}4\,(g + q)$$ | momentos, reações, armadura, cortante |
| ELS rara | $$p_{rare} = g + q$$ | verificação de fissuração (estádio) |
| ELS quase permanente | $$p_{qp} = g + \psi_2\, q$$ | flecha de longa duração |
| Parcela variável | $$p_q = q$$ | flecha devida à carga variável |

### 7.4 Momentos fletores

Os coeficientes $$\mu$$ são interpolados em $$\lambda$$:

$$
M_{x+} = \mu_{x+}\,\frac{p_{ELU}\, l_x^2}{100}, \qquad
M_{y+} = \mu_{y+}\,\frac{p_{ELU}\, l_x^2}{100}
$$

$$
M_{x-} = \mu_{x-}\,\frac{p_{ELU}\, l_x^2}{100}, \qquad
M_{y-} = \mu_{y-}\,\frac{p_{ELU}\, l_x^2}{100}
$$

Os momentos negativos só existem se o respectivo $$\mu > 0$$. Os momentos de serviço $$M_{x,rare}$$ e $$M_{y,rare}$$ usam a mesma fórmula com $$p_{rare}$$.

### 7.5 Reações de apoio

$$
R = k\,\frac{p_{ELU}\, l_x}{10}
$$

O código guarda as reações em borda apoiada (`Rx_ap`, `Ry_ap`) e em borda engastada (`Rx_eng`, `Ry_eng`). Os valores **críticos** são:

$$
R_x = \max(R_{x,ap},\, R_{x,eng}), \qquad R_y = \max(R_{y,ap},\, R_{y,eng})
$$

Se um tipo de borda não existe no caso, o valor correspondente é `None` e fica fora do máximo.

### 7.6 Dimensionamento à flexão

Faixa de largura $$b_w = 1{,}0$$ m, com bloco retangular de tensões e parâmetros:

$$
\alpha_c = 0{,}85, \qquad \eta_c = 1{,}0, \qquad \lambda_{bloco} = 0{,}8
$$

Equilíbrio de momentos, com $$\sigma_c = \alpha_c\,\eta_c\,f_{cd}$$ e $$A = \sigma_c\, b_w\, \lambda_{bloco}$$:

$$
M_d = A\, x\left(d - \frac{\lambda_{bloco}\, x}{2}\right)
$$

Resolvendo a equação do 2º grau para a linha neutra:

$$
x = \frac{A\,d - \sqrt{(A\,d)^2 - 2\,A\,\lambda_{bloco}\, M_d}}{A\,\lambda_{bloco}}
$$

Braço de alavanca e armadura:

$$
z = d - \frac{\lambda_{bloco}\, x}{2}
$$

$$
A_s = \frac{M_d}{f_{yd}\, z}
$$

O resultado é convertido para cm²/m.

- Se o discriminante for $$\le 0$$, a seção é insuficiente e o código pede maior $$h$$.
- **Dutilidade:** exige-se $$x/d \le 0{,}45$$ (escopo C20 a C40) em cada direção com momento. Se violado, lança erro.

### 7.7 Armadura mínima e detalhamento

$$
A_{s,min} = \frac{\rho_{min}}{100}\; b_w\; h \qquad (b_w = 100 \text{ cm})
$$

Observe que a taxa é referida a $$b_w\,h$$, e não a $$b_w\,d$$.

| Armadura | Mínimo aplicado |
|---|---|
| Positiva (duas direções) | $$0{,}67\, A_{s,min}$$ |
| Negativa | $$A_{s,min}$$ |

A armadura adotada é o maior valor entre a calculada e a mínima. Número de barras e espaçamento seguem as expressões da seção 6.8.

### 7.8 Flecha

**a) Momento de fissuração** (seção retangular, fator 1,5):

$$
I_c = \frac{b_w\, h^3}{12}, \qquad M_r = \frac{1{,}5\, f_{ctm}\, I_c}{h/2}
$$

**b) Momento de serviço crítico:** $$M_a$$ é o maior entre $$M_{x,rare}$$ e $$M_{y,rare}$$. Usam-se a armadura fornecida e a altura útil dessa direção.

**c) Estádio:**

- Se $$M_a \le M_r$$: **estádio I**, com $$I_{eq} = I_c$$.
- Se $$M_a > M_r$$: **estádio II**, com rigidez equivalente de Branson.

Relação modular e linha neutra no estádio II ($$\alpha_e = E_s / E_{cs}$$, $$E_s = 210\,000$$ MPa):

$$
\frac{b_w}{2}\, x_{II}^2 + \alpha_e\, A_s\, x_{II} - \alpha_e\, A_s\, d = 0
$$

Inércia fissurada:

$$
I_{II} = \frac{b_w\, x_{II}^3}{3} + \alpha_e\, A_s\,(d - x_{II})^2
$$

Inércia equivalente (Branson), limitada a $$I_c$$:

$$
I_{eq} = \left(\frac{M_r}{M_a}\right)^3 I_c + \left[1 - \left(\frac{M_r}{M_a}\right)^3\right] I_{II}
$$

**d) Flecha imediata.** A flecha elástica vem do coeficiente $$\alpha$$ tabelado e é corrigida pela perda de rigidez:

$$
f_{el} = \alpha\,\frac{p\, l_x^4}{E_{cs}\, h^3 \cdot 100}, \qquad
f = f_{el}\cdot\frac{I_c}{I_{eq}}
$$

São calculadas duas flechas imediatas: $$f_{qp}$$ (com $$p_{qp}$$) e $$f_q$$ (com $$p_q = q$$).

**e) Fluência** (sem armadura comprimida considerada, $$\rho' = 0$$):

$$
\alpha_f = \max\big(0,\; \xi(t) - \xi(t_0)\big)
$$

$$
f_{total} = f_{qp}\,(1 + \alpha_f)
$$

O tempo $$t_0$$ é a idade da aplicação da carga de longa duração (perfil da interface: 14 dias, ou seja, 0,47 mês). O tempo $$t$$ é o tempo final (70 meses).

**f) Limites verificados:**

| Verificação | Condição |
|---|---|
| Flecha total diferida | $$f_{total} \le l_x/250$$ |
| Parcela da carga variável | $$f_q \le l_x/350$$ |

O código **não** aplica uma verificação genérica de $$l/500$$, porque esse limite depende do efeito específico (por exemplo, deslocamentos que prejudicam elementos não estruturais).

### 7.9 Cisalhamento

Verificação feita **nas duas direções**, sem armadura transversal:

$$
f_{ctd} = \frac{f_{ctk,inf}}{\gamma_c}, \qquad \tau_{Rd} = 0{,}25\, f_{ctd}
$$

$$
\rho_1 = \min\!\left(\frac{A_{s1}}{b_w\, d},\; 0{,}02\right)
$$

$$
V_{Rd1} = \tau_{Rd}\; k\,(1{,}2 + 40\,\rho_1)\; b_w\, d
$$

com $$k = 1{,}0$$ (conservador, pois a ancoragem não é modelada) e $$A_{s1}$$ igual à armadura positiva fornecida.

Esforço solicitante, aproximado a uma distância $$d$$ da face do apoio:

$$
V_{Sd} = \max\!\left(R_{crit} - p_{ELU}\, d,\; 0\right)
$$

Condição: $$V_{Sd} \le V_{Rd1}$$ em x e em y.

---

## 8. Modelo unidirecional: `calcular_unidirecional(d)`

Modelo de **viga de 1 m de largura** no menor vão $$L = l_x$$, com carga uniformemente distribuída e análise elástica linear. Não representa balanços, torção de canto nem cargas concentradas.

### 8.1 Altura útil e cargas

$$
d_u = h - c - \frac{\phi}{2}
$$

Se $$d_u \le 0$$, lança erro. As cargas seguem as mesmas definições da seção 7.3:

$$
g = \gamma_{conc}\, h + g_{contrapiso} + g_{revest.inf} + g_{piso} + g_{paredes} + g_{outros}
$$

$$
p_d = 1{,}4\,(g + q), \qquad p_{qp} = g + \psi_2\, q
$$

### 8.2 Esforços e coeficiente de flecha

Conforme a condição de apoio (`apoio_1d`), por equilíbrio e análise elástica de viga prismática:

| Apoio | $$M^+$$ (positivo) | $$M^-$$ (negativo, módulo) | $$R_A$$ | $$R_B$$ | $$k_{flecha}$$ |
|---|---|---|---|---|---|
| 1 · A-A | $$p_d L^2/8$$ | 0 | $$p_d L/2$$ | $$p_d L/2$$ | $$5/384$$ |
| 2 · E-A | $$9\,p_d L^2/128$$ | $$p_d L^2/8$$ | $$5\,p_d L/8$$ | $$3\,p_d L/8$$ | $$0{,}00542$$ |
| 3 · E-E | $$p_d L^2/24$$ | $$p_d L^2/12$$ | $$p_d L/2$$ | $$p_d L/2$$ | $$1/384$$ |

No apoio 2, $$R_A$$ corresponde à extremidade engastada e $$R_B$$ à apoiada.

### 8.3 Dimensionamento à flexão

Usa o mesmo bloco retangular de tensões da seção 7.6, com $$\alpha_c = 0{,}85$$, $$\lambda_{bloco} = 0{,}8$$ e $$b_w = 1$$ m:

$$
x = \frac{A\,d_u - \sqrt{(A\,d_u)^2 - 2\,A\,\lambda_{bloco}\, M}}{A\,\lambda_{bloco}}, \qquad
z = d_u - 0{,}4\,x, \qquad
A_s = \frac{M}{f_{yd}\, z}
$$

- Para $$M \le 0$$ a armadura calculada é nula.
- Discriminante $$\le 0$$: erro de seção insuficiente (aumentar $$h$$).
- $$x/d_u > 0{,}45$$: erro de dutilidade.

### 8.4 Armaduras adotadas

$$
A_{s,base} = \frac{\rho_{min}}{100}\; 100\; (100\,h) \qquad \text{(cm²/m)}
$$

| Armadura | Valor adotado |
|---|---|
| Principal positiva | $$\max(A_{s,calc},\; A_{s,base})$$ |
| Principal negativa (só se $$M^- > 0$$) | $$\max(A_{s,calc},\; A_{s,base})$$ |
| Distribuição (transversal) | $$\max(0{,}20\,A_{s,pos},\; 0{,}90,\; 0{,}50\,A_{s,base})$$ |

Diferente do modelo bidirecional, na direção principal usa-se o **mínimo integral** $$A_{s,base}$$ (e não $$0{,}67\,A_{s,min}$$). O limite da armadura de distribuição segue a Tabela 19.1 da NBR 6118:2026 (armadura secundária).

O número de barras e o espaçamento seguem a seção 6.8.

### 8.5 Estado limite de serviço

Mesma sequência do modelo bidirecional (momento de fissuração, estádio I ou II, inércia equivalente de Branson), com:

$$
I_c = \frac{h^3}{12}, \qquad M_r = \frac{1{,}5\, f_{ctm}\, I_c}{h/2}
$$

Momento característico de serviço, com $$p_k = g + q$$:

| Apoio | $$M_a$$ |
|---|---|
| 1 · A-A | $$p_k L^2/8$$ |
| 2 · E-A | $$\max\!\left(p_k L^2/8,\; 9\,p_k L^2/128\right)$$ |
| 3 · E-E | $$p_k L^2/12$$ |

A armadura de serviço é a principal positiva fornecida, e a altura útil é $$d_u$$. A flecha usa o coeficiente $$k_{flecha}$$ da tabela da seção 8.2:

$$
f_{el} = k_{flecha}\,\frac{p_{qp}\, L^4}{E_{cs}\, I_c}, \qquad
f_{imed} = f_{el}\cdot\frac{I_c}{I_{eq}}
$$

$$
f_q = k_{flecha}\,\frac{q\, L^4}{E_{cs}\, I_{eq}}
$$

A fluência segue a mesma hipótese ($$\rho' = 0$$):

$$
\alpha_f = \max\big(0,\; \xi(t) - \xi(t_0)\big), \qquad
f_{dif} = \alpha_f\, f_{imed}, \qquad
f_{final} = f_{imed} + f_{dif}
$$

| Verificação | Condição |
|---|---|
| Flecha final | $$f_{final} \le L/250$$ |
| Parcela da carga variável | $$f_q \le L/350$$ |

A memória de cálculo traz o aviso de que o ELS é estimado por rigidez equivalente e não constitui análise completa de fissuração, de cargas sucessivas ou de condições específicas de uso.

### 8.6 Cisalhamento simplificado

$$
f_{ctd} = \frac{0{,}7\, f_{ctm}}{1{,}4}, \qquad
\rho_1 = \min\!\left(\frac{A_{s1}}{d_u},\; 0{,}02\right)
$$

$$
V_{Rd} = 0{,}25\, f_{ctd}\,(1{,}2 + 40\,\rho_1)\, d_u, \qquad
V_{Sd} = \max(R_A,\, R_B) - p_d\, d_u
$$

com $$A_{s1}$$ em m²/m (armadura principal positiva fornecida) e $$k = 1{,}0$$. Condição: $$V_{Sd} \le V_{Rd}$$.

---

## 9. Pós-processamento (comum aos dois modelos)

### 9.1 `anexar_verificacoes_complementares(d, r)`

Padroniza os campos de flecha entre os modelos. No bidirecional, define:

$$
f_{imediata} = f_{qp}, \qquad f_{diferida} = f_{total} - f_{qp}
$$

No unidirecional esses campos já vêm calculados.

### 9.2 `avaliar_detalhamento(d, r)`

Aplica `selecionar_barras()` às armaduras já dimensionadas e grava `r["detalhamento"]`, com `r["detalhamento_ok"]` e a lista `r["detalhamento_alertas"]`.

| Modelo | Armaduras avaliadas |
|---|---|
| Bidirecional | `x_positiva`, `y_positiva`, `x_negativa`, `y_negativa` |
| Unidirecional | `principal_positiva`, `principal_negativa`, `distribuicao` |

### 9.3 `auditar_limites_normativos(d, r)`

Triagem explícita de critérios verificáveis (NBR 6118:2026, itens 7.4.7, 13.2.4, 19.3.3, 20.1 e 20.2). Grava `r["auditoria_normativa"]` com `checks`, `pendencias` e `status`.

| Critério (`checks`) | Condição |
|---|---|
| `cobrimento_CAA_tabela_7_2` | $$c \ge c_{nom}$$ da CAA |
| `cobrimento_maior_igual_bitola` | $$c \ge \phi$$ |
| `agregado_dmax_menor_1_2_cobrimento` | $$d_{max} \le 1{,}2\,c$$ |
| `bitola_maxima_h_8` | $$\phi \le h/8$$ |
| `espessura_minima_tipo_informado` | $$h \ge h_{min}$$ |
| `espessura_util_para_uma_camada` | $$h > 2c + \phi$$ |
| `espacamento_maximo_*` | $$s \le \min(2h, 20 \text{ cm})$$; distribuição: $$s \le 33$$ cm |
| `espacamento_livre_*` | $$e_{livre} \ge \max(20, \phi, 1{,}2\,d_{max})$$ mm |
| `area_fornecida_*` | área fornecida $$\ge$$ área adotada |
| `armadura_secundaria_minima` (só unidirecional) | $$A_{s,dist} \ge \max(0{,}2\,A_{s,pos},\, 0{,}9,\, 0{,}5\,A_{s,base})$$ |

O status final é `NAO ATENDE` se algum critério falhar, ou `TRIAGEM ATENDE; VALIDACAO DE PROJETO PENDENTE` caso contrário. A lista `pendencias` registra o que **não** é verificado: armadura de borda sem continuidade, bordas livres e aberturas, ancoragem e emendas, momentos volventes, lajes lisas, balanços, cargas concentradas e punção, flecha refinada e as hipóteses acadêmicas fixas.

---

## 10. Memória de cálculo

### 10.1 Bidirecional: `imprimir(d, r)`

Imprime dez seções, na ordem:

1. Dados de entrada e escopo
2. Propriedades dos materiais
3. Alturas úteis
4. Cargas e combinações
5. Coeficientes e momentos
6. Reações de apoio
7. Dimensionamento e detalhamento das armaduras
8. Flecha (estádio I/II e rigidez equivalente)
9. Cisalhamento
10. Quadro-resumo

### 10.2 Unidirecional: `imprimir_unidirecional(d, r)`

Imprime oito seções:

1. Identificação, geometria e vinculação
2. Materiais e resistências de cálculo
3. Ações e combinações
4. Análise estrutural (esforços)
5. Dimensionamento e detalhamento das armaduras (principal positiva, negativa e distribuição)
6. Verificação simplificada de cisalhamento
7. Estado limite de serviço (flechas)
8. Quadro-resumo

### 10.3 Seções comuns

Depois da memória principal, a interface acrescenta:

- `imprimir_detalhamento(r)`: verificação geométrica do espaçamento das barras (quantidade por metro, espaçamento, área fornecida, espaçamento livre e livre mínimo, status e alertas);
- `imprimir_parecer_final(d, r)`: parecer de fácil leitura (ver abaixo);
- `imprimir_auditoria_normativa(r)`: lista `[OK]` ou `[FALHA]` para cada critério e o total de critérios atendidos.

**Parecer final.** Reúne as verificações calculadas:

| Verificação | Bidirecional | Unidirecional |
|---|---|---|
| Flecha final estimada (referência $$l_x/250$$) | sim | sim |
| Flecha da carga variável (referência $$l_x/350$$) | sim | sim |
| Cisalhamento simplificado | direções X e Y | único |
| Acomodação geométrica das barras | sim | sim |
| Limites normativos verificáveis | sim | sim |

A conclusão é um de três resultados: **atende aos critérios calculados**, **não atende** (com a lista dos itens reprovados) ou **parcialmente verificado** (algum item sem resultado conclusivo). O parecer deixa explícito que é uma triagem, e não uma aprovação integral do projeto.

Cada verificação aparece como `ATENDE` ou `NÃO ATENDE` (e `✔` ou `✘` nas seções da memória). Na interface, a saída é capturada com `redirect_stdout` e exibida em texto monoespaçado.

---

## 11. Validações de entrada

### 11.1 `classificar_laje`

| Verificação | Erro |
|---|---|
| Vãos positivos e finitos | "Informe dois vãos positivos e finitos, em metros." |

### 11.2 `validar_entrada_modelo`

Roda em toda chamada de `executar_modelo`, inclusive quando os dados são fornecidos por programa.

| Verificação | Erro lançado |
|---|---|
| `lx`, `ly`, `h`, `phi`, `fck`, `fyk`, `gc`, `alpha_E` positivos | Parâmetro deve ser positivo |
| `q`, `cob`, cargas permanentes, `t0` e `tinf` não negativos | Parâmetro não pode ser negativo |
| Todos os parâmetros numéricos e finitos | Parâmetro ausente, não numérico ou não finito |
| $$0 \le \psi_2 \le 1$$ | `psi2` deve estar entre 0 e 1 |
| $$t \ge t_0$$ | A idade final não pode anteceder a inicial |
| `caa` em I, II, III ou IV | Classe de agressividade inválida |
| $$h \ge h_{min}$$ | Espessura abaixo do mínimo da categoria |
| $$\phi \le h/8$$ | Bitola superior a h/8 |
| $$c \ge \phi$$ | Cobrimento inferior ao diâmetro da barra |
| $$h > 2c + \phi$$ | Espessura insuficiente para cobrimentos e armadura |

### 11.3 `executar_modelo`

| Situação | Erro lançado |
|---|---|
| Modelo unidirecional sem `apoio_1d` entre 1 e 3 | Escolha um dos 3 apoios unidirecionais |
| Modelo bidirecional com `caso` fora de 1 a 9 | Escolha um dos 9 casos bidirecionais |

### 11.4 Dentro dos cálculos

- $$\lambda$$ fora do intervalo tabelado (bidirecional): `ValueError` de `interpolar`.
- Altura útil $$\le 0$$: erro.
- Discriminante da flexão $$\le 0$$: seção insuficiente.
- $$x/d > 0{,}45$$: dutilidade não atendida.

---

## 12. Interface (`gui.py`)

### 12.1 Etapas

1. **Geometria.** O usuário informa os dois vãos. A interface chama `classificar_laje()`, mostra o título (laje uni ou bidirecional), $$l_x$$, $$l_y$$ e $$\lambda$$, e lista os casos de vinculação correspondentes. A vinculação pode ser escolhida pelo menu ou clicando no desenho do caso. Mudar os vãos descarta a vinculação anterior e bloqueia as próximas etapas.
2. **Parâmetros.** Classe de agressividade, bitola $$\phi$$, carga variável $$q_k$$ e espessura adotada $$h$$ (em cm). Uma caixa mostra a estimativa de Bastos.
3. **Resultados.** Indicadores, parecer final, tabelas (cargas e momentos, reações, armaduras, flechas), memória completa e exportação em PDF.

### 12.2 Hipóteses fixas (`montar_dados_padrao`)

A interface reproduz o perfil acadêmico da versão de terminal:

| Item | Valor |
|---|---|
| Tipo de laje | piso, não em balanço ($$h_{min} = 8$$ cm) |
| $$f_{ck}$$ | mínimo da CAA escolhida |
| Cobrimento nominal | o da CAA escolhida |
| Aço | CA-50 ($$f_{yk} = 500$$ MPa) |
| Agregado | granito/gnaisse ($$\alpha_E = 1{,}00$$) |
| Peso específico do concreto | 25 kN/m³ |
| $$g_{contrapiso}$$, $$g_{revest.inf}$$, $$g_{piso}$$, $$g_{paredes}$$ | 0 |
| $$g_{outros}$$ (carga permanente adicional) | 1,28 kN/m² |
| $$\psi_2$$ | 0,30 |
| $$t_0$$ e $$t$$ | 14 dias ($$14/30$$ mês) e 70 meses |

Apenas $$q_k$$ é variável. A espessura é informada em **centímetros** e convertida para metros ($$h = h_{cm}/100$$) ao montar o dicionário.

### 12.3 Tabelas de resultados

| Aba | Conteúdo |
|---|---|
| Cargas e momentos | $$g$$, $$q$$, $$p_{ELU}$$, $$p_{qp}$$; coeficientes $$\mu$$ e momentos (bidirecional) ou momentos de cálculo (unidirecional) |
| Reações | reações em borda apoiada e engastada (bi) ou $$R_A$$ e $$R_B$$ (uni) |
| Armaduras | $$A_s$$ calculada e adotada, barras por metro, espaçamento, área fornecida, espaçamento livre e verificação geométrica |
| Flechas | $$M_r$$, $$M_a$$, estádio, flechas imediata, diferida e final, limites e situação |

### 12.4 Teste de paridade

`test_paridade.py` compara a interface com o fluxo original de terminal em **14 casos**: os casos bidirecionais 1 a 9, os três apoios unidirecionais e duas combinações extras de CAA, bitola, carga e espessura. Para cada caso, compara o dicionário de entrada e a **memória de cálculo completa**. O resultado esperado é `Todos os casos idênticos.`

---

## 13. Dicionários de entrada e saída

### 13.1 Entrada `d` (principais chaves)

| Chave | Descrição |
|---|---|
| `lx`, `ly` | vãos (m), ordenados |
| `caso`, `unidirecional`, `apoio_1d` | vinculação; ver seção 3.4 |
| `tipo` | `"piso"` ou `"cobertura"` |
| `caa`, `cob`, `cob_nbr` | classe de agressividade; cobrimento adotado e nominal (mm) |
| `fck`, `fyk`, `phi` | resistências (MPa) e bitola (mm) |
| `agregado`, `alpha_E` | nome e fator do agregado |
| `gc`, `g_contrapiso`, `g_revest_inf`, `g_piso`, `g_paredes`, `g_outros` | peso específico do concreto e cargas permanentes |
| `q`, `psi2` | carga variável e coeficiente quase permanente |
| `h`, `h_min`, `h_est` | espessura adotada, mínima e estimada (m) |
| `t0`, `tinf` | idades para fluência (meses) |

### 13.2 Saída `r`: bidirecional

| Grupo | Chaves |
|---|---|
| Materiais | `fcd`, `fyd`, `fctm`, `fctk_inf`, `Eci_MPa`, `Ecs_MPa`, `alpha_i` |
| Geometria | `lam`, `d_xp`, `d_yp`, `d_xn`, `d_yn` |
| Cargas | `g1`, `g2`, `g`, `p_elu`, `p_rare`, `p_qp`, `p_q` |
| Coeficientes | `mu_xp`, `mu_yp`, `mu_xn`, `mu_yn`, `alpha` |
| Momentos | `Mx_pos`, `My_pos`, `Mx_neg`, `My_neg`, `Mx_rare`, `My_rare` |
| Reações | `Rx`, `Ry`, `Rx_ap`, `Rx_eng`, `Ry_ap`, `Ry_eng` |
| Armaduras | `As_*_calc`, `As_*` (adotada), `Asf_*` (fornecida), `n_*`, `s_*`, `As_min`, `As_min_2dir`, `s_max` |
| Dutilidade | `xid_xp`, `xid_yp`, `xid_xn`, `xid_yn`, `xi_lim` |
| Flecha | `Mr`, `Ma`, `estadio`, `dir_serv`, `Ic`, `III`, `Ieq`, `f_qp`, `f_q`, `alpha_f`, `f_total`, `f_imediata`, `f_diferida`, `lim_250`, `lim_350` |
| Cisalhamento | `Vsd_x`, `VRd1_x`, `Vsd_y`, `VRd1_y`, `cis_ok_x`, `cis_ok_y` |

### 13.3 Saída `r`: unidirecional

| Grupo | Chaves |
|---|---|
| Geral | `modelo`, `lam`, `du`, `g`, `q`, `pd`, `pqp` |
| Esforços | `Mpos`, `Mneg`, `Ra`, `Rb` |
| Armaduras | `Aspos_calc`, `Asneg_calc`, `Aspos`, `Asneg`, `Asdist`, `barras`, `xip`, `xin` |
| Flecha | `Mr`, `Ma`, `estadio`, `Ic`, `III`, `Ieq`, `f_el`, `f_imediata`, `f_diferida`, `f_total`, `f_q`, `alpha_f`, `lim_250`, `lim_350`, `els_total_ok`, `els_q_ok` |
| Cisalhamento | `Vsd`, `VRd`, `cis_ok` |

### 13.4 Chaves adicionadas nos dois modelos

`detalhamento`, `detalhamento_ok`, `detalhamento_alertas` e `auditoria_normativa`.

---

## 14. Limitações e pontos de atenção

1. **Conferência das tabelas bidirecionais.** Os comentários das tabelas `MOMENTOS` e o dicionário `DESCRICAO` não usam exatamente a mesma redação para alguns casos (por exemplo, 2, 3, 5 e 6). A interface desenha os casos conforme `DESCRICAO`. Confira a numeração e a orientação das bordas engastadas com os quadros do livro antes de usar o programa em um caso real.
2. **Coeficientes transcritos.** As tabelas foram transcritas e conferidas por amostras. Vale revisá-las contra o livro, principalmente os casos com engaste. Um exemplo de ponto a conferir é o valor $$\mu_{y+}$$ do caso 1 em $$\lambda = 1{,}60$$, que destoa da tendência da coluna.
3. **Combinação última simplificada:** $$1{,}4\,(g+q)$$ vale para uma única ação variável. Para mais ações, é preciso ponderar cada uma.
4. **Concreto limitado a C40.** Para C45 a C90 seria necessário implementar os parâmetros do bloco de tensões da norma para classes superiores. O módulo não bloqueia $$f_{ck}$$ fora da faixa; a interface sempre usa o mínimo da CAA (C20 a C40).
5. **Cisalhamento conservador:** adota-se $$k = 1{,}0$$, e a largura do apoio não é entrada. Por isso $$V_{Sd} = R - p\,d$$ é uma aproximação.
6. **Flecha:** a rigidez equivalente é calculada com a direção de maior momento rara (bidirecional) e aplicada às duas parcelas. Não há armadura comprimida na fluência ($$\rho' = 0$$). No modelo unidirecional, o ELS é preliminar e usa o coeficiente de flecha de viga prismática.
7. **Modelo unidirecional:** representa uma faixa de 1 m, sem torção de canto, balanços ou cargas concentradas. A armadura de distribuição segue um critério preliminar conservador.
8. **Compatibilização de momentos negativos** entre lajes adjacentes não é feita. Cada laje é tratada isoladamente.
9. **Fora do escopo:** balanços, lajes nervuradas, lajes lisas e cogumelo, aberturas, cargas concentradas, punção e geometrias não retangulares.
10. **Ancoragem e emendas** não são detalhadas, e o espaçamento livre é apenas uma triagem geométrica.
11. **Referências normativas:** os itens e tabelas da NBR 6118:2026 citados nos comentários do código devem ser conferidos contra o texto vigente da norma.
12. **Perfil acadêmico.** A carga permanente adicional de 1,28 kN/m², $$\psi_2 = 0{,}30$$, a idade de carregamento e o agregado são hipóteses de ensaio, não verificações de uso real.
13. O programa é uma **ferramenta de apoio acadêmico**. Os resultados devem ser revisados por engenheiro responsável antes de qualquer uso em projeto.

---

## 15. Como validar o código

1. Rode `python test_paridade.py` e confirme `Todos os casos idênticos.` (interface e terminal dão o mesmo resultado).
2. Resolva à mão (ou em planilha) um exemplo do livro e compare $$M$$, $$A_s$$ e a flecha com a saída.
3. **Modelo unidirecional:** confira os esforços pelas fórmulas fechadas da seção 8.2. Por exemplo, para o apoio A-A com $$p_d = 10$$ kN/m² e $$L = 3$$ m, $$M^+ = 10 \cdot 3^2 / 8 = 11{,}25$$ kN·m/m e $$R = 15$$ kN/m.
4. Teste os limites de classificação: $$\lambda = 2{,}00$$ (bidirecional) e $$\lambda = 2{,}01$$ (unidirecional).
5. Teste entradas inválidas: cobrimento abaixo do nominal, $$\phi > h/8$$, $$h$$ abaixo do mínimo, apoio unidirecional fora de 1 a 3, caso bidirecional fora de 1 a 9.
6. Verifique a coerência: aumentar $$h$$ deve reduzir $$A_s$$ e a flecha; aumentar $$q$$ deve aumentar $$M$$, $$A_s$$ e a flecha.
7. Escreva testes automatizados (`pytest`) chamando `executar_modelo()` com dicionários fixos e comparando com valores de referência.

---

## 16. Referências

- CARVALHO, R. C.; FIGUEIREDO FILHO, J. R. *Cálculo e Detalhamento de Estruturas Usuais de Concreto Armado*. 4ª ed.
- BASTOS, P. S. dos S. *Lajes de concreto*. Notas de aula (pré-dimensionamento).
- ABNT NBR 6118:2026 — Projeto de estruturas de concreto.
- ABNT NBR 6120:2019 — Ações para o cálculo de estruturas de edificações.