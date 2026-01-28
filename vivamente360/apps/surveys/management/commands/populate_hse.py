from django.core.management.base import BaseCommand
from apps.surveys.models import Dimensao, Pergunta


class Command(BaseCommand):
    help = 'Popula banco de dados com as 7 dimensões e 35 perguntas do HSE-IT'

    def handle(self, *args, **options):
        self.stdout.write('Populando dimensões HSE-IT...')

        dimensoes_data = [
            {"codigo": "demandas", "nome": "Demandas", "tipo": "negativo", "ordem": 1,
             "descricao": "Carga de trabalho, ritmo e exigências do trabalho"},
            {"codigo": "controle", "nome": "Controle", "tipo": "positivo", "ordem": 2,
             "descricao": "Autonomia e participação nas decisões sobre o trabalho"},
            {"codigo": "apoio_chefia", "nome": "Apoio da Chefia", "tipo": "positivo", "ordem": 3,
             "descricao": "Suporte e feedback recebidos da liderança"},
            {"codigo": "apoio_colegas", "nome": "Apoio dos Colegas", "tipo": "positivo", "ordem": 4,
             "descricao": "Suporte e colaboração entre colegas de trabalho"},
            {"codigo": "relacionamentos", "nome": "Relacionamentos", "tipo": "negativo", "ordem": 5,
             "descricao": "Conflitos e tensões interpessoais no ambiente de trabalho"},
            {"codigo": "cargo", "nome": "Cargo/Função", "tipo": "positivo", "ordem": 6,
             "descricao": "Clareza sobre papéis, responsabilidades e expectativas"},
            {"codigo": "comunicacao_mudancas", "nome": "Comunicação e Mudanças", "tipo": "positivo", "ordem": 7,
             "descricao": "Clareza na comunicação e gestão de mudanças organizacionais"},
        ]

        dimensoes = {}
        for dim_data in dimensoes_data:
            dim, created = Dimensao.objects.get_or_create(
                codigo=dim_data['codigo'],
                defaults={
                    'nome': dim_data['nome'],
                    'tipo': dim_data['tipo'],
                    'ordem': dim_data['ordem'],
                    'descricao': dim_data['descricao'],
                }
            )
            dimensoes[dim_data['codigo']] = dim
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Criada dimensão: {dim.nome}'))
            else:
                self.stdout.write(f'  Dimensão já existe: {dim.nome}')

        self.stdout.write('\nPopulando perguntas HSE-IT...')

        perguntas_data = [
            (1, "cargo", "Eu sei exatamente o que é esperado de mim no trabalho"),
            (2, "controle", "Posso decidir quando fazer uma pausa"),
            (3, "demandas", "Diferentes grupos no trabalho exigem coisas de mim que são difíceis de combinar"),
            (4, "cargo", "Eu sei como fazer meu trabalho"),
            (5, "relacionamentos", "Estou sujeito a atenção pessoal ou assédio na forma de palavras ou comportamentos ofensivos"),
            (6, "demandas", "Tenho prazos inatingíveis"),
            (7, "apoio_colegas", "Se o trabalho fica difícil, meus colegas me ajudam"),
            (8, "apoio_chefia", "Sou apoiado(a) em uma crise emocional no trabalho"),
            (9, "demandas", "Tenho que trabalhar muito intensamente"),
            (10, "controle", "Tenho voz nas mudanças no modo como faço meu trabalho"),
            (11, "cargo", "Tenho tempo suficiente para completar meu trabalho"),
            (12, "demandas", "Tenho que desconsiderar regras ou procedimentos para fazer o trabalho"),
            (13, "cargo", "Sei qual é o meu papel e responsabilidades"),
            (14, "relacionamentos", "Tenho que trabalhar com pessoas que têm valores de trabalho diferentes"),
            (15, "controle", "Posso planejar quando fazer as pausas"),
            (16, "demandas", "Tenho volume de trabalho pesado"),
            (17, "cargo", "Existe uma boa combinação entre o que a organização espera de mim e as habilidades que tenho"),
            (18, "demandas", "Tenho que trabalhar muito rapidamente"),
            (19, "controle", "Tenho uma palavra a dizer sobre o ritmo em que trabalho"),
            (20, "demandas", "Tenho que negligenciar alguns aspectos do meu trabalho porque tenho muito a fazer"),
            (21, "relacionamentos", "Existe fricção ou raiva entre colegas"),
            (22, "demandas", "Não tenho tempo para fazer uma pausa"),
            (23, "apoio_chefia", "Minha chefia imediata me encoraja no trabalho"),
            (24, "apoio_colegas", "Recebo o respeito no trabalho que mereço de meus colegas"),
            (25, "controle", "Tenho controle sobre quando fazer uma pausa"),
            (26, "comunicacao_mudancas", "Os funcionários são sempre consultados sobre mudanças no trabalho"),
            (27, "apoio_colegas", "Posso contar com meus colegas para me ajudar quando as coisas ficam difíceis no trabalho"),
            (28, "comunicacao_mudancas", "Posso conversar com minha chefia sobre algo que me incomodou"),
            (29, "apoio_chefia", "Minha chefia me apoia para o trabalho"),
            (30, "controle", "Tenho alguma participação em decisões sobre o meu trabalho"),
            (31, "apoio_colegas", "Recebo ajuda e apoio de meus colegas"),
            (32, "comunicacao_mudancas", "Quando ocorrem mudanças no trabalho, tenho clareza sobre como funcionará na prática"),
            (33, "apoio_chefia", "Recebo feedback sobre o meu trabalho"),
            (34, "relacionamentos", "Existe tensão entre mim e colegas de trabalho"),
            (35, "apoio_chefia", "Minha chefia me incentiva nas minhas atividades"),
        ]

        created_count = 0
        for numero, dimensao_codigo, texto in perguntas_data:
            dimensao = dimensoes[dimensao_codigo]
            pergunta, created = Pergunta.objects.get_or_create(
                numero=numero,
                dimensao=dimensao,
                defaults={
                    'texto': texto,
                    'ordem': numero,
                }
            )
            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f'\n✓ Criadas {created_count} perguntas'))
        self.stdout.write(self.style.SUCCESS('✓ Processo concluído!'))
