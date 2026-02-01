from django.db import migrations, models


def convert_admin_users_to_superusers(apps, schema_editor):
    """
    Converte usuários com role 'admin' em superusers e remove seus perfis.
    A role 'admin' é inútil pois o estado de Root já é vinculado ao criar a conta.
    """
    User = apps.get_model('auth', 'User')
    UserProfile = apps.get_model('accounts', 'UserProfile')

    # Encontrar todos os perfis com role 'admin'
    admin_profiles = UserProfile.objects.filter(role='admin')

    for profile in admin_profiles:
        user = profile.user
        # Marcar o usuário como superuser e staff
        user.is_superuser = True
        user.is_staff = True
        user.save()

        # Deletar o perfil (não é mais necessário para superusers)
        profile.delete()

    print(f"Convertidos {admin_profiles.count()} usuários admin para superusers")


def reverse_conversion(apps, schema_editor):
    """
    Não há como reverter essa migração de forma automática.
    Superusers já existem e não podemos saber quais foram convertidos.
    """
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            convert_admin_users_to_superusers,
            reverse_conversion
        ),
        # Alterar o campo role para remover a opção 'admin'
        migrations.AlterField(
            model_name='userprofile',
            name='role',
            field=models.CharField(
                max_length=15,
                choices=[
                    ('rh', 'RH'),
                    ('lideranca', 'Liderança'),
                ]
            ),
        ),
    ]
