"""
Management command para popular dados iniciais de Fatores de Risco Psicossocial (NR-1)
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from apps.surveys.models import CategoriaFatorRisco, FatorRisco, Dimensao


# Dados dos fatores de risco conforme NR-1
FATORES_RISCO_DATA = {
    'organizacao': {
        'nome': 'Organização do Trabalho',
        'descricao': 'Fatores relacionados à forma como o trabalho é estruturado e gerenciado',
        'icone': 'bi-diagram-3',
        'ordem': 1,
        'fatores': [
            {
                'codigo': 'ORG_001',
                'nome': 'Sobrecarga de Trabalho',
                'descricao': 'Volume excessivo de tarefas além da capacidade do trabalhador',
                'exemplos': 'Acúmulo de funções, equipe reduzida, demanda superior à capacidade',
                'dimensoes_hse': ['demandas'],
                'severidade_base': 4,
                'consequencias': ['saude_mental', 'saude_fisica', 'acidentes'],
            },
            {
                'codigo': 'ORG_002',
                'nome': 'Ritmo de Trabalho Intenso',
                'descricao': 'Trabalho controlado por máquinas ou sistemas que impõem ritmo acelerado',
                'exemplos': 'Linha de produção, call center com metas por minuto, entregas com GPS',
                'dimensoes_hse': ['demandas', 'controle'],
                'severidade_base': 4,
                'consequencias': ['saude_mental', 'saude_fisica'],
            },
            {
                'codigo': 'ORG_003',
                'nome': 'Prazos Excessivamente Curtos',
                'descricao': 'Urgências constantes e prazos que não respeitam a capacidade de entrega',
                'exemplos': 'Entregas "para ontem", reuniões de última hora, demandas emergenciais frequentes',
                'dimensoes_hse': ['demandas'],
                'severidade_base': 3,
                'consequencias': ['saude_mental'],
            },
            {
                'codigo': 'ORG_004',
                'nome': 'Jornadas Longas ou Imprevisíveis',
                'descricao': 'Trabalho além do expediente regular ou em horários que afetam a vida pessoal',
                'exemplos': 'Hora extra habitual, plantões, turnos rotativos, trabalho noturno',
                'dimensoes_hse': ['demandas', 'comunicacao_mudancas'],
                'severidade_base': 4,
                'consequencias': ['saude_mental', 'saude_fisica', 'acidentes'],
            },
            {
                'codigo': 'ORG_005',
                'nome': 'Falta de Clareza de Papéis',
                'descricao': 'Trabalhador não sabe exatamente o que se espera dele',
                'exemplos': 'Funções não definidas, responsabilidades conflitantes, objetivos vagos',
                'dimensoes_hse': ['cargo'],
                'severidade_base': 3,
                'consequencias': ['saude_mental'],
            },
        ]
    },
    'conteudo': {
        'nome': 'Conteúdo do Trabalho',
        'descricao': 'Fatores relacionados à natureza das tarefas executadas',
        'icone': 'bi-list-task',
        'ordem': 2,
        'fatores': [
            {
                'codigo': 'CON_001',
                'nome': 'Tarefas Monótonas ou Repetitivas',
                'descricao': 'Trabalho sem variação que não estimula cognitivamente',
                'exemplos': 'Digitação repetitiva, inspeção visual contínua, empacotamento manual',
                'dimensoes_hse': ['controle', 'cargo'],
                'severidade_base': 3,
                'consequencias': ['saude_mental', 'saude_fisica'],
            },
            {
                'codigo': 'CON_002',
                'nome': 'Fragmentação Excessiva',
                'descricao': 'Tarefas divididas ao ponto de perderem sentido para o trabalhador',
                'exemplos': 'Trabalho em etapas isoladas sem visão do todo, especialização extrema',
                'dimensoes_hse': ['cargo', 'controle'],
                'severidade_base': 2,
                'consequencias': ['saude_mental'],
            },
            {
                'codigo': 'CON_003',
                'nome': 'Subutilização de Habilidades',
                'descricao': 'Capacidade do trabalhador superior às demandas do cargo',
                'exemplos': 'Profissional qualificado em função operacional, estagnação de carreira',
                'dimensoes_hse': ['controle', 'cargo'],
                'severidade_base': 2,
                'consequencias': ['saude_mental'],
            },
            {
                'codigo': 'CON_004',
                'nome': 'Alta Demanda Emocional',
                'descricao': 'Exposição frequente a situações emocionalmente intensas',
                'exemplos': 'Atendimento a vítimas, trabalho com morte, público agressivo, cobrança',
                'dimensoes_hse': ['demandas', 'apoio_chefia'],
                'severidade_base': 5,
                'consequencias': ['saude_mental'],
            },
        ]
    },
    'relacoes': {
        'nome': 'Relações Interpessoais',
        'descricao': 'Fatores relacionados às interações no ambiente de trabalho',
        'icone': 'bi-people',
        'ordem': 3,
        'fatores': [
            {
                'codigo': 'REL_001',
                'nome': 'Assédio Moral',
                'descricao': 'Exposição repetitiva a situações humilhantes, constrangedoras ou vexatórias',
                'exemplos': 'Humilhação pública, isolamento proposital, sabotagem, críticas destrutivas',
                'dimensoes_hse': ['relacionamentos', 'apoio_chefia'],
                'severidade_base': 5,
                'consequencias': ['saude_mental'],
            },
            {
                'codigo': 'REL_002',
                'nome': 'Assédio Sexual',
                'descricao': 'Abordagens indesejadas de cunho sexual no ambiente de trabalho',
                'exemplos': 'Comentários inapropriados, toques não consentidos, propostas, chantagem',
                'dimensoes_hse': ['relacionamentos'],
                'severidade_base': 5,
                'consequencias': ['saude_mental'],
            },
            {
                'codigo': 'REL_003',
                'nome': 'Falta de Apoio',
                'descricao': 'Ausência de suporte de supervisores ou colegas quando necessário',
                'exemplos': 'Chefe inacessível, colegas que não colaboram, falta de mentoria',
                'dimensoes_hse': ['apoio_chefia', 'apoio_colegas'],
                'severidade_base': 3,
                'consequencias': ['saude_mental'],
            },
            {
                'codigo': 'REL_004',
                'nome': 'Isolamento Social',
                'descricao': 'Trabalho que impede ou dificulta interações com outras pessoas',
                'exemplos': 'Home office forçado, trabalho noturno sozinho, postos isolados',
                'dimensoes_hse': ['apoio_colegas', 'relacionamentos'],
                'severidade_base': 3,
                'consequencias': ['saude_mental'],
            },
            {
                'codigo': 'REL_005',
                'nome': 'Gestão Autoritária',
                'descricao': 'Liderança que não permite participação ou questionamentos',
                'exemplos': 'Microgerenciamento, punição por erros, falta de autonomia total',
                'dimensoes_hse': ['controle', 'apoio_chefia', 'comunicacao_mudancas'],
                'severidade_base': 4,
                'consequencias': ['saude_mental'],
            },
        ]
    },
    'individuais': {
        'nome': 'Fatores Individuais/Contextuais',
        'descricao': 'Fatores relacionados ao contexto e circunstâncias do trabalhador',
        'icone': 'bi-person-badge',
        'ordem': 4,
        'fatores': [
            {
                'codigo': 'IND_001',
                'nome': 'Insegurança no Emprego',
                'descricao': 'Medo constante de demissão ou precarização do vínculo',
                'exemplos': 'Contratos temporários, ameaças de corte, instabilidade econômica',
                'dimensoes_hse': ['comunicacao_mudancas'],
                'severidade_base': 4,
                'consequencias': ['saude_mental'],
            },
            {
                'codigo': 'IND_002',
                'nome': 'Desequilíbrio Vida-Trabalho',
                'descricao': 'Trabalho que invade o tempo pessoal e familiar',
                'exemplos': 'Mensagens fora do expediente, viagens constantes, falta de férias',
                'dimensoes_hse': ['demandas', 'controle'],
                'severidade_base': 4,
                'consequencias': ['saude_mental', 'saude_fisica'],
            },
            {
                'codigo': 'IND_003',
                'nome': 'Exposição a Violência',
                'descricao': 'Risco de sofrer agressões no exercício da função',
                'exemplos': 'Assaltos a motoristas, agressões a profissionais de saúde, ameaças',
                'dimensoes_hse': ['relacionamentos'],
                'severidade_base': 5,
                'consequencias': ['saude_mental', 'saude_fisica'],
            },
            {
                'codigo': 'IND_004',
                'nome': 'Traumas Ocupacionais',
                'descricao': 'Exposição a eventos traumáticos no trabalho',
                'exemplos': 'Acidentes fatais, desastres, atendimento a emergências graves',
                'dimensoes_hse': ['demandas', 'apoio_chefia'],
                'severidade_base': 5,
                'consequencias': ['saude_mental'],
            },
        ]
    }
}


class Command(BaseCommand):
    help = 'Popula dados iniciais de Fatores de Risco Psicossocial (NR-1)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Limpa dados existentes antes de popular',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        clear = options.get('clear', False)

        if clear:
            self.stdout.write(self.style.WARNING('Limpando dados existentes...'))
            FatorRisco.objects.all().delete()
            CategoriaFatorRisco.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Dados limpos com sucesso!'))

        # Verificar se já existem dados
        if CategoriaFatorRisco.objects.exists() and not clear:
            self.stdout.write(
                self.style.WARNING(
                    'Categorias já existem. Use --clear para limpar antes de popular.'
                )
            )
            return

        self.stdout.write(self.style.MIGRATE_HEADING('\nPopulando Fatores de Risco Psicossocial (NR-1)'))
        self.stdout.write(self.style.MIGRATE_LABEL('=' * 70))

        total_categorias = 0
        total_fatores = 0

        # Criar categorias e fatores
        for codigo, dados in FATORES_RISCO_DATA.items():
            self.stdout.write(f"\n📁 Categoria: {dados['nome']}")

            # Criar categoria
            categoria, created = CategoriaFatorRisco.objects.get_or_create(
                codigo=codigo,
                defaults={
                    'nome': dados['nome'],
                    'descricao': dados['descricao'],
                    'icone': dados['icone'],
                    'ordem': dados['ordem'],
                }
            )

            if created:
                total_categorias += 1
                self.stdout.write(f"  ✓ Categoria criada")
            else:
                self.stdout.write(f"  ℹ Categoria já existia")

            # Criar fatores desta categoria
            for fator_data in dados['fatores']:
                fator, created = FatorRisco.objects.get_or_create(
                    codigo=fator_data['codigo'],
                    defaults={
                        'categoria': categoria,
                        'nome': fator_data['nome'],
                        'descricao': fator_data['descricao'],
                        'exemplos': fator_data['exemplos'],
                        'severidade_base': fator_data['severidade_base'],
                        'consequencias': fator_data['consequencias'],
                        'ativo': True,
                    }
                )

                if created:
                    total_fatores += 1
                    # Mapear dimensões HSE-IT
                    for dimensao_codigo in fator_data['dimensoes_hse']:
                        try:
                            dimensao = Dimensao.objects.get(codigo=dimensao_codigo)
                            fator.dimensoes_hse.add(dimensao)
                        except Dimensao.DoesNotExist:
                            self.stdout.write(
                                self.style.WARNING(
                                    f"    ⚠ Dimensão '{dimensao_codigo}' não encontrada"
                                )
                            )

                    self.stdout.write(
                        f"  ✓ {fator_data['codigo']} - {fator_data['nome']} "
                        f"(S={fator_data['severidade_base']})"
                    )

        # Resumo final
        self.stdout.write(self.style.MIGRATE_LABEL('\n' + '=' * 70))
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Processo concluído!\n'
                f'   • {total_categorias} categorias criadas\n'
                f'   • {total_fatores} fatores de risco criados\n'
            )
        )

        # Estatísticas por categoria
        self.stdout.write(self.style.MIGRATE_HEADING('\n📊 Resumo por Categoria:'))
        for categoria in CategoriaFatorRisco.objects.all():
            total = categoria.fatores.count()
            self.stdout.write(f"   {categoria.icone} {categoria.nome}: {total} fatores")
