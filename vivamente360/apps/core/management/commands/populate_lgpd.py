from django.core.management.base import BaseCommand
from apps.tenants.models import Empresa
from apps.core.models import LGPDComplianceItem


class Command(BaseCommand):
    help = 'Popula os itens padrão de conformidade LGPD para cada empresa'

    LGPD_ITEMS = [
        {
            'ordem': 1,
            'item': 'Mapeamento de Dados Pessoais',
            'descricao': 'Realizar inventário completo de todos os dados pessoais coletados, processados e armazenados pela organização, incluindo categorias de dados, finalidades, bases legais e fluxos de compartilhamento.'
        },
        {
            'ordem': 2,
            'item': 'Política de Privacidade e Termos de Uso',
            'descricao': 'Elaborar e publicar política de privacidade clara e acessível, detalhando como os dados pessoais são tratados, direitos dos titulares e informações de contato do DPO/encarregado.'
        },
        {
            'ordem': 3,
            'item': 'Base Legal para Tratamento de Dados',
            'descricao': 'Identificar e documentar a base legal adequada (consentimento, legítimo interesse, cumprimento de obrigação legal, etc.) para cada atividade de tratamento de dados pessoais.'
        },
        {
            'ordem': 4,
            'item': 'Gestão de Consentimento',
            'descricao': 'Implementar mecanismos para obter, registrar, gerenciar e revogar o consentimento dos titulares de dados de forma clara, específica e inequívoca.'
        },
        {
            'ordem': 5,
            'item': 'Direitos dos Titulares',
            'descricao': 'Estabelecer processos para atender solicitações de titulares (confirmação, acesso, correção, anonimização, portabilidade, eliminação de dados) dentro dos prazos legais.'
        },
        {
            'ordem': 6,
            'item': 'Segurança da Informação',
            'descricao': 'Implementar medidas técnicas e administrativas de segurança adequadas para proteger dados pessoais contra acessos não autorizados, vazamentos, perda ou destruição acidental.'
        },
        {
            'ordem': 7,
            'item': 'Nomeação do Encarregado (DPO)',
            'descricao': 'Nomear um encarregado de proteção de dados (DPO) responsável por supervisionar a conformidade com a LGPD, servir como ponto de contato e orientar práticas de proteção de dados.'
        },
        {
            'ordem': 8,
            'item': 'Resposta a Incidentes de Segurança',
            'descricao': 'Desenvolver e testar plano de resposta a incidentes de segurança, incluindo procedimentos para comunicação à ANPD e aos titulares afetados em caso de vazamento de dados.'
        },
        {
            'ordem': 9,
            'item': 'Contratos e Terceiros',
            'descricao': 'Revisar e adequar contratos com fornecedores, operadores e parceiros que processam dados pessoais, garantindo cláusulas de proteção de dados e responsabilidade compartilhada.'
        },
        {
            'ordem': 10,
            'item': 'Treinamento e Conscientização',
            'descricao': 'Realizar treinamentos regulares para colaboradores sobre princípios da LGPD, boas práticas de proteção de dados e responsabilidades individuais na proteção de informações pessoais.'
        }
    ]

    def handle(self, *args, **options):
        empresas = Empresa.objects.all()

        if not empresas.exists():
            self.stdout.write(self.style.WARNING('Nenhuma empresa encontrada no sistema.'))
            return

        total_created = 0
        total_skipped = 0

        for empresa in empresas:
            self.stdout.write(f'\nProcessando empresa: {empresa.nome}')

            for item_data in self.LGPD_ITEMS:
                # Verificar se o item já existe para esta empresa
                item, created = LGPDComplianceItem.objects.get_or_create(
                    empresa=empresa,
                    ordem=item_data['ordem'],
                    defaults={
                        'item': item_data['item'],
                        'descricao': item_data['descricao'],
                    }
                )

                if created:
                    total_created += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✓ Criado: {item_data["item"]}')
                    )
                else:
                    total_skipped += 1
                    self.stdout.write(
                        self.style.WARNING(f'  - Já existe: {item_data["item"]}')
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n\nResumo:\n'
                f'  Itens criados: {total_created}\n'
                f'  Itens já existentes: {total_skipped}\n'
                f'  Total de empresas processadas: {empresas.count()}'
            )
        )
