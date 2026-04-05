# admin.py ya forms.py

from django import forms
from decimal import Decimal, InvalidOperation
import re
from ..models.CustomerLedgerTransaction import CustomerLedgerTransaction
from datetime import date

class CustomerLedgerTransactionForm(forms.ModelForm):

    class Meta:
        model = CustomerLedgerTransaction
        fields = '__all__'

    def clean_amount(self):
        value = self.cleaned_data.get('amount')

        if value is None:
            return value

        # string me convert
        value = str(value)

        # ₹, comma remove
        value = re.sub(r'[^\d.-]', '', value)

        try:
            return Decimal(value)
        except InvalidOperation:
            raise forms.ValidationError("Invalid amount format")
        
    def clean_paid_on(self):
        value = self.cleaned_data.get('paid_on')
        return value or date.today()