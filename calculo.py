"""
================================================================================
  CÁLCULO DE LAJES MACIÇAS DE CONCRETO ARMADO
  Ref. livro : Carvalho & Figueiredo – Cálculo e Detalhamento de Estruturas
               Usuais de Concreto Armado (4ª ed.)
  Ref. norma : ABNT NBR 6118:2026
================================================================================
  Saída: memória de cálculo completa no terminal
  Cobre: pré-dimensionamento, cargas (ELU e ELS), momentos, reações,
         dimensionamento da armadura, verificação de flecha (com fluência
         e limites da NBR) e verificação ao cisalhamento.
================================================================================
"""

import math

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                        TABELAS DO LIVRO E DA NBR                             ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# ─── Quadro 7.3 / 7.4 / 7.5 — Coeficientes µ para MOMENTOS ──────────────────
# Fórmula: M = µ × p × lx² / 100   (kNm/m)
# Cada linha: [λ, µx_pos, µy_pos, µx_neg, µy_neg]
# Zeros indicam que não há engaste naquela direção para o caso.

MOMENTOS = {
    # Caso 1 – 4 bordas simplesmente apoiadas
    1: [
        [1.00, 4.41, 4.41, 0,    0   ], [1.05, 4.80, 4.45, 0,    0   ],
        [1.10, 5.18, 4.49, 0,    0   ], [1.15, 5.56, 4.49, 0,    0   ],
        [1.20, 5.90, 4.48, 0,    0   ], [1.25, 6.27, 4.45, 0,    0   ],
        [1.30, 6.60, 4.42, 0,    0   ], [1.35, 6.93, 4.37, 0,    0   ],
        [1.40, 7.25, 4.33, 0,    0   ], [1.45, 7.55, 4.30, 0,    0   ],
        [1.50, 7.86, 4.25, 0,    0   ], [1.55, 8.12, 4.20, 0,    0   ],
        [1.60, 8.34, 4.14, 0,    0   ], [1.65, 8.62, 4.07, 0,    0   ],
        [1.70, 8.86, 4.00, 0,    0   ], [1.75, 9.06, 3.96, 0,    0   ],
        [1.80, 9.27, 3.91, 0,    0   ], [1.85, 9.45, 3.83, 0,    0   ],
        [1.90, 9.63, 3.75, 0,    0   ], [1.95, 9.77, 3.71, 0,    0   ],
        [2.00,10.00, 3.64, 0,    0   ],
    ],
    # Caso 2 – 2 bordas opostas engastadas (paralelas a ly)
    2: [
        [1.00, 3.07, 3.94, 0, 8.52], [1.05, 3.42, 3.78, 0, 8.79],
        [1.10, 3.77, 3.90, 0, 9.18], [1.15, 4.14, 3.97, 0, 9.53],
        [1.20, 4.51, 4.05, 0, 9.88], [1.25, 4.88, 4.10, 0, 10.16],
        [1.30, 5.25, 4.15, 0, 10.41], [1.35, 5.60, 4.18, 0, 10.64],
        [1.40, 5.95, 4.21, 0, 10.86], [1.45, 6.27, 4.19, 0, 11.05],
        [1.50, 6.60, 4.18, 0, 11.23], [1.55, 6.90, 4.17, 0, 11.39],
        [1.60, 7.21, 4.14, 0, 11.55], [1.65, 7.42, 4.12, 0, 11.67],
        [1.70, 7.62, 4.09, 0, 11.79], [1.75, 7.66, 4.05, 0, 11.88],
        [1.80, 7.69, 3.99, 0, 11.96], [1.85, 8.22, 3.97, 0, 12.03],
        [1.90, 8.74, 3.94, 0, 12.14], [1.95, 8.97, 3.88, 0, 12.17],
        [2.00, 9.18, 3.80, 0, 12.20],
    ],
    # Caso 3 – 1 borda engastada (paralela a lx — bordo em y)
    3: [
        [1.00, 3.94, 3.07, 8.52, 0], [1.05, 4.19, 2.84, 8.91, 0],
        [1.10, 4.43, 2.76, 9.30, 0], [1.15, 4.64, 2.68, 9.63, 0],
        [1.20, 4.85, 2.59, 9.95, 0], [1.25, 5.03, 2.51, 10.22, 0],
        [1.30, 5.20, 2.42, 10.48, 0], [1.35, 5.36, 2.34, 10.71, 0],
        [1.40, 5.51, 2.25, 10.92, 0], [1.45, 5.64, 2.19, 11.10, 0],
        [1.50, 5.77, 2.12, 11.27, 0], [1.55, 5.87, 2.04, 11.42, 0],
        [1.60, 5.98, 1.95, 11.55, 0], [1.65, 6.07, 1.87, 11.67, 0],
        [1.70, 6.16, 1.79, 11.80, 0], [1.75, 6.24, 1.74, 11.92, 0],
        [1.80, 6.31, 1.68, 12.04, 0], [1.85, 6.38, 1.64, 12.14, 0],
        [1.90, 6.43, 1.59, 12.24, 0], [1.95, 6.47, 1.54, 12.29, 0],
        [2.00, 6.51, 1.48, 12.34, 0],
    ],
    # Caso 4 – 2 bordas adjacentes engastadas
    4: [
        [1.00, 2.81, 2.81, 6.99, 6.99], [1.05, 3.05, 2.81, 7.43, 7.18],
        [1.10, 3.30, 2.81, 7.87, 7.36], [1.15, 3.53, 2.80, 8.28, 7.50],
        [1.20, 3.76, 2.79, 8.69, 7.63], [1.25, 3.96, 2.74, 9.03, 7.72],
        [1.30, 4.16, 2.69, 9.37, 7.81], [1.35, 4.33, 2.65, 9.65, 7.88],
        [1.40, 4.51, 2.60, 9.93, 7.94], [1.45, 4.66, 2.55, 10.41, 8.00],
        [1.50, 4.81, 2.47, 10.62, 8.06], [1.55, 4.93, 2.39, 10.82, 8.09],
        [1.60, 5.06, 2.31, 10.99, 8.12], [1.65, 5.16, 2.24, 11.16, 8.14],
        [1.70, 5.27, 2.16, 11.30, 8.15], [1.75, 5.36, 2.11, 11.43, 8.16],
        [1.80, 5.45, 2.04, 11.55, 8.17], [1.85, 5.53, 1.99, 11.57, 8.17],
        [1.90, 5.60, 1.93, 11.67, 8.18], [1.95, 5.67, 1.91, 11.78, 8.19],
        [2.00, 5.74, 1.88, 11.89, 8.20],
    ],
    # Caso 5 – 2 bordas opostas engastadas (paralelas a lx)
    5: [
        [1.00, 2.15, 3.17, 0,    6.99], [1.05, 2.47, 3.32, 0,    7.43],
        [1.10, 2.78, 3.47, 0,    7.87], [1.15, 3.08, 3.58, 0,    8.26],
        [1.20, 3.38, 3.70, 0,    8.65], [1.25, 3.79, 3.80, 0,    9.03],
        [1.30, 4.15, 3.90, 0,    9.33], [1.35, 4.50, 3.96, 0,    9.69],
        [1.40, 4.85, 4.03, 0,   10.00], [1.45, 5.19, 4.09, 0,   10.25],
        [1.50, 5.53, 4.14, 0,   10.49], [1.55, 5.86, 4.16, 0,   10.70],
        [1.60, 6.18, 4.17, 0,   10.91], [1.65, 6.48, 4.14, 0,   11.08],
        [1.70, 6.81, 4.12, 0,   11.24], [1.75, 7.11, 4.12, 0,   11.39],
        [1.80, 7.41, 4.10, 0,   11.43], [1.85, 7.68, 4.08, 0,   11.65],
        [1.90, 7.95, 4.04, 0,   11.77], [1.95, 8.21, 3.99, 0,   11.83],
        [2.00, 8.47, 3.92, 0,   11.88],
    ],
    # Caso 6 – 2 bordas opostas engastadas (paralelas a ly) — variante
    6: [
        [1.00, 3.17, 3.17, 6.99, 0], [1.05, 3.29, 3.32, 7.20, 0],
        [1.10, 3.42, 3.47, 7.41, 0], [1.15, 3.52, 3.58, 7.56, 0],
        [1.20, 3.63, 3.70, 7.70, 0], [1.25, 3.71, 3.80, 7.82, 0],
        [1.30, 3.79, 3.90, 7.93, 0], [1.35, 3.84, 3.96, 8.02, 0],
        [1.40, 3.90, 4.03, 8.11, 0], [1.45, 3.94, 4.09, 8.13, 0],
        [1.50, 3.99, 4.14, 8.15, 0], [1.55, 4.03, 4.16, 8.20, 0],
        [1.60, 4.06, 4.17, 8.25, 0], [1.65, 4.09, 4.14, 8.28, 0],
        [1.70, 4.12, 4.12, 8.30, 0], [1.75, 4.14, 4.12, 8.31, 0],
        [1.80, 4.15, 4.10, 8.32, 0], [1.85, 4.16, 4.08, 8.33, 0],
        [1.90, 4.17, 4.04, 8.33, 0], [1.95, 4.17, 3.99, 8.33, 0],
        [2.00, 4.18, 3.92, 8.33, 0],
    ],
    # Caso 7 – 4 bordas engastadas
    7: [
        [1.00, 2.13, 5.46, 2.60, 6.17], [1.05, 2.38, 5.98, 2.66, 6.46],
        [1.10, 2.57, 6.46, 2.77, 6.75], [1.15, 2.76, 6.92, 2.85, 7.01],
        [1.20, 2.93, 7.33, 2.93, 7.24], [1.25, 3.09, 7.71, 3.00, 7.45],
        [1.30, 3.22, 8.06, 3.06, 7.64], [1.35, 3.35, 8.36, 3.11, 7.80],
        [1.40, 3.46, 8.63, 3.16, 7.94], [1.45, 3.56, 8.87, 3.19, 8.05],
        [1.50, 3.65, 9.08, 3.22, 8.15], [1.55, 3.74, 9.24, 3.23, 8.22],
        [1.60, 3.81, 9.38, 3.24, 8.28], [1.65, 3.87, 9.49, 3.25, 8.33],
        [1.70, 3.92, 9.59, 3.25, 8.37], [1.75, 3.97, 9.68, 3.25, 8.40],
        [1.80, 4.01, 9.76, 3.26, 8.43], [1.85, 4.04, 9.82, 3.26, 8.45],
        [1.90, 4.08, 9.87, 3.26, 8.46], [1.95, 4.11, 9.90, 3.26, 8.47],
        [2.00, 4.13, 9.93, 3.26, 8.48],
    ],
    # Caso 8 – 3 bordas engastadas + 1 borda livre (paralela a ly)
    8: [
        [1.00, 2.60, 6.17, 2.13, 5.46], [1.05, 2.78, 6.47, 2.09, 5.56],
        [1.10, 2.96, 6.78, 2.06, 5.66], [1.15, 3.12, 7.07, 2.03, 5.75],
        [1.20, 3.28, 7.34, 2.00, 5.83], [1.25, 3.42, 7.58, 1.97, 5.90],
        [1.30, 3.55, 7.81, 1.93, 5.95], [1.35, 3.66, 8.01, 1.89, 6.00],
        [1.40, 3.77, 8.19, 1.86, 6.05], [1.45, 3.86, 8.36, 1.82, 6.08],
        [1.50, 3.95, 8.51, 1.78, 6.11], [1.55, 4.03, 8.64, 1.75, 6.14],
        [1.60, 4.10, 8.76, 1.71, 6.16], [1.65, 4.17, 8.86, 1.67, 6.17],
        [1.70, 4.23, 8.96, 1.64, 6.18], [1.75, 4.28, 9.04, 1.61, 6.19],
        [1.80, 4.33, 9.12, 1.58, 6.20], [1.85, 4.37, 9.18, 1.54, 6.20],
        [1.90, 4.41, 9.24, 1.51, 6.21], [1.95, 4.45, 9.30, 1.48, 6.21],
        [2.00, 4.48, 9.35, 1.44, 6.22],
    ],
    # Caso 9 – 3 bordas engastadas + 1 borda livre (paralela a lx)
    9: [
        [1.00, 2.11, 5.15, 2.11, 5.15], [1.05, 2.31, 5.50, 2.09, 5.56],
        [1.10, 2.53, 5.88, 2.06, 5.66], [1.15, 2.73, 6.25, 2.03, 5.75],
        [1.20, 2.93, 6.61, 2.00, 5.83], [1.25, 3.12, 6.95, 1.97, 5.90],
        [1.30, 3.30, 7.27, 1.93, 5.95], [1.35, 3.46, 7.56, 1.89, 6.00],
        [1.40, 3.62, 7.83, 1.86, 6.05], [1.45, 3.76, 8.08, 1.82, 6.08],
        [1.50, 3.89, 8.31, 1.78, 6.11], [1.55, 4.01, 8.52, 1.75, 6.14],
        [1.60, 4.12, 8.71, 1.71, 6.16], [1.65, 4.22, 8.88, 1.67, 6.17],
        [1.70, 4.31, 9.04, 1.64, 6.18], [1.75, 4.40, 9.18, 1.61, 6.19],
        [1.80, 4.47, 9.31, 1.58, 6.20], [1.85, 4.54, 9.42, 1.54, 6.20],
        [1.90, 4.61, 9.53, 1.51, 6.21], [1.95, 4.67, 9.62, 1.48, 6.21],
        [2.00, 4.72, 9.71, 1.44, 6.22],
    ],
}

