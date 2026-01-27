class ScoreService:
    DIMENSOES = {
        "demandas": [3, 6, 9, 12, 16, 18, 20, 22],
        "controle": [2, 10, 15, 19, 25, 30],
        "apoio_chefia": [8, 23, 29, 33, 35],
        "apoio_colegas": [7, 24, 27, 31],
        "relacionamentos": [5, 14, 21, 34],
        "cargo": [1, 4, 11, 13, 17],
        "comunicacao_mudancas": [26, 28, 32],
    }

    DIMENSOES_NEGATIVAS = ["demandas", "relacionamentos"]

    @classmethod
    def calcular_score_dimensao(cls, respostas: dict, dimensao: str) -> float:
        itens = cls.DIMENSOES[dimensao]
        soma = sum(respostas.get(str(i), 0) for i in itens)
        return round(soma / len(itens), 2)

    @classmethod
    def classificar_risco(cls, score: float, dimensao: str) -> dict:
        eh_negativo = dimensao in cls.DIMENSOES_NEGATIVAS

        if eh_negativo:
            if score >= 3.1:
                return {"classificacao": "ALTO RISCO", "probabilidade": 4}
            elif score >= 2.1:
                return {"classificacao": "Risco Moderado", "probabilidade": 3}
            elif score >= 1.1:
                return {"classificacao": "Risco Médio", "probabilidade": 2}
            else:
                return {"classificacao": "Baixo Risco", "probabilidade": 1}
        else:
            if score <= 1.0:
                return {"classificacao": "ALTO RISCO", "probabilidade": 4}
            elif score <= 2.0:
                return {"classificacao": "Risco Moderado", "probabilidade": 3}
            elif score <= 3.0:
                return {"classificacao": "Risco Médio", "probabilidade": 2}
            else:
                return {"classificacao": "Baixo Risco", "probabilidade": 1}

    @classmethod
    def calcular_nivel_risco(cls, probabilidade: int, severidade: int) -> dict:
        nr = probabilidade * severidade

        if nr <= 4:
            return {"nivel": nr, "interpretacao": "Aceitável", "cor": "verde"}
        elif nr <= 8:
            return {"nivel": nr, "interpretacao": "Moderado", "cor": "amarelo"}
        elif nr <= 12:
            return {"nivel": nr, "interpretacao": "Importante", "cor": "laranja"}
        else:
            return {"nivel": nr, "interpretacao": "Crítico", "cor": "vermelho"}

    @classmethod
    def processar_resposta_completa(cls, respostas: dict, severidade_base: int = 2) -> dict:
        resultado = {}
        for dimensao in cls.DIMENSOES.keys():
            score = cls.calcular_score_dimensao(respostas, dimensao)
            risco = cls.classificar_risco(score, dimensao)
            nivel = cls.calcular_nivel_risco(risco['probabilidade'], severidade_base)

            resultado[dimensao] = {
                "score": score,
                **risco,
                **nivel
            }
        return resultado
