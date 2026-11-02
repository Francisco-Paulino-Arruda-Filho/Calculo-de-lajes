# PERFIL ACADÊMICO DE ENSAIO: piso não em balanço, CA-50, agregado granito/gnaisse,
# carregamento global adicional 1,28 kN/m² e q=1,50 kN/m².
# NÃO USAR COMO DIMENSIONAMENTO FINAL DE OBRAS: cargas, tipo de uso, agregado,
# idade de carregamento e materiais precisam ser definidos para cada projeto.
# Verificações do módulo 1D (flecha/fissuração) são preliminares.

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

MOMENTOS = {1: [[1.0, 4.41, 4.41, 0, 0], [1.05, 4.8, 4.45, 0, 0], [1.1, 5.18, 4.49, 0, 0], [1.15, 5.56, 4.49, 0, 0], [1.2, 5.9, 4.48, 0, 0], [1.25, 6.27, 4.45, 0, 0], [1.3, 6.6, 4.42, 0, 0], [1.35, 6.93, 4.37, 0, 0], [1.4, 7.25, 4.33, 0, 0], [1.45, 7.55, 4.3, 0, 0], [1.5, 7.86, 4.25, 0, 0], [1.55, 8.12, 4.2, 0, 0], [1.6, 8.34, 3.14, 0, 0], [1.65, 8.62, 4.07, 0, 0], [1.7, 8.86, 4.0, 0, 0], [1.75, 9.06, 3.96, 0, 0], [1.8, 9.27, 3.91, 0, 0], [1.85, 9.45, 3.83, 0, 0], [1.9, 9.63, 3.75, 0, 0], [1.95, 9.77, 3.71, 0, 0], [2.0, 10.0, 3.64, 0, 0]], 2: [[1.0, 3.07, 3.94, 8.52, 0], [1.05, 3.42, 3.78, 8.79, 0], [1.1, 3.77, 3.9, 9.18, 0], [1.15, 4.14, 3.97, 9.53, 0], [1.2, 4.51, 4.05, 9.88, 0], [1.25, 4.88, 4.1, 10.16, 0], [1.3, 5.25, 4.15, 10.41, 0], [1.35, 5.6, 4.18, 10.64, 0], [1.4, 5.95, 4.21, 10.86, 0], [1.45, 6.27, 4.19, 11.05, 0], [1.5, 6.6, 4.18, 11.23, 0], [1.55, 6.9, 4.17, 11.39, 0], [1.6, 7.21, 4.14, 11.55, 0], [1.65, 7.42, 4.12, 11.67, 0], [1.7, 7.62, 4.09, 11.79, 0], [1.75, 7.66, 4.05, 11.88, 0], [1.8, 7.69, 3.99, 11.96, 0], [1.85, 8.22, 3.97, 12.03, 0], [1.9, 8.74, 3.94, 12.14, 0], [1.95, 8.97, 3.88, 12.17, 0], [2.0, 9.18, 3.8, 12.2, 0]], 3: [[1.0, 3.94, 3.07, 0, 8.52], [1.05, 4.19, 2.84, 0, 8.91], [1.1, 4.43, 2.76, 0, 9.3], [1.15, 4.64, 2.68, 0, 9.63], [1.2, 4.85, 2.59, 0, 9.95], [1.25, 5.03, 2.51, 0, 10.22], [1.3, 5.2, 2.42, 0, 10.48], [1.35, 5.36, 2.34, 0, 10.71], [1.4, 5.51, 2.25, 0, 10.92], [1.45, 5.64, 2.19, 0, 11.1], [1.5, 5.77, 2.12, 0, 11.27], [1.55, 5.87, 2.04, 0, 11.42], [1.6, 5.98, 1.95, 0, 11.55], [1.65, 6.07, 1.87, 0, 11.67], [1.7, 6.16, 1.79, 0, 11.8], [1.75, 6.24, 1.74, 0, 11.92], [1.8, 6.31, 1.68, 0, 12.04], [1.85, 6.38, 1.64, 0, 12.14], [1.9, 6.43, 1.59, 0, 12.24], [1.95, 6.47, 1.54, 0, 12.29], [2.0, 6.51, 1.48, 0, 12.34]], 4: [[1.0, 2.81, 2.81, 6.99, 6.99], [1.05, 3.05, 2.81, 7.43, 7.18], [1.1, 3.3, 2.81, 7.87, 7.36], [1.15, 3.53, 2.8, 8.28, 7.5], [1.2, 3.76, 2.79, 8.69, 7.63], [1.25, 3.96, 2.74, 9.03, 7.72], [1.3, 4.16, 2.69, 9.37, 7.81], [1.35, 4.33, 2.65, 9.65, 7.88], [1.4, 4.51, 2.6, 9.93, 7.94], [1.45, 4.66, 2.55, 10.41, 8.0], [1.5, 4.81, 2.47, 10.62, 8.06], [1.55, 4.93, 2.39, 10.82, 8.09], [1.6, 5.06, 2.31, 10.99, 8.12], [1.65, 5.16, 2.24, 11.16, 8.14], [1.7, 5.27, 2.16, 11.3, 8.15], [1.75, 5.36, 2.11, 11.43, 8.16], [1.8, 5.45, 2.04, 11.55, 8.17], [1.85, 5.53, 1.99, 11.57, 8.17], [1.9, 5.6, 1.93, 11.67, 8.18], [1.95, 5.67, 1.91, 11.78, 8.19], [2.0, 5.74, 1.88, 11.89, 8.2]], 5: [[1.0, 2.15, 3.17, 6.99, 0], [1.05, 2.47, 3.32, 7.43, 0], [1.1, 2.78, 3.47, 7.87, 0], [1.15, 3.08, 3.58, 8.26, 0], [1.2, 3.38, 3.7, 8.65, 0], [1.25, 3.79, 3.8, 9.03, 0], [1.3, 4.15, 3.9, 9.33, 0], [1.35, 4.5, 3.96, 9.69, 0], [1.4, 4.85, 4.03, 10.0, 0], [1.45, 5.19, 4.09, 10.25, 0], [1.5, 5.53, 4.14, 10.49, 0], [1.55, 5.86, 4.16, 10.7, 0], [1.6, 6.18, 4.17, 10.91, 0], [1.65, 6.48, 4.14, 11.08, 0], [1.7, 6.81, 4.12, 11.24, 0], [1.75, 7.11, 4.12, 11.39, 0], [1.8, 7.41, 4.1, 11.43, 0], [1.85, 7.68, 4.08, 11.65, 0], [1.9, 7.95, 4.04, 11.77, 0], [1.95, 8.21, 3.99, 11.83, 0], [2.0, 8.47, 3.92, 11.88, 0]], 6: [[1.0, 3.17, 2.15, 0, 6.99], [1.05, 3.29, 2.07, 0, 7.2], [1.1, 3.42, 1.99, 0, 7.41], [1.15, 3.52, 1.89, 0, 7.56], [1.2, 3.63, 1.8, 0, 7.7], [1.25, 3.71, 1.74, 0, 7.82], [1.3, 3.79, 1.67, 0, 7.93], [1.35, 3.84, 1.59, 0, 8.02], [1.4, 3.9, 1.52, 0, 8.11], [1.45, 3.94, 1.45, 0, 8.13], [1.5, 3.99, 1.38, 0, 8.15], [1.55, 4.03, 1.34, 0, 8.2], [1.6, 4.06, 1.28, 0, 8.25], [1.65, 4.09, 1.23, 0, 8.28], [1.7, 4.12, 1.18, 0, 8.3], [1.75, 4.14, 1.15, 0, 8.31], [1.8, 4.15, 1.11, 0, 8.32], [1.85, 4.16, 1.08, 0, 8.33], [1.9, 4.17, 1.04, 0, 8.33], [1.95, 4.17, 1.01, 0, 8.33], [2.0, 4.18, 0.97, 0, 8.33]], 7: [[1.0, 2.13, 2.6, 5.46, 6.17], [1.05, 2.38, 2.66, 5.98, 6.46], [1.1, 2.63, 2.71, 6.5, 6.75], [1.15, 2.87, 2.75, 7.11, 6.97], [1.2, 3.11, 2.78, 7.72, 7.19], [1.25, 3.43, 2.79, 8.81, 7.36], [1.3, 3.56, 2.77, 8.59, 7.51], [1.35, 3.76, 2.74, 8.74, 7.63], [1.4, 3.96, 2.71, 8.88, 7.74], [1.45, 4.15, 2.67, 9.16, 7.83], [1.5, 4.32, 2.63, 9.44, 7.91], [1.55, 4.48, 2.6, 9.68, 7.98], [1.6, 4.63, 2.55, 9.91, 8.02], [1.65, 4.78, 2.5, 10.13, 8.03], [1.7, 4.92, 2.45, 10.34, 8.1], [1.75, 5.04, 2.39, 10.53, 8.13], [1.8, 5.17, 2.32, 10.71, 8.17], [1.85, 5.26, 2.27, 10.88, 8.16], [1.9, 5.36, 2.22, 11.04, 8.14], [1.95, 5.45, 2.14, 11.2, 8.13], [2.0, 5.55, 2.07, 11.35, 8.12]], 8: [[1.0, 2.6, 2.13, 6.17, 5.46], [1.05, 2.78, 2.09, 6.47, 5.56], [1.1, 2.95, 2.04, 6.76, 5.65], [1.15, 3.09, 1.98, 6.99, 5.7], [1.2, 3.23, 1.92, 7.22, 5.75], [1.25, 3.34, 1.85, 7.4, 5.75], [1.3, 3.46, 1.78, 7.57, 5.76], [1.35, 3.55, 1.72, 7.7, 5.75], [1.4, 3.64, 1.64, 7.82, 5.74], [1.45, 3.71, 1.59, 7.91, 5.73], [1.5, 3.78, 1.53, 8.0, 5.72], [1.55, 3.84, 1.47, 8.07, 5.69], [1.6, 3.89, 1.42, 8.14, 5.66], [1.65, 3.94, 1.37, 8.2, 5.62], [1.7, 3.98, 1.32, 8.25, 5.58], [1.75, 4.01, 1.27, 8.3, 5.56], [1.8, 4.04, 1.2, 8.34, 5.54], [1.85, 4.07, 1.17, 8.38, 5.55], [1.9, 4.1, 1.14, 8.42, 5.56], [1.95, 4.11, 1.11, 8.45, 5.6], [2.0, 4.13, 1.08, 8.47, 5.64]], 9: [[1.0, 2.11, 2.11, 5.15, 5.15], [1.05, 2.31, 2.1, 5.5, 5.29], [1.1, 2.5, 2.09, 5.85, 5.43], [1.15, 2.73, 2.06, 6.14, 5.51], [1.2, 2.94, 2.02, 6.43, 5.59], [1.25, 3.04, 1.97, 6.67, 5.64], [1.3, 3.13, 1.91, 6.9, 5.68], [1.35, 3.25, 1.86, 7.09, 5.69], [1.4, 3.38, 1.81, 7.28, 5.7], [1.45, 3.48, 1.73, 7.43, 5.71], [1.5, 3.58, 1.66, 7.57, 5.72], [1.55, 3.66, 1.6, 7.68, 5.72], [1.6, 3.73, 1.54, 7.79, 5.72], [1.65, 3.8, 1.47, 7.88, 5.72], [1.7, 3.86, 1.4, 7.97, 5.72], [1.75, 3.91, 1.36, 8.05, 5.72], [1.8, 3.95, 1.32, 8.12, 5.72], [1.85, 3.98, 1.26, 8.18, 5.72], [1.9, 4.01, 1.21, 8.24, 5.72], [1.95, 4.04, 1.19, 8.29, 5.72], [2.0, 4.07, 1.16, 8.33, 5.72]]}


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
        [1.00,1.83,3.17,1.83,3.17],
        [1.05,1.92,3.32,1.83,3.17],
        [1.10,2.00,3.46,1.83,3.17],
        [1.15,2.07,3.58,1.83,3.17],
        [1.20,2.14,3.70,1.83,3.17],
        [1.25,2.20,3.80,1.83,3.17],
        [1.30,2.25,3.90,1.83,3.17],
        [1.35,2.30,3.99,1.83,3.17],
        [1.40,2.35,4.08,1.83,3.17],
        [1.45,2.40,4.15,1.83,3.17],
        [1.50,2.44,4.23,1.83,3.17],
        [1.55,2.48,4.29,1.83,3.17],
        [1.60,2.52,4.36,1.83,3.17],
        [1.65,2.55,4.42,1.83,3.17],
        [1.70,2.58,4.48,1.83,3.17],
        [1.75,2.61,4.53,1.83,3.17],
        [1.80,2.64,4.58,1.83,3.17],
        [1.85,2.67,4.63,1.83,3.17],
        [1.90,2.70,4.67,1.83,3.17],
        [1.95,2.72,4.71,1.83,3.17],
        [2.00,2.75,4.75,1.83,3.17],
    ],
    5: [
        [1.00,1.44,3.56],
        [1.05,1.52,3.66],
        [1.10,1.59,3.75],
        [1.15,1.66,3.84],
        [1.20,1.73,3.92],
        [1.25,1.80,3.99],
        [1.30,1.88,4.06],
        [1.35,1.95,4.12],
        [1.40,2.02,4.17],
        [1.45,2.09,4.22],
        [1.50,2.17,4.25],
        [1.55,2.24,4.28],
        [1.60,2.31,4.30],
        [1.65,2.38,4.32],
        [1.70,2.45,4.33],
        [1.75,2.53,4.33],
        [1.80,2.59,4.33],
        [1.85,2.66,4.33],
        [1.90,2.72,4.33],
        [1.95,2.78,4.33],
        [2.00,2.84,4.33],
    ],
    6: [
        [1.00,3.56,1.44],
        [1.05,3.63,1.44],
        [1.10,3.69,1.44],
        [1.15,3.74,1.44],
        [1.20,3.80,1.44],
        [1.25,3.85,1.44],
        [1.30,3.89,1.44],
        [1.35,3.93,1.44],
        [1.40,3.97,1.44],
        [1.45,4.00,1.44],
        [1.50,4.04,1.44],
        [1.55,4.07,1.44],
        [1.60,4.10,1.44],
        [1.65,4.13,1.44],
        [1.70,4.15,1.44],
        [1.75,4.17,1.44],
        [1.80,4.20,1.44],
        [1.85,4.22,1.44],
        [1.90,4.24,1.44],
        [1.95,4.26,1.44],
        [2.00,4.28,1.44],
    ],
}


