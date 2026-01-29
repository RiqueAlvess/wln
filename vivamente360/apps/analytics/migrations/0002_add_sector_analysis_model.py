# Generated manually on 2026-01-29

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("analytics", "0001_initial"),
        ("surveys", "0001_initial"),
        ("structure", "0001_initial"),
        ("tenants", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="SectorAnalysis",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Criado em"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="Atualizado em"),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("processing", "Processando"),
                            ("completed", "Concluído"),
                            ("failed", "Falhou"),
                        ],
                        default="processing",
                        max_length=20,
                    ),
                ),
                ("diagnostico", models.TextField(blank=True)),
                ("fatores_contribuintes", models.JSONField(default=list)),
                ("pontos_atencao", models.JSONField(default=list)),
                ("pontos_fortes", models.JSONField(default=list)),
                ("recomendacoes", models.JSONField(default=list)),
                ("impacto_esperado", models.TextField(blank=True)),
                ("alertas_sentimento", models.JSONField(default=list)),
                ("total_respostas", models.IntegerField(default=0)),
                ("scores", models.JSONField(default=dict)),
                ("generated_by", models.CharField(default="GPT-4o", max_length=100)),
                ("error_message", models.TextField(blank=True)),
                (
                    "campaign",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sector_analyses",
                        to="surveys.campaign",
                    ),
                ),
                (
                    "empresa",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sector_analyses",
                        to="tenants.empresa",
                    ),
                ),
                (
                    "setor",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="analyses",
                        to="structure.setor",
                    ),
                ),
            ],
            options={
                "verbose_name": "Análise de Setor",
                "verbose_name_plural": "Análises de Setores",
                "db_table": "analytics_sector_analysis",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="sectoranalysis",
            index=models.Index(fields=["empresa", "campaign"], name="analytics_s_empresa_idx"),
        ),
        migrations.AddIndex(
            model_name="sectoranalysis",
            index=models.Index(fields=["setor", "campaign"], name="analytics_s_setor_c_idx"),
        ),
        migrations.AddIndex(
            model_name="sectoranalysis",
            index=models.Index(fields=["status"], name="analytics_s_status_idx"),
        ),
        migrations.AlterUniqueTogether(
            name="sectoranalysis",
            unique_together={("setor", "campaign")},
        ),
    ]
