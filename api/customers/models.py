from django.db import models

class Owner(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Customer(models.Model):
    username = models.CharField(max_length=150, primary_key=True)
    owner = models.ForeignKey(Owner, on_delete=models.CASCADE)
    debt_amount = models.IntegerField(default=0)

    def __str__(self):
        return self.username

class Payment(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)  # Linking to Customer
    amount = models.DecimalField(max_digits=10, decimal_places=2)  # Payment amount
    payment_date = models.DateTimeField(auto_now_add=True)  # Automatically set to now when created

    def __str__(self):
        return f'{self.customer.username} - {self.amount} - {self.payment_date}'