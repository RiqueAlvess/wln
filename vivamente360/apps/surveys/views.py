from django.views.generic import ListView, CreateView, DetailView
from django.urls import reverse_lazy
from apps.core.mixins import RHRequiredMixin
from apps.surveys.models import Campaign
from selectors.campaign_selectors import CampaignSelectors


class CampaignListView(RHRequiredMixin, ListView):
    model = Campaign
    template_name = 'campaigns/list.html'
    context_object_name = 'campaigns'
    paginate_by = 25

    def get_queryset(self):
        return CampaignSelectors.get_user_campaigns(self.request.user)


class CampaignCreateView(RHRequiredMixin, CreateView):
    model = Campaign
    template_name = 'campaigns/create.html'
    fields = ['nome', 'descricao', 'empresa', 'data_inicio', 'data_fim', 'status']
    success_url = reverse_lazy('surveys:list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class CampaignDetailView(RHRequiredMixin, DetailView):
    model = Campaign
    template_name = 'campaigns/detail.html'
    context_object_name = 'campaign'

    def get_queryset(self):
        return CampaignSelectors.get_user_campaigns(self.request.user)
