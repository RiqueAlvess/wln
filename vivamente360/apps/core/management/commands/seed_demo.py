"""
Comando para popular o banco com dados de demonstração.

Cria:
  - 1 Empresa
  - 3 Unidades com 2-3 Setores cada
  - 5 Cargos
  - 1 Campanha ativa
  - 80 respostas anônimas com distribuição realista de riscos

Uso:
    python manage.py seed_demo --settings=config.settings.development
    python manage.py seed_demo --clear  # apaga dados anteriores antes de criar
"""

import random
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify

User = get_user_model()


# Mapeamento de perguntas por dimensão (igual ao score_service.py)
DIMENSOES = {
    "demandas":            [3, 6, 9, 12, 16, 18, 20, 22],
    "controle":            [2, 10, 15, 19, 25, 30],
    "apoio_chefia":        [8, 23, 29, 33, 35],
    "apoio_colegas":       [7, 24, 27, 31],
    "relacionamentos":     [5, 14, 21, 34],
    "cargo":               [1, 4, 11, 13, 17],
    "comunicacao_mudancas":[26, 28, 32],
}

# Perfis de risco: peso (0-4) por dimensão para simular padrões diferentes
# demandas e relacionamentos são negativas (score alto = mais risco)
# restantes são positivas (score baixo = mais risco)
PERFIS = {
    "alto_risco": {
        "demandas": (3, 4),         # negativa: score alto → risco alto
        "controle": (0, 1),         # positiva: score baixo → risco alto
        "apoio_chefia": (0, 1),
        "apoio_colegas": (1, 2),
        "relacionamentos": (3, 4),  # negativa: score alto → risco alto
        "cargo": (0, 1),
        "comunicacao_mudancas": (0, 1),
    },
    "moderado": {
        "demandas": (2, 3),
        "controle": (2, 3),
        "apoio_chefia": (2, 3),
        "apoio_colegas": (2, 3),
        "relacionamentos": (1, 2),
        "cargo": (2, 3),
        "comunicacao_mudancas": (2, 3),
    },
    "baixo_risco": {
        "demandas": (0, 1),
        "controle": (3, 4),
        "apoio_chefia": (3, 4),
        "apoio_colegas": (3, 4),
        "relacionamentos": (0, 1),
        "cargo": (3, 4),
        "comunicacao_mudancas": (3, 4),
    },
}


def _gerar_respostas(perfil_nome: str) -> dict:
    """Gera o JSONField `respostas` simulando um perfil de risco."""
    perfil = PERFIS[perfil_nome]
    respostas = {}
    for dimensao, perguntas in DIMENSOES.items():
        low, high = perfil[dimensao]
        for p in perguntas:
            respostas[str(p)] = str(random.randint(low, high))
    return respostas


