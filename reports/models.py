from django.db import models


class UserCustomerLedger(models.Model):
    class Meta:
        managed = False
        verbose_name = 'User Customer Ledger'
        verbose_name_plural = 'User Customer Ledger Report'


class ProjectExpenses(models.Model):
    class Meta:
        managed = False
        verbose_name = 'Project Expenses'
        verbose_name_plural = 'Project Expenses Report'
