from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile Information'
    fk_name = 'user'

class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline, )

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super(UserAdmin, self).get_inline_instances(request, obj)

    @admin.action(description="Make selected users Admin (Superuser)")
    def make_admin(self, request, queryset):
        queryset.update(is_staff=True, is_superuser=True)
        self.message_user(request, "Selected users are now Admins.")

    @admin.action(description="Make selected users Staff (Moderator)")
    def make_staff(self, request, queryset):
        queryset.update(is_staff=True, is_superuser=False)
        self.message_user(request, "Selected users are now Staff/Moderators.")

    @admin.action(description="Make selected users Regular Users")
    def make_regular(self, request, queryset):
        queryset.update(is_staff=False, is_superuser=False)
        self.message_user(request, "Selected users are now Regular Users.")

    actions = ['make_admin', 'make_staff', 'make_regular']

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number')
    search_fields = ('user__email', 'user__username', 'phone_number')