class Command(BaseCommand):
    help = "Popula o banco com dados de demonstração (empresa, campanha e respostas)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Remove dados de demo anteriores antes de criar novos",
        )
        parser.add_argument(
            "--respostas",
            type=int,
            default=80,
            help="Quantidade de respostas a gerar (padrão: 80)",
        )

    def handle(self, *args, **options):
        from apps.responses.models import SurveyResponse
        from apps.structure.models import Cargo, Setor, Unidade
        from apps.surveys.models import Campaign, Dimensao
        from apps.tenants.models import Empresa

        total_respostas = options["respostas"]

        if options["clear"]:
            self._clear(Empresa, Campaign, SurveyResponse, Unidade, Setor, Cargo)

        # ── 1. Empresa ────────────────────────────────────────────────────
        empresa, created = Empresa.objects.get_or_create(
            cnpj="12.345.678/0001-99",
            defaults={
                "nome": "Demo Indústria e Comércio Ltda",
                "slug": "demo-industria-e-comercio",
                "total_funcionarios": 320,
                "cnae": "62.01-5",
                "cnae_descricao": "Desenvolvimento de programas de computador sob encomenda",
                "cor_primaria": "#0d6efd",
                "cor_secundaria": "#6c757d",
                "cor_fonte": "#ffffff",
                "nome_app": "VIVAMENTE 360º Demo",
                "ativo": True,
            },
        )
        self._log(created, "Empresa", empresa.nome)

        # ── 2. Estrutura organizacional ───────────────────────────────────
        estrutura = {
            "Unidade São Paulo": ["Tecnologia", "Comercial", "Financeiro"],
            "Unidade Rio de Janeiro": ["Operações", "RH"],
            "Unidade Belo Horizonte": ["Suporte", "Logística"],
        }

        unidades, setores_por_unidade = [], {}
        for nome_unidade, nomes_setores in estrutura.items():
            codigo = slugify(nome_unidade).replace("-", "")[:20].upper()
            unidade, created = Unidade.objects.get_or_create(
                empresa=empresa,
                nome=nome_unidade,
                defaults={"codigo": codigo, "ativo": True},
            )
            self._log(created, "Unidade", nome_unidade)
            unidades.append(unidade)
            setores_por_unidade[unidade] = []
            for nome_setor in nomes_setores:
                cod_setor = slugify(nome_setor).replace("-", "")[:20].upper()
                setor, created = Setor.objects.get_or_create(
                    unidade=unidade,
                    nome=nome_setor,
                    defaults={"codigo": cod_setor, "ativo": True},
                )
                self._log(created, "  Setor", nome_setor)
                setores_por_unidade[unidade].append(setor)

        # ── 3. Cargos ─────────────────────────────────────────────────────
        cargos_data = [
            ("Analista", "junior"),
            ("Desenvolvedor Sênior", "senior"),
            ("Gerente", "gerencia"),
            ("Coordenador", "coordenacao"),
            ("Assistente Administrativo", "junior"),
        ]
        for nome_cargo, nivel in cargos_data:
            cargo, created = Cargo.objects.get_or_create(
                empresa=empresa,
                nome=nome_cargo,
                defaults={"nivel": nivel, "ativo": True},
            )
            self._log(created, "Cargo", nome_cargo)

        # ── 4. Verifica dimensões HSE-IT ──────────────────────────────────
        if not Dimensao.objects.exists():
            self.stdout.write(self.style.WARNING(
                "  Aviso: dimensões HSE-IT não encontradas. "
                "Execute 'python manage.py populate_hse' primeiro."
            ))

        # ── 5. Campanha ───────────────────────────────────────────────────
        hoje = date.today()
        campaign, created = Campaign.objects.get_or_create(
            empresa=empresa,
            nome="Campanha Demo 2025 – Saúde Psicossocial",
            defaults={
                "descricao": (
                    "Campanha de demonstração para avaliação dos fatores "
                    "de risco psicossocial conforme NR-1."
                ),
                "status": "active",
                "data_inicio": hoje - timedelta(days=30),
                "data_fim": hoje + timedelta(days=30),
                "created_by": User.objects.filter(is_superuser=True).first()
                    or User.objects.first(),
            },
        )
        self._log(created, "Campanha", campaign.nome)

        if not created and options["clear"] is False:
            self.stdout.write(self.style.WARNING(
                "  Campanha já existe. Use --clear para recriar as respostas."
            ))

        # ── 6. Respostas anônimas ─────────────────────────────────────────
        existentes = SurveyResponse.objects.filter(campaign=campaign).count()
        if existentes and not options["clear"]:
            self.stdout.write(
                f"  Campanha já possui {existentes} respostas. "
                "Use --clear para recriar."
            )
        else:
            todos_setores = [
                (unidade, setor)
                for unidade, setores in setores_por_unidade.items()
                for setor in setores
            ]

            # Distribuição: 30 % alto risco, 45 % moderado, 25 % baixo risco
            perfis_pool = (
                ["alto_risco"] * int(total_respostas * 0.30)
                + ["moderado"] * int(total_respostas * 0.45)
                + ["baixo_risco"] * int(total_respostas * 0.25)
            )
            # Completa até total_respostas com moderado
            while len(perfis_pool) < total_respostas:
                perfis_pool.append("moderado")
            random.shuffle(perfis_pool)

            faixas = ["18-24", "25-34", "35-49", "50-59", "60+"]
            tempos = ["0-1", "1-3", "3-5", "5-10", "10+"]
            generos = ["M", "F", "O", "N"]
            genero_pesos = [0.45, 0.45, 0.07, 0.03]

            bulk = []
            for i, perfil_nome in enumerate(perfis_pool):
                unidade, setor = random.choice(todos_setores)
                genero = random.choices(generos, weights=genero_pesos, k=1)[0]
                bulk.append(SurveyResponse(
                    campaign=campaign,
                    unidade=unidade,
                    setor=setor,
                    faixa_etaria=random.choice(faixas),
                    tempo_empresa=random.choice(tempos),
                    genero=genero,
                    respostas=_gerar_respostas(perfil_nome),
                    lgpd_aceito=True,
                    lgpd_aceito_em=timezone.now(),
                ))

            SurveyResponse.objects.bulk_create(bulk)
            self.stdout.write(self.style.SUCCESS(
                f"  ✓ {len(bulk)} respostas criadas "
                f"(30 % alto risco / 45 % moderado / 25 % baixo risco)"
            ))

        # ── 7. Rebuild analytics (se disponível) ──────────────────────────
        try:
            from django.core import management
            self.stdout.write("\nRecalculando analytics...")
            management.call_command(
                "rebuild_analytics",
                campaign=campaign.pk,
                verbosity=0,
            )
            self.stdout.write(self.style.SUCCESS("  ✓ Analytics recalculados"))
        except Exception:
            self.stdout.write(
                "  (rebuild_analytics ignorado — rode manualmente se necessário)"
            )

        # ── Resumo ────────────────────────────────────────────────────────
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write(self.style.SUCCESS("  Demo populado com sucesso!"))
        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write(f"  Empresa : {empresa.nome}")
        self.stdout.write(f"  Campanha: {campaign.nome}")
        self.stdout.write(f"  Status  : {campaign.status}")
        self.stdout.write(f"  Respostas no banco: "
                          f"{SurveyResponse.objects.filter(campaign=campaign).count()}")
        self.stdout.write("")
        self.stdout.write("  Próximos passos:")
        self.stdout.write("    1. Crie um superusuário: make superuser")
        self.stdout.write("    2. Inicie o servidor  : make run")
        self.stdout.write("    3. Acesse o dashboard em /dashboard/")

    # ── helpers ───────────────────────────────────────────────────────────

    def _log(self, created: bool, tipo: str, nome: str):
        if created:
            self.stdout.write(self.style.SUCCESS(f"  ✓ {tipo} criado: {nome}"))
        else:
            self.stdout.write(f"  · {tipo} já existe: {nome}")

    def _clear(self, Empresa, Campaign, SurveyResponse, Unidade, Setor, Cargo):
        self.stdout.write(self.style.WARNING("Removendo dados de demo anteriores..."))
        empresa_qs = Empresa.objects.filter(cnpj="12.345.678/0001-99")
        if empresa_qs.exists():
            empresa = empresa_qs.first()
            camp_ids = Campaign.objects.filter(empresa=empresa).values_list("id", flat=True)
            deleted, _ = SurveyResponse.objects.filter(campaign_id__in=camp_ids).delete()
            self.stdout.write(f"  · {deleted} respostas removidas")
            Campaign.objects.filter(empresa=empresa).delete()
            Setor.objects.filter(unidade__empresa=empresa).delete()
            Unidade.objects.filter(empresa=empresa).delete()
            Cargo.objects.filter(empresa=empresa).delete()
            empresa_qs.delete()
            self.stdout.write(self.style.SUCCESS("  ✓ Dados removidos"))
        else:
            self.stdout.write("  · Nenhum dado de demo encontrado")
