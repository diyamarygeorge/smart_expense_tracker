from django.shortcuts import render, redirect

from django.contrib.auth.models import User

from django.contrib.auth import authenticate, login, logout

from django.contrib import messages
from datetime import date
from collections import defaultdict
import calendar
from .models import Expense



# HOME PAGE

def home(request):

    return render(request, 'home.html')



# REGISTER PAGE

def register_user(request):

    if request.method == "POST":

        username = request.POST['username']

        email = request.POST['email']

        password = request.POST['password']


        # CHECK IF USERNAME EXISTS

        if User.objects.filter(username=username).exists():

            messages.error(request, "Username already exists")

            return redirect('register')


        # CREATE USER

        user = User.objects.create_user(

            username=username,
            email=email,
            password=password

        )

        user.save()

        return redirect('login')


    return render(request, 'register.html')



# LOGIN PAGE

def login_user(request):

    if request.method == "POST":

        username = request.POST['username']

        password = request.POST['password']


        # AUTHENTICATE USER

        user = authenticate(

            request,
            username=username,
            password=password

        )


        # IF USER EXISTS

        if user is not None:

            login(request, user)

            return redirect('dashboard')

        else:

            messages.error(
                request,
                "Invalid username or password"
            )


    return render(request, 'login.html')



# LOGOUT

def logout_user(request):

    logout(request)

    return redirect('home')


def dashboard(request):

    if request.method == "POST":

        item_name = request.POST['item_name']

        category = request.POST['category']

        amount = request.POST['amount']

        expense_date = request.POST['expense_date']


        Expense.objects.create(

            user=request.user,

            item_name=item_name,

            category=category,

            amount=amount,

            expense_date=expense_date

        )


        return redirect('dashboard')


    today = date.today()

    expenses = Expense.objects.filter(
        user=request.user,
        expense_date__month=today.month,
        expense_date__year=today.year
    ).order_by('-expense_date')


    total_spent = sum(
        expense.amount
        for expense in expenses
    )

    # ---------- SUMMARY CARD STATS ----------

    txn_count = expenses.count()

    # Daily average — total / days elapsed this month so far
    days_elapsed = today.day
    daily_avg = total_spent / days_elapsed if days_elapsed else 0

    # Category totals (used for biggest category + donut chart)
    cat_totals = defaultdict(float)
    for e in expenses:
        cat_totals[e.category] += float(e.amount)

    if cat_totals:
        biggest_category = max(cat_totals, key=cat_totals.get)
        biggest_category_amount = cat_totals[biggest_category]
    else:
        biggest_category = "—"
        biggest_category_amount = 0

    # ---------- CHART DATA ----------

    # Donut: category -> total
    category_labels = list(cat_totals.keys())
    category_values = [round(cat_totals[c], 2) for c in category_labels]

    # Line: spending per day across this month
    days_in_month = calendar.monthrange(today.year, today.month)[1]
    daily_totals = [0.0] * days_in_month
    for e in expenses:
        daily_totals[e.expense_date.day - 1] += float(e.amount)

    day_labels = [str(d) for d in range(1, days_in_month + 1)]
    daily_values = [round(v, 2) for v in daily_totals]

    context = {

        'today': today,

        'current_month': today.strftime("%B %Y"),

        'expenses': expenses,

        'total_spent': total_spent,

        # summary cards
        'txn_count': txn_count,
        'daily_avg': round(daily_avg, 2),
        'biggest_category': biggest_category,
        'biggest_category_amount': round(biggest_category_amount, 2),

        # charts (json-encoded in template)
        'category_labels': category_labels,
        'category_values': category_values,
        'day_labels': day_labels,
        'daily_values': daily_values,

    }

    return render(
        request,
        'index.html',
        context
    )

def edit_expense(request, id):

    expense = Expense.objects.get(id=id)

    if request.method == "POST":

        expense.item_name = request.POST['item_name']

        expense.category = request.POST['category']

        expense.amount = request.POST['amount']

        expense.expense_date = request.POST['expense_date']

        expense.save()

        return redirect('dashboard')

    return render(
        request,
        'edit_expense.html',
        {'expense': expense}
    )
def delete_expense(request, id):

    expense = Expense.objects.get(id=id)

    expense.delete()

    return redirect('dashboard')

def monthly_history(request):
    today = date.today()

    try:
        selected_month = int(request.GET.get('month', today.month))
        selected_year = int(request.GET.get('year', today.year))
    except (ValueError, TypeError):
        selected_month = today.month
        selected_year = today.year

    expenses = Expense.objects.filter(
        user=request.user,
        expense_date__month=selected_month,
        expense_date__year=selected_year
    ).order_by('expense_date')

    total_spent = sum(expense.amount for expense in expenses)

    first_expense = Expense.objects.filter(user=request.user).order_by('expense_date').first()
    min_year = first_expense.expense_date.year if first_expense else today.year
    max_year = today.year

    months = [
        (1, 'January'), (2, 'February'), (3, 'March'),
        (4, 'April'),   (5, 'May'),      (6, 'June'),
        (7, 'July'),    (8, 'August'),   (9, 'September'),
        (10, 'October'),(11, 'November'),(12, 'December'),
    ]

    context = {
        'expenses': expenses,
        'total_spent': total_spent,
        'selected_month': selected_month,
        'selected_year': selected_year,
        'months': months,
        'min_year': min_year,
        'max_year': max_year,
        'selected_month_name': date(selected_year, selected_month, 1).strftime("%B %Y"),
    }

    return render(request, 'monthly_history.html', context)