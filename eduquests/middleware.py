from django.utils import translation

from .i18n_strings import SUPPORTED_LANGS


class EduQuestsLocaleMiddleware:
    """Activate session language (en, ru, tg) for each request."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        lang = request.session.get("django_language", "en")
        if lang not in SUPPORTED_LANGS:
            lang = "en"
        translation.activate(lang)
        request.LANGUAGE_CODE = lang
        response = self.get_response(request)
        translation.deactivate()
        return response
