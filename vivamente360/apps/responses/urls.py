from django.urls import path
from .views import SurveyFormView

app_name = 'responses'

urlpatterns = [
    path('<uuid:token>/', SurveyFormView.as_view(), name='survey'),
]
