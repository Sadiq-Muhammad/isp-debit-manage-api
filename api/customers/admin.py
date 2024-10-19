from django.contrib import admin
from .models import Customer, Owner

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('username', 'name', 'owner', 'mobile_number', 'account_name', 'account_price', 'debt_amount', 'exp_date')
    search_fields = ('username', 'name', 'mobile_number')

@admin.register(Owner)
class OwnerAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
