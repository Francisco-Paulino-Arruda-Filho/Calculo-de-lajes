---
layout: default
title: Calculadora de Lajes Maciças
---

<script async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>

# Calculadora de Lajes Maciças de Concreto Armado

Documentação do código de cálculo (`calculo.py`)

Referências citadas no código: Carvalho & Figueiredo, *Cálculo e Detalhamento de Estruturas Usuais de Concreto Armado* (4ª ed.); Bastos (pré-dimensionamento); ABNT NBR 6118:2026; ABNT NBR 6120:2019.

---

## 1. Visão geral

O módulo dimensiona **lajes maciças retangulares armadas em duas direções**, por coeficientes tabelados, e produz uma memória de cálculo completa. Ele cobre:

1. Pré-dimensionamento da espessura.
2. Levantamento de cargas (ELU e ELS).
3. Momentos fletores e reações de apoio.
4. Dimensionamento da armadura de flexão.
5. Armadura mínima e espaçamento máximo.
6. Verificação de flecha, com fissuração (Branson) e fluência.
7. Verificação ao cisalhamento.

### 1.1 Escopo validado

| Item | Limite nesta versão |
|---|---|
| Geometria | Laje retangular, $$1 \le \lambda = l_y/l_x \le 2$$ |
| Casos de vinculação | 1 a 6 (7 a 9 estão nas tabelas, mas bloqueados) |
| Concreto | C20 a C40 |
| Tipo de laje | Piso ou cobertura, não em balanço |
| Ação variável | Uma única ação variável |

Fora desse escopo o código **lança `ValueError`** em vez de extrapolar silenciosamente.

---

## 2. Arquitetura e fluxo de dados

```
Interface (gui.py)
   │  coletar()  → dicionário de valores brutos
   ▼
montar_dados(v)  → valida e devolve o dicionário d
   ▼
calcular(d)      → devolve o dicionário r (todos os resultados)
   ▼
imprimir(d, r)   → escreve a memória de cálculo (capturada com redirect_stdout)
```

- `calcular()` **não imprime nada**: recebe `d` e devolve `r`. Isso permite testar o núcleo sem interface.
- `imprimir()` só formata `d` e `r`. Não calcula nada novo.
- Erros de entrada ou de modelo são `ValueError` ou `KeyError`, tratados na interface com `QMessageBox`.

---

## 3. Convenções

### 3.1 Eixos e vãos

- `lx` é o **menor vão** e `ly` o maior. Se o usuário os inverter, o código troca.
- O parâmetro de forma é:

$$
\lambda = \frac{l_y}{l_x}
$$

- Direção **x**: armadura paralela a `lx`, na camada inferior.
- Direção **y**: armadura paralela a `ly`, uma bitola acima (segunda camada).

### 3.2 Unidades

| Grandeza | Unidade |
|---|---|
| Vãos, alturas, cobrimentos (internamente) | m |
| Cobrimento e bitola na entrada | mm |
| Cargas distribuídas | kN/m² |
| Momentos | kNm/m |
| Reações e cortantes | kN/m |
| Resistências e módulos | MPa (convertidos para kN/m² nas contas) |
| Armadura | cm²/m |
| Espaçamento | cm |

### 3.3 Sufixos de variáveis

| Sufixo | Significado |
|---|---|
| `_xp`, `_yp` | momento/armadura **positivo** em x e em y |
| `_xn`, `_yn` | momento/armadura **negativo** (engaste) em x e em y |
| `_elu`, `_rare`, `_qp` | combinação última, rara e quase permanente |

---

## 4. Tabelas de coeficientes

Todas são listas de linhas com $$\lambda$$ de 1,00 a 2,00, em passos de 0,05.

### 4.1 `MOMENTOS` (Quadros 7.3 a 7.5)

Cada linha: `[λ, µx+, µy+, µx−, µy−]`. Zero significa que **não há engaste** naquela direção.

$$
M = \mu \cdot \frac{p \, l_x^2}{100}
$$

### 4.2 `REACOES` (Quadros 7.8 e 7.9)

Cada linha: `[λ, kx, ky]`. Os coeficientes de borda engastada (`kxp`, `kyp`) e alguns valores constantes são completados em `coef_reacoes()`.

$$
R = k \cdot \frac{p \, l_x}{10}
$$