# ─── Quadros 7.8 / 7.9 — Coeficientes k para REAÇÕES ─────────────────────────
# Fórmula: R = k × p × lx / 10   (kN/m)
# Cada linha: [λ, kx, ky]

REACOES = {
    1: [
        [1.00,2.50,2.50],[1.05,2.62,2.50],[1.10,2.73,2.50],[1.15,2.83,2.50],
        [1.20,2.92,2.50],[1.25,3.00,2.50],[1.30,3.08,2.50],[1.35,3.15,2.50],
        [1.40,3.21,2.50],[1.45,3.28,2.50],[1.50,3.33,2.50],[1.55,3.39,2.50],
        [1.60,3.44,2.50],[1.65,3.48,2.50],[1.70,3.53,2.50],[1.75,3.57,2.50],
        [1.80,3.61,2.50],[1.85,3.65,2.50],[1.90,3.68,2.50],[1.95,3.72,2.50],
        [2.00,3.75,2.50],
    ],
    2: [
        [1.00,1.83,2.32],[1.05,1.92,2.37],[1.10,2.01,2.41],[1.15,2.10,2.44],
        [1.20,2.20,2.46],[1.25,2.29,2.48],[1.30,2.38,2.49],[1.35,2.47,2.50],
        [1.40,2.56,2.50],[1.45,2.64,2.50],[1.50,2.72,2.50],[1.55,2.80,2.50],
        [1.60,2.87,2.50],[1.65,2.93,2.50],[1.70,2.99,2.50],[1.75,3.05,2.50],
        [1.80,3.10,2.50],[1.85,3.15,2.50],[1.90,3.20,2.50],[1.95,3.25,2.50],
        [2.00,3.29,2.50],
    ],
    3: [
        [1.00,2.32,4.02],[1.05,2.38,4.13],[1.10,2.44,4.23],[1.15,2.50,4.32],
        [1.20,2.54,4.41],[1.25,2.59,4.48],[1.30,2.63,4.55],[1.35,2.67,4.62],
        [1.40,2.70,4.68],[1.45,2.74,4.74],[1.50,2.77,4.79],[1.55,2.80,4.84],
        [1.60,2.82,4.89],[1.65,2.85,4.93],[1.70,2.87,4.97],[1.75,2.89,5.01],
        [1.80,2.92,5.05],[1.85,2.94,5.09],[1.90,2.96,5.12],[1.95,2.97,5.15],
        [2.00,2.99,5.18],
    ],
    4: [
        [1.00,1.83,3.17],[1.05,1.92,3.32],[1.10,2.00,3.46],[1.15,2.07,3.58],
        [1.20,2.14,3.70],[1.25,2.20,3.80],[1.30,2.25,3.89],[1.35,2.30,3.99],
        [1.40,2.35,4.08],[1.45,2.40,4.15],[1.50,2.44,4.23],[1.55,2.48,4.29],
        [1.60,2.52,4.36],[1.65,2.55,4.42],[1.70,2.58,4.47],[1.75,2.61,4.52],
        [1.80,2.63,4.57],[1.85,2.65,4.61],[1.90,2.67,4.65],[1.95,2.69,4.68],
        [2.00,2.71,4.71],
    ],
    5: [
        [1.00,1.44,3.56],[1.05,1.52,3.66],[1.10,1.59,3.75],[1.15,1.66,3.84],
        [1.20,1.73,3.92],[1.25,1.80,3.99],[1.30,1.88,4.06],[1.35,1.95,4.12],
        [1.40,2.02,4.17],[1.45,2.09,4.22],[1.50,2.17,4.25],[1.55,2.24,4.28],
        [1.60,2.31,4.30],[1.65,2.38,4.32],[1.70,2.44,4.33],[1.75,2.50,4.34],
        [1.80,2.56,4.35],[1.85,2.62,4.36],[1.90,2.68,4.37],[1.95,2.73,4.37],
        [2.00,2.78,4.38],
    ],
    6: [
        [1.00,3.56,1.44],[1.05,3.63,1.44],[1.10,3.69,1.44],[1.15,3.74,1.44],
        [1.20,3.80,1.44],[1.25,3.85,1.44],[1.30,3.89,1.44],[1.35,3.93,1.44],
        [1.40,3.97,1.44],[1.45,4.00,1.44],[1.50,4.04,1.44],[1.55,4.07,1.44],
        [1.60,4.10,1.44],[1.65,4.13,1.44],[1.70,4.15,1.44],[1.75,4.16,1.44],
        [1.80,4.17,1.44],[1.85,4.18,1.44],[1.90,4.19,1.44],[1.95,4.19,1.44],
        [2.00,4.20,1.44],
    ],
}