# Quadro 7.10: reações dos casos 7 a 9.
REACOES.update({7: [[1.0, 1.44, 2.5, 3.03], [1.05, 1.52, 2.63, 3.08], [1.1, 1.59, 2.75, 3.11], [1.15, 1.66, 2.88, 3.14], [1.2, 1.73, 3.0, 3.16], [1.25, 1.8, 3.13, 3.17], [1.3, 1.88, 3.25, 3.17], [1.35, 1.94, 3.36, 3.17], [1.4, 2.0, 3.47, 3.17], [1.45, 2.06, 3.57, 3.17], [1.5, 2.11, 3.66, 3.17], [1.55, 2.16, 3.75, 3.17], [1.6, 2.21, 3.83, 3.17], [1.65, 2.25, 3.9, 3.17], [1.7, 2.3, 3.98, 3.17], [1.75, 2.33, 4.04, 3.17], [1.8, 2.37, 4.11, 3.17], [1.85, 2.4, 4.17, 3.17], [1.9, 2.44, 4.21, 3.17], [1.95, 2.47, 4.28, 3.17], [2.0, 2.5, 4.33, 3.17]], 8: [[1.0, 3.03, 3.03, 1.44, 2.5], [1.05, 3.08, 3.12, 1.44, 2.5], [1.1, 3.11, 3.21, 1.44, 2.5], [1.15, 3.14, 3.29, 1.44, 2.5], [1.2, 3.16, 3.36, 1.44, 2.5], [1.25, 3.17, 3.42, 1.44, 2.5], [1.3, 3.17, 3.48, 1.44, 2.5], [1.35, 3.17, 3.54, 1.44, 2.5], [1.4, 3.17, 3.59, 1.44, 2.5], [1.45, 3.17, 3.64, 1.44, 2.5], [1.5, 3.17, 3.69, 1.44, 2.5], [1.55, 3.17, 3.73, 1.44, 2.5], [1.6, 3.17, 3.77, 1.44, 2.5], [1.65, 3.17, 3.81, 1.44, 2.5], [1.7, 3.17, 3.84, 1.44, 2.5], [1.75, 3.17, 3.87, 1.44, 2.5], [1.8, 3.17, 3.9, 1.44, 2.5], [1.85, 3.17, 3.93, 1.44, 2.5], [1.9, 3.17, 3.96, 1.44, 2.5], [1.95, 3.17, 3.99, 1.44, 2.5], [2.0, 3.17, 4.01, 1.44, 2.5]], 9: [[1.0, 2.5, 2.5], [1.05, 2.62, 2.5], [1.1, 2.73, 2.5], [1.15, 2.83, 2.5], [1.2, 2.92, 2.5], [1.25, 3.0, 2.5], [1.3, 3.08, 2.5], [1.35, 3.15, 2.5], [1.4, 3.21, 2.5], [1.45, 3.28, 2.5], [1.5, 3.33, 2.5], [1.55, 3.39, 2.5], [1.6, 3.44, 2.5], [1.65, 3.48, 2.5], [1.7, 3.53, 2.5], [1.75, 3.57, 2.5], [1.8, 3.61, 2.5], [1.85, 3.65, 2.5], [1.9, 3.68, 2.5], [1.95, 3.72, 2.5], [2.0, 3.75, 2.5]]})

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
    2: "1 borda engastada paralela a ly; demais apoiadas",
    3: "1 borda engastada paralela a lx; demais apoiadas",
    4: "2 bordas adjacentes engastadas; demais apoiadas",
    5: "2 bordas opostas engastadas paralelas a ly; demais apoiadas",
    6: "2 bordas opostas engastadas paralelas a lx; demais apoiadas",
    7: "3 bordas engastadas; borda apoiada paralela a ly",
    8: "3 bordas engastadas; borda apoiada paralela a lx",
    9: "4 bordas engastadas",
}

  
# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                          FUNÇÕES AUXILIARES                                  ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# Escopo desta versão:
# - lajes maciças retangulares armadas em DUAS direções (lambda <= 2,0);
# - casos 1 a 9 das tabelas de Carvalho & Figueiredo (quadros 7.2 a 7.5 e 7.8 a 7.10);
# - concreto C20 a C40 nesta revisão (para evitar extrapolar o bloco de tensões sem
#   implementar integralmente os parâmetros adicionais da NBR 6118:2026 para C45-C90).
# Coeficientes transcritos e conferidos por amostras; validar resultados antes de uso profissional.

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
    """Coeficientes por tipo de borda, quadros 7.8 a 7.10 (Carvalho e Figueiredo Filho, 2014).

    kx/kxp: reações em bordas perpendiculares ao eixo x (apoiada/engastada).
    ky/kyp: reações em bordas perpendiculares ao eixo y (apoiada/engastada).
    """
    vals = interpolar(REACOES[caso], lam)
    if caso == 1:
        return {"kx": vals[0], "ky": vals[1]}
    if caso == 2:
        # Duas bordas x apoiadas; uma borda y apoiada e outra engastada.
        tabela_extra = [[1.00 + 0.05*i, v] for i, v in enumerate(_KYP_CASO2)]
        return {"kx": vals[0], "ky": vals[1], "kyp": interpolar(tabela_extra, lam, col=0)}
    if caso == 3:
        # Uma borda x apoiada e outra engastada; duas bordas y apoiadas.
        return {"kx": vals[0], "kxp": vals[1], "ky": 1.83}
    if caso == 4:
        return {"kx": vals[0], "kxp": vals[1], "ky": 1.83, "kyp": 3.17}
    if caso == 5:
        return {"kxp": vals[0], "ky": vals[1]}
    if caso == 6:
        return {"kx": vals[0], "kyp": vals[1]}
    if caso == 7:
        return {"kx": vals[0], "kxp": vals[1], "kyp": vals[2]}
    if caso == 8:
        return {"kxp": vals[1], "ky": vals[2], "kyp": vals[3]}
    if caso == 9:
        return {"kxp": vals[0], "kyp": vals[1]}
    raise ValueError("Caso de vinculação inválido (1 a 9).")


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
    print(f"  {label:<52} {val:>10.2f}  {un}")
