from django.contrib import admin
from django.contrib.admin import AdminSite
from .models import Profile, Skill, Job, Application, InterviewAvailability, InterviewSlot, ApplicationReview


admin.site.register(Profile)
admin.site.register(Skill)
admin.site.register(Job)
admin.site.register(InterviewAvailability)
admin.site.register(InterviewSlot)
admin.site.register(ApplicationReview)

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "job",
        "status",
        "ai_score",
        "interview_slot",
        "applied_at",
    )

    list_filter = (
        "status",
        "job",
    )

    search_fields = (
        "user__username",
        "full_name",
        "job__title",
    )


admin.site.site_header = "SOORTY Denimkind"
admin.site.site_title = "SOORTY Admin"
admin.site.index_title = "Recruitment Portal"
admin.site.site_url = "/admin-dashboard/"

AdminSite.login_redirect_url = "/admin-dashboard/"