# ─── Quadro 7.2 — Coeficientes α para FLECHA ELÁSTICA ────────────────────────
# Fórmula: f = α × p × lx⁴ / (Ecs × h³ × 100)
# Cada linha: [λ, α_caso1, α_caso2, ..., α_caso9]

ALPHA_FLECHA = [
    #   λ      C1     C2     C3     C4     C5     C6     C7     C8     C9
    [1.00,   4.67,  3.20,  3.20,  2.42,  2.21,  2.21,  1.81,  1.81,  1.46],
    [1.05,   5.17,  3.61,  3.42,  2.67,  2.55,  2.31,  2.04,  1.92,  1.60],
    [1.10,   5.64,  4.04,  3.63,  2.91,  2.92,  2.41,  2.27,  2.04,  1.74],
    [1.15,   6.09,  4.47,  3.82,  3.12,  3.29,  2.48,  2.49,  2.14,  1.87],
    [1.20,   6.52,  4.91,  4.02,  3.34,  3.67,  2.56,  2.72,  2.24,  1.98],
    [1.25,   6.95,  5.34,  4.18,  3.55,  4.07,  2.63,  2.95,  2.33,  2.10],
    [1.30,   7.36,  5.77,  4.35,  3.73,  4.48,  2.69,  3.16,  2.42,  2.20],
    [1.35,   7.76,  6.21,  4.50,  3.92,  4.92,  2.72,  3.36,  2.48,  2.30],
    [1.40,   8.14,  6.62,  4.65,  4.08,  5.31,  2.75,  3.56,  2.56,  2.37],
    [1.45,   8.51,  7.02,  4.78,  4.23,  5.73,  2.80,  3.73,  2.62,  2.45],
    [1.50,   8.87,  7.41,  4.92,  4.38,  6.14,  2.84,  3.91,  2.68,  2.51],
    [1.55,   9.22,  7.81,  5.00,  4.53,  6.54,  2.86,  4.07,  2.53,  2.57],
    [1.60,   9.54,  8.17,  5.09,  4.65,  6.93,  2.87,  4.22,  2.87,  2.63],
    [1.65,   9.86,  8.52,  5.13,  4.77,  7.33,  2.87,  4.37,  2.78,  2.68],
    [1.70,  10.15,  8.87,  5.17,  4.88,  7.70,  2.88,  4.51,  2.79,  2.72],
    [1.75,  10.43,  9.19,  5.26,  4.97,  8.06,  2.88,  4.63,  2.81,  2.76],
    [1.80,  10.71,  9.52,  5.36,  5.07,  8.43,  2.89,  4.75,  2.83,  2.80],
    [1.85,  10.96,  9.82,  5.43,  5.15,  8.77,  2.89,  4.87,  2.85,  2.83],
    [1.90,  11.21, 10.11,  5.50,  5.23,  9.08,  2.90,  4.98,  2.87,  2.85],
    [1.95,  11.44, 10.39,  5.58,  5.31,  9.41,  2.90,  5.08,  2.89,  2.88],
    [2.00,  11.68, 10.68,  5.66,  5.39,  9.72,  2.91,  5.19,  2.91,  2.91],
]

