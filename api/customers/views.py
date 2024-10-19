from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
import requests
from datetime import datetime
from .models import Customer, Owner, Payment
from .serializers import CustomerSerializer
from django.utils import timezone
from django.db.models import Sum

def fetch_user_data(username, password):
    # Step 1: Get the token
    token_response = requests.post(
        'https://ubapi.earthlink.iq/api/user/Token',
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        data={
            'grant_type': 'password',
            'username': username,
            'password': password,
            'Logintype': '0'
        }
    )

    if token_response.status_code != 200:
        raise Exception(f'Failed to fetch token with status code: {token_response.status_code}')

    cookies = token_response.json()
    token = f"{cookies['token_type']} {cookies['access_token']}"

    # Step 2: Get user data
    user_response = requests.get(
        'https://ubapi.earthlink.iq/api/user/GetUserDataAr',
        headers={"Authorization": token}
    )

    if user_response.status_code != 200:
        raise Exception(f'Failed to fetch user data with status code: {user_response.status_code}')

    data = user_response.json()

    # Extract relevant fields
    account_price_value = int(data['accountPrice']['value'].replace(',', '').rstrip('IQD'))
    exp_date_str = data['accountExpirationDate']['value']
    exp_date = datetime.strptime(exp_date_str[:-1].strip(), '%d/%m/%Y %H:%M:%S')

    return {
        "name": data['fullName']['value'],
        "mobile_number": data['mobileNumber']['value'],
        "agent_name": data['agentName']['value'],
        "account_name": data['accountName']['value'],
        "account_price": account_price_value,
        "exp_date": exp_date,
    }

