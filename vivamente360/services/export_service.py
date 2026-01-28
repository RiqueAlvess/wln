from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from django.http import HttpResponse

class ExportService:
    @staticmethod
    def export_plano_acao_word(campaign, planos):
        doc = Document()

        # Cabeçalho
        heading = doc.add_heading(f'Plano de Ação - {campaign.nome}', 0)
        heading.alignment = WD_ALIGN_PARAGRAPH.CENTER

        doc.add_paragraph(f'Empresa: {campaign.empresa.nome}')
        doc.add_paragraph(f'Período: {campaign.data_inicio} a {campaign.data_fim}')
        doc.add_paragraph('')

        # Tabela de Riscos
        doc.add_heading('Riscos Identificados', level=1)

        table = doc.add_table(rows=1, cols=5)
        table.style = 'Light Grid Accent 1'
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = 'Dimensão'
        hdr_cells[1].text = 'Nível de Risco'
        hdr_cells[2].text = 'Ação Proposta'
        hdr_cells[3].text = 'Responsável'
        hdr_cells[4].text = 'Prazo'

        for plano in planos:
            row_cells = table.add_row().cells
            row_cells[0].text = plano.dimensao.nome
            row_cells[1].text = plano.nivel_risco
            row_cells[2].text = plano.acao_proposta[:100] + '...'
            row_cells[3].text = plano.responsavel
            row_cells[4].text = str(plano.prazo)

        # Detalhamento
        doc.add_page_break()
        doc.add_heading('Detalhamento das Ações', level=1)

        for i, plano in enumerate(planos, 1):
            doc.add_heading(f'Ação {i}: {plano.dimensao.nome}', level=2)
            doc.add_paragraph(f'Nível de Risco: {plano.nivel_risco}')
            doc.add_paragraph(f'Descrição do Risco: {plano.descricao_risco}')
            doc.add_paragraph(f'Ação Proposta: {plano.acao_proposta}')
            doc.add_paragraph(f'Responsável: {plano.responsavel}')
            doc.add_paragraph(f'Prazo: {plano.prazo}')
            if plano.recursos_necessarios:
                doc.add_paragraph(f'Recursos: {plano.recursos_necessarios}')
            if plano.indicadores:
                doc.add_paragraph(f'Indicadores: {plano.indicadores}')
            doc.add_paragraph('')

        # Assinaturas
        doc.add_page_break()
        doc.add_heading('Aprovações', level=1)
        doc.add_paragraph('_' * 40)
        doc.add_paragraph('Responsável pela Área de SST')
        doc.add_paragraph('')
        doc.add_paragraph('_' * 40)
        doc.add_paragraph('Gerente de RH')

        return doc
