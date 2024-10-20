**[POST]**

/api/customers/ # To add customer to database.

body = {"username": "ali140@nstr5", "owner": "Interlink", "debt_amount": 40000}

**[POST]**

/api/customers/register_payment/ # To register payment of the customer.

body = {"owner": "Owner", "username": "Username", "payment": 40000}

**[POST]**

/api/customers/register_debt/ # To register debt of the customer.

body = {"owner": "Owner", "username": "Username", "debt": 40000}

**[GET]**

/api/customers/?owner=Owner # To get all customers.

**[GET]**

/api/customers/get_payments/?owner=Owner&username=Username # To get the payment history.