| Caso | Coeficientes devolvidos |
|---|---|
| 1 | `kx`, `ky` |
| 2 | `kx`, `ky`, `kyp` |
| 3 | `kx`, `kxp`, `ky` (fixo 1,83) |
| 4 | `kx`, `kxp`, `ky` (fixo 1,83), `kyp` (fixo 3,17) |
| 5 | `kx`, `kyp` |
| 6 | `kxp`, `ky` |

Chaves com `p` (`kxp`, `kyp`) são de **borda engastada**. As demais, de borda apoiada.

### 4.3 `ALPHA_FLECHA` (Quadro 7.2)

Cada linha: `[λ, α_caso1, ..., α_caso9]`. A coluna usada é `caso − 1`.

$$
f = \alpha \cdot \frac{p \, l_x^4}{E_{cs} \, h^3 \cdot 100}
$$

### 4.4 Tabelas normativas

**Cobrimento nominal mínimo e fck mínimo por classe de agressividade (CAA):**

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

A tabela completa vai até C90. `rho_min(fck)` interpola linearmente entre os valores.

### 4.5 `AGREGADOS`

Fator $$\alpha_E$$ para o módulo de elasticidade:

| Código | Agregado | $$\alpha_E$$ |
|---|---|---|
| 1 | basalto/diabásio | 1,20 |
| 2 | granito/gnaisse | 1,00 |
| 3 | calcário | 0,90 |
| 4 | arenito | 0,70 |

---

## 5. Funções auxiliares

### 5.1 `interpolar(tabela, lam, col=None)`

Interpolação linear entre duas linhas consecutivas da tabela:

$$
v = v_0 + t \,(v_1 - v_0), \qquad t = \frac{\lambda - \lambda_0}{\lambda_1 - \lambda_0}
$$

- Se $$\lambda$$ estiver fora do intervalo tabelado, lança `ValueError` (**sem extrapolação**).
- Com `col=None`, devolve a lista de coeficientes da linha. Com `col=i`, devolve só o i-ésimo.

### 5.2 `coef_reacoes(caso, lam)` e `reacoes_kNm(caso, lam, p, lx)`

A primeira devolve o dicionário de coeficientes `k` do caso, com os valores constantes e a tabela extra `_KYP_CASO2`. A segunda multiplica cada `k` por $$p\,l_x/10$$.

### 5.3 `xi(t_meses)`: coeficiente $$\xi(t)$$ de fluência

$$
\xi(t) =
\begin{cases}
0 & t \le 0 \\
0{,}68 \cdot 0{,}996^{\,t} \cdot t^{0{,}32} & 0 < t \le 70 \text{ meses} \\
2{,}0 & t > 70 \text{ meses}
\end{cases}
$$

### 5.4 `fctm_nbr(fck)`: resistência média à tração

$$
f_{ctm} =
\begin{cases}
0{,}3 \, f_{ck}^{2/3} & f_{ck} \le 50 \text{ MPa} \\
2{,}12 \ln\!\big(1 + 0{,}1\,(f_{ck} + 8)\big) & f_{ck} > 50 \text{ MPa}
\end{cases}
$$

### 5.5 `modulos_concreto(fck, alpha_E)`: módulos de elasticidade

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

### 5.6 `altura_minima(tipo)`

| Tipo | h mínimo |
|---|---|
| Piso não em balanço | 8 cm |
| Cobertura não em balanço | 7 cm |

### 5.7 `estimar_h_bastos(lx, ly, caso, cob, phi)`

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

A espessura sugerida é `max(h_est, h_min)`.

---

## 6. `calcular(d)`: passo a passo

### 6.1 Materiais

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

### 6.2 Alturas úteis

$$
d_{x} = h - c - \frac{\phi}{2}
$$

$$
d_{y} = h - c - \frac{3\phi}{2}
$$

A armadura em x fica na camada mais externa. A de y fica uma bitola acima, por isso perde $$\phi$$ de altura útil. As mesmas expressões valem para a armadura negativa. Se alguma altura útil for $$\le 0$$, o código lança erro.

### 6.3 Cargas

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

### 6.4 Momentos fletores

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

### 6.5 Reações de apoio

$$
R = k\,\frac{p_{ELU}\, l_x}{10}
$$

O código guarda as reações em borda apoiada (`Rx_ap`, `Ry_ap`) e em borda engastada (`Rx_eng`, `Ry_eng`). Os valores **críticos** são:

$$
R_x = \max(R_{x,ap},\, R_{x,eng}), \qquad R_y = \max(R_{y,ap},\, R_{y,eng})
$$