def ok_nok(cond, msg_ok, msg_no):
    print(f"  {'✔' if cond else '✘'}  {msg_ok if cond else msg_no}")


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                            ENTRADA DE DADOS                                  ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# ============================================================================
# API PARA A INTERFACE GRAFICA — NAO ALTERAR AS REGRAS DE CLASSIFICACAO
# ============================================================================
# A interface deve chamar classificar_laje(lado_a, lado_b) quando o usuario
# terminar de informar as duas dimensoes. A classificacao nao depende da
# selecao do caso de vinculacao. Os lados sao ordenados automaticamente:
# lx = menor vao, ly = maior vao, lambda = ly/lx.
# lambda <= 2.0: laje bidirecional -> apresentar casos 1 a 9 e imagem 2D.
# lambda >  2.0: laje unidirecional -> apresentar casos 1 a 3 e imagem 1D.
# ATENCAO: os tres casos 1D sao APOIADA-APOIADA, ENGASTADA-APOIADA,
# ENGASTADA-ENGASTADA NA DIRECAO DO MENOR VAO. NAO representam 3 casos
# numericamente equivalentes aos casos 1, 3 e 5 do modulo bidirecional.
# Para calculo 1D: d['unidirecional']=True; d['apoio_1d']=caso_1d;
# d['caso']=1 (marcador apenas para estimativa de espessura).
# Para calculo 2D: d['unidirecional']=False; d['caso']=caso_2d;
# d['apoio_1d']=None.
# Ao trocar as dimensoes, limpar a selecao anterior de vinculacao.

CASOS_UNIDIRECIONAIS = {
    1: 'Apoiada nas duas extremidades da faixa (A-A)',
    2: 'Engastada em uma extremidade e apoiada na outra (E-A)',
    3: 'Engastada nas duas extremidades da faixa (E-E)',
}


def classificar_laje(lado_a, lado_b):
    """Retorna informacoes prontas para a GUI; nao executa dimensionamento."""
    a, b = float(lado_a), float(lado_b)
    if not (math.isfinite(a) and math.isfinite(b) and a > 0 and b > 0):
        raise ValueError('Informe dois vaos positivos e finitos, em metros.')
    lx, ly = sorted((a, b))
    lam = ly / lx
    uni = lam > 2.0
    return {
        'lx': lx, 'ly': ly, 'lambda': lam,
        'unidirecional': uni,
        'modelo': 'unidirecional' if uni else 'bidirecional',
        'titulo': 'LAJE UNIDIRECIONAL' if uni else 'LAJE BIDIRECIONAL',
        'casos': dict(CASOS_UNIDIRECIONAIS) if uni else dict(DESCRICAO),
        'imagem': 'vinculacoes_unidirecionais_precisas.jpeg' if uni else 'vinculacoes_bidirecionais_precisas.jpeg',
        'nota': ('Os apoios se referem a uma faixa de 1 m na direcao do menor vao.'
                 if uni else 'Casos 1 a 9 segundo as tabelas cadastradas.'),
    }