# ─── Tabela 17.3 NBR 6118:2026 — ρ_mín (%) para seção retangular ─────────────
RHO_MIN_TAB = {
    20:0.150, 25:0.150, 30:0.150, 35:0.164, 40:0.179,
    45:0.194, 50:0.208, 55:0.211, 60:0.219, 65:0.226,
    70:0.233, 75:0.239, 80:0.245, 85:0.251, 90:0.256,
}

def rho_min(fck):
    chaves = sorted(RHO_MIN_TAB)
    if fck <= chaves[0]:  return RHO_MIN_TAB[chaves[0]]
    if fck >= chaves[-1]: return RHO_MIN_TAB[chaves[-1]]
    for i in range(len(chaves)-1):
        f0, f1 = chaves[i], chaves[i+1]
        if f0 <= fck <= f1:
            t = (fck-f0)/(f1-f0)
            return RHO_MIN_TAB[f0] + t*(RHO_MIN_TAB[f1]-RHO_MIN_TAB[f0])

# ─── Tabela 7.2 NBR 6118:2026 — Cobrimento nominal mínimo (mm) ───────────────
COB_NOMINAL = {"I": 20, "II": 25, "III": 35, "IV": 45}
FCK_MIN_CAA = {"I": 20, "II": 25, "III": 30, "IV": 40}

DESCRICAO = {
    1: "4 bordas simplesmente apoiadas",
    2: "1 borda engastada paralela a lx; demais apoiadas",
    3: "1 borda engastada paralela a ly; demais apoiadas",
    4: "2 bordas adjacentes engastadas; demais apoiadas",
    5: "2 bordas opostas engastadas paralelas a lx; demais apoiadas",
    6: "2 bordas opostas engastadas paralelas a ly; demais apoiadas",
    7: "3 bordas engastadas; borda apoiada paralela a ly",
    8: "3 bordas engastadas; borda apoiada paralela a lx",
    9: "4 bordas engastadas",
}

  
# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                          FUNÇÕES AUXILIARES                                  ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# Escopo desta versão:
# - lajes maciças retangulares armadas em DUAS direções (lambda <= 2,0);
# - casos 1 a 6 das tabelas de Carvalho & Figueiredo, já conferidos no material-base;
# - concreto C20 a C40 nesta revisão (para evitar extrapolar o bloco de tensões sem
#   implementar integralmente os parâmetros adicionais da NBR 6118:2026 para C45-C90).
# Casos 7 a 9 permanecem nas tabelas originais apenas para rastreabilidade, mas são
# bloqueados nesta versão até conferência integral da transcrição.

AGREGADOS = {
    "1": ("basalto/diabásio", 1.20),
    "2": ("granito/gnaisse", 1.00),
    "3": ("calcário", 0.90),
    "4": ("arenito", 0.70),
}

N_BORDAS_ENGASTADAS = {1: 0, 2: 1, 3: 1, 4: 2, 5: 2, 6: 2, 7: 3, 8: 3, 9: 4}


def interpolar(tabela, lam, col=None):
    """Interpolação linear SEM extrapolação silenciosa."""
    lo, hi = tabela[0][0], tabela[-1][0]
    if not (lo <= lam <= hi):
        raise ValueError(f"lambda={lam:.3f} fora do intervalo tabelado [{lo:.2f}, {hi:.2f}].")
    for i in range(len(tabela)-1):
        l0, l1 = tabela[i][0], tabela[i+1][0]
        if l0 <= lam <= l1:
            if abs(lam-l0) < 1e-12:
                vals = list(tabela[i][1:])
            else:
                t = (lam-l0)/(l1-l0)
                vals = [tabela[i][j]+t*(tabela[i+1][j]-tabela[i][j])
                        for j in range(1, len(tabela[i]))]
            return vals[col] if col is not None else vals
    vals = list(tabela[-1][1:])
    return vals[col] if col is not None else vals


# Coeficientes completos de reação para os casos 1 a 6.
# Chaves: kx/ky = borda apoiada; kxp/kyp = borda engastada.
_KYP_CASO2 = [4.02,4.10,4.17,4.22,4.27,4.30,4.32,4.33,4.33,4.33,4.33,4.33,4.33,4.33,4.33,4.33,4.33,4.33,4.33,4.33,4.33]

def coef_reacoes(caso, lam):
    vals = interpolar(REACOES[caso], lam)
    if caso == 1:
        return {"kx": vals[0], "ky": vals[1]}
    if caso == 2:
        # tabela armazenada: kx, ky; acrescenta k'y do Quadro 7.8
        tabela_extra = [[1.00 + 0.05*i, v] for i, v in enumerate(_KYP_CASO2)]
        return {"kx": vals[0], "ky": vals[1], "kyp": interpolar(tabela_extra, lam, col=0)}
    if caso == 3:
        # tabela armazenada: kx, k'x; ky = 1,83
        return {"kx": vals[0], "kxp": vals[1], "ky": 1.83}
    if caso == 4:
        # tabela armazenada: kx, k'x; ky = 1,83 e k'y = 3,17
        return {"kx": vals[0], "kxp": vals[1], "ky": 1.83, "kyp": 3.17}
    if caso == 5:
        # tabela armazenada: kx, k'y
        return {"kx": vals[0], "kyp": vals[1]}
    if caso == 6:
        # tabela armazenada: k'x, ky
        return {"kxp": vals[0], "ky": vals[1]}
    raise ValueError("Coeficientes completos de reação disponíveis apenas para os casos 1 a 6.")