### 6.6 Dimensionamento à flexão

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
- **Dutilidade:** exige-se $$x/d \le 0{,}45$$ (escopo C20 a C40). Se violado, lança erro.

### 6.7 Armadura mínima e detalhamento

$$
A_{s,min} = \frac{\rho_{min}}{100}\; b_w\; h \qquad (b_w = 100 \text{ cm})
$$

Observe que a taxa é referida a $$b_w\,h$$, e não a $$b_w\,d$$.

| Armadura | Mínimo aplicado |
|---|---|
| Positiva (duas direções) | $$0{,}67\, A_{s,min}$$ |
| Negativa | $$A_{s,min}$$ |

A armadura adotada é o maior valor entre a calculada e a mínima.

**Número de barras e espaçamento:**

$$
A_b = \frac{\pi \phi^2}{4} \qquad \text{(cm² por barra)}
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

### 6.8 Flecha

**a) Momento de fissuração** (seção retangular, $$\alpha = 1{,}5$$):

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
\alpha_f = \xi(t) - \xi(t_0)
$$

$$
f_{total} = f_{qp}\,(1 + \alpha_f)
$$

O tempo $$t_0$$ é a idade da aplicação da carga de longa duração (padrão 0,47 mês, ou seja, 14 dias). O tempo $$t$$ é o tempo final (padrão 70 meses).

**f) Limites verificados:**

| Verificação | Condição |
|---|---|
| Flecha total diferida | $$f_{total} \le l_x/250$$ |
| Parcela da carga variável | $$f_q \le l_x/350$$ |

### 6.8.1 Observação sobre o limite l/500

O código **não** aplica uma verificação genérica de $$l/500$$, porque esse limite depende do efeito específico (por exemplo, deslocamentos que prejudicam elementos não estruturais).

### 6.9 Cisalhamento

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

## 7. Validações de entrada (`montar_dados`)

| Verificação | Erro lançado |
|---|---|
| `lx`, `ly` positivos | Vãos devem ser positivos |
| $$\lambda \le 2{,}0$$ | Laje armada em uma direção, fora do escopo |
| Caso em 1 a 6 | Casos 7 a 9 bloqueados |
| Cobrimento $$\ge$$ nominal da CAA | Cobrimento menor que o mínimo |
| $$20 \le f_{ck} \le 40$$ | Fora do escopo validado |
| $$f_{ck} \ge$$ mínimo da CAA | Classe de concreto insuficiente |
| $$\phi > 0$$ e cobrimento $$\ge \phi$$ | Diâmetro inválido |
| $$\phi \le h/8$$ | Bitola excede h/8 |
| $$h \ge h_{min}$$ | Espessura abaixo do mínimo |
| $$0 \le \psi_2 \le 1$$ | Coeficiente inválido |
| $$t \ge t_0$$ | Tempo final menor que o inicial |

Valores `0` em `h` e `cob` significam "automático": usa-se a estimativa de Bastos (limitada ao mínimo) e o cobrimento nominal da CAA, respectivamente.

---

## 8. Memória de cálculo (`imprimir`)

Imprime dez seções, na ordem:

1. Dados de entrada e escopo
2. Propriedades dos materiais
3. Alturas úteis
4. Cargas e combinações
5. Coeficientes e momentos
6. Reações nas vigas
7. Armaduras (mínimos, dutilidade, barras e espaçamentos)
8. Flecha (estádio, Ieq, fluência e limites)
9. Cisalhamento
10. Resumo (armaduras finais e flecha)

Cada verificação aparece com `✔` (atende) ou `✘` (não atende). Na interface, a saída é capturada com `redirect_stdout` e exibida em texto monoespaçado.

---

## 9. Dicionários de entrada e saída

### 9.1 Entrada `d` (principais chaves)

| Chave | Descrição |
|---|---|
| `lx`, `ly` | vãos (m) |
| `caso`, `tipo` | vinculação (1 a 6); `"piso"` ou `"cobertura"` |
| `caa`, `cob` | classe de agressividade; cobrimento adotado (mm) |
| `fck`, `fyk`, `phi` | resistências (MPa) e bitola (mm) |
| `agregado`, `alpha_E` | nome e fator do agregado |
| `gc`, `g_contrapiso`, `g_revest_inf`, `g_piso`, `g_paredes`, `g_outros` | cargas permanentes |
| `q`, `psi2` | carga variável e coeficiente quase permanente |
| `h`, `h_min`, `h_est` | espessura adotada, mínima e estimada (m) |
| `t0`, `tinf` | idades para fluência (meses) |

