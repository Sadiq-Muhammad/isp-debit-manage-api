from django.db import models

class Owner(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Customer(models.Model):
    username = models.CharField(max_length=150, primary_key=True)
    password = models.CharField(max_length=128)  # Store hashed passwords in production
    owner = models.ForeignKey(Owner, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    mobile_number = models.CharField(max_length=15)
    agent_name = models.CharField(max_length=255)
    account_name = models.CharField(max_length=255)
    account_price = models.IntegerField(default=0)
    debt_amount = models.IntegerField(default=0)
    exp_date = models.DateTimeField()

    def __str__(self):
        return self.username

class Payment(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)  # Linking to Customer
    amount = models.DecimalField(max_digits=10, decimal_places=2)  # Payment amount
    payment_date = models.DateTimeField(auto_now_add=True)  # Automatically set to now when created

    def __str__(self):
        return f'{self.customer.username} - {self.amount} - {self.payment_date}'