def reacoes_kNm(caso, lam, p, lx):
    k = coef_reacoes(caso, lam)
    return {nome: coef*p*lx/10 for nome, coef in k.items()}


def xi(t_meses):
    """Coeficiente xi(t), Tabela 17.1 / expressão aproximada da NBR 6118."""
    if t_meses > 70:
        return 2.0
    if t_meses <= 0:
        return 0.0
    return 0.68 * (0.996**t_meses) * (t_meses**0.32)


def fctm_nbr(fck):
    if fck <= 50:
        return 0.3 * fck**(2/3)
    return 2.12 * math.log(1 + 0.1*(fck + 8))


def modulos_concreto(fck, alpha_E):
    """Eci e Ecs em MPa, conforme item 8.2.8 da NBR 6118:2026."""
    if fck <= 50:
        Eci = alpha_E * 5600 * math.sqrt(fck)
    else:
        Eci = alpha_E * 21500 * ((fck/10 + 1.25)**(1/3))
    alpha_i = min(0.8 + 0.2*fck/80, 1.0)
    Ecs = alpha_i * Eci
    return Eci, Ecs, alpha_i


def altura_minima(tipo):
    # NBR 6118:2026, 13.2.4.1 — apenas categorias compatíveis com este programa.
    return 0.08 if tipo == "piso" else 0.07


def estimar_h_bastos(lx, ly, caso, cob_m, phi_m):
    """Estimativa de h baseada nas Eq. 15 a 18 de Bastos (pré-dimensionamento)."""
    n = N_BORDAS_ENGASTADAS[caso]
    # l* em m: menor entre lx e 0,7 ly (com lx <= ly)
    l_estrela = min(lx, 0.7*ly)
    d_cm = (2.5 - 0.1*n) * l_estrela
    d_m = d_cm/100
    h_m = d_m + cob_m + phi_m/2
    return d_m, h_m, l_estrela, n


def sep(c="=", n=76): print(c*n)
def cab(t): sep(); print(f"  {t}"); sep()
def lin(label, val, un=""):
    print(f"  {label:<52} {val:>10.4f}  {un}")
def ok_nok(cond, msg_ok, msg_no):
    print(f"  {'✔' if cond else '✘'}  {msg_ok if cond else msg_no}")


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                             CÁLCULO PRINCIPAL                                ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

