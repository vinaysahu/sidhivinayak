from django.test import TestCase
from django.contrib.auth.models import User
from projects.models.Projects import Projects
from .models.UserLedger import UserLedger
from .models.UserLedgerTransaction import UserLedgerTransaction
from decimal import Decimal

class UserLedgerModelTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='creditor', first_name='John')
        self.user2 = User.objects.create_user(username='debtor', first_name='Doe')
        self.project = Projects.objects.create(name='Test Project', area_sqyd=100)
        self.ledger = UserLedger.objects.create(
            creditor=self.user1,
            debtor=self.user2,
            project_id=self.project,
            amount=Decimal('5000.00'),
            balance=Decimal('5000.00')
        )

    def test_ledger_creation(self):
        self.assertEqual(self.ledger.amount, Decimal('5000.00'))
        self.assertEqual(str(self.ledger), f"Ledger ({self.ledger.id}) - (John -> Doe)")

    def test_transaction_creation(self):
        transaction = UserLedgerTransaction.objects.create(
            user_ledger=self.ledger,
            payment_type='credited',
            amount=Decimal('1000.00'),
            detail='Initial payment'
        )
        self.assertEqual(transaction.amount, Decimal('1000.00'))
        self.assertEqual(str(transaction), "John - credited - 1000.00")
