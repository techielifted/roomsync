from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Apartment, ScheduleSlot, ChatMessage

# Register your custom user model
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['email', 'username', 'apartment_id', 'is_staff']
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('apartment_id',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('apartment_id',)}),
    )

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Apartment)
admin.site.register(ScheduleSlot)
admin.site.register(ChatMessage)