class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer

    def create(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')
        owner_name = request.data.get('owner')

        # Check if owner exists in the database
        try:
            owner = Owner.objects.get(name=owner_name)
        except Owner.DoesNotExist:
            return Response({'error': 'Owner does not exist'}, status=status.HTTP_400_BAD_REQUEST)

        # Fetch user data from external API
        try:
            user_data = fetch_user_data(username, password)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Create customer with fetched data
        customer = Customer(
            username=username,
            password=password,
            owner=owner,
            name=user_data['name'],
            mobile_number=user_data['mobile_number'],
            agent_name=user_data['agent_name'],
            account_name=user_data['account_name'],
            account_price=user_data['account_price'],
            debt_amount=user_data['account_price'],  # Initial debt is the account price
            exp_date=user_data['exp_date']
        )
        customer.save()

        return Response({
            "username": customer.username,
            "name": customer.name,
            "exp_date": customer.exp_date,
            "debt_amount": customer.debt_amount,
            "account_name": customer.account_name,
            "mobile_number": customer.mobile_number,
        }, status=status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        owner_name = request.query_params.get('owner')
        username = request.query_params.get('username')
        name = request.query_params.get('name')
        agent_name = request.query_params.get('agent_name')  # New parameter for filtering by agent name

        # Check if the owner is provided
        if not owner_name:
            return Response({'error': 'Owner is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve owner and handle errors
        try:
            owner = Owner.objects.get(name=owner_name)
        except Owner.DoesNotExist:
            return Response({'error': 'Owner does not exist'}, status=status.HTTP_400_BAD_REQUEST)

        # Filter customers by owner
        queryset = self.get_queryset().filter(owner=owner)

        # Apply additional filters if provided
        if username:
            queryset = queryset.filter(username=username)
        if name:
            queryset = queryset.filter(name=name)
        if agent_name:  # Filter by agent name if provided
            queryset = queryset.filter(agent_name=agent_name)

        # Handle case when no customers are found
        if not queryset.exists():
            return Response({'error': 'No customers found'}, status=status.HTTP_404_NOT_FOUND)

        # Serialize and return the data
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


    @action(detail=False, methods=['post'])
    def update_info(self, request):
        # Retrieve owner and username from request data
        owner_name = request.data.get('owner')
        username = request.data.get('username')
        password = request.data.get('password')

        # Validate that both owner and username are provided
        if not owner_name or not username:
            return Response({'error': 'Owner and username are required'}, status=status.HTTP_400_BAD_REQUEST)

        # Fetch the owner and handle error if owner does not exist
        try:
            owner = Owner.objects.get(name=owner_name)
        except Owner.DoesNotExist:
            return Response({'error': 'Owner does not exist'}, status=status.HTTP_400_BAD_REQUEST)

        # Fetch the customer by username and owner
        try:
            customer = Customer.objects.get(owner=owner, username=username)
        except Customer.DoesNotExist:
            return Response({'error': 'Customer not found for this owner'}, status=status.HTTP_404_NOT_FOUND)

        # Fetch updated user data from external API
        try:
            user_data = fetch_user_data(username, password)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Update customer information, but don't change the debt
        customer.name = user_data['name']
        customer.mobile_number = user_data['mobile_number']
        customer.agent_name = user_data['agent_name']
        customer.account_name = user_data['account_name']
        customer.account_price = user_data['account_price']
        customer.exp_date = user_data['exp_date']

        # Save the updated customer data
        customer.save()

        # Return the updated customer data
        return Response({
            "username": customer.username,
            "name": customer.name,
            "exp_date": customer.exp_date,
            "account_price": customer.account_price,
            "account_name": customer.account_name,
            "mobile_number": customer.mobile_number,
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def update_debt(self):
        customers = Customer.objects.all()
        for customer in customers:
            if customer.exp_date < timezone.now():
                # Fetch new user data from external API
                try:
                    user_data = fetch_user_data(customer.username, customer.password)
                    new_exp_date = user_data['exp_date']
                    account_price = user_data['account_price']
                except Exception as e:
                    return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

                # Check if the expiration date has changed
                if customer.exp_date != new_exp_date:
                    # Update the debt amount and exp_date
                    customer.debt_amount += account_price
                    customer.exp_date = new_exp_date
                    customer.account_price = account_price  # Update account price if needed
                    customer.save()

        return Response({'status': 'debts updated'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def register_payment(self, request):
        """
        Register a payment for a specific customer identified by username.
        """
        owner_name = request.data.get('owner')
        user_name = request.data.get('username')

        # Validate owner
        try:
            owner = Owner.objects.get(name=owner_name)
        except Owner.DoesNotExist:
            return Response({'error': 'Owner does not exist'}, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve the customer by username
        customer = Customer.objects.get(username=user_name)
        if customer.owner != owner:
            return Response({'error': 'This customer does not belong to the specified owner'}, status=status.HTTP_403_FORBIDDEN)

        # Process payment
        payment_amount = request.data.get('payment', 0)
        try:
            customer.debt_amount -= int(payment_amount)
            customer.save()
            
            Payment.objects.create(customer=customer, amount=payment_amount)
            
        except ValueError:
            return Response({'error': 'Invalid payment amount'}, status=status.HTTP_400_BAD_REQUEST)

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

    
    @action(detail=False, methods=['get'])
    def retrieve_unique_agents(self, request):
        """
        Retrieves a list of unique agent names for a specific owner.
        """
        owner_name = request.query_params.get('owner')

        if not owner_name:
            return Response({'error': 'Owner is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Filter customers by owner
        try:
            owner = Owner.objects.get(name=owner_name)
        except Owner.DoesNotExist:
            return Response({'error': 'Owner does not exist'}, status=status.HTTP_400_BAD_REQUEST)

        # Get distinct agent names for the specific owner
        unique_agents = Customer.objects.filter(owner=owner).values_list('agent_name', flat=True).distinct()

        return Response({"unique_agents": list(unique_agents)}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def owner_statistics(self, request):
        owner_name = request.query_params.get('owner')

        # Check if the owner is provided
        if not owner_name:
            return Response({'error': 'Owner is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve the owner
        try:
            owner = Owner.objects.get(name=owner_name)
        except Owner.DoesNotExist:
            return Response({'error': 'Owner does not exist'}, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve all customers for the given owner
        customers = Customer.objects.filter(owner=owner)

        # Calculate statistics
        total_customers = customers.count()
        customers_in_debt = customers.filter(debt_amount__gt=0).count()
        total_debt = customers.aggregate(total_debt=Sum('debt_amount'))['total_debt'] or 0

        # Retrieve all payments for the customers of the given owner
        total_payments = Payment.objects.filter(customer__owner=owner).aggregate(total_payment=Sum('amount'))['total_payment'] or 0

        # Return the statistics
        return Response({
            'total_customers': total_customers,
            'customers_in_debt': customers_in_debt,
            'total_debt': total_debt,
            'total_payments': total_payments
        }, status=status.HTTP_200_OK)