def validar_entrada_modelo(d):
    """Protege a API e a futura interface contra parâmetros fisicamente inválidos.

    Não altera o perfil de cargas fixas definido no terminal; somente rejeita
    valores inconsistentes, inclusive quando fornecidos programaticamente.
    """
    campos_positivos = ('lx','ly','h','phi','fck','fyk','gc','alpha_E')
    campos_nao_negativos = ('q','cob','g_contrapiso','g_revest_inf',
                           'g_piso','g_paredes','g_outros','t0','tinf')
    for nome in campos_positivos + campos_nao_negativos + ('psi2',):
        try:
            v = float(d[nome])
        except (KeyError,TypeError,ValueError) as exc:
            raise ValueError(f"Parâmetro {nome} ausente ou não numérico.") from exc
        if not math.isfinite(v):
            raise ValueError(f"Parâmetro {nome} deve ser finito.")
        if nome in campos_positivos and v <= 0:
            raise ValueError(f"Parâmetro {nome} deve ser positivo.")
        if nome in campos_nao_negativos and v < 0:
            raise ValueError(f"Parâmetro {nome} não pode ser negativo.")
    if not 0 <= d['psi2'] <= 1:
        raise ValueError('psi2 deve estar entre 0 e 1.')
    if d['tinf'] < d['t0']:
        raise ValueError('A idade final não pode anteceder a idade inicial de carregamento.')
    if d.get('caa') not in COB_NOMINAL:
        raise ValueError('Classe de agressividade ambiental inválida.')
    if d['h'] < altura_minima(d['tipo']):
        raise ValueError('Espessura abaixo do mínimo da categoria de laje.')
    if d['phi']/1000 > d['h']/8:
        raise ValueError('Bitola superior a h/8.')
    if d['cob'] < d['phi']:
        raise ValueError('Cobrimento nominal inferior ao diâmetro da barra.')
    if d['h']*1000 <= 2*d['cob']+d['phi']:
        raise ValueError('Espessura insuficiente para cobrimentos e armadura.')


def executar_modelo(dados):
    """Ponto unico de entrada para calculo; seleciona o modulo adequado."""
    validar_entrada_modelo(dados)
    info = classificar_laje(dados['lx'], dados['ly'])
    d = dict(dados)
    d['lx'], d['ly'] = info['lx'], info['ly']
    d['unidirecional'] = info['unidirecional']
    if info['unidirecional']:
        apoio = d.get('apoio_1d')
        if apoio not in CASOS_UNIDIRECIONAIS:
            raise ValueError('Escolha um dos 3 apoios unidirecionais.')
        d['caso'] = 1
        return d, auditar_limites_normativos(d, avaliar_detalhamento(d, anexar_verificacoes_complementares(d, calcular_unidirecional(d))))
    caso = d.get('caso')
    if caso not in DESCRICAO:
        raise ValueError('Escolha um dos 9 casos bidirecionais.')
    d['apoio_1d'] = None
    return d, auditar_limites_normativos(d, avaliar_detalhamento(d, anexar_verificacoes_complementares(d, calcular(d))))


def selecionar_barras(As_cm2_m, phi_mm, h_m, cob_mm, agregado_max_mm=19.0, s_max_cm=None):
    """Escolha de barras por metro com controle de espaçamento e alerta.

    Para faixas de laje, o espaçamento livre é avaliado como s-phi.
    Critério geométrico conservador adotado: >= max(20 mm, phi, 1.2*dmax).
    A norma e as condições de execução devem ser conferidas para projeto real.
    """
    if As_cm2_m <= 0:
        return {'n':0,'s_cm':0.,'As_fornecida':0.,'status':'NÃO APLICÁVEL','avisos':[]}
    if not all(math.isfinite(float(v)) for v in (As_cm2_m,phi_mm,h_m,cob_mm)):
        raise ValueError('Dados não finitos no detalhamento.')
    if phi_mm <= 0 or h_m <= 0 or cob_mm < 0:
        raise ValueError('Geometria inválida para detalhamento.')
    Ab = math.pi*(phi_mm/10)**2/4  # cm²/barra
    smax = min(20.,2*h_m*100) if s_max_cm is None else float(s_max_cm)
    if smax <= 0: raise ValueError('Espaçamento máximo inválido.')
    n = max(math.ceil(As_cm2_m/Ab - 1e-10), math.ceil(100/smax))
    s = 100/n
    livre_mm = s*10 - phi_mm
    livre_min_mm = max(20., phi_mm, 1.2*agregado_max_mm)
    avisos=[]
    if livre_mm < livre_min_mm - 1e-9:
        alternativas=[]
        for diam in (6.3,8.,10.,12.5,16.,20.,25.):
            if diam <= phi_mm or diam > 1000*h_m/8 or diam > cob_mm: continue
            ab_alt=math.pi*(diam/10)**2/4
            n_alt=max(math.ceil(As_cm2_m/ab_alt-1e-10),math.ceil(100/smax))
            livre_alt=1000/n_alt-diam
            if livre_alt >= max(20.,diam,1.2*agregado_max_mm):
                alternativas.append(f'barra de diâmetro {diam/10:.2f} cm a cada {100/n_alt:.2f} cm')
        sugestao=(' Alternativas geométricas preliminares: '+', '.join(alternativas[:3])+'.') if alternativas else ' Sem alternativa de uma camada entre as bitolas ensaiadas: rever espessura, cargas ou solução estrutural.'
        avisos.append(f'Espaçamento livre {livre_mm/10:.2f} cm inferior ao mínimo geométrico adotado {livre_min_mm/10:.2f} cm.'+sugestao)
    if n > 100:
        avisos.append(f'Quantidade excessiva ({n} barras/m). NÃO aceitar automaticamente: rever geometria, cargas e bitola.')
    if phi_mm > 1000*h_m/8:
        avisos.append('Diâmetro da barra excede um oitavo da espessura da laje.')
    if cob_mm < phi_mm:
        avisos.append('Cobrimento menor que diâmetro da barra.')
    return {'n':n,'s_cm':s,'As_fornecida':n*Ab,'livre_mm':livre_mm,
            'livre_min_mm':livre_min_mm,'status':'NÃO ATENDE' if avisos else 'ATENDE (triagem geométrica)',
            'avisos':avisos}


def avaliar_detalhamento(d, r):
    """Atribui triagem geométrica às armaduras já dimensionadas, sem esconder falhas."""
    if d['unidirecional']:
        itens=[('principal_positiva',r['Aspos']),('principal_negativa',r['Asneg']),('distribuicao',r['Asdist'])]
    else:
        itens=[('x_positiva',r['As_xp']),('y_positiva',r['As_yp']),('x_negativa',r['As_xn']),('y_negativa',r['As_yn'])]
    r['detalhamento']={k:selecionar_barras(a,d['phi'],d['h'],d['cob']) for k,a in itens}
    r['detalhamento_ok']=all(v['status'] != 'NÃO ATENDE' for v in r['detalhamento'].values())
    r['detalhamento_alertas']=[f'{k}: {msg}' for k,v in r['detalhamento'].items() for msg in v['avisos']]
    return r


def imprimir_detalhamento(r):
    """Memória didática de acomodação das barras, com comprimentos em cm."""
    cab('VERIFICAÇÃO GEOMÉTRICA DO ESPAÇAMENTO DAS ARMADURAS')
    titulos = {
        'principal_positiva': 'Armadura principal — região de momento positivo',
        'principal_negativa': 'Armadura principal — região de momento negativo',
        'distribuicao': 'Armadura de distribuição',
        'x_positiva': 'Direção X — armadura positiva',
        'y_positiva': 'Direção Y — armadura positiva',
        'x_negativa': 'Direção X — armadura negativa',
        'y_negativa': 'Direção Y — armadura negativa',
    }
    grupos = [('ARMADURAS PRINCIPAIS E DE DISTRIBUIÇÃO', list(r['detalhamento']))] if 'distribuicao' in r['detalhamento'] else [
        ('ARMADURAS POSITIVAS', [k for k in r['detalhamento'] if 'positiva' in k]),
        ('ARMADURAS NEGATIVAS', [k for k in r['detalhamento'] if 'negativa' in k]),
    ]
    for titulo, chaves in grupos:
        print('\n' + titulo)
        print('-' * 70)
        for chave in chaves:
            v = r['detalhamento'][chave]
            print(f"\n  {titulos.get(chave, chave.replace('_', ' ').capitalize())}")
            print(f"    Quantidade por metro de faixa : {v['n']} barras/m")
            print(f"    Espaçamento entre eixos       : {v['s_cm']:.2f} cm")
            print(f"    Área de aço fornecida         : {v['As_fornecida']:.2f} cm²/m")
            if v['n']:
                print(f"    Espaçamento livre calculado   : {v['livre_mm']/10:.2f} cm")
                print(f"    Espaçamento livre mínimo      : {v['livre_min_mm']/10:.2f} cm")
            print(f"    Verificação geométrica        : {'ATENDE' if not v['avisos'] else 'NÃO ATENDE'}")
            for aviso in v['avisos']:
                print('    ATENÇÃO:', aviso)
    print('\n' + '-' * 70)
    print('RESULTADO GERAL DA ACOMODAÇÃO')
    print('  ' + ('ATENDE aos critérios geométricos preliminares adotados.'
                  if r.get('detalhamento_ok') else
                  'NÃO ATENDE: revisar as armaduras indicadas nos alertas.'))
    print('\nOBSERVAÇÕES')
    print('  - A quantidade é expressa por metro de largura da laje, não no painel inteiro.')
    print('  - O espaçamento livre corresponde ao espaço entre faces de barras vizinhas.')
    sep()


