from django.db import migrations, models
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


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0003_add_cor_fonte'),
    ]

    operations = [
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
        migrations.RunPython(generate_slugs, migrations.RunPython.noop),
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
    ]