def calcular(d):
    lx, ly, h, caso = d["lx"], d["ly"], d["h"], d["caso"]
    cob, phi = d["cob"]/1000, d["phi"]/1000
    fck, fyk = d["fck"], d["fyk"]
    lam = ly/lx

    # Resistências e módulos — combinação normal
    gamma_c, gamma_s = 1.4, 1.15
    fcd = fck/gamma_c
    fyd = fyk/gamma_s
    fctm = fctm_nbr(fck)
    fctk_inf = 0.7*fctm
    Eci_MPa, Ecs_MPa, alpha_i = modulos_concreto(fck, d["alpha_E"])
    Ecs = Ecs_MPa*1000  # kN/m²

    # Alturas úteis: x é considerada a camada inferior; y fica uma bitola acima.
    d_xp = h - cob - 0.5*phi
    d_yp = h - cob - 1.5*phi
    d_xn = h - cob - 0.5*phi
    d_yn = h - cob - 1.5*phi
    if min(d_xp, d_yp, d_xn, d_yn) <= 0:
        raise ValueError("Altura útil não positiva; reveja h, cobrimento e bitola.")

    # Cargas
    g1 = d["gc"]*h
    g2 = d["g_contrapiso"] + d["g_revest_inf"] + d["g_piso"] + d["g_paredes"] + d["g_outros"]
    g = g1 + g2
    q = d["q"]
    # Uma ação variável: combinação última normal simplificada = 1,4(g+q)
    p_elu = 1.4*(g + q)
    p_rare = g + q
    p_qp = g + d["psi2"]*q
    p_q = q

    # Coeficientes — somente domínio tabelado 1 <= lambda <= 2
    mu_xp, mu_yp, mu_xn, mu_yn = interpolar(MOMENTOS[caso], lam)
    alpha = interpolar(ALPHA_FLECHA, lam, col=caso-1)

    # Momentos ELU
    Mx_pos = mu_xp*p_elu*lx**2/100
    My_pos = mu_yp*p_elu*lx**2/100
    Mx_neg = mu_xn*p_elu*lx**2/100 if mu_xn > 0 else 0.0
    My_neg = mu_yn*p_elu*lx**2/100 if mu_yn > 0 else 0.0

    # Momentos de serviço raros para verificação do estádio
    Mx_rare = mu_xp*p_rare*lx**2/100
    My_rare = mu_yp*p_rare*lx**2/100

    # Reações completas: distingue bordas apoiadas e engastadas
    reacoes = reacoes_kNm(caso, lam, p_elu, lx)
    Rx_ap = reacoes.get("kx")
    Rx_eng = reacoes.get("kxp")
    Ry_ap = reacoes.get("ky")
    Ry_eng = reacoes.get("kyp")
    Rx = max(v for v in (Rx_ap, Rx_eng) if v is not None)
    Ry = max(v for v in (Ry_ap, Ry_eng) if v is not None)

    # Flexão com bloco retangular para C20-C40, faixa de 1,0 m
    alpha_c = 0.85
    eta_c = 1.0  # escopo C20-C40 desta versão
    lamb = 0.8
    bw = 1.0
    fcd_k = fcd*1000
    fyd_k = fyd*1000

    def dim(Md, du):
        if Md <= 0:
            return 0.0, 0.0, 0.0, 0.0
        sigma_c = alpha_c*eta_c*fcd_k
        A = sigma_c*bw*lamb
        disc = (A*du)**2 - 2*A*lamb*Md
        if disc <= 0:
            raise ValueError("Seção insuficiente à flexão: aumente h.")
        x = (A*du - math.sqrt(disc))/(A*lamb)
        z = du - 0.5*lamb*x
        As_m2 = Md/(fyd_k*z)
        xi_x = x/du
        return As_m2*1e4, xi_x, z, x

    As_xp_calc, xid_xp, z_xp, x_xp = dim(Mx_pos, d_xp)
    As_yp_calc, xid_yp, z_yp, x_yp = dim(My_pos, d_yp)
    As_xn_calc, xid_xn, z_xn, x_xn = dim(Mx_neg, d_xn)
    As_yn_calc, xid_yn, z_yn, x_yn = dim(My_neg, d_yn)

    # Dutilidade: para o escopo C20-C40, x/d <= 0,45
    xi_lim = 0.45
    for nome, xi_val, M in (("X+", xid_xp, Mx_pos), ("Y+", xid_yp, My_pos),
                            ("X-", xid_xn, Mx_neg), ("Y-", xid_yn, My_neg)):
        if M > 0 and xi_val > xi_lim:
            raise ValueError(
                f"Dutilidade não atendida em {nome}: x/d={xi_val:.3f} > {xi_lim:.2f}. "
                "Aumente a espessura/altura útil ou reavalie a seção."
            )

    # Armadura mínima: rho_s = As/(bw*h), não As/(bw*d)
    rho_m = rho_min(fck)
    As_min_base = rho_m/100 * 100 * (h*100)  # cm²/m
    As_min_2dir = 0.67*As_min_base
    As_xp = max(As_xp_calc, As_min_2dir)
    As_yp = max(As_yp_calc, As_min_2dir)
    As_xn = max(As_xn_calc, As_min_base) if Mx_neg > 0 else 0.0
    As_yn = max(As_yn_calc, As_min_base) if My_neg > 0 else 0.0

    # Barras/espaçamentos
    Ab = math.pi*d["phi"]**2/4/100  # cm² por barra
    s_max = min(20.0, 2.0*h*100)    # NBR: 2h ou 20 cm

    def barras(As):
        if As <= 0:
            return 0, 0.0, 0.0
        n_area = math.ceil(As/Ab)
        n_esp = max(1, math.ceil(100/s_max))
        n = max(n_area, n_esp)
        s = 100/n
        As_fornec = n*Ab
        return n, s, As_fornec

    n_xp,s_xp,Asf_xp = barras(As_xp)
    n_yp,s_yp,Asf_yp = barras(As_yp)
    n_xn,s_xn,Asf_xn = barras(As_xn)
    n_yn,s_yn,Asf_yn = barras(As_yn)

    # Flecha — verificação de estádio e rigidez equivalente de Branson
    Ic = bw*h**3/12
    yt = h/2
    Mr = 1.5*(fctm*1000)*Ic/yt  # kNm/m
    if Mx_rare >= My_rare:
        Ma = Mx_rare; As_serv_cm2 = Asf_xp; d_serv = d_xp; dir_serv = "x"
    else:
        Ma = My_rare; As_serv_cm2 = Asf_yp; d_serv = d_yp; dir_serv = "y"
    Es_MPa = 210000.0
    alpha_e = Es_MPa/Ecs_MPa
    As_serv = As_serv_cm2/1e4  # m²/m

    if Ma <= Mr or As_serv <= 0:
        estadio = "I (não fissurado)"
        III = Ic
        Ieq = Ic
    else:
        estadio = "II / rigidez equivalente"
        a = 0.5*bw
        bq = alpha_e*As_serv
        cq = -alpha_e*As_serv*d_serv
        disc = bq*bq - 4*a*cq
        xII = (-bq + math.sqrt(disc))/(2*a)
        III = bw*xII**3/3 + alpha_e*As_serv*(d_serv-xII)**2
        ratio = min(Mr/Ma, 1.0)
        Ieq = ratio**3*Ic + (1-ratio**3)*III
        Ieq = min(Ieq, Ic)

    rigidez_ratio = Ic/Ieq
    f_qp_elastica = alpha*p_qp*lx**4/(Ecs*h**3*100)
    f_q_elastica = alpha*p_q*lx**4/(Ecs*h**3*100)
    f_qp = f_qp_elastica*rigidez_ratio
    f_q = f_q_elastica*rigidez_ratio

    # Fluência: sem armadura comprimida explicitamente considerada (rho'=0)
    xi_t0, xi_t = xi(d["t0"]), xi(d["tinf"])
    delta_xi = max(0.0, xi_t-xi_t0)
    alpha_f = delta_xi
    f_total = f_qp*(1+alpha_f)

    lim_250 = lx/250
    lim_350 = lx/350

    # Cisalhamento nas duas direções.
    # Como o detalhamento de ancoragem não é modelado nesta versão, adota-se k=1,0
    # de forma conservadora. Considera-se As1 igual à armadura positiva fornecida.
    fctd = fctk_inf/gamma_c
    tau_Rd = 0.25*fctd*1000

    def verificar_cisalhamento(Rcrit, Asf_cm2, du):
        As1_m2 = Asf_cm2/1e4
        rho1 = min(As1_m2/(bw*du), 0.02)
        k_cis = 1.0
        VRd1 = tau_Rd*k_cis*(1.2+40*rho1)*bw*du
        Vsd = max(Rcrit - p_elu*du, 0.0)
        return Vsd, VRd1, rho1, k_cis

    Vsd_x, VRd1_x, rho1_x, k_cis_x = verificar_cisalhamento(Rx, Asf_xp, d_xp)
    Vsd_y, VRd1_y, rho1_y, k_cis_y = verificar_cisalhamento(Ry, Asf_yp, d_yp)
    cis_ok_x = Vsd_x <= VRd1_x
    cis_ok_y = Vsd_y <= VRd1_y

    return dict(
        lam=lam, fcd=fcd, fyd=fyd, fctm=fctm, fctk_inf=fctk_inf,
        Eci_MPa=Eci_MPa, Ecs_MPa=Ecs_MPa, alpha_i=alpha_i,
        d_xp=d_xp, d_yp=d_yp, d_xn=d_xn, d_yn=d_yn,
        g1=g1, g2=g2, g=g, p_elu=p_elu, p_rare=p_rare, p_qp=p_qp, p_q=p_q,
        mu_xp=mu_xp, mu_yp=mu_yp, mu_xn=mu_xn, mu_yn=mu_yn, alpha=alpha,
        Mx_pos=Mx_pos, My_pos=My_pos, Mx_neg=Mx_neg, My_neg=My_neg,
        Mx_rare=Mx_rare, My_rare=My_rare, Rx=Rx, Ry=Ry,
        Rx_ap=Rx_ap, Rx_eng=Rx_eng, Ry_ap=Ry_ap, Ry_eng=Ry_eng,
        As_xp_calc=As_xp_calc, As_yp_calc=As_yp_calc,
        As_xn_calc=As_xn_calc, As_yn_calc=As_yn_calc,
        As_xp=As_xp, As_yp=As_yp, As_xn=As_xn, As_yn=As_yn,
        As_min=As_min_base, As_min_2dir=As_min_2dir, rho_m=rho_m, Ab=Ab,
        n_xp=n_xp, s_xp=s_xp, Asf_xp=Asf_xp,
        n_yp=n_yp, s_yp=s_yp, Asf_yp=Asf_yp,
        n_xn=n_xn, s_xn=s_xn, Asf_xn=Asf_xn,
        n_yn=n_yn, s_yn=s_yn, Asf_yn=Asf_yn, s_max=s_max,
        xid_xp=xid_xp, xid_yp=xid_yp, xid_xn=xid_xn, xid_yn=xid_yn, xi_lim=xi_lim,
        Mr=Mr, Ma=Ma, estadio=estadio, dir_serv=dir_serv, Ic=Ic, III=III, Ieq=Ieq,
        f_qp_elastica=f_qp_elastica, f_q_elastica=f_q_elastica,
        f_qp=f_qp, f_q=f_q, xi_t0=xi_t0, xi_t=xi_t,
        delta_xi=delta_xi, alpha_f=alpha_f, f_total=f_total,
        lim_250=lim_250, lim_350=lim_350,
        fctd=fctd, tau_Rd=tau_Rd,
        rho1_x=rho1_x, rho1_y=rho1_y,
        Vsd_x=Vsd_x, VRd1_x=VRd1_x, Vsd_y=Vsd_y, VRd1_y=VRd1_y,
        k_cis_x=k_cis_x, k_cis_y=k_cis_y, cis_ok_x=cis_ok_x, cis_ok_y=cis_ok_y,
    )


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                         MEMÓRIA DE CÁLCULO                                   ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