def calcular_unidirecional(d):
    """Faixa de 1 m, carga uniformemente distribuída, teoria elástica linear.

    Condições: A-A, E-A e E-E. Não representa balanços, torção de canto
    ou cargas concentradas.
    """
    L, h = d["lx"], d["h"]
    fck, fyk = d["fck"], d["fyk"]
    c, phi = d["cob"]/1000, d["phi"]/1000
    du = h - c - phi/2
    if du <= 0:
        raise ValueError("Altura útil não positiva.")
    g = d["gc"]*h + sum(d[k] for k in (
        "g_contrapiso", "g_revest_inf", "g_piso", "g_paredes", "g_outros"))
    q = d["q"]
    pd = 1.4*(g+q)
    pqp = g + d["psi2"]*q
    # Equilíbrio e análise elástica de uma viga prismática sob carga uniforme.
    # Para E-A: M_eng = -pL²/8, M_pos,max = 9pL²/128,
    # R_eng = 5pL/8, R_ap = 3pL/8.
    # Para E-E: M_eng = -pL²/12, M_pos,meio = pL²/24.
    apoio = d["apoio_1d"]
    if apoio == 1:
        Mpos, Mneg, Ra, Rb, kflecha = pd*L*L/8, 0., pd*L/2, pd*L/2, 5/384
    elif apoio == 2:
        Mpos, Mneg, Ra, Rb, kflecha = 9*pd*L*L/128, pd*L*L/8, 5*pd*L/8, 3*pd*L/8, 0.00542
    else:
        Mpos, Mneg, Ra, Rb, kflecha = pd*L*L/24, pd*L*L/12, pd*L/2, pd*L/2, 1/384
    fcd = fck/1.4*1000  # kN/m²
    fyd = fyk/1.15*1000
    sig = 0.85*fcd
    def flexao(M):
        if M <= 0: return 0., 0.
        # M = 0.85 fcd b (0.8x) (d - 0.4x)
        A = sig*0.8
        discr = (A*du)**2 - 2*A*0.8*M
        if discr <= 0: raise ValueError("Seção insuficiente à flexão: aumente h.")
        x = (A*du-math.sqrt(discr))/(A*0.8)
        if x/du > 0.45: raise ValueError("Limite de ductilidade x/d ultrapassado.")
        z = du - 0.4*x
        return M/(fyd*z)*1e4, x/du
    Aspos_calc, xip = flexao(Mpos)
    Asneg_calc, xin = flexao(Mneg)
    Asbase = rho_min(fck)/100*100*(h*100)
    # Adota-se mínimo integral conservador na direção principal;
    # armadura transversal de distribuição: critério preliminar conservador.
    Aspos = max(Aspos_calc, Asbase)
    Asneg = max(Asneg_calc, Asbase) if Mneg > 0 else 0.
    Asdist = max(0.20*Aspos, 0.90, 0.50*Asbase)  # NBR 6118:2026, Tabela 19.1: armadura secundária
    Ab = math.pi*d["phi"]**2/400  # cm²/barra
    def detalhar(As):
        if As <= 0: return (0, 0., 0.)
        smax = min(20., 2*h*100)
        n = max(math.ceil(As/Ab), math.ceil(100/smax))
        return n, 100/n, n*Ab
    barras = {nome: detalhar(As) for nome, As in (
        ("principal_positiva",Aspos), ("principal_negativa",Asneg),
        ("distribuicao",Asdist))}
    # ELS: rigidez equivalente da seção fissurada (modelo simplificado de Branson).
    # Emprega momento CARACTERÍSTICO (combinação rara) para verificar fissuração,
    # e combinação quase permanente para flecha de longa duração.
    _, Ecs_MPa, _ = modulos_concreto(fck, d["alpha_E"])
    Ecs = Ecs_MPa*1000.0  # kN/m²
    Es_MPa = 210000.0
    Ic = h**3/12.0  # faixa de largura b=1 m
    fctm = fctm_nbr(fck)
    Mr = 1.5*(fctm*1000.0)*Ic/(h/2.0)  # kN.m/m
    pk = g+q
    if apoio == 1:
        Ma = pk*L**2/8.0
    elif apoio == 2:
        Ma = max(pk*L**2/8.0, 9*pk*L**2/128.0)
    else:
        Ma = pk*L**2/12.0
    As_serv = barras["principal_positiva"][2]/1e4  # m²/m
    alpha_e = Es_MPa/Ecs_MPa
    if Ma <= Mr or As_serv <= 0:
        estadio, III, Ieq = "I (não fissurado)", Ic, Ic
    else:
        # Linha neutra de seção retangular fissurada, sem armadura comprimida.
        B = alpha_e*As_serv
        xII = -B + math.sqrt(B**2 + 2*B*du)
        III = xII**3/3 + alpha_e*As_serv*(du-xII)**2
        rel = min(Mr/Ma, 1.0)
        Ieq = min(Ic, rel**3*Ic + (1-rel**3)*III)
        estadio = "II / rigidez equivalente"
    rigidez_ratio = Ic/Ieq
    flecha_elastica = kflecha*pqp*L**4/(Ecs*Ic)
    flecha_imediata = flecha_elastica*rigidez_ratio
    flecha_q = kflecha*q*L**4/(Ecs*Ieq)
    xi_t0, xi_t = xi(d["t0"]), xi(d["tinf"])
    # Sem armadura comprimida: rho' = 0. Hipótese aproximada de fluência.
    alpha_f = max(0.0, xi_t-xi_t0)
    flecha_diferida = alpha_f*flecha_imediata
    flecha_final = flecha_imediata+flecha_diferida
    limite_250, limite_350 = L/250, L/350
    fctd = 0.7*fctm_nbr(fck)/1.4
    Asf = barras["principal_positiva"][2]/1e4
    rho = min(Asf/du,0.02)
    VRd = 0.25*fctd*1000*(1.2+40*rho)*du
    Vsd = max(Ra,Rb)-pd*du
    return dict(modelo="unidirecional", lam=d["ly"]/L, g=g, q=q, pd=pd,
        pqp=pqp, Mpos=Mpos, Mneg=Mneg, Ra=Ra, Rb=Rb,
        Aspos_calc=Aspos_calc, Asneg_calc=Asneg_calc,
        Aspos=Aspos, Asneg=Asneg, Asdist=Asdist, barras=barras,
        xip=xip, xin=xin, du=du, f_el=flecha_elastica,
        f_imediata=flecha_imediata, f_diferida=flecha_diferida,
        f_total=flecha_final, f_q=flecha_q,
        limite=limite_250, lim_250=limite_250, lim_350=limite_350,
        els_total_ok=flecha_final<=limite_250,
        els_q_ok=flecha_q<=limite_350,
        Mr=Mr, Ma=Ma, Ic=Ic, III=III, Ieq=Ieq, estadio=estadio,
        alpha_f=alpha_f, xi_t0=xi_t0, xi_t=xi_t,
        Vsd=Vsd, VRd=VRd, cis_ok=Vsd<=VRd)


