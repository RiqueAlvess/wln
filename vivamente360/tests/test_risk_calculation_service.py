"""
Testes para o RiskCalculationService
"""

import unittest
from services.risk_calculation_service import RiskCalculationService


class TestRiskCalculationService(unittest.TestCase):
    """Testes unitários para o serviço de cálculo de risco"""

    def test_calcular_probabilidade_dimensao_negativa(self):
        """
        Testa mapeamento de scores para probabilidades em dimensões negativas
        (onde score alto = risco alto, como 'demandas')
        """
        # Score muito alto (3.6) → Probabilidade Quase Certa (5)
        self.assertEqual(
            RiskCalculationService.calcular_probabilidade(3.6, 'negativo'),
            5
        )

        # Score alto (3.0) → Probabilidade Provável (4)
        self.assertEqual(
            RiskCalculationService.calcular_probabilidade(3.0, 'negativo'),
            4
        )

        # Score médio (2.0) → Probabilidade Possível (3)
        self.assertEqual(
            RiskCalculationService.calcular_probabilidade(2.0, 'negativo'),
            3
        )

        # Score baixo (1.0) → Probabilidade Improvável (2)
        self.assertEqual(
            RiskCalculationService.calcular_probabilidade(1.0, 'negativo'),
            2
        )

        # Score muito baixo (0.3) → Probabilidade Rara (1)
        self.assertEqual(
            RiskCalculationService.calcular_probabilidade(0.3, 'negativo'),
            1
        )

    def test_calcular_probabilidade_dimensao_positiva(self):
        """
        Testa mapeamento de scores para probabilidades em dimensões positivas
        (onde score baixo = risco alto, como 'controle', 'apoio_chefia')
        """
        # Score muito baixo (0.3) → Probabilidade Quase Certa (5)
        self.assertEqual(
            RiskCalculationService.calcular_probabilidade(0.3, 'positivo'),
            5
        )

        # Score baixo (1.0) → Probabilidade Provável (4)
        self.assertEqual(
            RiskCalculationService.calcular_probabilidade(1.0, 'positivo'),
            4
        )

        # Score médio (2.0) → Probabilidade Possível (3)
        self.assertEqual(
            RiskCalculationService.calcular_probabilidade(2.0, 'positivo'),
            3
        )

        # Score alto (3.0) → Probabilidade Improvável (2)
        self.assertEqual(
            RiskCalculationService.calcular_probabilidade(3.0, 'positivo'),
            2
        )

        # Score muito alto (3.8) → Probabilidade Rara (1)
        self.assertEqual(
            RiskCalculationService.calcular_probabilidade(3.8, 'positivo'),
            1
        )

    def test_matriz_risco_p_x_s(self):
        """Testa cálculo da matriz de risco (P × S)"""
        # Probabilidade 5 × Severidade 5 = NR 25
        self.assertEqual(
            RiskCalculationService.MATRIZ_RISCO[(5, 5)],
            25
        )

        # Probabilidade 3 × Severidade 4 = NR 12
        self.assertEqual(
            RiskCalculationService.MATRIZ_RISCO[(3, 4)],
            12
        )

        # Probabilidade 1 × Severidade 1 = NR 1
        self.assertEqual(
            RiskCalculationService.MATRIZ_RISCO[(1, 1)],
            1
        )

        # Probabilidade 2 × Severidade 3 = NR 6
        self.assertEqual(
            RiskCalculationService.MATRIZ_RISCO[(2, 3)],
            6
        )

    def test_calcular_nivel_risco_intoleravel(self):
        """Testa classificação de risco INTOLERÁVEL"""
        # NR = 25 (P=5, S=5)
        resultado = RiskCalculationService.calcular_nivel_risco(5, 5)

        self.assertEqual(resultado['nr'], 25)
        self.assertEqual(resultado['classificacao'], 'INTOLERÁVEL')
        self.assertEqual(resultado['prioridade'], 0)
        self.assertEqual(resultado['prazo'], 'Imediato')

        # NR = 20 (P=4, S=5)
        resultado = RiskCalculationService.calcular_nivel_risco(4, 5)
        self.assertEqual(resultado['nr'], 20)
        self.assertEqual(resultado['classificacao'], 'INTOLERÁVEL')

    def test_calcular_nivel_risco_substancial(self):
        """Testa classificação de risco SUBSTANCIAL"""
        # NR = 15 (P=3, S=5)
        resultado = RiskCalculationService.calcular_nivel_risco(3, 5)

        self.assertEqual(resultado['nr'], 15)
        self.assertEqual(resultado['classificacao'], 'SUBSTANCIAL')
        self.assertEqual(resultado['prioridade'], 1)
        self.assertEqual(resultado['prazo'], '30 dias')

        # NR = 16 (P=4, S=4)
        resultado = RiskCalculationService.calcular_nivel_risco(4, 4)
        self.assertEqual(resultado['nr'], 16)
        self.assertEqual(resultado['classificacao'], 'SUBSTANCIAL')

    def test_calcular_nivel_risco_moderado(self):
        """Testa classificação de risco MODERADO"""
        # NR = 12 (P=3, S=4)
        resultado = RiskCalculationService.calcular_nivel_risco(3, 4)

        self.assertEqual(resultado['nr'], 12)
        self.assertEqual(resultado['classificacao'], 'MODERADO')
        self.assertEqual(resultado['prioridade'], 2)
        self.assertEqual(resultado['prazo'], '90 dias')

        # NR = 10 (P=2, S=5)
        resultado = RiskCalculationService.calcular_nivel_risco(2, 5)
        self.assertEqual(resultado['nr'], 10)
        self.assertEqual(resultado['classificacao'], 'MODERADO')

    def test_calcular_nivel_risco_toleravel(self):
        """Testa classificação de risco TOLERÁVEL"""
        # NR = 6 (P=2, S=3)
        resultado = RiskCalculationService.calcular_nivel_risco(2, 3)

        self.assertEqual(resultado['nr'], 6)
        self.assertEqual(resultado['classificacao'], 'TOLERÁVEL')
        self.assertEqual(resultado['prioridade'], 3)
        self.assertEqual(resultado['prazo'], '180 dias')

        # NR = 9 (P=3, S=3)
        resultado = RiskCalculationService.calcular_nivel_risco(3, 3)
        self.assertEqual(resultado['nr'], 9)
        self.assertEqual(resultado['classificacao'], 'TOLERÁVEL')

    def test_calcular_nivel_risco_trivial(self):
        """Testa classificação de risco TRIVIAL"""
        # NR = 1 (P=1, S=1)
        resultado = RiskCalculationService.calcular_nivel_risco(1, 1)

        self.assertEqual(resultado['nr'], 1)
        self.assertEqual(resultado['classificacao'], 'TRIVIAL')
        self.assertEqual(resultado['prioridade'], 4)
        self.assertIsNone(resultado['prazo'])

        # NR = 4 (P=2, S=2)
        resultado = RiskCalculationService.calcular_nivel_risco(2, 2)
        self.assertEqual(resultado['nr'], 4)
        self.assertEqual(resultado['classificacao'], 'TRIVIAL')

    def test_probabilidade_labels_completos(self):
        """Testa se todos os labels de probabilidade estão definidos"""
        for p in range(1, 6):
            self.assertIn(p, RiskCalculationService.PROBABILIDADE_LABELS)
            label = RiskCalculationService.PROBABILIDADE_LABELS[p]
            self.assertIn('nome', label)
            self.assertIn('descricao', label)
            self.assertIn('cor', label)
            self.assertIn('icone', label)

    def test_severidade_labels_completos(self):
        """Testa se todos os labels de severidade estão definidos"""
        for s in range(1, 6):
            self.assertIn(s, RiskCalculationService.SEVERIDADE_LABELS)
            label = RiskCalculationService.SEVERIDADE_LABELS[s]
            self.assertIn('nome', label)
            self.assertIn('descricao', label)
            self.assertIn('exemplos', label)
            self.assertIn('cor', label)
            self.assertIn('icone', label)

    def test_todas_combinacoes_matriz_existem(self):
        """Testa se todas as combinações P×S estão na matriz"""
        for p in range(1, 6):
            for s in range(1, 6):
                self.assertIn((p, s), RiskCalculationService.MATRIZ_RISCO)
                nr = RiskCalculationService.MATRIZ_RISCO[(p, s)]
                self.assertEqual(nr, p * s)

    def test_todos_niveis_risco_cobertos(self):
        """Testa se todos os NR possíveis têm uma classificação"""
        niveis_possiveis = set()
        for p in range(1, 6):
            for s in range(1, 6):
                niveis_possiveis.add(p * s)

        # Verificar se cada NR possível tem uma classificação
        for nr in niveis_possiveis:
            classificacao_encontrada = False
            for (min_nr, max_nr), _ in RiskCalculationService.CLASSIFICACAO_NR.items():
                if min_nr <= nr <= max_nr:
                    classificacao_encontrada = True
                    break
            self.assertTrue(
                classificacao_encontrada,
                f"NR {nr} não tem classificação definida"
            )

    def test_prioridades_consistentes(self):
        """Testa se as prioridades estão em ordem decrescente de risco"""
        classificacoes = [
            ('INTOLERÁVEL', 0),
            ('SUBSTANCIAL', 1),
            ('MODERADO', 2),
            ('TOLERÁVEL', 3),
            ('TRIVIAL', 4),
        ]

        for class_nome, prioridade_esperada in classificacoes:
            for (min_nr, max_nr), dados in RiskCalculationService.CLASSIFICACAO_NR.items():
                if dados['classificacao'] == class_nome:
                    self.assertEqual(
                        dados['prioridade'],
                        prioridade_esperada,
                        f"Prioridade incorreta para {class_nome}"
                    )

    def test_gerar_matriz_visual_vazia(self):
        """Testa geração de matriz visual sem fatores"""
        resultado = RiskCalculationService.gerar_matriz_visual([])

        self.assertEqual(resultado['total_fatores'], 0)
        self.assertIn('matriz', resultado)

        # Verificar que matriz tem todas as células
        for p in range(1, 6):
            for s in range(1, 6):
                self.assertIn((p, s), resultado['matriz'])
                self.assertEqual(resultado['matriz'][(p, s)]['count'], 0)

    def test_gerar_matriz_visual_com_fatores(self):
        """Testa geração de matriz visual com fatores"""
        fatores = [
            {'probabilidade': 5, 'severidade': 5, 'nr': 25, 'fator': 'A'},
            {'probabilidade': 5, 'severidade': 5, 'nr': 25, 'fator': 'B'},
            {'probabilidade': 3, 'severidade': 4, 'nr': 12, 'fator': 'C'},
        ]

        resultado = RiskCalculationService.gerar_matriz_visual(fatores)

        self.assertEqual(resultado['total_fatores'], 3)

        # Verificar célula (5,5) tem 2 fatores
        self.assertEqual(resultado['matriz'][(5, 5)]['count'], 2)
        self.assertEqual(len(resultado['matriz'][(5, 5)]['fatores']), 2)

        # Verificar célula (3,4) tem 1 fator
        self.assertEqual(resultado['matriz'][(3, 4)]['count'], 1)
        self.assertEqual(len(resultado['matriz'][(3, 4)]['fatores']), 1)


if __name__ == '__main__':
    unittest.main()
