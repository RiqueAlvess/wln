from django.db import connection, migrations, models
from django.utils.text import slugify


def generate_slugs(apps, schema_editor):
    Empresa = apps.get_model('tenants', 'Empresa')
    for empresa in Empresa.objects.all():
        base_slug = slugify(empresa.nome)
        slug = base_slug
        counter = 1
        while Empresa.objects.filter(slug=slug).exclude(pk=empresa.pk).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        empresa.slug = slug
        empresa.save(update_fields=['slug'])


def add_slug_field_if_not_exists(apps, schema_editor):
    """Add slug column only if it doesn't already exist."""
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'tenants_empresa' AND column_name = 'slug'"
        )
        if not cursor.fetchone():
            cursor.execute(
                'ALTER TABLE "tenants_empresa" ADD COLUMN "slug" varchar(255) '
                "NOT NULL DEFAULT ''"
            )


def make_slug_unique_if_not_already(apps, schema_editor):
    """Add unique constraint on slug only if it doesn't already exist."""
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT 1 FROM pg_indexes "
            "WHERE tablename = 'tenants_empresa' AND indexname = 'tenants_empresa_slug_304ba91f_like'"
        )
        if cursor.fetchone():
            return
        cursor.execute(
            'ALTER TABLE "tenants_empresa" ADD CONSTRAINT '
            '"tenants_empresa_slug_key" UNIQUE ("slug")'
        )


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0003_add_cor_fonte'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name='empresa',
                    name='slug',
                    field=models.SlugField(
                        blank=True,
                        default='',
                        help_text='Slug para URLs públicas (gerado automaticamente)',
                        max_length=255,
                    ),
                    preserve_default=False,
                ),
            ],
            database_operations=[
                migrations.RunPython(add_slug_field_if_not_exists, migrations.RunPython.noop),
            ],
        ),
        migrations.RunPython(generate_slugs, migrations.RunPython.noop),
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name='empresa',
                    name='slug',
                    field=models.SlugField(
                        blank=True,
                        help_text='Slug para URLs públicas (gerado automaticamente)',
                        max_length=255,
                        unique=True,
                    ),
                ),
            ],
            database_operations=[
                migrations.RunPython(make_slug_unique_if_not_already, migrations.RunPython.noop),
            ],
        ),
    ]
