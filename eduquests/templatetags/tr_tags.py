from django import template

from eduquests.i18n_strings import get_text

register = template.Library()


@register.simple_tag(takes_context=True)
def tr(context, key):
    request = context.get("request")
    lang = "en"
    if request:
        lang = getattr(request, "LANGUAGE_CODE", None) or request.session.get("django_language", "en")
    return get_text(key, lang)
