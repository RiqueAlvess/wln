# Removes unused data-warehouse models (DimTempo, DimEstrutura, DimDemografia,
# DimDimensaoHSE, FactScoreDimensao, FactIndicadorCampanha, FactRespostaPergunta)
# that were never queried. SectorAnalysis is preserved.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("analytics", "0003_rename_analytics_s_empresa_idx_analytics_s_empresa_93b4f0_idx_and_more"),
    ]

    operations = [
        migrations.DeleteModel(name="FactRespostaPergunta"),
        migrations.DeleteModel(name="FactIndicadorCampanha"),
        migrations.DeleteModel(name="FactScoreDimensao"),
        migrations.DeleteModel(name="DimDimensaoHSE"),
        migrations.DeleteModel(name="DimDemografia"),
        migrations.DeleteModel(name="DimEstrutura"),
        migrations.DeleteModel(name="DimTempo"),
    ]
