from .i18n_strings import LANG_LABELS, SUPPORTED_LANGS


def i18n_theme_context(request):
    lang = getattr(request, "LANGUAGE_CODE", None) or request.session.get("django_language", "en")
    if lang not in SUPPORTED_LANGS:
        lang = "en"
    return {
        "current_language": lang,
        "supported_languages": SUPPORTED_LANGS,
        "lang_labels": LANG_LABELS,
    }