### 9.2 Saída `r` (agrupada)

| Grupo | Chaves |
|---|---|
| Materiais | `fcd`, `fyd`, `fctm`, `fctk_inf`, `Eci_MPa`, `Ecs_MPa`, `alpha_i` |
| Geometria | `lam`, `d_xp`, `d_yp`, `d_xn`, `d_yn` |
| Cargas | `g1`, `g2`, `g`, `p_elu`, `p_rare`, `p_qp`, `p_q` |
| Coeficientes | `mu_xp`, `mu_yp`, `mu_xn`, `mu_yn`, `alpha` |
| Momentos | `Mx_pos`, `My_pos`, `Mx_neg`, `My_neg`, `Mx_rare`, `My_rare` |
| Reações | `Rx`, `Ry`, `Rx_ap`, `Rx_eng`, `Ry_ap`, `Ry_eng` |
| Armaduras | `As_*_calc`, `As_*` (requerida), `Asf_*` (fornecida), `n_*`, `s_*`, `As_min`, `s_max` |
| Dutilidade | `xid_xp`, `xid_yp`, `xid_xn`, `xid_yn`, `xi_lim` |
| Flecha | `Mr`, `Ma`, `estadio`, `Ic`, `III`, `Ieq`, `f_qp`, `f_q`, `alpha_f`, `f_total`, `lim_250`, `lim_350` |
| Cisalhamento | `Vsd_x`, `VRd1_x`, `Vsd_y`, `VRd1_y`, `cis_ok_x`, `cis_ok_y` |

---

## 10. Limitações e pontos de atenção

