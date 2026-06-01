from django.shortcuts import redirect
from django.views.decorators.http import require_POST

from .i18n_strings import SUPPORTED_LANGS


@require_POST
def set_language(request):
    lang = (request.POST.get("language") or "").strip().lower()
    if lang in SUPPORTED_LANGS:
        request.session["django_language"] = lang
        request.session.modified = True
    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER") or "/"
    return redirect(next_url)
