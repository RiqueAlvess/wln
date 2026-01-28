from django.views.generic import TemplateView
from django.shortcuts import redirect
from django.http import JsonResponse
from django.utils import timezone
from django.db import transaction
from .models import LGPDComplianceItem
from .mixins import RHRequiredMixin


class HomeView(TemplateView):
    template_name = 'home.html'

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('analytics:dashboard')
        return redirect('accounts:login')


class LGPDComplianceView(RHRequiredMixin, TemplateView):
    template_name = 'core/lgpd_compliance.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Obter empresa do usuário
        empresa = None
        if hasattr(self.request.user, 'profile') and self.request.user.profile.empresas.exists():
            empresa = self.request.user.profile.empresas.first()

        if empresa:
            # Obter itens de conformidade
            items = LGPDComplianceItem.objects.filter(empresa=empresa)

            # Calcular percentual de conclusão
            total_items = items.count()
            completed_items = items.filter(concluido=True).count()
            completion_percentage = (completed_items / total_items * 100) if total_items > 0 else 0

            context['items'] = items
            context['completion_percentage'] = round(completion_percentage, 1)
            context['total_items'] = total_items
            context['completed_items'] = completed_items
        else:
            context['items'] = []
            context['completion_percentage'] = 0
            context['total_items'] = 0
            context['completed_items'] = 0

        context['empresa'] = empresa
        return context

    def post(self, request, *args, **kwargs):
        # Obter empresa do usuário
        empresa = None
        if hasattr(request.user, 'profile') and request.user.profile.empresas.exists():
            empresa = request.user.profile.empresas.first()

        if not empresa:
            return JsonResponse({'success': False, 'error': 'Empresa não encontrada'}, status=400)

        try:
            with transaction.atomic():
                # Processar cada item do formulário
                for key, value in request.POST.items():
                    if key.startswith('item_'):
                        item_id = int(key.split('_')[1])
                        item = LGPDComplianceItem.objects.get(id=item_id, empresa=empresa)

                        # Atualizar status de conclusão
                        concluido = request.POST.get(f'concluido_{item_id}') == 'on'
                        item.concluido = concluido

                        # Se foi marcado como concluído, registrar data
                        if concluido and not item.data_conclusao:
                            item.data_conclusao = timezone.now()
                        elif not concluido:
                            item.data_conclusao = None

                        # Atualizar observações
                        item.observacoes = request.POST.get(f'observacoes_{item_id}', '')
                        item.save()

                return JsonResponse({'success': True, 'message': 'Progresso salvo com sucesso!'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
