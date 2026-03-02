from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        'Placeholder — tabelas data-warehouse (DimTempo, FactScoreDimensao, etc.) '
        'foram removidas na migration analytics/0004. Analytics são calculados '
        'on-the-fly via DashboardSelectors a partir de SurveyResponse.'
    )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.WARNING(
                'rebuild_analytics: tabelas data-warehouse removidas. '
                'Métricas do dashboard são calculadas on-the-fly. '
                'Este comando é agora um no-op.'
            )
        )
