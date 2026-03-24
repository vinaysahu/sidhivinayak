from django.db import models
from django.contrib.auth.models import User
from projects.models.Projects import Projects

class UserLedger(models.Model):
    creditor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='creditor_ledgers'
    )
    debtor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='debtor_ledgers'
    )
    project_id = models.ForeignKey(Projects, on_delete=models.CASCADE, verbose_name="Project_ledger")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    balance = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Ledger ({self.id}) - ({self.creditor.first_name} -> {self.debtor.first_name})"