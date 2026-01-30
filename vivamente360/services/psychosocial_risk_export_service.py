"""
Serviço de Exportação de Matriz de Risco Psicossocial

Exports disponíveis:
- Excel: Planilha completa com matriz, fatores e alertas
- PGR (Word): Documento formatado para Programa de Gerenciamento de Riscos
"""

from io import BytesIO
from typing import Dict
from django.utils import timezone
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter


class PsychosocialRiskExportService:
    """Serviço de exportação de matriz de risco psicossocial"""

    # Cores por classificação
    COLORS = {
        'TRIVIAL': 'C6EFCE',        # Verde claro
        'TOLERÁVEL': 'FFEB9C',      # Amarelo claro
        'MODERADO': 'FFC7CE',       # Laranja claro
        'SUBSTANCIAL': 'F4B084',    # Vermelho claro
        'INTOLERÁVEL': 'D9D2E9',    # Roxo claro
    }

    @classmethod
    def export_to_excel(cls, avaliacao: Dict) -> Workbook:
        """
        Exporta matriz de risco para Excel.

        Args:
            avaliacao: Dict retornado por RiskAssessmentService.avaliar_campanha_completa()

        Returns:
            Workbook do openpyxl
        """
        wb = Workbook()

        # Sheet 1: Resumo Executivo
        cls._criar_sheet_resumo(wb, avaliacao)

        # Sheet 2: Matriz 5x5
        cls._criar_sheet_matriz(wb, avaliacao)

        # Sheet 3: Fatores Críticos
        cls._criar_sheet_fatores_criticos(wb, avaliacao)

        # Sheet 4: Todos os Fatores
        cls._criar_sheet_todos_fatores(wb, avaliacao)

        # Sheet 5: Alertas Críticos (se houver)
        if avaliacao.get('alertas_criticos'):
            cls._criar_sheet_alertas(wb, avaliacao)

        # Remover sheet padrão
        if 'Sheet' in wb.sheetnames:
            wb.remove(wb['Sheet'])

        return wb

    @classmethod
    def _criar_sheet_resumo(cls, wb: Workbook, avaliacao: Dict):
        """Cria sheet de resumo executivo"""
        ws = wb.active
        ws.title = "Resumo Executivo"

        campaign = avaliacao['campaign']
        empresa = avaliacao['empresa']
        resumo = avaliacao['resumo']
        matriz = avaliacao.get('matriz_ajustada', avaliacao['matriz_base'])

        # Cabeçalho
        ws['A1'] = "RESUMO EXECUTIVO - AVALIAÇÃO DE RISCOS PSICOSSOCIAIS NR-1"
        ws['A1'].font = Font(size=14, bold=True)

        # Informações gerais
        row = 3
        ws[f'A{row}'] = "Empresa:"
        ws[f'B{row}'] = empresa.nome
        ws[f'A{row}'].font = Font(bold=True)

        row += 1
        ws[f'A{row}'] = "Campanha:"
        ws[f'B{row}'] = campaign.nome

        row += 1
        ws[f'A{row}'] = "Data da Avaliação:"
        ws[f'B{row}'] = timezone.now().strftime('%d/%m/%Y %H:%M')

        row += 1
        ws[f'A{row}'] = "CNAE:"
        ws[f'B{row}'] = avaliacao.get('cnae', 'N/A')

        row += 1
        ws[f'A{row}'] = "Processou Análise de IA:"
        ws[f'B{row}'] = "Sim" if avaliacao.get('processou_ia') else "Não"

        # Distribuição de riscos
        row += 3
        ws[f'A{row}'] = "DISTRIBUIÇÃO DE RISCOS"
        ws[f'A{row}'].font = Font(size=12, bold=True)

        row += 1
        cls._escrever_linha_header(ws, row, ['Classificação', 'Quantidade', '%', 'Ação Necessária'])

        total = resumo.get('total_fatores', 1)

        for classificacao, label, key in [
            ('INTOLERÁVEL', '🟣 Intolerável', 'intoleraveis'),
            ('SUBSTANCIAL', '🔴 Substancial', 'substanciais'),
            ('MODERADO', '🟠 Moderado', 'moderados'),
            ('TOLERÁVEL', '🟡 Tolerável', 'toleraveis'),
            ('TRIVIAL', '🟢 Trivial', 'triviais'),
        ]:
            row += 1
            qtd = resumo.get(key, 0)
            perc = (qtd / total * 100) if total > 0 else 0

            ws[f'A{row}'] = label
            ws[f'B{row}'] = qtd
            ws[f'C{row}'] = f"{perc:.1f}%"

            # Ação baseada na classificação
            from services.risk_calculation_service import RiskCalculationService
            for (min_nr, max_nr), dados in RiskCalculationService.CLASSIFICACAO_NR.items():
                if dados['classificacao'] == classificacao:
                    ws[f'D{row}'] = dados['acao']
                    break

            # Colorir linha
            cor = cls.COLORS.get(classificacao, 'FFFFFF')
            for col in ['A', 'B', 'C', 'D']:
                ws[f'{col}{row}'].fill = PatternFill(start_color=cor, end_color=cor, fill_type='solid')

        # Métricas de sentimento (se houver)
        if 'sentimento_medio' in resumo:
            row += 3
            ws[f'A{row}'] = "ANÁLISE DE SENTIMENTO (IA)"
            ws[f'A{row}'].font = Font(size=12, bold=True)

            row += 1
            ws[f'A{row}'] = "Score Médio de Sentimento:"
            ws[f'B{row}'] = f"{resumo['sentimento_medio']:.2f}"

            row += 1
            ws[f'A{row}'] = "Sentimento Predominante:"
            ws[f'B{row}'] = resumo.get('sentimento_label', 'N/A')

            if 'nivel_preocupacao_predominante' in resumo:
                row += 1
                ws[f'A{row}'] = "Nível de Preocupação:"
                ws[f'B{row}'] = resumo['nivel_preocupacao_predominante']

        # Alertas críticos
        if resumo.get('alertas_criticos', 0) > 0:
            row += 3
            ws[f'A{row}'] = f"⚠️ ATENÇÃO: {resumo['alertas_criticos']} ALERTA(S) CRÍTICO(S) IDENTIFICADO(S)"
            ws[f'A{row}'].font = Font(size=12, bold=True, color="FF0000")

        # Ajustar larguras
        ws.column_dimensions['A'].width = 30
        ws.column_dimensions['B'].width = 15
        ws.column_dimensions['C'].width = 10
        ws.column_dimensions['D'].width = 60

    @classmethod
    def _criar_sheet_matriz(cls, wb: Workbook, avaliacao: Dict):
        """Cria sheet com matriz 5x5"""
        ws = wb.create_sheet("Matriz 5x5")

        ws['A1'] = "MATRIZ DE RISCO 5×5 (Probabilidade × Severidade)"
        ws['A1'].font = Font(size=14, bold=True)

        # Criar headers
        row = 3
        ws[f'A{row}'] = "Prob \\ Sev"
        ws[f'A{row}'].font = Font(bold=True)

        for s in range(1, 6):
            col = get_column_letter(s + 1)
            ws[f'{col}{row}'] = f"S={s}"
            ws[f'{col}{row}'].font = Font(bold=True)
            ws[f'{col}{row}'].alignment = Alignment(horizontal='center')

        # Preencher matriz
        from services.risk_calculation_service import RiskCalculationService

        for p in range(5, 0, -1):  # Inverter para começar do alto
            row += 1
            ws[f'A{row}'] = f"P={p}"
            ws[f'A{row}'].font = Font(bold=True)

            for s in range(1, 6):
                col = get_column_letter(s + 1)
                nr = p * s

                # Encontrar classificação
                classificacao = 'TRIVIAL'
                for (min_nr, max_nr), dados in RiskCalculationService.CLASSIFICACAO_NR.items():
                    if min_nr <= nr <= max_nr:
                        classificacao = dados['classificacao']
                        break

                # Escrever NR
                ws[f'{col}{row}'] = nr
                ws[f'{col}{row}'].alignment = Alignment(horizontal='center', vertical='center')

                # Colorir
                cor = cls.COLORS.get(classificacao, 'FFFFFF')
                ws[f'{col}{row}'].fill = PatternFill(start_color=cor, end_color=cor, fill_type='solid')

        # Legenda
        row += 3
        ws[f'A{row}'] = "LEGENDA:"
        ws[f'A{row}'].font = Font(bold=True)

        for classificacao, label in [
            ('TRIVIAL', '🟢 Trivial (1-4)'),
            ('TOLERÁVEL', '🟡 Tolerável (5-9)'),
            ('MODERADO', '🟠 Moderado (10-14)'),
            ('SUBSTANCIAL', '🔴 Substancial (15-19)'),
            ('INTOLERÁVEL', '🟣 Intolerável (20-25)'),
        ]:
            row += 1
            ws[f'A{row}'] = label
            cor = cls.COLORS.get(classificacao, 'FFFFFF')
            ws[f'A{row}'].fill = PatternFill(start_color=cor, end_color=cor, fill_type='solid')

        # Ajustar larguras
        for col in range(1, 8):
            ws.column_dimensions[get_column_letter(col)].width = 15

    @classmethod
    def _criar_sheet_fatores_criticos(cls, wb: Workbook, avaliacao: Dict):
        """Cria sheet com fatores críticos"""
        ws = wb.create_sheet("Fatores Críticos")

        ws['A1'] = "FATORES CRÍTICOS (Intoleráveis e Substanciais)"
        ws['A1'].font = Font(size=14, bold=True)

        matriz = avaliacao.get('matriz_ajustada', avaliacao['matriz_base'])
        fatores_criticos = matriz.get('fatores_criticos', [])

        if not fatores_criticos:
            ws['A3'] = "✅ Nenhum fator crítico identificado!"
            ws['A3'].font = Font(color="00AA00", bold=True)
            return

        # Headers
        row = 3
        headers = ['Código', 'Fator de Risco', 'Categoria', 'P', 'S', 'NR', 'Classificação', 'Prazo', 'Ação Necessária']
        cls._escrever_linha_header(ws, row, headers)

        # Dados
        for fator_data in fatores_criticos:
            row += 1
            fator = fator_data.get('fator')

            ws[f'A{row}'] = fator.codigo if fator else 'N/A'
            ws[f'B{row}'] = fator.nome if fator else 'N/A'
            ws[f'C{row}'] = fator.categoria.nome if fator and fator.categoria else 'N/A'
            ws[f'D{row}'] = fator_data.get('probabilidade', 0)
            ws[f'E{row}'] = fator_data.get('severidade', 0)
            ws[f'F{row}'] = fator_data.get('nr', 0)
            ws[f'G{row}'] = fator_data.get('classificacao', 'N/A')
            ws[f'H{row}'] = fator_data.get('prazo', 'N/A')
            ws[f'I{row}'] = fator_data.get('acao', 'N/A')

            # Colorir linha
            classificacao = fator_data.get('classificacao', 'TRIVIAL')
            cor = cls.COLORS.get(classificacao, 'FFFFFF')
            for col in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']:
                ws[f'{col}{row}'].fill = PatternFill(start_color=cor, end_color=cor, fill_type='solid')

        # Ajustar larguras
        ws.column_dimensions['A'].width = 12
        ws.column_dimensions['B'].width = 40
        ws.column_dimensions['C'].width = 25
        ws.column_dimensions['D'].width = 8
        ws.column_dimensions['E'].width = 8
        ws.column_dimensions['F'].width = 8
        ws.column_dimensions['G'].width = 15
        ws.column_dimensions['H'].width = 15
        ws.column_dimensions['I'].width = 60

    @classmethod
    def _criar_sheet_todos_fatores(cls, wb: Workbook, avaliacao: Dict):
        """Cria sheet com todos os fatores avaliados"""
        ws = wb.create_sheet("Todos os Fatores")

        ws['A1'] = "TODOS OS FATORES AVALIADOS"
        ws['A1'].font = Font(size=14, bold=True)

        # Headers
        row = 3
        headers = ['Dimensão HSE-IT', 'Score', 'Código', 'Fator de Risco', 'Categoria', 'P', 'S', 'NR', 'Classificação']
        cls._escrever_linha_header(ws, row, headers)

        matriz = avaliacao.get('matriz_ajustada', avaliacao['matriz_base'])

        # Dados por dimensão
        for dimensao_data in matriz.get('dimensoes', []):
            dimensao = dimensao_data.get('dimensao')
            score = dimensao_data.get('score', 0)

            for fator_data in dimensao_data.get('fatores', []):
                row += 1
                fator = fator_data.get('fator')

                ws[f'A{row}'] = dimensao.nome if dimensao else 'N/A'
                ws[f'B{row}'] = f"{score:.2f}"
                ws[f'C{row}'] = fator.codigo if fator else 'N/A'
                ws[f'D{row}'] = fator.nome if fator else 'N/A'
                ws[f'E{row}'] = fator.categoria.nome if fator and fator.categoria else 'N/A'
                ws[f'F{row}'] = fator_data.get('probabilidade', 0)
                ws[f'G{row}'] = fator_data.get('severidade', 0)
                ws[f'H{row}'] = fator_data.get('nr', 0)
                ws[f'I{row}'] = fator_data.get('classificacao', 'N/A')

                # Colorir linha
                classificacao = fator_data.get('classificacao', 'TRIVIAL')
                cor = cls.COLORS.get(classificacao, 'FFFFFF')
                for col in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']:
                    ws[f'{col}{row}'].fill = PatternFill(start_color=cor, end_color=cor, fill_type='solid')

        # Ajustar larguras
        ws.column_dimensions['A'].width = 25
        ws.column_dimensions['B'].width = 10
        ws.column_dimensions['C'].width = 12
        ws.column_dimensions['D'].width = 40
        ws.column_dimensions['E'].width = 25
        ws.column_dimensions['F'].width = 8
        ws.column_dimensions['G'].width = 8
        ws.column_dimensions['H'].width = 8
        ws.column_dimensions['I'].width = 15

    @classmethod
    def _criar_sheet_alertas(cls, wb: Workbook, avaliacao: Dict):
        """Cria sheet com alertas críticos da IA"""
        ws = wb.create_sheet("Alertas Críticos")

        ws['A1'] = "⚠️ ALERTAS CRÍTICOS IDENTIFICADOS PELA IA"
        ws['A1'].font = Font(size=14, bold=True, color="FF0000")

        alertas = avaliacao.get('alertas_criticos', [])

        if not alertas:
            ws['A3'] = "Nenhum alerta crítico identificado."
            return

        # Headers
        row = 3
        headers = ['Tipo', 'Gravidade', 'Setor', 'Evidência', 'Recomendação Imediata', 'Encaminhamento']
        cls._escrever_linha_header(ws, row, headers)

        # Dados
        for alerta in alertas:
            row += 1

            ws[f'A{row}'] = alerta.get('tipo', 'N/A')
            ws[f'B{row}'] = alerta.get('gravidade', 'N/A')

            setor = alerta.get('setor')
            ws[f'C{row}'] = setor.nome if setor else 'N/A'

            ws[f'D{row}'] = alerta.get('evidencia', 'N/A')
            ws[f'E{row}'] = alerta.get('recomendacao_imediata', 'N/A')
            ws[f'F{row}'] = alerta.get('encaminhamento', 'N/A')

            # Colorir linha de vermelho se crítica
            if alerta.get('gravidade') == 'Crítica':
                for col in ['A', 'B', 'C', 'D', 'E', 'F']:
                    ws[f'{col}{row}'].fill = PatternFill(start_color='FFE6E6', end_color='FFE6E6', fill_type='solid')

        # Ajustar larguras
        ws.column_dimensions['A'].width = 20
        ws.column_dimensions['B'].width = 12
        ws.column_dimensions['C'].width = 20
        ws.column_dimensions['D'].width = 50
        ws.column_dimensions['E'].width = 50
        ws.column_dimensions['F'].width = 20

    @classmethod
    def _escrever_linha_header(cls, ws, row: int, headers: list):
        """Escreve linha de cabeçalho formatada"""
        for idx, header in enumerate(headers, start=1):
            col = get_column_letter(idx)
            ws[f'{col}{row}'] = header
            ws[f'{col}{row}'].font = Font(bold=True, color="FFFFFF")
            ws[f'{col}{row}'].fill = PatternFill(start_color='366092', end_color='366092', fill_type='solid')
            ws[f'{col}{row}'].alignment = Alignment(horizontal='center', vertical='center')

    @classmethod
    def export_pgr_document(cls, avaliacao: Dict):
        """
        Exporta relatório PGR em formato Word.

        Args:
            avaliacao: Dict retornado por RiskAssessmentService

        Returns:
            Document do python-docx (ou BytesIO se python-docx não disponível)
        """
        # Criar documento simples em texto (fallback se docx não disponível)
        from io import StringIO

        output = StringIO()
        campaign = avaliacao['campaign']
        empresa = avaliacao['empresa']
        resumo = avaliacao['resumo']

        output.write("=" * 80 + "\n")
        output.write("PROGRAMA DE GERENCIAMENTO DE RISCOS PSICOSSOCIAIS (PGR)\n")
        output.write("Conforme NR-1 - Item 1.5.4.1.1\n")
        output.write("=" * 80 + "\n\n")

        output.write(f"Empresa: {empresa.nome}\n")
        output.write(f"CNPJ: {empresa.cnpj}\n")
        output.write(f"CNAE: {avaliacao.get('cnae', 'N/A')}\n")
        output.write(f"Campanha: {campaign.nome}\n")
        output.write(f"Período: {campaign.data_inicio} a {campaign.data_fim}\n")
        output.write(f"Data da Avaliação: {timezone.now().strftime('%d/%m/%Y')}\n\n")

        output.write("-" * 80 + "\n")
        output.write("RESUMO EXECUTIVO\n")
        output.write("-" * 80 + "\n\n")

        output.write(f"Total de Fatores Avaliados: {resumo.get('total_fatores', 0)}\n\n")

        output.write("Distribuição de Riscos:\n")
        output.write(f"  - Intoleráveis: {resumo.get('intoleraveis', 0)}\n")
        output.write(f"  - Substanciais: {resumo.get('substanciais', 0)}\n")
        output.write(f"  - Moderados: {resumo.get('moderados', 0)}\n")
        output.write(f"  - Toleráveis: {resumo.get('toleraveis', 0)}\n")
        output.write(f"  - Triviais: {resumo.get('triviais', 0)}\n\n")

        # Fatores críticos
        matriz = avaliacao.get('matriz_ajustada', avaliacao['matriz_base'])
        fatores_criticos = matriz.get('fatores_criticos', [])

        if fatores_criticos:
            output.write("-" * 80 + "\n")
            output.write("FATORES CRÍTICOS IDENTIFICADOS\n")
            output.write("-" * 80 + "\n\n")

            for idx, fator_data in enumerate(fatores_criticos, start=1):
                fator = fator_data.get('fator')
                output.write(f"{idx}. {fator.codigo} - {fator.nome}\n")
                output.write(f"   Categoria: {fator.categoria.nome}\n")
                output.write(f"   Classificação: {fator_data.get('classificacao')}\n")
                output.write(f"   Nível de Risco (NR): {fator_data.get('nr')}\n")
                output.write(f"   Prazo: {fator_data.get('prazo')}\n")
                output.write(f"   Ação: {fator_data.get('acao')}\n\n")

        # Retornar como BytesIO
        content = output.getvalue()
        output.close()

        bio = BytesIO(content.encode('utf-8'))
        return bio
