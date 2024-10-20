from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Customer, Owner, Payment
from .serializers import CustomerSerializer


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer

    def create(self, request, *args, **kwargs):
        username = request.data.get('username')
        owner_name = request.data.get('owner')
        customer_debt = request.data.get('debt_amount', 0)
        
        # Check if owner exists in the database
        try:
            owner = Owner.objects.get(name=owner_name)
        except Owner.DoesNotExist:
            return Response({'error': f'Owner {owner_name} does not exist'}, status=status.HTTP_400_BAD_REQUEST)

        # Create customer with fetched data
        customer = Customer(
            username=username,
            owner=owner,
            debt_amount=customer_debt
        )
        customer.save()

        return Response({'success': 'The customer have been added'}, status=status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        owner_name = request.query_params.get('owner')

        # Check if the owner is provided
        if not owner_name:
            return Response({'error': 'Owner is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve owner and handle errors
        try:
            owner = Owner.objects.get(name=owner_name)
        except Owner.DoesNotExist:
            return Response({'error': 'Owner does not exist'}, status=status.HTTP_400_BAD_REQUEST)

        # Filter customers by owner
        queryset = Customer.objects.filter(owner=owner)

        # Handle case when no customers are found
        if not queryset.exists():
            return Response({'error': 'No customers found'}, status=status.HTTP_404_NOT_FOUND)

        # Serialize and return the data
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'])
    def register_debt(self, request):
        customer, debt_amount = self._process_payment(request, is_debt=True)
        if isinstance(customer, Response):  # If the response is an error, return it
            return customer

        customer.debt_amount += debt_amount
        customer.save()

        return Response({'status': 'debt registered', 'new_debt_amount': customer.debt_amount}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def register_payment(self, request):
        customer, payment_amount = self._process_payment(request, is_debt=False)
        if isinstance(customer, Response):
            return customer

        customer.debt_amount -= payment_amount
        customer.save()

        Payment.objects.create(customer=customer, amount=payment_amount)

        return Response({'status': 'payment registered', 'new_debt_amount': customer.debt_amount}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def get_payments(self, request):
        owner_name = request.query_params.get('owner')
        username = request.query_params.get('username')

        # Validate owner
        try:
            owner = Owner.objects.get(name=owner_name)
        except Owner.DoesNotExist:
            return Response({'error': 'Owner does not exist'}, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve customer by username
        try:
            customer = Customer.objects.get(username=username, owner=owner)
        except Customer.DoesNotExist:
            return Response({'error': 'Customer not found for the specified owner'}, status=status.HTTP_404_NOT_FOUND)

        # Retrieve payment records for the customer
        payments = Payment.objects.filter(customer=customer)

        # Serialize payments
        payment_data = [{
            "amount": payment.amount,
            "payment_date": payment.payment_date,
        } for payment in payments]

        return Response(payment_data, status=status.HTTP_200_OK)
    
    def _process_payment(self, request, is_debt):
        owner_name = request.data.get('owner')
        user_name = request.data.get('username')
        amount_key = 'debt' if is_debt else 'payment'
        amount = request.data.get(amount_key)

        # Validate owner
        try:
            owner = Owner.objects.get(name=owner_name)
        except Owner.DoesNotExist:
            return Response({'error': 'Owner does not exist'}, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve the customer by username
        try:
            customer = Customer.objects.get(username=user_name)
        except Customer.DoesNotExist:
            return Response({'error': 'Customer not found'}, status=status.HTTP_404_NOT_FOUND)

        if customer.owner != owner:
            return Response({'error': 'This customer does not belong to the specified owner'}, status=status.HTTP_403_FORBIDDEN)

        try:
            amount = int(amount)
        except ValueError:
            return Response({'error': f'Invalid {amount_key} amount'}, status=status.HTTP_400_BAD_REQUEST)

        return customer, amount
