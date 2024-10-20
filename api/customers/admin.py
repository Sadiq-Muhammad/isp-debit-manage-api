from django.contrib import admin
from .models import Customer, Owner

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('username', 'owner', 'debt_amount')
    search_fields = ('username',)

@admin.register(Owner)
class OwnerAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
