from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.hashers import make_password
from .models.Customers import Customers
from .models.CustomerLedger import CustomerLedger
from projects.models.Projects import Projects
from projects.models.ProjectHouses import ProjectHouses
from decimal import Decimal

class CustomerModelTest(TestCase):
    def setUp(self):
        self.customer = Customers.objects.create(
            username='johndoe',
            email='john@example.com',
            password_hash=make_password('password123'),
            status=Customers.STATUS_ACTIVE
        )

    def test_customer_creation(self):
        self.assertEqual(self.customer.username, 'johndoe')
        self.assertEqual(str(self.customer), 'johndoe')

class CustomerViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.customer = Customers.objects.create(
            username='testuser',
            password_hash=make_password('testpass'),
            status=Customers.STATUS_ACTIVE,
            first_name='Test',
            last_name='User'
        )
        self.project = Projects.objects.create(name='Test Project', area_sqyd=100)
        self.house = ProjectHouses.objects.create(project_id=self.project, plot_no=101, area_sqyd=50)
        self.ledger = CustomerLedger.objects.create(
            customer_id=self.customer,
            project_id=self.project,
            project_house_id=self.house,
            amount=Decimal('10000.00'),
            balance=Decimal('10000.00')
        )

    def test_login_view(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'frontend/customer/login.html')

    def test_login_success(self):
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpass'
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.session['customer_id'], self.customer.id)

    def test_dashboard_view_authenticated(self):
        session = self.client.session
        session['customer_id'] = self.customer.id
        session.save()
        
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'frontend/customer/dashboard.html')
        self.assertIn('total_amount', response.context)
