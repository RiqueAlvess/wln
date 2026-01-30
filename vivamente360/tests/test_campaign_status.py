"""
Testes para validar a funcionalidade de gestão de status de campanhas
e invalidação de links.

Para executar:
    python manage.py test tests.test_campaign_status
"""

from django.test import TestCase
from django.utils import timezone
from datetime import timedelta, date
from apps.surveys.models import Campaign
from apps.invitations.models import SurveyInvitation
from apps.tenants.models import Empresa
from apps.structure.models import Unidade, Setor, Cargo
from tasks.campaign_tasks import verificar_campanhas_expiradas


class CampaignStatusTestCase(TestCase):
    """Testes para gestão de status de campanhas"""

    def setUp(self):
        """Configurar dados de teste"""
        # Criar empresa
        self.empresa = Empresa.objects.create(
            nome='Empresa Teste',
            cnpj='12345678901234'
        )

        # Criar estrutura organizacional
        self.unidade = Unidade.objects.create(
            empresa=self.empresa,
            nome='Unidade Teste'
        )

        self.setor = Setor.objects.create(
            empresa=self.empresa,
            nome='Setor Teste'
        )

        self.cargo = Cargo.objects.create(
            empresa=self.empresa,
            nome='Cargo Teste'
        )

        # Criar campanha ativa
        self.campanha = Campaign.objects.create(
            empresa=self.empresa,
            nome='Campanha Teste',
            descricao='Descrição de teste',
            status='active',
            data_inicio=date.today(),
            data_fim=date.today() + timedelta(days=30)
        )

    def test_contar_convites_ativos(self):
        """Testar contagem de convites ativos"""
        # Criar convites com diferentes status
        SurveyInvitation.objects.create(
            empresa=self.empresa,
            campaign=self.campanha,
            unidade=self.unidade,
            setor=self.setor,
            cargo=self.cargo,
            email_encrypted='test1@example.com',
            status='pending',
            expires_at=timezone.now() + timedelta(hours=48)
        )

        SurveyInvitation.objects.create(
            empresa=self.empresa,
            campaign=self.campanha,
            unidade=self.unidade,
            setor=self.setor,
            cargo=self.cargo,
            email_encrypted='test2@example.com',
            status='sent',
            expires_at=timezone.now() + timedelta(hours=48)
        )

        SurveyInvitation.objects.create(
            empresa=self.empresa,
            campaign=self.campanha,
            unidade=self.unidade,
            setor=self.setor,
            cargo=self.cargo,
            email_encrypted='test3@example.com',
            status='used',
            expires_at=timezone.now() + timedelta(hours=48)
        )

        # Contar convites
        resultado = self.campanha.contar_convites_ativos()

        self.assertEqual(resultado['pendentes'], 1)
        self.assertEqual(resultado['enviados'], 1)
        self.assertEqual(resultado['total_ativos'], 2)

    def test_encerrar_campanha_ativa(self):
        """Testar encerramento de campanha ativa"""
        # Criar convites
        for i in range(5):
            SurveyInvitation.objects.create(
                empresa=self.empresa,
                campaign=self.campanha,
                unidade=self.unidade,
                setor=self.setor,
                cargo=self.cargo,
                email_encrypted=f'test{i}@example.com',
                status='pending' if i < 3 else 'sent',
                expires_at=timezone.now() + timedelta(hours=48)
            )

        # Encerrar campanha
        resultado = self.campanha.encerrar()

        # Verificar resultado
        self.assertTrue(resultado['success'])
        self.assertEqual(resultado['invalidated_count'], 5)

        # Verificar status da campanha
        self.campanha.refresh_from_db()
        self.assertEqual(self.campanha.status, 'closed')

        # Verificar que todos os convites foram invalidados
        convites_expirados = SurveyInvitation.objects.filter(
            campaign=self.campanha,
            status='expired'
        ).count()
        self.assertEqual(convites_expirados, 5)

    def test_encerrar_campanha_ja_encerrada(self):
        """Testar tentativa de encerrar campanha já encerrada"""
        # Encerrar campanha
        self.campanha.status = 'closed'
        self.campanha.save()

        # Tentar encerrar novamente
        resultado = self.campanha.encerrar()

        # Verificar que retorna erro
        self.assertFalse(resultado['success'])
        self.assertEqual(resultado['invalidated_count'], 0)
        self.assertIn('já está encerrada', resultado['message'])

    def test_verificar_campanhas_expiradas(self):
        """Testar task de verificação de campanhas expiradas"""
        # Criar campanha expirada
        campanha_expirada = Campaign.objects.create(
            empresa=self.empresa,
            nome='Campanha Expirada',
            status='active',
            data_inicio=date.today() - timedelta(days=60),
            data_fim=date.today() - timedelta(days=30)
        )

        # Criar convites para campanha expirada
        for i in range(3):
            SurveyInvitation.objects.create(
                empresa=self.empresa,
                campaign=campanha_expirada,
                unidade=self.unidade,
                setor=self.setor,
                cargo=self.cargo,
                email_encrypted=f'expired{i}@example.com',
                status='pending',
                expires_at=timezone.now() + timedelta(hours=48)
            )

        # Executar task
        estatisticas = verificar_campanhas_expiradas()

        # Verificar estatísticas
        self.assertEqual(estatisticas['campanhas_encerradas'], 1)
        self.assertEqual(estatisticas['total_convites_invalidados'], 3)

        # Verificar que campanha foi encerrada
        campanha_expirada.refresh_from_db()
        self.assertEqual(campanha_expirada.status, 'closed')

        # Verificar que campanha ativa NÃO foi encerrada
        self.campanha.refresh_from_db()
        self.assertEqual(self.campanha.status, 'active')

    def test_nao_invalidar_convites_ja_usados(self):
        """Testar que convites já usados não são alterados"""
        # Criar convites
        SurveyInvitation.objects.create(
            empresa=self.empresa,
            campaign=self.campanha,
            unidade=self.unidade,
            setor=self.setor,
            cargo=self.cargo,
            email_encrypted='used@example.com',
            status='used',
            expires_at=timezone.now() + timedelta(hours=48)
        )

        SurveyInvitation.objects.create(
            empresa=self.empresa,
            campaign=self.campanha,
            unidade=self.unidade,
            setor=self.setor,
            cargo=self.cargo,
            email_encrypted='pending@example.com',
            status='pending',
            expires_at=timezone.now() + timedelta(hours=48)
        )

        # Encerrar campanha
        resultado = self.campanha.encerrar()

        # Verificar que apenas 1 convite foi invalidado
        self.assertEqual(resultado['invalidated_count'], 1)

        # Verificar que convite usado permanece como 'used'
        convite_usado = SurveyInvitation.objects.get(
            email_encrypted='used@example.com'
        )
        self.assertEqual(convite_usado.status, 'used')


