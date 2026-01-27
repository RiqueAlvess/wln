import csv
from io import StringIO
from apps.structure.models import Unidade, Setor, Cargo
from apps.invitations.models import SurveyInvitation
from services.token_service import TokenService


class ImportService:
    REQUIRED_COLUMNS = ['unidade', 'setor', 'cargo', 'email']

    @classmethod
    def validate_csv(cls, file_content: str):
        try:
            reader = csv.DictReader(StringIO(file_content))
            headers = reader.fieldnames

            missing = [col for col in cls.REQUIRED_COLUMNS if col not in headers]
            if missing:
                return False, f"Colunas faltando: {', '.join(missing)}", []

            rows = list(reader)
            if not rows:
                return False, "Arquivo vazio", []

            return True, "", rows
        except Exception as e:
            return False, f"Erro ao processar CSV: {str(e)}", []

    @classmethod
    def process_import(cls, empresa, campaign, rows: list, crypto_service) -> dict:
        created = 0
        errors = []

        for i, row in enumerate(rows, start=2):
            try:
                unidade, _ = Unidade.objects.get_or_create(
                    empresa=empresa,
                    nome=row['unidade'].strip()
                )
                setor, _ = Setor.objects.get_or_create(
                    unidade=unidade,
                    nome=row['setor'].strip()
                )
                cargo, _ = Cargo.objects.get_or_create(
                    empresa=empresa,
                    nome=row['cargo'].strip()
                )

                email_encrypted = crypto_service.encrypt(row['email'].strip().lower())

                SurveyInvitation.objects.create(
                    empresa=empresa,
                    campaign=campaign,
                    unidade=unidade,
                    setor=setor,
                    cargo=cargo,
                    email_encrypted=email_encrypted,
                    expires_at=TokenService.get_expiry()
                )
                created += 1

            except Exception as e:
                errors.append(f"Linha {i}: {str(e)}")

        return {"created": created, "errors": errors}
