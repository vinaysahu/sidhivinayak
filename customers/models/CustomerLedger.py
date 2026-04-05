from django.db import models
from .Customers import Customers

class CustomerLedger(models.Model):
    customer_id = models.ForeignKey(
        Customers,
        on_delete=models.CASCADE,
        related_name='customer_ledgers'
    )
    project_id = models.ForeignKey('projects.Projects', on_delete=models.CASCADE, verbose_name="Project_customer_ledger")
    project_house_id = models.ForeignKey('projects.ProjectHouses', on_delete=models.CASCADE, verbose_name="Project_house_ledger")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    balance = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Ledger {self.customer_id.first_name} {self.customer_id.last_name}"