1. **Descrição dos casos.** Os comentários das tabelas `MOMENTOS` e o dicionário `DESCRICAO` não usam exatamente a mesma redação para alguns casos (por exemplo, 2, 3, 5 e 6). Confira a numeração e a orientação das bordas engastadas com os quadros do livro antes de usar o programa em um caso real.
2. **Combinação última simplificada:** $$1{,}4\,(g+q)$$ vale para uma única ação variável. Para mais ações, é preciso ponderar cada uma.
3. **Concreto limitado a C40.** Para C45 a C90 seria necessário implementar os parâmetros do bloco de tensões da norma para classes superiores.
4. **Cisalhamento conservador:** adota-se $$k = 1{,}0$$, e a largura do apoio não é entrada. Por isso $$V_{Sd} = R - p\,d$$ é uma aproximação.
5. **Flecha:** a rigidez equivalente é calculada com a direção de maior momento rara e aplicada às duas parcelas. Não há armadura comprimida na fluência ($$\rho' = 0$$).
6. **Compatibilização de momentos negativos** entre lajes adjacentes não é feita. Cada laje é tratada isoladamente.
7. **Lajes com $$\lambda > 2$$** (armadas em uma direção), balanços, lajes nervuradas e lajes lisas não são cobertas.
8. **Referências normativas:** os itens e tabelas da NBR 6118:2026 citados nos comentários do código devem ser conferidos contra o texto vigente da norma.
9. O programa é uma **ferramenta de apoio acadêmico**. Os resultados devem ser revisados por engenheiro responsável antes de qualquer uso em projeto.

---

## 11. Como validar o código

1. Resolva à mão (ou em planilha) um exemplo do livro e compare $$M$$, $$A_s$$ e a flecha com a saída.
2. Teste os limites: $$\lambda = 1{,}00$$, $$\lambda = 2{,}00$$, $$\lambda = 2{,}01$$ (deve dar erro).
3. Teste entradas inválidas: cobrimento abaixo do nominal, $$\phi > h/8$$, caso 7 a 9, $$f_{ck} = 45$$.
4. Verifique a coerência: aumentar $$h$$ deve reduzir $$A_s$$ e a flecha; aumentar $$q$$ deve aumentar $$M$$, $$A_s$$ e a flecha.
5. Escreva testes automatizados (`pytest`) chamando `montar_dados()` e `calcular()` com dicionários fixos e comparando com valores de referência.

---

## 12. Referências

- CARVALHO, R. C.; FIGUEIREDO FILHO, J. R. *Cálculo e Detalhamento de Estruturas Usuais de Concreto Armado*. 4ª ed.
- BASTOS, P. S. dos S. *Lajes de concreto*. Notas de aula (pré-dimensionamento).
- ABNT NBR 6118:2026 — Projeto de estruturas de concreto.
- ABNT NBR 6120:2019 — Ações para o cálculo de estruturas de edificações.# Cálculo de Lajes Maciças de Concreto Armado

Documentação do código de cálculo (`calculo.py`)

Referências citadas no código: Carvalho & Figueiredo, *Cálculo e Detalhamento de Estruturas Usuais de Concreto Armado* (4ª ed.); Bastos (pré-dimensionamento); ABNT NBR 6118:2026; ABNT NBR 6120:2019.

---

## 1. Visão geral

O módulo dimensiona **lajes maciças retangulares armadas em duas direções**, por coeficientes tabelados, e produz uma memória de cálculo completa. Ele cobre:

1. Pré-dimensionamento da espessura.
2. Levantamento de cargas (ELU e ELS).
3. Momentos fletores e reações de apoio.
4. Dimensionamento da armadura de flexão.
5. Armadura mínima e espaçamento máximo.
6. Verificação de flecha, com fissuração (Branson) e fluência.
7. Verificação ao cisalhamento.

### 1.1 Escopo validado

| Item | Limite nesta versão |
|---|---|
| Geometria | Laje retangular, $$1 \le \lambda = l_y/l_x \le 2$$ |
| Casos de vinculação | 1 a 6 (7 a 9 estão nas tabelas, mas bloqueados) |
| Concreto | C20 a C40 |
| Tipo de laje | Piso ou cobertura, não em balanço |
| Ação variável | Uma única ação variável |

Fora desse escopo o código **lança `ValueError`** em vez de extrapolar silenciosamente.

---

## 2. Arquitetura e fluxo de dados

```
Interface (gui.py)
   │  coletar()  → dicionário de valores brutos
   ▼
montar_dados(v)  → valida e devolve o dicionário d
   ▼
calcular(d)      → devolve o dicionário r (todos os resultados)
   ▼
imprimir(d, r)   → escreve a memória de cálculo (capturada com redirect_stdout)
```

- `calcular()` **não imprime nada**: recebe `d` e devolve `r`. Isso permite testar o núcleo sem interface.
- `imprimir()` só formata `d` e `r`. Não calcula nada novo.
- Erros de entrada ou de modelo são `ValueError` ou `KeyError`, tratados na interface com `QMessageBox`.

---

## 3. Convenções

### 3.1 Eixos e vãos

- `lx` é o **menor vão** e `ly` o maior. Se o usuário os inverter, o código troca.
- O parâmetro de forma é:

$$
\lambda = \frac{l_y}{l_x}
$$

- Direção **x**: armadura paralela a `lx`, na camada inferior.
- Direção **y**: armadura paralela a `ly`, uma bitola acima (segunda camada).

### 3.2 Unidades

| Grandeza | Unidade |
|---|---|
| Vãos, alturas, cobrimentos (internamente) | m |
| Cobrimento e bitola na entrada | mm |
| Cargas distribuídas | kN/m² |
| Momentos | kNm/m |
| Reações e cortantes | kN/m |
| Resistências e módulos | MPa (convertidos para kN/m² nas contas) |
| Armadura | cm²/m |
| Espaçamento | cm |

### 3.3 Sufixos de variáveis

| Sufixo | Significado |
|---|---|
| `_xp`, `_yp` | momento/armadura **positivo** em x e em y |
| `_xn`, `_yn` | momento/armadura **negativo** (engaste) em x e em y |
| `_elu`, `_rare`, `_qp` | combinação última, rara e quase permanente |

---

## 4. Tabelas de coeficientes

Todas são listas de linhas com $$\lambda$$ de 1,00 a 2,00, em passos de 0,05.

### 4.1 `MOMENTOS` (Quadros 7.3 a 7.5)

Cada linha: `[λ, µx+, µy+, µx−, µy−]`. Zero significa que **não há engaste** naquela direção.

$$
M = \mu \cdot \frac{p \, l_x^2}{100}
$$

### 4.2 `REACOES` (Quadros 7.8 e 7.9)

Cada linha: `[λ, kx, ky]`. Os coeficientes de borda engastada (`kxp`, `kyp`) e alguns valores constantes são completados em `coef_reacoes()`.

$$
R = k \cdot \frac{p \, l_x}{10}
$$

| Caso | Coeficientes devolvidos |
|---|---|
| 1 | `kx`, `ky` |
| 2 | `kx`, `ky`, `kyp` |
| 3 | `kx`, `kxp`, `ky` (fixo 1,83) |
| 4 | `kx`, `kxp`, `ky` (fixo 1,83), `kyp` (fixo 3,17) |
| 5 | `kx`, `kyp` |
| 6 | `kxp`, `ky` |

Chaves com `p` (`kxp`, `kyp`) são de **borda engastada**. As demais, de borda apoiada.

### 4.3 `ALPHA_FLECHA` (Quadro 7.2)

Cada linha: `[λ, α_caso1, ..., α_caso9]`. A coluna usada é `caso − 1`.

$$
f = \alpha \cdot \frac{p \, l_x^4}{E_{cs} \, h^3 \cdot 100}
$$

### 4.4 Tabelas normativas

**Cobrimento nominal mínimo e fck mínimo por classe de agressividade (CAA):**

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

A tabela completa vai até C90. `rho_min(fck)` interpola linearmente entre os valores.

### 4.5 `AGREGADOS`

Fator $$\alpha_E$$ para o módulo de elasticidade:

| Código | Agregado | $$\alpha_E$$ |
|---|---|---|
| 1 | basalto/diabásio | 1,20 |
| 2 | granito/gnaisse | 1,00 |
| 3 | calcário | 0,90 |
| 4 | arenito | 0,70 |

---

## 5. Funções auxiliares

### 5.1 `interpolar(tabela, lam, col=None)`

Interpolação linear entre duas linhas consecutivas da tabela:

$$
v = v_0 + t \,(v_1 - v_0), \qquad t = \frac{\lambda - \lambda_0}{\lambda_1 - \lambda_0}
$$

- Se $$\lambda$$ estiver fora do intervalo tabelado, lança `ValueError` (**sem extrapolação**).
- Com `col=None`, devolve a lista de coeficientes da linha. Com `col=i`, devolve só o i-ésimo.

### 5.2 `coef_reacoes(caso, lam)` e `reacoes_kNm(caso, lam, p, lx)`

A primeira devolve o dicionário de coeficientes `k` do caso, com os valores constantes e a tabela extra `_KYP_CASO2`. A segunda multiplica cada `k` por $$p\,l_x/10$$.

### 5.3 `xi(t_meses)`: coeficiente $$\xi(t)$$ de fluência

$$
\xi(t) =
\begin{cases}
0 & t \le 0 \\
0{,}68 \cdot 0{,}996^{\,t} \cdot t^{0{,}32} & 0 < t \le 70 \text{ meses} \\
2{,}0 & t > 70 \text{ meses}
\end{cases}
$$

### 5.4 `fctm_nbr(fck)`: resistência média à tração

$$
f_{ctm} =
\begin{cases}
0{,}3 \, f_{ck}^{2/3} & f_{ck} \le 50 \text{ MPa} \\
2{,}12 \ln\!\big(1 + 0{,}1\,(f_{ck} + 8)\big) & f_{ck} > 50 \text{ MPa}
\end{cases}
$$

### 5.5 `modulos_concreto(fck, alpha_E)`: módulos de elasticidade

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

### 5.6 `altura_minima(tipo)`

| Tipo | h mínimo |
|---|---|
| Piso não em balanço | 8 cm |
| Cobertura não em balanço | 7 cm |

### 5.7 `estimar_h_bastos(lx, ly, caso, cob, phi)`

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

A espessura sugerida é `max(h_est, h_min)`.

---

## 6. `calcular(d)`: passo a passo

### 6.1 Materiais

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

### 6.2 Alturas úteis

$$
d_{x} = h - c - \frac{\phi}{2}
$$

$$
d_{y} = h - c - \frac{3\phi}{2}
$$

A armadura em x fica na camada mais externa. A de y fica uma bitola acima, por isso perde $$\phi$$ de altura útil. As mesmas expressões valem para a armadura negativa. Se alguma altura útil for $$\le 0$$, o código lança erro.

### 6.3 Cargas

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

### 6.4 Momentos fletores

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

### 6.5 Reações de apoio

$$
R = k\,\frac{p_{ELU}\, l_x}{10}
$$

O código guarda as reações em borda apoiada (`Rx_ap`, `Ry_ap`) e em borda engastada (`Rx_eng`, `Ry_eng`). Os valores **críticos** são:

$$
R_x = \max(R_{x,ap},\, R_{x,eng}), \qquad R_y = \max(R_{y,ap},\, R_{y,eng})
$$

### 6.6 Dimensionamento à flexão

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
- **Dutilidade:** exige-se $$x/d \le 0{,}45$$ (escopo C20 a C40). Se violado, lança erro.

### 6.7 Armadura mínima e detalhamento

$$
A_{s,min} = \frac{\rho_{min}}{100}\; b_w\; h \qquad (b_w = 100 \text{ cm})
$$

Observe que a taxa é referida a $$b_w\,h$$, e não a $$b_w\,d$$.

| Armadura | Mínimo aplicado |
|---|---|
| Positiva (duas direções) | $$0{,}67\, A_{s,min}$$ |
| Negativa | $$A_{s,min}$$ |

A armadura adotada é o maior valor entre a calculada e a mínima.

**Número de barras e espaçamento:**

$$
A_b = \frac{\pi \phi^2}{4} \qquad \text{(cm² por barra)}
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

### 6.8 Flecha

**a) Momento de fissuração** (seção retangular, $$\alpha = 1{,}5$$):

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
\alpha_f = \xi(t) - \xi(t_0)
$$

