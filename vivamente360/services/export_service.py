from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from django.http import HttpResponse
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import datetime

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

    @staticmethod
    def export_checklist_nr1_pdf(campaign, itens_por_etapa, progresso_geral, total_itens, total_concluidos):
        """
        Exporta o checklist NR-1 completo para PDF
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)

        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#0d6efd'),
            spaceAfter=30,
            alignment=TA_CENTER
        )

        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#212529'),
            spaceAfter=12,
            spaceBefore=12
        )

        normal_style = styles['Normal']

        # Conteúdo do documento
        story = []

        # Título
        story.append(Paragraph("Checklist de Compliance NR-1", title_style))
        story.append(Spacer(1, 0.2*inch))

        # Informações da Campanha
        info_data = [
            ['Campanha:', campaign.nome],
            ['Empresa:', campaign.empresa.nome_fantasia],
            ['Período:', f'{campaign.data_inicio.strftime("%d/%m/%Y")} a {campaign.data_fim.strftime("%d/%m/%Y")}'],
            ['Data de Geração:', datetime.now().strftime("%d/%m/%Y %H:%M")],
        ]

        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e9ecef')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))

        story.append(info_table)
        story.append(Spacer(1, 0.3*inch))

        # Progresso Geral
        progresso_data = [
            ['Progresso Geral:', f'{progresso_geral:.0f}%'],
            ['Itens Concluídos:', f'{total_concluidos} de {total_itens}'],
        ]

        progresso_table = Table(progresso_data, colWidths=[2*inch, 4*inch])
        progresso_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#d1ecf1')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))

        story.append(progresso_table)
        story.append(Spacer(1, 0.3*inch))

        # Itens por Etapa
        for etapa_num, etapa_data in sorted(itens_por_etapa.items()):
            # Cabeçalho da Etapa
            story.append(Paragraph(f"ETAPA {etapa_num}: {etapa_data['nome'].upper()}", heading_style))
            story.append(Paragraph(
                f"Progresso: {etapa_data['progresso']:.0f}% ({etapa_data['concluidos']}/{etapa_data['total']} itens)",
                normal_style
            ))
            story.append(Spacer(1, 0.1*inch))

            # Tabela de Itens
            items_data = [['Status', 'Item', 'Responsável', 'Prazo', 'Evidências']]

            for item in etapa_data['itens']:
                status = '✓' if item.concluido else '○'
                item_texto = item.item_texto[:60] + '...' if len(item.item_texto) > 60 else item.item_texto
                if item.automatico:
                    item_texto += ' (Automático)'
                responsavel = item.responsavel if item.responsavel else '-'
                prazo = item.prazo.strftime("%d/%m/%Y") if item.prazo else '-'
                evidencias = str(item.evidencias.count())

                items_data.append([status, item_texto, responsavel, prazo, evidencias])

            items_table = Table(items_data, colWidths=[0.5*inch, 3*inch, 1.5*inch, 0.8*inch, 0.7*inch])
            items_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d6efd')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            ]))

            story.append(items_table)
            story.append(Spacer(1, 0.2*inch))

        # Assinaturas
        story.append(PageBreak())
        story.append(Paragraph("APROVAÇÕES", heading_style))
        story.append(Spacer(1, 0.3*inch))

        assinaturas_data = [
            ['_' * 50],
            ['Responsável pela Área de SST'],
            [''],
            ['_' * 50],
            ['Gerente de RH'],
            [''],
            ['_' * 50],
            ['Diretor/Presidente'],
        ]

        assinaturas_table = Table(assinaturas_data, colWidths=[6*inch])
        assinaturas_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))

        story.append(assinaturas_table)

        # Gerar PDF
        doc.build(story)
        pdf = buffer.getvalue()
        buffer.close()

        return pdf
