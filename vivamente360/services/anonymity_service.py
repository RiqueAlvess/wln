class AnonymityService:
    @staticmethod
    def validate_blind_drop_integrity():
        """
        Valida que o padrão blind-drop está intacto:
        1. SurveyResponse NÃO tem FK para SurveyInvitation
        2. SurveyResponse NÃO tem FK para Cargo (previne regressão de codificação)
        3. SurveyResponse NÃO tem FK para User
        """
        from apps.responses.models import SurveyResponse

        response_fields = [f.name for f in SurveyResponse._meta.get_fields()]

        has_fk_to_invitation = any(
            'invitation' in field.lower() for field in response_fields
        )

        has_cargo = 'cargo' in response_fields

        has_user = any(
            field in ('user', 'user_id', 'respondente') for field in response_fields
        )

        violations = []
        if has_fk_to_invitation:
            violations.append('SurveyResponse contém referência a SurveyInvitation')
        if has_cargo:
            violations.append('SurveyResponse contém campo cargo (risco de de-anonimização)')
        if has_user:
            violations.append('SurveyResponse contém referência a User')

        return len(violations) == 0, violations

    @staticmethod
    def check_minimum_sample_size(queryset, minimum=5):
        """
        Garante amostra mínima para prevenir identificação em grupos pequenos.
        """
        count = queryset.count()
        if count < minimum:
            return False, f"Dados insuficientes para análise (mínimo {minimum} respostas)"
        return True, ""
