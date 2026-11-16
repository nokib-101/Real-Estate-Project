from django.contrib import admin, messages

from .models import Realtor


@admin.action(description='Approve selected realtors')
def approve_realtors(modeladmin, request, queryset):
    count = queryset.update(is_approved=True)
    modeladmin.message_user(request, f'{count} realtor(s) approved.', messages.SUCCESS)


class RealtorAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'user', 'is_approved', 'is_mvp')
    list_display_links = ('id', 'name')
    list_editable = ('is_approved',)
    list_filter = ('is_approved', 'is_mvp')
    search_fields = ('name', 'email', 'user__username')
    actions = [approve_realtors]
    raw_id_fields = ('user',)
    list_per_page = 15


admin.site.register(Realtor, RealtorAdmin)
