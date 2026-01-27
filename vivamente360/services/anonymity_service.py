class AnonymityService:
    @staticmethod
    def validate_blind_drop_integrity():
        from apps.invitations.models import SurveyInvitation
        from apps.responses.models import SurveyResponse

        invitation_fields = [f.name for f in SurveyInvitation._meta.get_fields()]
        response_fields = [f.name for f in SurveyResponse._meta.get_fields()]

        has_fk_to_invitation = any(
            'invitation' in field.lower() for field in response_fields
        )

        return not has_fk_to_invitation

    @staticmethod
    def check_minimum_sample_size(queryset, minimum=5):
        count = queryset.count()
        if count < minimum:
            return False, f"Dados insuficientes para análise (mínimo {minimum} respostas)"
        return True, ""
