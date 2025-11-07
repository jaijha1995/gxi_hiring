from django.contrib import admin
from django import forms
from django_summernote.admin import SummernoteModelAdmin

from .models import Skills, Department, Job_types, Location, Teams, add_job
from superadmin.models import UserProfile


# ---------------------------
# Forms
# ---------------------------
class AddJobForm(forms.ModelForm):
    class Meta:
        model = add_job
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Manager dropdown → only Managers
        if 'Manager' in self.fields:
            self.fields['Manager'].queryset = UserProfile.objects.filter(
                role=UserProfile.ROLE_MANAGER
            )

        # Resolve selected manager from POST data, initial, or instance
        manager_id = (
            self.data.get('Manager')
            or self.initial.get('Manager')
            or (self.instance.manager_id if getattr(self.instance, 'pk', None) else None)
        )

        # Hiring Manager + HR lists depend on selected manager
        if 'HiringManager' in self.fields:
            if manager_id:
                self.fields['HiringManager'].queryset = UserProfile.objects.filter(
                    role=UserProfile.Hiring_Manager,
                    created_by_manager_id=manager_id
                )
            else:
                self.fields['HiringManager'].queryset = UserProfile.objects.none()

        if 'HR' in self.fields:
            if manager_id:
                self.fields['HR'].queryset = UserProfile.objects.filter(
                    role=UserProfile.ROLE_HR,
                    created_by_manager_id=manager_id
                )
            else:
                self.fields['HR'].queryset = UserProfile.objects.none()


# ---------------------------
# Admins
# ---------------------------
@admin.register(Teams)
class TeamsAdmin(admin.ModelAdmin):
    """Teams now ONLY has name and department_types."""
    list_display = ('name', 'department_types')
    search_fields = ('name',)                      # <-- required for autocomplete on Teams
    list_filter = ('department_types',)


@admin.register(add_job)
class AddJobAdmin(SummernoteModelAdmin):
    form = AddJobForm
    summernote_fields = ('Description',)

    list_display = (
        'title', 'job_id', 'teams', 'manager', 'hiring_manager',
        'employments_types', 'is_active', 'created_at'
    )

admin.site.register(Skills)
admin.site.register(Department)
admin.site.register(Job_types)
admin.site.register(Location)
