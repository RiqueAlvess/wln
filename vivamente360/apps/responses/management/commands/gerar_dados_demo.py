import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction

from apps.tenants.models import Empresa
from apps.structure.models import Unidade, Setor, Cargo
from apps.surveys.models import Campaign, Pergunta
from apps.invitations.models import SurveyInvitation
from apps.responses.models import SurveyResponse


class Command(BaseCommand):
    help = 'Gera 100 colaboradores com respostas aleatórias para demonstração'

    def add_arguments(self, parser):
        parser.add_argument(
            '--campaign-id',
            type=int,
            help='ID da campanha (opcional, usa a primeira ativa se não especificado)',
        )
        parser.add_argument(
            '--quantidade',
            type=int,
            default=100,
            help='Quantidade de colaboradores a gerar (padrão: 100)',
        )

    def handle(self, *args, **options):
        quantidade = options['quantidade']

        try:
            with transaction.atomic():
                # Buscar campanha
                campaign_id = options.get('campaign_id')
                if campaign_id:
                    campaign = Campaign.objects.get(id=campaign_id)
                else:
                    campaign = Campaign.objects.filter(status='active').first()
                    if not campaign:
                        campaign = Campaign.objects.first()

                if not campaign:
                    self.stdout.write(self.style.ERROR('Nenhuma campanha encontrada. Crie uma campanha primeiro.'))
                    return

                self.stdout.write(f'Usando campanha: {campaign.nome}')

                # Buscar empresa
                empresa = campaign.empresa

                # Buscar ou criar estruturas organizacionais
                unidades = self._criar_unidades(empresa)
                setores = self._criar_setores(unidades)
                cargos = self._criar_cargos(empresa)

                # Buscar perguntas ativas
                perguntas = list(Pergunta.objects.filter(ativo=True).order_by('numero'))
                if not perguntas:
                    self.stdout.write(self.style.ERROR('Nenhuma pergunta encontrada. Execute o comando de seed primeiro.'))
                    return

                self.stdout.write(f'Encontradas {len(perguntas)} perguntas')

                # Gerar colaboradores e respostas
                self.stdout.write(f'Gerando {quantidade} colaboradores com respostas...')

                for i in range(quantidade):
                    self._criar_colaborador_com_resposta(
                        campaign=campaign,
                        empresa=empresa,
                        unidades=unidades,
                        setores=setores,
                        cargos=cargos,
                        perguntas=perguntas,
                        numero=i+1
                    )

                    if (i + 1) % 10 == 0:
                        self.stdout.write(f'  {i + 1}/{quantidade} colaboradores criados...')

                self.stdout.write(self.style.SUCCESS(
                    f'\n✓ {quantidade} colaboradores com respostas criados com sucesso!'
                ))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erro: {str(e)}'))
            raise

    def _criar_unidades(self, empresa):
        """Cria ou busca unidades existentes"""
        nomes_unidades = [
            'Matriz',
            'Filial São Paulo',
            'Filial Rio de Janeiro',
            'Filial Belo Horizonte',
            'Filial Curitiba',
        ]

        unidades = []
        for nome in nomes_unidades:
            unidade, created = Unidade.objects.get_or_create(
                empresa=empresa,
                nome=nome,
                defaults={'ativo': True}
            )
            unidades.append(unidade)
            if created:
                self.stdout.write(f'  Unidade criada: {nome}')

        return unidades

    def _criar_setores(self, unidades):
        """Cria ou busca setores existentes"""
        nomes_setores = [
            'Administrativo',
            'Comercial',
            'Financeiro',
            'Recursos Humanos',
            'TI',
            'Operações',
            'Marketing',
            'Atendimento',
            'Logística',
            'Qualidade',
        ]

        setores = []
        for unidade in unidades:
            # Cada unidade tem alguns setores aleatórios
            num_setores = random.randint(3, 7)
            setores_unidade = random.sample(nomes_setores, num_setores)

            for nome in setores_unidade:
                setor, created = Setor.objects.get_or_create(
                    unidade=unidade,
                    nome=nome,
                    defaults={'ativo': True}
                )
                setores.append(setor)

        return setores

    def _criar_cargos(self, empresa):
        """Cria ou busca cargos existentes"""
        nomes_cargos = [
            ('Analista Jr', 'Junior'),
            ('Analista Pl', 'Pleno'),
            ('Analista Sr', 'Senior'),
            ('Assistente', 'Junior'),
            ('Coordenador', 'Gerencial'),
            ('Gerente', 'Gerencial'),
            ('Diretor', 'Executivo'),
            ('Especialista', 'Senior'),
            ('Supervisor', 'Gerencial'),
            ('Técnico', 'Junior'),
            ('Auxiliar', 'Junior'),
            ('Trainee', 'Junior'),
        ]

        cargos = []
        for nome, nivel in nomes_cargos:
            cargo, created = Cargo.objects.get_or_create(
                empresa=empresa,
                nome=nome,
                defaults={'nivel': nivel, 'ativo': True}
            )
            cargos.append(cargo)

        return cargos

    def _criar_colaborador_com_resposta(self, campaign, empresa, unidades, setores, cargos, perguntas, numero):
        """Cria um convite e uma resposta para um colaborador"""
        # Selecionar aleatoriamente estrutura organizacional
        setor = random.choice(setores)
        unidade = setor.unidade
        cargo = random.choice(cargos)

        # Dados demográficos aleatórios
        faixa_etaria = random.choice([choice[0] for choice in SurveyResponse.FAIXA_ETARIA_CHOICES])
        tempo_empresa = random.choice([choice[0] for choice in SurveyResponse.TEMPO_EMPRESA_CHOICES])
        genero = random.choice([choice[0] for choice in SurveyResponse.GENERO_CHOICES])

        # Criar convite (marcado como usado)
        dias_atras = random.randint(1, 30)
        data_resposta = timezone.now() - timedelta(days=dias_atras)

        invitation = SurveyInvitation.objects.create(
            email_encrypted=f'demo{numero}@example.com',  # Dados fictícios
            nome_encrypted=f'Colaborador Demo {numero}',
            empresa=empresa,
            campaign=campaign,
            unidade=unidade,
            setor=setor,
            cargo=cargo,
            status='used',
            expires_at=timezone.now() + timedelta(days=30),
            sent_at=data_resposta - timedelta(hours=2),
            used_at=data_resposta,
        )

        # Gerar respostas aleatórias para cada pergunta
        # Escala Likert de 1 a 5
        respostas_dict = {}
        for pergunta in perguntas:
            # Criar distribuição mais realista (tendência para valores médios/altos)
            # 70% entre 3-5, 30% entre 1-2
            if random.random() < 0.7:
                valor = random.randint(3, 5)
            else:
                valor = random.randint(1, 2)

            respostas_dict[str(pergunta.id)] = valor

        # Criar resposta
        SurveyResponse.objects.create(
            campaign=campaign,
            unidade=unidade,
            setor=setor,
            cargo=cargo,
            faixa_etaria=faixa_etaria,
            tempo_empresa=tempo_empresa,
            genero=genero,
            respostas=respostas_dict,
            lgpd_aceito=True,
            lgpd_aceito_em=data_resposta,
            created_at=data_resposta,
            updated_at=data_resposta,
        )