$$
f_{total} = f_{qp}\,(1 + \alpha_f)
$$

O tempo $$t_0$$ é a idade da aplicação da carga de longa duração (padrão 0,47 mês, ou seja, 14 dias). O tempo $$t$$ é o tempo final (padrão 70 meses).

**f) Limites verificados:**

| Verificação | Condição |
|---|---|
| Flecha total diferida | $$f_{total} \le l_x/250$$ |
| Parcela da carga variável | $$f_q \le l_x/350$$ |

### 6.8.1 Observação sobre o limite l/500

O código **não** aplica uma verificação genérica de $$l/500$$, porque esse limite depende do efeito específico (por exemplo, deslocamentos que prejudicam elementos não estruturais).

### 6.9 Cisalhamento

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

## 7. Validações de entrada (`montar_dados`)

| Verificação | Erro lançado |
|---|---|
| `lx`, `ly` positivos | Vãos devem ser positivos |
| $$\lambda \le 2{,}0$$ | Laje armada em uma direção, fora do escopo |
| Caso em 1 a 6 | Casos 7 a 9 bloqueados |
| Cobrimento $$\ge$$ nominal da CAA | Cobrimento menor que o mínimo |
| $$20 \le f_{ck} \le 40$$ | Fora do escopo validado |
| $$f_{ck} \ge$$ mínimo da CAA | Classe de concreto insuficiente |
| $$\phi > 0$$ e cobrimento $$\ge \phi$$ | Diâmetro inválido |
| $$\phi \le h/8$$ | Bitola excede h/8 |
| $$h \ge h_{min}$$ | Espessura abaixo do mínimo |
| $$0 \le \psi_2 \le 1$$ | Coeficiente inválido |
| $$t \ge t_0$$ | Tempo final menor que o inicial |

