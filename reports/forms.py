from django import forms
from django.contrib.auth import get_user_model
from projects.models.Projects import Projects

User = get_user_model()


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
