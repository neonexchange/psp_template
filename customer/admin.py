from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .forms import PSPUserCreationForm,PSPUserChangeForm
from .models import PSPUser,ReceiveableAccount,Purchase,Deposit

class PSPUserAdmin(BaseUserAdmin):
    # The forms to add and change user instances
    form = PSPUserChangeForm
    add_form = PSPUserCreationForm

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ('email', 'date_joined', 'last_login', 'is_admin')
    list_filter = ('is_admin',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name','last_name', 'customer_type','is_seller','pending_deposit',)}),
        ('Permissions', {'fields': ('is_admin',)}),
    )
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2','first_name','last_name')}
        ),
    )
    search_fields = ('email','first_name','last_name')
    ordering = ('email','first_name','last_name')
    filter_horizontal = ()


class ReceiveableAdmin(admin.ModelAdmin):
    model = ReceiveableAccount
    list_display = ('user','account_id',)

class PurchaseAdmin(admin.ModelAdmin):
    model = Purchase
    list_display = ('user','transfer_url','amount')

class DepositAdmin(admin.ModelAdmin):
    model = Deposit
    list_display = ('user','date_created','status',)

# Now register the new UserAdmin...
admin.site.register(PSPUser, PSPUserAdmin)
admin.site.register(ReceiveableAccount, ReceiveableAdmin)
admin.site.register(Purchase, PurchaseAdmin)
admin.site.register(Deposit, DepositAdmin)

# ... and, since we're not using Django's built-in permissions,
# unregister the Group model from admin.
admin.site.unregister(Group)