def imprimir_unidirecional(d, r):
    """Relatório de apresentação; não altera nenhuma fórmula de cálculo."""
    apoio = {1: "Duas extremidades apoiadas", 2: "Uma engastada e outra apoiada",
             3: "Duas extremidades engastadas"}[d["apoio_1d"]]
    cab("MEMÓRIA DE CÁLCULO | LAJE MACIÇA UNIDIRECIONAL")
    print("  Método: faixa de 1,00 m, análise elástica linear")
    print(f"  Vinculação: {apoio}")

    cab("1. IDENTIFICAÇÃO, GEOMETRIA E VINCULAÇÃO")
    lin("Vão principal lx", d["lx"], "m")
    lin("Vão transversal ly", d["ly"], "m")
    lin("Relação λ = ly/lx", r["lam"])
    lin("Espessura adotada h", d["h"]*100, "cm")
    lin("Espessura mínima do perfil", d["h_min"]*100, "cm")
    lin("Cobrimento nominal", d["cob"], "mm")
    lin("Bitola selecionada", d["phi"], "mm")
    lin("Altura útil principal", r["du"]*100, "cm")

    cab("2. MATERIAIS E RESISTÊNCIAS DE CÁLCULO")
    print(f"  Classe ambiental: {d['caa']} | Agregado: {d['agregado']}")
    lin("fck do concreto", d["fck"], "MPa")
    lin("fcd = fck/1,40", d["fck"]/1.4, "MPa")
    lin("fyk do aço CA-50", d["fyk"], "MPa")
    lin("fyd = fyk/1,15", d["fyk"]/1.15, "MPa")

    cab("3. AÇÕES E COMBINAÇÕES")
    lin("Peso próprio", d["gc"]*d["h"], "kN/m²")
    lin("Demais cargas permanentes", r["g"]-d["gc"]*d["h"], "kN/m²")
    lin("Carga permanente total gk", r["g"], "kN/m²")
    lin("Carga variável qk", r["q"], "kN/m²")
    lin("ELU: pd = 1,4 (gk + qk)", r["pd"], "kN/m²")
    lin("ELS: pqp = gk + ψ₂ qk", r["pqp"], "kN/m²")

    cab("4. ANÁLISE ESTRUTURAL | ESFORÇOS")
    lin("Momento positivo de cálculo", r["Mpos"], "kN.m/m")
    lin("Momento negativo de cálculo (módulo)", r["Mneg"], "kN.m/m")
    lin("Reação no apoio A", r["Ra"], "kN/m")
    lin("Reação no apoio B", r["Rb"], "kN/m")

    cab("5. DIMENSIONAMENTO E DETALHAMENTO DAS ARMADURAS")
    lin("Taxa mínima ρₘᵢₙ", rho_min(d["fck"]), "%")
    lin("Relação ξ = x/d | momento positivo", r["xip"])
    if r["Mneg"] > 0:
        lin("Relação ξ = x/d | momento negativo", r["xin"])
    itens = (
        ("5.1 ARMADURA PRINCIPAL POSITIVA", "principal_positiva", "Aspos_calc", "Aspos"),
        ("5.2 ARMADURA PRINCIPAL NEGATIVA", "principal_negativa", "Asneg_calc", "Asneg"),
        ("5.3 ARMADURA TRANSVERSAL DE DISTRIBUIÇÃO", "distribuicao", None, "Asdist"),
    )
    for titulo, chave, calculada, requerida in itens:
        print(f"\n  {titulo}")
        if calculada:
            lin("Área calculada", r[calculada], "cm²/m")
        lin("Área adotada", r[requerida], "cm²/m")
        n, espacamento, fornecida = r["barras"][chave]
        if n:
            lin("Área fornecida", fornecida, "cm²/m")
            lin("Quantidade de barras por metro", n, "barras/m")
            lin("Espaçamento", espacamento, "cm")
            print(f"  Detalhamento: φ {d['phi']:g} mm a cada {espacamento:.2f} cm")
        else:
            print("  Sem armadura adicional solicitada neste modelo")

    cab("6. VERIFICAÇÃO SIMPLIFICADA DE CISALHAMENTO")
    lin("Solicitação cortante Vsd", r["Vsd"], "kN/m")
    lin("Resistência estimada VRd", r["VRd"], "kN/m")
    ok_nok(r["cis_ok"], "Verificação simplificada: atende", "Verificação simplificada: NÃO atende")

    cab("7. ESTADO LIMITE DE SERVIÇO | FLECHAS")
    lin("Momento de fissuração Mᵣ", r["Mr"], "kN.m/m")
    lin("Momento máximo característico Mₐ", r["Ma"], "kN.m/m")
    print(f"  Estádio da seção: {r['estadio']}")
    lin("Inércia bruta I꜀", r["Ic"], "m⁴/m")
    lin("Inércia equivalente Iₑq", r["Ieq"], "m⁴/m")
    lin("Flecha elástica bruta (referência)", r["f_el"]*100, "cm")
    lin("Flecha imediata (rigidez equivalente)", r["f_imediata"]*100, "cm")
    lin("Coeficiente diferido α𝒇", r["alpha_f"])
    lin("Flecha diferida estimada", r["f_diferida"]*100, "cm")
    lin("Flecha final estimada", r["f_total"]*100, "cm")
    lin("Limite geométrico lₓ/250", r["lim_250"]*100, "cm")
    ok_nok(r["els_total_ok"], "Flecha final atende l/250", "Flecha final NÃO atende l/250")
    lin("Flecha da parcela variável", r["f_q"]*100, "cm")
    lin("Referência lₓ/350", r["lim_350"]*100, "cm")
    ok_nok(r["els_q_ok"], "Parcela variável atende l/350", "Parcela variável NÃO atende l/350")
    print("  AVISO: ELS estimado por rigidez equivalente; não constitui análise completa")
    print("  de fissuração, efeitos de cargas sucessivas ou condições específicas de uso.")

    cab("8. QUADRO-RESUMO")
    print(f"  Modelo unidirecional | lx={d['lx']:.2f} m | ly={d['ly']:.2f} m | h={d['h']*100:.2f} cm")
    for nome, chave in (("Principal positiva", "principal_positiva"),
                        ("Principal negativa", "principal_negativa"),
                        ("Distribuição", "distribuicao")):
        n, esp, af = r["barras"][chave]
        print(f"  {nome:<25} {af:>8.3f} cm²/m | φ {d['phi']:g} c/{esp:.2f} cm" if n else f"  {nome}: não aplicável")
    print(f"  Flecha imediata={r['f_imediata']*100:.2f} cm | diferida={r['f_diferida']*100:.2f} cm")
    print(f"  Flecha final={r['f_total']*100:.2f} cm | limite l/250={r['lim_250']*100:.2f} cm")
    print("  LIMITAÇÕES: ancoragem e abertura de fissuras não são calculadas;")
    print("  avaliação completa de ELS; flechas estimadas pelo modelo simplificado.")
    print("  Uso acadêmico: conferir os resultados antes de qualquer aplicação estrutural.")
    sep()


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
    phi_s = f"φ {d['phi']:.2f} mm"
    cab("MEMÓRIA DE CÁLCULO | LAJE MACIÇA BIDIRECIONAL")
    print("  Análise por coeficientes tabelados | Carvalho & Figueiredo Filho")

    cab("1. DADOS DE ENTRADA E ESCOPO")
    lin("lx", d["lx"], "m"); lin("ly", d["ly"], "m"); lin("λ=ly/lx", r["lam"])
    print(f"  Classificação: laje armada em duas direções (λ ≤ 2,0)")
    print(f"  Caso {d['caso']}: {DESCRICAO[d['caso']]}")
    lin("h adotado", d["h"]*100, "cm"); lin("h mínimo", d["h_min"]*100, "cm")
    lin("h estimado (Bastos)", d["h_est"]*100, "cm")
    lin("cobrimento adotado", d["cob"], "mm"); lin("cobrimento Tabela 7.2", d["cob_nbr"], "mm")
    lin("fck (resistência característica)", d["fck"], "MPa"); lin("fyk (resistência característica)", d["fyk"], "MPa")
    print(f"  Agregado: {d['agregado']} (α_E={d['alpha_E']})")

    cab("2. PROPRIEDADES DOS MATERIAIS")
    lin("fcd = fck/1,40", r["fcd"], "MPa"); lin("fyd = fyk/1,15", r["fyd"], "MPa")
    lin("fctm", r["fctm"], "MPa"); lin("fctk,inf=0,7 fctm", r["fctk_inf"], "MPa")
    lin("Eci", r["Eci_MPa"], "MPa"); lin("αᵢ", r["alpha_i"])
    lin("Ecs = αᵢ · Eci", r["Ecs_MPa"], "MPa")

    cab("3. ALTURAS ÚTEIS")
    lin("dₓ positivo (camada inferior)", r["d_xp"]*100, "cm")
    lin("dᵧ positivo (2ª camada)", r["d_yp"]*100, "cm")
    lin("dₓ negativo", r["d_xn"]*100, "cm"); lin("dᵧ negativo", r["d_yn"]*100, "cm")
    lin("φ máximo=h/8", d["h"]*1000/8, "mm")

    cab("4. CARGAS E COMBINAÇÕES")
    lin("g1 peso próprio", r["g1"], "kN/m²"); lin("g2 demais permanentes", r["g2"], "kN/m²")
    lin("g total", r["g"], "kN/m²"); lin("q", d["q"], "kN/m²")
    lin("ELU normal 1,4(g+q)", r["p_elu"], "kN/m²")
    lin("ELS rara g+q", r["p_rare"], "kN/m²")
    lin("ELS quase permanente g+ψ₂ q", r["p_qp"], "kN/m²")

    cab("5. COEFICIENTES E MOMENTOS")
    lin("μₓ⁺", r["mu_xp"]); lin("μᵧ⁺", r["mu_yp"])
    if r["mu_xn"]: lin("μₓ⁻", r["mu_xn"])
    if r["mu_yn"]: lin("μᵧ⁻", r["mu_yn"])
    lin("α (coeficiente de flecha)", r["alpha"])
    lin("Mx+ ELU", r["Mx_pos"], "kNm/m"); lin("My+ ELU", r["My_pos"], "kNm/m")
    if r["Mx_neg"]: lin("Mx- ELU", r["Mx_neg"], "kNm/m")
    if r["My_neg"]: lin("My- ELU", r["My_neg"], "kNm/m")

    cab("6. REAÇÕES DE APOIO")
    if r["Rx_ap"] is not None: lin("Rx em borda apoiada", r["Rx_ap"], "kN/m")
    if r["Rx_eng"] is not None: lin("Rx' em borda engastada", r["Rx_eng"], "kN/m")
    if r["Ry_ap"] is not None: lin("Ry em borda apoiada", r["Ry_ap"], "kN/m")
    if r["Ry_eng"] is not None: lin("Ry' em borda engastada", r["Ry_eng"], "kN/m")
    lin("Rx crítico", r["Rx"], "kN/m"); lin("Ry crítico", r["Ry"], "kN/m")

    cab("7. DIMENSIONAMENTO E DETALHAMENTO DAS ARMADURAS")
    lin("ρₘᵢₙ", r["rho_m"], "%")
    lin("Aₛ,min base=ρₘᵢₙ*b*h", r["As_min"], "cm²/m")
    lin("Aₛ,min positiva 2 dir=0,67 Aₛ,min", r["As_min_2dir"], "cm²/m")
    lin("sₘₐₓ=min(2h;20cm)", r["s_max"], "cm")
    lin("limite de dutilidade ξ = x/d", r["xi_lim"])
    if r["Mx_pos"] > 0: lin("ξ = x/d X+", r["xid_xp"])
    if r["My_pos"] > 0: lin("ξ = x/d Y+", r["xid_yp"])
    if r["Mx_neg"] > 0: lin("ξ = x/d X-", r["xid_xn"])
    if r["My_neg"] > 0: lin("ξ = x/d Y-", r["xid_yn"])

    def arm(lbl, As_calc, As_req, As_for, n, s):
        print(f"\n  {lbl}")
        lin("Aₛ calculada", As_calc, "cm²/m"); lin("Aₛ requerida c/ mínimo", As_req, "cm²/m")
        lin("Aₛ fornecida", As_for, "cm²/m"); lin("n barras/m", n, "barras")
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
    lin("α𝒇", r["alpha_f"])
    lin("flecha total diferida", r["f_total"]*100, "cm")
    lin("limite l/250", r["lim_250"]*100, "cm"); lin("limite l/350", r["lim_350"]*100, "cm")
    ok_nok(r["f_total"] <= r["lim_250"], "flecha total atende l/250", "flecha total NÃO atende l/250")
    ok_nok(r["f_q"] <= r["lim_350"], "parcela variável atende l/350", "parcela variável NÃO atende l/350")
    print("  Nota: não foi aplicada uma verificação genérica l/500; esse limite depende do efeito específico.")

    cab("9. CISALHAMENTO")
    print("  Direção x")
    lin("Vsd,x aprox. na seção a d da face", r["Vsd_x"], "kN/m")
    lin("VRd1,x", r["VRd1_x"], "kN/m"); lin("ρ₁,x", r["rho1_x"]); lin("k", r["k_cis_x"])
    ok_nok(r["cis_ok_x"], "cisalhamento em x atende", "cisalhamento em x NÃO atende")
    print("  Direção y")
    lin("Vsd,y aprox. na seção a d da face", r["Vsd_y"], "kN/m")
    lin("VRd1,y", r["VRd1_y"], "kN/m"); lin("ρ₁,y", r["rho1_y"]); lin("k", r["k_cis_y"])
    ok_nok(r["cis_ok_y"], "cisalhamento em y atende", "cisalhamento em y NÃO atende")
    print("  Nota: sem modelagem explícita da ancoragem, adotou-se k=1,0 de forma conservadora.")
    print("  Nota: como a largura do apoio não é entrada, Vsd usa aproximação R - p*d.")

    cab("10. QUADRO-RESUMO")
    print(f"  h={d['h']*100:.2f} cm | {phi_s}")
    print(f"  X+: {r['Asf_xp']:.2f} cm²/m -> {phi_s} c/{r['s_xp']:.2f} cm")
    print(f"  Y+: {r['Asf_yp']:.2f} cm²/m -> {phi_s} c/{r['s_yp']:.2f} cm")
    if r["Asf_xn"]: print(f"  X-: {r['Asf_xn']:.2f} cm²/m -> {phi_s} c/{r['s_xn']:.2f} cm")
    if r["Asf_yn"]: print(f"  Y-: {r['Asf_yn']:.2f} cm²/m -> {phi_s} c/{r['s_yn']:.2f} cm")
    print(f"  Flecha imediata={r['f_qp']*100:.2f} cm | diferida={(r['f_total']-r['f_qp'])*100:.2f} cm")
    print(f"  Flecha final={r['f_total']*100:.2f} cm (l/250={r['lim_250']*100:.2f} cm)")
    print("  LIMITAÇÕES: ancoragens exigem dados adicionais;")
    print("  nem análise integral de ELS; a flecha é estimativa simplificada.")
    sep(); print()