class CampaignTaskTestCase(TestCase):
    """Testes para tasks de campanha"""

    def setUp(self):
        """Configurar dados de teste"""
        self.empresa = Empresa.objects.create(
            nome='Empresa Teste',
            cnpj='12345678901234'
        )

    def test_verificar_campanhas_sem_expiradas(self):
        """Testar task quando não há campanhas expiradas"""
        # Criar campanha ativa e no prazo
        Campaign.objects.create(
            empresa=self.empresa,
            nome='Campanha Ativa',
            status='active',
            data_inicio=date.today(),
            data_fim=date.today() + timedelta(days=30)
        )

        # Executar task
        estatisticas = verificar_campanhas_expiradas()

        # Verificar que nada foi encerrado
        self.assertEqual(estatisticas['campanhas_encerradas'], 0)
        self.assertEqual(estatisticas['total_convites_invalidados'], 0)

    def test_nao_encerrar_campanhas_draft_ou_closed(self):
        """Testar que apenas campanhas ativas são encerradas"""
        # Criar campanhas em diferentes status
        Campaign.objects.create(
            empresa=self.empresa,
            nome='Campanha Draft Expirada',
            status='draft',
            data_inicio=date.today() - timedelta(days=60),
            data_fim=date.today() - timedelta(days=30)
        )

        Campaign.objects.create(
            empresa=self.empresa,
            nome='Campanha Já Encerrada',
            status='closed',
            data_inicio=date.today() - timedelta(days=60),
            data_fim=date.today() - timedelta(days=30)
        )

        # Executar task
        estatisticas = verificar_campanhas_expiradas()

        # Verificar que nenhuma campanha foi encerrada
        self.assertEqual(estatisticas['campanhas_encerradas'], 0)


if __name__ == '__main__':
    print("Execute os testes com: python manage.py test tests.test_campaign_status")
