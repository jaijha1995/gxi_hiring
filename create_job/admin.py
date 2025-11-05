from django.contrib import admin
from django_summernote.admin import SummernoteModelAdmin
from .models import Skills, Department, Job_types , Location , Teams  , add_job
from superadmin.models import UserProfile
from django import forms

# class JobAdmin(SummernoteModelAdmin):
#     summernote_fields = ('Description',)  # ✅ field to use summernote editor

# admin.site.register(Job, JobAdmin)

class TeamsForm(forms.ModelForm):
    class Meta:
        model = Teams
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Manager dropdown → only Managers
        self.fields['manager'].queryset = UserProfile.objects.filter(role=UserProfile.ROLE_MANAGER)

        # determine selected manager (initial payload or instance)
        manager_id = (
            self.data.get('manager') or
            self.initial.get('manager') or
            (self.instance.manager_id if self.instance and self.instance.pk else None)
        )

        if manager_id:
            self.fields['hiring_manager'].queryset = UserProfile.objects.filter(
                role=UserProfile.Hiring_Manager,
                created_by_manager_id=manager_id
            )
            self.fields['hr_team_members'].queryset = UserProfile.objects.filter(
                role=UserProfile.ROLE_HR,
                created_by_manager_id=manager_id
            )
        else:
            self.fields['hiring_manager'].queryset = UserProfile.objects.none()
            self.fields['hr_team_members'].queryset = UserProfile.objects.none()



admin.site.register(Skills)
admin.site.register(Department)
admin.site.register(Job_types)
admin.site.register(Location)
admin.site.register(add_job)
@admin.register(Teams)
class TeamsAdmin(admin.ModelAdmin):
    form = TeamsForm
    list_display = ('name', 'department_types', 'manager', 'hiring_manager')
    search_fields = ('name',)
    list_filter = ('department_types',)
