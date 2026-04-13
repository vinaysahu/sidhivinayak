from django.test import TestCase
from django.contrib.auth.models import User
from projects.models.Projects import Projects
from accounts.models.UserLedger import UserLedger
from accounts.models.UserLedgerTransaction import UserLedgerTransaction
from decimal import Decimal

class UserLedgerSignalTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', first_name='Creditor')
        self.user2 = User.objects.create_user(username='user2', first_name='Debtor')
        self.project = Projects.objects.create(name='Test Project', area_sqyd=100)
        self.ledger = UserLedger.objects.create(
            creditor=self.user1,
            debtor=self.user2,
            project_id=self.project,
            amount=Decimal('1000.00'),
            balance=Decimal('1000.00')
        )

    def test_credited_transaction_updates_balance(self):
        # balance = amount - credited + debited
        # 1000 - 200 = 800
        UserLedgerTransaction.objects.create(
            user_ledger=self.ledger,
            payment_type='credited',
            amount=Decimal('200.00')
        )
        self.ledger.refresh_from_db()
        self.assertEqual(self.ledger.balance, Decimal('800.00'))

    def test_debited_transaction_updates_balance(self):
        # 1000 + 300 = 1300
        UserLedgerTransaction.objects.create(
            user_ledger=self.ledger,
            payment_type='debited',
            amount=Decimal('300.00')
        )
        self.ledger.refresh_from_db()
        self.assertEqual(self.ledger.balance, Decimal('1300.00'))

    def test_multiple_transactions_update_balance(self):
        # 1000 - 200 + 500 = 1300
        UserLedgerTransaction.objects.create(user_ledger=self.ledger, payment_type='credited', amount=Decimal('200.00'))
        UserLedgerTransaction.objects.create(user_ledger=self.ledger, payment_type='debited', amount=Decimal('500.00'))
        self.ledger.refresh_from_db()
        self.assertEqual(self.ledger.balance, Decimal('1300.00'))

    def test_delete_transaction_updates_balance(self):
        t = UserLedgerTransaction.objects.create(user_ledger=self.ledger, payment_type='credited', amount=Decimal('200.00'))
        self.ledger.refresh_from_db()
        self.assertEqual(self.ledger.balance, Decimal('800.00'))
        
        t.delete()
        self.ledger.refresh_from_db()
        self.assertEqual(self.ledger.balance, Decimal('1000.00'))
