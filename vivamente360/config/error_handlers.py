"""
Custom error handlers for Django
"""
from django.shortcuts import render
from django.http import HttpResponse
import logging

logger = logging.getLogger(__name__)


def handler404(request, exception=None):
    """
    Custom 404 error handler
    """
    logger.warning(f"404 Error: {request.path} - User: {getattr(request.user, 'username', 'Anonymous')}")
    return render(request, '404.html', status=404)


def handler500(request):
    """
    Custom 500 error handler
    """
    logger.error(f"500 Error: {request.path} - User: {getattr(request.user, 'username', 'Anonymous')}")
    return render(request, '500.html', status=500)


def handler403(request, exception=None):
    """
    Custom 403 error handler (permission denied)
    """
    logger.warning(f"403 Error: {request.path} - User: {getattr(request.user, 'username', 'Anonymous')}")
    context = {
        'error_code': '403',
        'error_title': 'Acesso Negado',
        'error_message': 'Você não tem permissão para acessar esta página.',
    }
    return render(request, '403.html', context, status=403)


def handler400(request, exception=None):
    """
    Custom 400 error handler (bad request)
    """
    logger.warning(f"400 Error: {request.path} - User: {getattr(request.user, 'username', 'Anonymous')}")
    context = {
        'error_code': '400',
        'error_title': 'Requisição Inválida',
        'error_message': 'A requisição não pôde ser processada.',
    }
    return render(request, '400.html', context, status=400)
