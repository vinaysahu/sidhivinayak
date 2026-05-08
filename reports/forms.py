from django import forms
from django.contrib.auth import get_user_model
from projects.models.Projects import Projects
from customers.models.Customers import Customers
from customers.models.CustomerLedger import CustomerLedger

User = get_user_model()


class ProjectExpenseFilterForm(forms.Form):
    project = forms.ModelChoiceField(
        queryset=Projects.objects.all().order_by('name'),
        label="Project",
        empty_label="-- Select Project --",
        widget=forms.Select(attrs={'class': 'form-control select2'}),
    )


class CustomerReportFilterForm(forms.Form):
    project = forms.ModelChoiceField(
        queryset=Projects.objects.all().order_by('name'),
        label="Project",
        empty_label="-- Select Project --",
        widget=forms.Select(attrs={'class': 'form-control select2'}),
    )


class UserCustomerLedgerFilterForm(forms.Form):
    user = forms.ModelChoiceField(
        queryset=User.objects.all().order_by('username'),
        label="User",
        empty_label="-- Select User --",
        widget=forms.Select(attrs={'class': 'form-control select2', 'id': 'id_user'}),
    )
    project = forms.ModelChoiceField(
        queryset=Projects.objects.none(),
        label="Project",
        empty_label="-- Select Project --",
        required=False,
        widget=forms.Select(attrs={'class': 'form-control select2', 'id': 'id_project'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'user' in self.data:
            try:
                user_id = int(self.data.get('user'))
                project_ids = self._get_project_ids_for_user(user_id)
                self.fields['project'].queryset = Projects.objects.filter(
                    id__in=project_ids
                ).order_by('name')
            except (ValueError, TypeError):
                pass
        elif self.initial.get('user'):
            try:
                user_id = int(self.initial.get('user'))
                project_ids = self._get_project_ids_for_user(user_id)
                self.fields['project'].queryset = Projects.objects.filter(
                    id__in=project_ids
                ).order_by('name')
            except (ValueError, TypeError):
                pass

    @staticmethod
    def _get_project_ids_for_user(user_id):
        from customers.models.CustomerLedgerTransaction import CustomerLedgerTransaction
        return (
            CustomerLedgerTransaction.objects
            .filter(paid_to_id=user_id)
            .values_list('customer_ledger__project_id', flat=True)
            .distinct()
        )


class CustomerUserLedgerFilterForm(forms.Form):
    project = forms.ModelChoiceField(
        queryset=Projects.objects.all().order_by('name'),
        label="Project",
        empty_label="-- Select Project --",
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_cul_project'}),
    )
    customer = forms.ModelChoiceField(
        queryset=Customers.objects.none(),
        label="Customer",
        empty_label="-- Select Customer --",
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_cul_customer'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'project' in self.data:
            try:
                project_id = int(self.data.get('project'))
                customer_ids = (
                    CustomerLedger.objects
                    .filter(project_id_id=project_id)
                    .values_list('customer_id_id', flat=True)
                    .distinct()
                )
                self.fields['customer'].queryset = Customers.objects.filter(
                    id__in=customer_ids
                ).order_by('first_name', 'last_name')
            except (ValueError, TypeError):
                pass