# ============================================================================
# PADRONIZAÇÃO DAS FLECHAS - APLICÁVEL A AMBAS AS DIREÇÕES
# As verificações de serviço usam os resultados de cada modelo.
# Não confundir estimativas de pré-dimensionamento com verificação normativa.
# ============================================================================

def _status(ok):
    return "NÃO VERIFICADO" if ok is None else ("ATENDE" if ok else "NÃO ATENDE")


def anexar_verificacoes_complementares(d, r):
    """Padroniza os campos de flecha nos dois modelos."""
    if 'f_imediata' not in r and 'f_qp' in r:
        r['f_imediata'] = r['f_qp']
        r['f_diferida'] = r['f_total']-r['f_qp']
    return r


def auditar_limites_normativos(d, r):
    """Triagem explícita: NBR 6118:2026, 7.4.7, 13.2.4, 19.3.3, 20.1-20.2.

    NÃO substitui verificação de continuidade, ancoragem, aberturas,
    momentos volventes, fissuração, carregamentos e condições de contorno.
    """
    h_mm = 1000.0 * d['h']
    phi = float(d['phi'])
    cob = float(d['cob'])
    caa = d['caa']
    agregado_max = float(d.get('agregado_max_mm', 19.0))
    checks = {}
    checks['cobrimento_CAA_tabela_7_2'] = cob >= COB_NOMINAL[caa] - 1e-9
    checks['cobrimento_maior_igual_bitola'] = cob >= phi - 1e-9
    checks['agregado_dmax_menor_1_2_cobrimento'] = agregado_max <= 1.2*cob + 1e-9
    checks['bitola_maxima_h_8'] = phi <= h_mm/8 + 1e-9
    checks['espessura_minima_tipo_informado'] = d['h'] >= altura_minima(d['tipo']) - 1e-9
    checks['espessura_util_para_uma_camada'] = h_mm > 2*cob + phi
    for nome, detal in r.get('detalhamento', {}).items():
        if detal['n'] <= 0: continue
        smax = 33.0 if nome == 'distribuicao' else min(20.0, 2.0*d['h']*100)
        checks['espacamento_maximo_'+nome] = detal['s_cm'] <= smax + 1e-9
        checks['espacamento_livre_'+nome] = detal.get('livre_mm',-1) >= max(20., phi, 1.2*agregado_max) - 1e-9
        checks['area_fornecida_'+nome] = detal['As_fornecida'] + 1e-9 >= (
            r['Asdist'] if nome=='distribuicao' else
            r['Aspos'] if nome=='principal_positiva' else
            r['Asneg'] if nome=='principal_negativa' else
            r[{'x_positiva':'As_xp','y_positiva':'As_yp','x_negativa':'As_xn','y_negativa':'As_yn'}[nome]])
    if d['unidirecional']:
        base = rho_min(d['fck'])/100*100*(d['h']*100)
        checks['armadura_secundaria_minima'] = r['Asdist'] + 1e-9 >= max(0.2*r['Aspos'], 0.9, 0.5*base)
    # Hipóteses não identificáveis a partir dos dados do terminal.
    pendencias = [
        'Bordas sem continuidade ligadas aos apoios: armadura negativa de borda >= 0,67 rho_min e extensão >= 0,15 lx (19.3.3.2/Tabela 19.1); geometria das bordas não informada.',
        'Bordas livres e aberturas: armaduras longitudinais e transversais adicionais (20.2); aberturas não modeladas.',
        'Comprimentos de ancoragem, emendas, prolongamento de armadura positiva >= 4 cm além do eixo teórico do apoio e escalonamento (20.1): não detalhados.',
        'Momentos volventes e compatibilidade com lajes adjacentes: não modelados explicitamente.',
        'Lajes lisas/cogumelo, balanços, cargas concentradas, veículos, punção e geometrias não retangulares: fora do escopo.',
        'Modelo simplificado de flecha: coeficientes de placas/rigidez equivalente não substituem análise refinada de fissuração, fluência, retração e sequência construtiva.',
        'Carga permanente adicional fixa de 1,28 kN/m², psi2=0,30, idade de carregamento e agregado são hipóteses acadêmicas, não verificações de uso real.'
    ]
    r['auditoria_normativa'] = {'checks':checks,'pendencias':pendencias,
        'status':'NAO ATENDE' if not all(checks.values()) else 'TRIAGEM ATENDE; VALIDACAO DE PROJETO PENDENTE'}
    return r


