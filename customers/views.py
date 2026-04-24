from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from .models.Customers import Customers
from .models.CustomerLedger import CustomerLedger
from common.utils.format_currency import format_indian_currency
from num2words import num2words
from django.forms import modelform_factory
from customers.models.CustomerRequestTransaction import CustomerRequestTransaction


def customer_login(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            customer = Customers.objects.get(username=username)
        except Customers.DoesNotExist:
            customer = None

        if customer:
            if customer.status != Customers.STATUS_ACTIVE:
                messages.error(request, "Account is inactive. Contact to superadmin")
                return redirect('login')

            if check_password(password, customer.password_hash):
                request.session['customer_id'] = customer.id
                request.session['customer_name'] = customer.username

                return redirect('dashboard')
            else:
                messages.error(request, "Wrong password")
        else:
            messages.error(request, "Invalid username and password")

    return render(request, 'frontend/customer/login.html')

def customer_logout(request):
    request.session.flush()
    return redirect('login')

def customer_dashboard(request):
    if not request.session.get('customer_id'):
        return redirect('login')
    
    customer_id = request.session.get('customer_id')
    customer = Customers.objects.get(id=customer_id)

    customerLedger = CustomerLedger.objects.filter(customer_id=customer).first()

    if not customerLedger:
        messages.error(request, "No ledger found for your account. Please contact admin.")
        return render(request, 'frontend/customer/dashboard.html', {
            'customer': customer,
            'name': (customer.first_name or '') + ' ' + (customer.last_name or ''),
        })

    customerTransactions = customerLedger.customer_ledger_transactions.all().order_by('-paid_on')

    total_amount_words = num2words(customerLedger.amount, lang='en_IN').title()
    balance_words = num2words(customerLedger.balance, lang='en_IN').title()
    paid_amount = customerLedger.amount - customerLedger.balance
    paid_amount_words = num2words(paid_amount, lang='en_IN').title()

    context = {
        'customer': customer,
        'name': (customer.first_name or '') + ' ' + (customer.last_name or ''),
        'email': customer.email,
        'total_amount': format_indian_currency(customerLedger.amount),
        'total_amount_words': total_amount_words,
        'balance': format_indian_currency(customerLedger.balance),
        'balance_words': balance_words,
        'paid_amount': format_indian_currency(paid_amount),
        'paid_amount_words': paid_amount_words,
        'transactions': customerTransactions,
        'house_no': customerLedger.project_house_id.plot_no,
        'format_indian_currency': format_indian_currency,
    }

    return render(request, 'frontend/customer/dashboard.html', context)

def customer_request_list(request):
    if not request.session.get('customer_id'):
        return redirect('login')
    
    customer_id = request.session.get('customer_id')
    customer = Customers.objects.get(id=customer_id)

    customerLedger = CustomerLedger.objects.filter(customer_id=customer).first()

    if not customerLedger:
        messages.error(request, "No ledger found for your account. Please contact admin.")
        return render(request, 'frontend/customer/request_listing.html', {
            'customer': customer,
            'name': (customer.first_name or '') + ' ' + (customer.last_name or ''),
            'transactions': [],
        })

    customerRequestTransactions = customerLedger.customer_transactions.filter(
        status=CustomerRequestTransaction.STATUS_NEW
    ).order_by('-paid_on')

    total_amount_words = num2words(customerLedger.amount, lang='en_IN').title()
    balance_words = num2words(customerLedger.balance, lang='en_IN').title()
    paid_amount = customerLedger.amount - customerLedger.balance
    paid_amount_words = num2words(paid_amount, lang='en_IN').title()

    context = {
        'customer': customer,
        'name': (customer.first_name or '') + ' ' + (customer.last_name or ''),
        'email': customer.email,
        'total_amount': format_indian_currency(customerLedger.amount),
        'total_amount_words': total_amount_words,
        'balance': format_indian_currency(customerLedger.balance),
        'balance_words': balance_words,
        'paid_amount': format_indian_currency(paid_amount),
        'paid_amount_words': paid_amount_words,
        'transactions': customerRequestTransactions,
        'house_no': customerLedger.project_house_id.plot_no,
        'format_indian_currency': format_indian_currency,
    }

    return render(request, 'frontend/customer/request_listing.html', context)


def customer_request_dashboard(request):

    if not request.session.get('customer_id'):
        return redirect('login')
    
    customer_id = request.session.get('customer_id')
    customer = Customers.objects.get(id=customer_id)

    customerLedger = CustomerLedger.objects.filter(customer_id=customer).first()

    CustomerRequestTransactionForm = modelform_factory(
        CustomerRequestTransaction,
        exclude=['created_at', 'updated_at','customer_ledger','status']
    )

    if request.method == 'POST':
        form = CustomerRequestTransactionForm(request.POST)
    else:
        form = CustomerRequestTransactionForm()

    for field_name, field in form.fields.items():

        if field.widget.__class__.__name__ in ['CheckboxInput']:
            field.widget.attrs['class'] = 'form-check-input'
        else:
            field.widget.attrs['class'] = 'form-control'

        if field_name == 'paid_on':
            field.widget.input_type = 'date'
            field.widget.attrs['class'] = 'form-control'

    if request.method == 'POST':
        if form.is_valid():
            obj = form.save(commit=False)
            obj.customer_ledger = customerLedger

            obj.save()
            messages.success(request, "Your request is submitted successfully.")
            return redirect('/customer/requests/')

    context = {
        'form': form
    }

    return render(request, 'frontend/customer/request.html', context)