def imprimir(d, r):
    phi_s = f"phi{d['phi']:.0f}mm"
    sep(); print("       M E M Ó R I A   D E   C Á L C U L O")
    print("       Laje Maciça de Concreto Armado — revisão NBR 6118:2026"); sep()

    cab("1. DADOS DE ENTRADA E ESCOPO")
    lin("lx", d["lx"], "m"); lin("ly", d["ly"], "m"); lin("lambda=ly/lx", r["lam"])
    print(f"  Classificação: laje armada em duas direções (lambda <= 2,0)")
    print(f"  Caso {d['caso']}: {DESCRICAO[d['caso']]}")
    lin("h adotado", d["h"]*100, "cm"); lin("h mínimo", d["h_min"]*100, "cm")
    lin("h estimado (Bastos)", d["h_est"]*100, "cm")
    lin("cobrimento adotado", d["cob"], "mm"); lin("cobrimento Tabela 7.2", d["cob_nbr"], "mm")
    lin("fck", d["fck"], "MPa"); lin("fyk", d["fyk"], "MPa")
    print(f"  Agregado: {d['agregado']} (alpha_E={d['alpha_E']})")

    cab("2. PROPRIEDADES DOS MATERIAIS")
    lin("fcd=fck/1,4", r["fcd"], "MPa"); lin("fyd=fyk/1,15", r["fyd"], "MPa")
    lin("fctm", r["fctm"], "MPa"); lin("fctk,inf=0,7 fctm", r["fctk_inf"], "MPa")
    lin("Eci", r["Eci_MPa"], "MPa"); lin("alpha_i", r["alpha_i"])
    lin("Ecs=alpha_i Eci", r["Ecs_MPa"], "MPa")

    cab("3. ALTURAS ÚTEIS")
    lin("d_x positivo (camada inferior)", r["d_xp"]*100, "cm")
    lin("d_y positivo (2ª camada)", r["d_yp"]*100, "cm")
    lin("d_x negativo", r["d_xn"]*100, "cm"); lin("d_y negativo", r["d_yn"]*100, "cm")
    lin("phi máximo=h/8", d["h"]*1000/8, "mm")

    cab("4. CARGAS E COMBINAÇÕES")
    lin("g1 peso próprio", r["g1"], "kN/m²"); lin("g2 demais permanentes", r["g2"], "kN/m²")
    lin("g total", r["g"], "kN/m²"); lin("q", d["q"], "kN/m²")
    lin("ELU normal 1,4(g+q)", r["p_elu"], "kN/m²")
    lin("ELS rara g+q", r["p_rare"], "kN/m²")
    lin("ELS quase permanente g+psi2 q", r["p_qp"], "kN/m²")

    cab("5. COEFICIENTES E MOMENTOS")
    lin("mu_x+", r["mu_xp"]); lin("mu_y+", r["mu_yp"])
    if r["mu_xn"]: lin("mu_x-", r["mu_xn"])
    if r["mu_yn"]: lin("mu_y-", r["mu_yn"])
    lin("alpha de flecha", r["alpha"])
    lin("Mx+ ELU", r["Mx_pos"], "kNm/m"); lin("My+ ELU", r["My_pos"], "kNm/m")
    if r["Mx_neg"]: lin("Mx- ELU", r["Mx_neg"], "kNm/m")
    if r["My_neg"]: lin("My- ELU", r["My_neg"], "kNm/m")

    cab("6. REAÇÕES NAS VIGAS")
    if r["Rx_ap"] is not None: lin("Rx em borda apoiada", r["Rx_ap"], "kN/m")
    if r["Rx_eng"] is not None: lin("Rx' em borda engastada", r["Rx_eng"], "kN/m")
    if r["Ry_ap"] is not None: lin("Ry em borda apoiada", r["Ry_ap"], "kN/m")
    if r["Ry_eng"] is not None: lin("Ry' em borda engastada", r["Ry_eng"], "kN/m")
    lin("Rx crítico", r["Rx"], "kN/m"); lin("Ry crítico", r["Ry"], "kN/m")

    cab("7. ARMADURAS")
    lin("rho_min", r["rho_m"], "%")
    lin("As_min base=rho_min*b*h", r["As_min"], "cm²/m")
    lin("As_min positiva 2 dir=0,67 As_min", r["As_min_2dir"], "cm²/m")
    lin("s_max=min(2h;20cm)", r["s_max"], "cm")
    lin("limite de dutilidade x/d", r["xi_lim"])
    if r["Mx_pos"] > 0: lin("x/d X+", r["xid_xp"])
    if r["My_pos"] > 0: lin("x/d Y+", r["xid_yp"])
    if r["Mx_neg"] > 0: lin("x/d X-", r["xid_xn"])
    if r["My_neg"] > 0: lin("x/d Y-", r["xid_yn"])

    def arm(lbl, As_calc, As_req, As_for, n, s):
        print(f"\n  {lbl}")
        lin("As calculada", As_calc, "cm²/m"); lin("As requerida c/ mínimo", As_req, "cm²/m")
        lin("As fornecida", As_for, "cm²/m"); lin("n barras/m", n, "barras")
        lin("espaçamento", s, "cm")
        ok_nok(s <= r["s_max"], "espaçamento atende ao máximo", "espaçamento NÃO atende")

    arm("X POSITIVA", r["As_xp_calc"], r["As_xp"], r["Asf_xp"], r["n_xp"], r["s_xp"])
    arm("Y POSITIVA", r["As_yp_calc"], r["As_yp"], r["Asf_yp"], r["n_yp"], r["s_yp"])
    if r["As_xn"]: arm("X NEGATIVA", r["As_xn_calc"], r["As_xn"], r["Asf_xn"], r["n_xn"], r["s_xn"])
    if r["As_yn"]: arm("Y NEGATIVA", r["As_yn_calc"], r["As_yn"], r["Asf_yn"], r["n_yn"], r["s_yn"])

    cab("8. FLECHA — ESTÁDIO I/II + RIGIDEZ EQUIVALENTE")
    lin("Mr (momento de fissuração)", r["Mr"], "kNm/m")
    lin(f"Ma raro crítico (dir. {r['dir_serv']})", r["Ma"], "kNm/m")
    print(f"  Estádio adotado: {r['estadio']}")
    lin("Ic", r["Ic"], "m⁴/m"); lin("Ieq", r["Ieq"], "m⁴/m")
    lin("flecha imediata quase permanente", r["f_qp"]*100, "cm")
    lin("flecha imediata carga variável", r["f_q"]*100, "cm")
    lin("alpha_f", r["alpha_f"])
    lin("flecha total diferida", r["f_total"]*100, "cm")
    lin("limite l/250", r["lim_250"]*100, "cm"); lin("limite l/350", r["lim_350"]*100, "cm")
    ok_nok(r["f_total"] <= r["lim_250"], "flecha total atende l/250", "flecha total NÃO atende l/250")
    ok_nok(r["f_q"] <= r["lim_350"], "parcela variável atende l/350", "parcela variável NÃO atende l/350")
    print("  Nota: não foi aplicada uma verificação genérica l/500; esse limite depende do efeito específico.")

    cab("9. CISALHAMENTO")
    print("  Direção x")
    lin("Vsd,x aprox. na seção a d da face", r["Vsd_x"], "kN/m")
    lin("VRd1,x", r["VRd1_x"], "kN/m"); lin("rho1,x", r["rho1_x"]); lin("k", r["k_cis_x"])
    ok_nok(r["cis_ok_x"], "cisalhamento em x atende", "cisalhamento em x NÃO atende")
    print("  Direção y")
    lin("Vsd,y aprox. na seção a d da face", r["Vsd_y"], "kN/m")
    lin("VRd1,y", r["VRd1_y"], "kN/m"); lin("rho1,y", r["rho1_y"]); lin("k", r["k_cis_y"])
    ok_nok(r["cis_ok_y"], "cisalhamento em y atende", "cisalhamento em y NÃO atende")
    print("  Nota: sem modelagem explícita da ancoragem, adotou-se k=1,0 de forma conservadora.")
    print("  Nota: como a largura do apoio não é entrada, Vsd usa aproximação R - p*d.")

    cab("10. RESUMO")
    print(f"  h={d['h']*100:.1f} cm | {phi_s}")
    print(f"  X+: {r['Asf_xp']:.3f} cm²/m -> {phi_s} c/{r['s_xp']:.1f} cm")
    print(f"  Y+: {r['Asf_yp']:.3f} cm²/m -> {phi_s} c/{r['s_yp']:.1f} cm")
    if r["Asf_xn"]: print(f"  X-: {r['Asf_xn']:.3f} cm²/m -> {phi_s} c/{r['s_xn']:.1f} cm")
    if r["Asf_yn"]: print(f"  Y-: {r['Asf_yn']:.3f} cm²/m -> {phi_s} c/{r['s_yn']:.1f} cm")
    print(f"  Flecha total={r['f_total']*100:.3f} cm (l/250={r['lim_250']*100:.3f} cm)")
    sep(); print()

