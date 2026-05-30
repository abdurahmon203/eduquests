from django.contrib import admin

from .models import TutorQuestion, TutorResponse


class TutorResponseInline(admin.StackedInline):
    model = TutorResponse
    extra = 0
    readonly_fields = ("answer_text", "created_at")


@admin.register(TutorQuestion)
class TutorQuestionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "question_text_short", "subject", "level", "created_at")
    list_filter = ("subject", "created_at")
    search_fields = ("question_text", "user__username", "user__email")
    readonly_fields = ("created_at",)
    inlines = [TutorResponseInline]

    def question_text_short(self, obj):
        return obj.question_text[:50]

    question_text_short.short_description = "Question"


@admin.register(TutorResponse)
class TutorResponseAdmin(admin.ModelAdmin):
    list_display = ("id", "tutor_question", "created_at")
    readonly_fields = ("tutor_question", "answer_text", "created_at")