def imprimir_auditoria_normativa(r):
    """Exibe somente os critérios calculados, sem listar limitações no terminal.

    Os dados completos de auditoria e as limitações de escopo continuam
    disponíveis em r['auditoria_normativa'] para documentação técnica.
    """
    a = r.get('auditoria_normativa')
    if not a:
        return
    print('\n' + '=' * 76)
    print('  VERIFICAÇÕES NORMATIVAS — NBR 6118:2026')
    print('=' * 76)
    for nome, atende in a['checks'].items():
        print(('  [OK] ' if atende else '  [FALHA] ') + nome.replace('_', ' '))
    total = len(a['checks'])
    aprovados = sum(bool(v) for v in a['checks'].values())
    print(f'  RESULTADO DOS CRITÉRIOS VERIFICADOS: {aprovados}/{total} atendidos.')
    if aprovados < total:
        print('  ATENÇÃO: há critérios calculados que não foram atendidos.')


def imprimir_parecer_final(d, r):
    """Parecer de fácil leitura, sem confundir triagem com aprovação integral."""
    largura = 78
    def titulo(txt):
        print("\n" + "═" * largura)
        print("  " + txt)
        print("═" * largura)
    def secao(txt):
        print("\n  " + txt)
        print("  " + "─" * (largura - 4))
    def item(nome, situacao, calculado=None, limite=None):
        print(f"  {nome}")
        print(f"      Situação: {situacao}")
        if calculado is not None and limite is not None:
            print(f"      Flecha calculada : {calculado*100:8.2f} cm")
            print(f"      Limite de referência: {limite*100:5.2f} cm")
        print()

    titulo("PARECER FINAL | VERIFICAÇÕES DA LAJE")
    modelo = "UNIDIRECIONAL" if d['unidirecional'] else "BIDIRECIONAL"
    print(f"\n  Modelo estrutural  : {modelo}")
    print(f"  Dimensões           : lₓ = {d['lx']:.2f} m  |  lᵧ = {d['ly']:.2f} m")
    print(f"  Espessura           : h = {d['h']*100:.2f} cm")
    print(f"  Armadura principal  : Ø {d['phi']:g} mm")
    print(f"  Carga variável      : qₖ = {d['q']:.2f} kN/m²")

    checks=[]
    if d['unidirecional']:
        checks.extend([
            ("Flecha final estimada (referência lₓ/250)",r.get('els_total_ok'),r.get('f_total'),r.get('lim_250')),
            ("Flecha de carga variável (referência lₓ/350)",r.get('els_q_ok'),r.get('f_q'),r.get('lim_350')),
            ("Cisalhamento simplificado",r.get('cis_ok'),None,None),
        ])
    else:
        checks.extend([
            ("Flecha final estimada (referência lₓ/250)",r['f_total'] <= r['lim_250'],r['f_total'],r['lim_250']),
            ("Flecha de carga variável (referência lₓ/350)",r['f_q'] <= r['lim_350'],r['f_q'],r['lim_350']),
            ("Cisalhamento simplificado — direção X",r.get('cis_ok_x'),None,None),
            ("Cisalhamento simplificado — direção Y",r.get('cis_ok_y'),None,None),
        ])
    checks.append(("Acomodação geométrica das barras",r.get('detalhamento_ok'),None,None))
    checks.append(("Limites normativos verificáveis", all(r.get('auditoria_normativa',{}).get('checks',{}).values()),None,None))

    secao("01 | VERIFICAÇÕES CALCULADAS")
    for nome, cond, valor, limite in checks:
        item(nome,_status(cond),valor,limite)

    secao("02 | CONCLUSÃO")
    falhas=[nome for nome,cond,_,_ in checks if cond is False]
    pendentes=[nome for nome,cond,_,_ in checks if cond is None]
    if falhas:
        print("  RESULTADO: NÃO ATENDE A TODOS OS CRITÉRIOS CALCULADOS.")
        print("\n  Itens que não atenderam:")
        for nome in falhas: print("    • " + nome)
        print("\n  Orientação: revisar os parâmetros e recalcular a laje.")
    elif pendentes:
        print("  RESULTADO: CRITÉRIOS PARCIALMENTE VERIFICADOS.")
        print("  Há verificações calculáveis sem resultado conclusivo.")
    else:
        print("  RESULTADO: ATENDE AOS CRITÉRIOS CALCULADOS NO MODELO.")
    print("\n  Referências de estudo: ABNT NBR 6118:2026 e NBR 6120:2019.")
    print("═" * largura + "\n")