def montar_dados(v: dict) -> dict:
    lx, ly = v["lx"], v["ly"]
    if lx <= 0 or ly <= 0:
        raise ValueError("Os vãos devem ser positivos.")
    if ly < lx:
        lx, ly = ly, lx
    if ly / lx > 2.0:
        raise ValueError("lambda > 2,0: laje armada em uma direção. Fora do escopo desta versão.")

    caso = int(v["caso"])
    if caso not in range(1, 7):
        raise ValueError("Casos 7–9 estão bloqueados nesta versão.")

    caa = v["caa"]
    cob_nbr = COB_NOMINAL[caa]
    cob = v["cob"] or cob_nbr          # 0 = usar o nominal
    if cob < cob_nbr:
        raise ValueError(f"Cobrimento menor que o nominal de {cob_nbr} mm para CAA {caa}.")

    fck, phi = v["fck"], v["phi"]
    if not (20 <= fck <= 40):
        raise ValueError("Use 20 <= fck <= 40 MPa nesta versão.")
    if fck < FCK_MIN_CAA[caa]:
        raise ValueError(f"Para CAA {caa}, adote no mínimo C{FCK_MIN_CAA[caa]}.")
    if phi <= 0 or cob < phi:
        raise ValueError("Diâmetro inválido ou maior que o cobrimento.")

    agregado, alpha_E = AGREGADOS[v["agregado"]]
    if not (0 <= v["psi2"] <= 1):
        raise ValueError("psi2 deve estar entre 0 e 1.")

    tipo = v["tipo"]
    _, h_est, _, _ = estimar_h_bastos(lx, ly, caso, cob/1000, phi/1000)
    h_min = altura_minima(tipo)
    h = v["h"] or max(h_est, h_min)    # 0 = automático
    if h < h_min:
        raise ValueError(f"h menor que o mínimo de {h_min*100:.1f} cm.")
    if phi/1000 > h/8:
        raise ValueError(f"phi excede h/8 = {h*1000/8:.1f} mm.")
    if v["tinf"] < v["t0"]:
        raise ValueError("O tempo final deve ser >= t0.")

    return dict(
        lx=lx, ly=ly, caso=caso, tipo=tipo, caa=caa, cob=cob, cob_nbr=cob_nbr,
        fck=fck, fyk=v["fyk"], phi=phi, agregado=agregado, alpha_E=alpha_E,
        gc=v["gc"], g_contrapiso=v["g_contrapiso"], g_revest_inf=v["g_revest_inf"],
        g_piso=v["g_piso"], g_paredes=v["g_paredes"], g_outros=v["g_outros"],
        q=v["q"], psi2=v["psi2"], h=h, h_min=h_min, h_est=h_est,
        t0=v["t0"], tinf=v["tinf"],
    )