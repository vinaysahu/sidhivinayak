from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from .models.Customers import Customers
from .models.CustomerLedger import CustomerLedger
from common.utils.format_currency import format_indian_currency
from num2words import num2words

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

    customerTransactions = []
    if customerLedger:
        customerTransactions = customerLedger.customer_transactions.all().order_by('-paid_on')

    total_amount_words = num2words(customerLedger.amount, lang='en_IN').title()
    balance_words = num2words(customerLedger.balance, lang='en_IN').title()
    paid_amount = (customerLedger.amount-customerLedger.balance)
    paid_amount_words = num2words(paid_amount, lang='en_IN').title()

    context = {
        'customer': customer,
        'name': customer.first_name +" "+customer.last_name,
        'email': customer.email,
        'total_amount': format_indian_currency(customerLedger.amount),
        'total_amount_words':total_amount_words,
        'balance': format_indian_currency(customerLedger.balance),
        'balance_words':balance_words,
        'paid_amount': format_indian_currency(paid_amount),
        'paid_amount_words':paid_amount_words,
        'transactions':customerTransactions,
        'house_no': customerLedger.project_house_id.plot_no,
        'format_indian_currency':format_indian_currency
    }

    return render(request, 'frontend/customer/dashboard.html',context)