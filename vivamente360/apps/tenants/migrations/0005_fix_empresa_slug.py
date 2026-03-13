from django.db import connection, migrations
from django.utils.text import slugify


def add_slug_column_if_missing(apps, schema_editor):
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'tenants_empresa' AND column_name = 'slug'"
        )
        if not cursor.fetchone():
            cursor.execute(
                "ALTER TABLE \"tenants_empresa\" ADD COLUMN \"slug\" varchar(255) NOT NULL DEFAULT ''"
            )


def generate_missing_slugs(apps, schema_editor):
    Empresa = apps.get_model('tenants', 'Empresa')
    for empresa in Empresa.objects.filter(slug=''):
        base_slug = slugify(empresa.nome)
        slug = base_slug
        counter = 1
        while Empresa.objects.filter(slug=slug).exclude(pk=empresa.pk).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        empresa.slug = slug
        empresa.save(update_fields=['slug'])


def add_unique_constraint_if_missing(apps, schema_editor):
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT 1 FROM pg_constraint "
            "WHERE conrelid = 'tenants_empresa'::regclass AND conname = 'tenants_empresa_slug_key'"
        )
        if cursor.fetchone():
            return
        cursor.execute(
            "SELECT 1 FROM pg_indexes "
            "WHERE tablename = 'tenants_empresa' AND indexname LIKE '%slug%unique%' "
            "   OR (tablename = 'tenants_empresa' AND indexname = 'tenants_empresa_slug_304ba91f_like')"
        )
        if cursor.fetchone():
            return
        cursor.execute(
            'ALTER TABLE "tenants_empresa" ADD CONSTRAINT "tenants_empresa_slug_key" UNIQUE ("slug")'
        )


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ('tenants', '0004_empresa_slug'),
    ]

    operations = [
        migrations.RunPython(add_slug_column_if_missing, migrations.RunPython.noop),
        migrations.RunPython(generate_missing_slugs, migrations.RunPython.noop),
        migrations.RunPython(add_unique_constraint_if_missing, migrations.RunPython.noop),
    ]