Valores `0` em `h` e `cob` significam "automático": usa-se a estimativa de Bastos (limitada ao mínimo) e o cobrimento nominal da CAA, respectivamente.

---

## 8. Memória de cálculo (`imprimir`)

Imprime dez seções, na ordem:

1. Dados de entrada e escopo
2. Propriedades dos materiais
3. Alturas úteis
4. Cargas e combinações
5. Coeficientes e momentos
6. Reações nas vigas
7. Armaduras (mínimos, dutilidade, barras e espaçamentos)
8. Flecha (estádio, Ieq, fluência e limites)
9. Cisalhamento
10. Resumo (armaduras finais e flecha)

Cada verificação aparece com `✔` (atende) ou `✘` (não atende). Na interface, a saída é capturada com `redirect_stdout` e exibida em texto monoespaçado.

---

## 9. Dicionários de entrada e saída

### 9.1 Entrada `d` (principais chaves)

| Chave | Descrição |
|---|---|
| `lx`, `ly` | vãos (m) |
| `caso`, `tipo` | vinculação (1 a 6); `"piso"` ou `"cobertura"` |
| `caa`, `cob` | classe de agressividade; cobrimento adotado (mm) |
| `fck`, `fyk`, `phi` | resistências (MPa) e bitola (mm) |
| `agregado`, `alpha_E` | nome e fator do agregado |
| `gc`, `g_contrapiso`, `g_revest_inf`, `g_piso`, `g_paredes`, `g_outros` | cargas permanentes |
| `q`, `psi2` | carga variável e coeficiente quase permanente |
| `h`, `h_min`, `h_est` | espessura adotada, mínima e estimada (m) |
| `t0`, `tinf` | idades para fluência (meses) |

