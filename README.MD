**[POST]**
/api/customers/ # To add customer to database.
body = {"username": "Username", "password": "******", "owner": "Owner"}

**[POST]**
/api/customers/register_payment/ # To register payment of the customer.
body = {"owner": "Owner", "username": "Username", "payment": 40000}

**[POST]**
/api/customers/update_info/ # To update customer infromation on demand.
body = {"owner": "Owner", "username": "Username", "password": "a140"}

**[GET]**
/api/customers/?owner=Owner # To get all customers.
/api/customers/?owner=Owner&agent_name=AgentX # To get customers by Agent Name
/api/customers/?owner=Owner&username=Username # To get customer by username.
/api/customers/?owner=Owner&name=CustomerName # To get customer by name.

**[GET]**
/api/customers/retrieve_unique_agents/?owner=Owner # To get agent list.

**[GET]**
/api/customers/get_payments/?owner=Owner&username=Username # To get the payment history.

**[GET]**
/api/customers/owner_statistics/?owner=Owner # To get owner statistics