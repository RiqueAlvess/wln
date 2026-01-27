from django.core.management.base import BaseCommand
from apps.surveys.models import Campaign
from tasks.analytics_tasks import rebuild_campaign_analytics


class Command(BaseCommand):
    help = 'Reconstrói tabelas analíticas'

    def add_arguments(self, parser):
        parser.add_argument('--campaign', type=int, help='ID da campanha específica')

    def handle(self, *args, **options):
        campaign_id = options.get('campaign')

        if campaign_id:
            try:
                campaign = Campaign.objects.get(pk=campaign_id)
                self.stdout.write(f'Reconstruindo analytics para {campaign.nome}...')
                rebuild_campaign_analytics(campaign)
                self.stdout.write(self.style.SUCCESS(f'Concluído para {campaign.nome}'))
            except Campaign.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Campanha {campaign_id} não encontrada'))
        else:
            campaigns = Campaign.objects.filter(status__in=['active', 'closed'])
            self.stdout.write(f'Reconstruindo analytics para {campaigns.count()} campanhas...')

            for campaign in campaigns:
                self.stdout.write(f'Processando {campaign.nome}...')
                rebuild_campaign_analytics(campaign)

            self.stdout.write(self.style.SUCCESS('Concluído para todas as campanhas'))