### 9.2 Saída `r` (agrupada)

| Grupo | Chaves |
|---|---|
| Materiais | `fcd`, `fyd`, `fctm`, `fctk_inf`, `Eci_MPa`, `Ecs_MPa`, `alpha_i` |
| Geometria | `lam`, `d_xp`, `d_yp`, `d_xn`, `d_yn` |
| Cargas | `g1`, `g2`, `g`, `p_elu`, `p_rare`, `p_qp`, `p_q` |
| Coeficientes | `mu_xp`, `mu_yp`, `mu_xn`, `mu_yn`, `alpha` |
| Momentos | `Mx_pos`, `My_pos`, `Mx_neg`, `My_neg`, `Mx_rare`, `My_rare` |
| Reações | `Rx`, `Ry`, `Rx_ap`, `Rx_eng`, `Ry_ap`, `Ry_eng` |
| Armaduras | `As_*_calc`, `As_*` (requerida), `Asf_*` (fornecida), `n_*`, `s_*`, `As_min`, `s_max` |
| Dutilidade | `xid_xp`, `xid_yp`, `xid_xn`, `xid_yn`, `xi_lim` |
| Flecha | `Mr`, `Ma`, `estadio`, `Ic`, `III`, `Ieq`, `f_qp`, `f_q`, `alpha_f`, `f_total`, `lim_250`, `lim_350` |
| Cisalhamento | `Vsd_x`, `VRd1_x`, `Vsd_y`, `VRd1_y`, `cis_ok_x`, `cis_ok_y` |

---

## 10. Limitações e pontos de atenção

1. **Descrição dos casos.** Os comentários das tabelas `MOMENTOS` e o dicionário `DESCRICAO` não usam exatamente a mesma redação para alguns casos (por exemplo, 2, 3, 5 e 6). Confira a numeração e a orientação das bordas engastadas com os quadros do livro antes de usar o programa em um caso real.
2. **Combinação última simplificada:** $$1{,}4\,(g+q)$$ vale para uma única ação variável. Para mais ações, é preciso ponderar cada uma.
3. **Concreto limitado a C40.** Para C45 a C90 seria necessário implementar os parâmetros do bloco de tensões da norma para classes superiores.
4. **Cisalhamento conservador:** adota-se $$k = 1{,}0$$, e a largura do apoio não é entrada. Por isso $$V_{Sd} = R - p\,d$$ é uma aproximação.
5. **Flecha:** a rigidez equivalente é calculada com a direção de maior momento rara e aplicada às duas parcelas. Não há armadura comprimida na fluência ($$\rho' = 0$$).
6. **Compatibilização de momentos negativos** entre lajes adjacentes não é feita. Cada laje é tratada isoladamente.
7. **Lajes com $$\lambda > 2$$** (armadas em uma direção), balanços, lajes nervuradas e lajes lisas não são cobertas.
8. **Referências normativas:** os itens e tabelas da NBR 6118:2026 citados nos comentários do código devem ser conferidos contra o texto vigente da norma.
9. O programa é uma **ferramenta de apoio acadêmico**. Os resultados devem ser revisados por engenheiro responsável antes de qualquer uso em projeto.

---

## 11. Como validar o código

1. Resolva à mão (ou em planilha) um exemplo do livro e compare $$M$$, $$A_s$$ e a flecha com a saída.
2. Teste os limites: $$\lambda = 1{,}00$$, $$\lambda = 2{,}00$$, $$\lambda = 2{,}01$$ (deve dar erro).
3. Teste entradas inválidas: cobrimento abaixo do nominal, $$\phi > h/8$$, caso 7 a 9, $$f_{ck} = 45$$.
4. Verifique a coerência: aumentar $$h$$ deve reduzir $$A_s$$ e a flecha; aumentar $$q$$ deve aumentar $$M$$, $$A_s$$ e a flecha.
5. Escreva testes automatizados (`pytest`) chamando `montar_dados()` e `calcular()` com dicionários fixos e comparando com valores de referência.

---

## 12. Referências

- CARVALHO, R. C.; FIGUEIREDO FILHO, J. R. *Cálculo e Detalhamento de Estruturas Usuais de Concreto Armado*. 4ª ed.
- BASTOS, P. S. dos S. *Lajes de concreto*. Notas de aula (pré-dimensionamento).
- ABNT NBR 6118:2026 — Projeto de estruturas de concreto.
- ABNT NBR 6120:2019 — Ações para o cálculo de estruturas de edificações.