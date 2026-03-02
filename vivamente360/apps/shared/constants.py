# Thresholds para classificação de risco HSE-IT (NR-1)
# score_service.py usa estes valores para classificar cada dimensão.

# Dimensões "negativas": score alto = risco alto (ex: demandas excessivas).
# Dimensões "positivas": score baixo = risco alto (ex: baixo controle/apoio).

SCORE_THRESHOLDS_NEGATIVO = {
    'alto':     3.1,   # score >= 3.1 → probabilidade 4
    'moderado': 2.1,   # score >= 2.1 → probabilidade 3
    'medio':    1.1,   # score >= 1.1 → probabilidade 2
    # abaixo de 1.1 → probabilidade 1
}

SCORE_THRESHOLDS_POSITIVO = {
    'alto':     1.0,   # score <= 1.0 → probabilidade 4
    'moderado': 2.0,   # score <= 2.0 → probabilidade 3
    'medio':    3.0,   # score <= 3.0 → probabilidade 2
    # acima de 3.0 → probabilidade 1
}
