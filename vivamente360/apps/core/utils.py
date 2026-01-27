from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


def get_paginated_queryset(queryset, page, per_page=25):
    paginator = Paginator(queryset, per_page)
    try:
        paginated = paginator.page(page)
    except PageNotAnInteger:
        paginated = paginator.page(1)
    except EmptyPage:
        paginated = paginator.page(paginator.num_pages)
    return paginated


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')
