from django.shortcuts import render, redirect, get_object_or_404

from django.contrib.auth.models import User

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from django.contrib import messages
from datetime import date
from collections import defaultdict
import calendar
from .models import Expense, Budget, CategoryBudget


CATEGORIES = ['Food', 'Travel', 'Shopping', 'Bills', 'Education', 'Other']


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

@login_required
def logout_user(request):

    logout(request)

    return redirect('home')


@login_required
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

    # ---------- READ FILTERS FROM URL ----------
    search_query = request.GET.get('search', '').strip()
    category_filter = request.GET.get('category', '').strip()

    # Base: this month's expenses for this user
    expenses = Expense.objects.filter(
        user=request.user,
        expense_date__month=today.month,
        expense_date__year=today.year
    )

    # Apply search (item name contains)
    if search_query:
        expenses = expenses.filter(item_name__icontains=search_query)

    # Apply category filter
    if category_filter and category_filter != 'All':
        expenses = expenses.filter(category=category_filter)

    expenses = expenses.order_by('-expense_date')


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

    # ---------- BUDGET ----------
    # Budget progress is based on the FULL month's spend (not the filtered view),
    # so the bar stays accurate even while the table is filtered.
    budget = Budget.objects.filter(user=request.user).first()
    monthly_limit = float(budget.monthly_limit) if budget else 0

    full_month_spent = sum(
        e.amount for e in Expense.objects.filter(
            user=request.user,
            expense_date__month=today.month,
            expense_date__year=today.year
        )
    )
    full_month_spent = float(full_month_spent)

    if monthly_limit > 0:
        budget_percent = min(round((full_month_spent / monthly_limit) * 100), 100)
        budget_remaining = round(monthly_limit - full_month_spent, 2)
        budget_overage = round(full_month_spent - monthly_limit, 2) if full_month_spent > monthly_limit else 0
        # status: ok < 75%, warn 75-99%, over >= 100%
        raw_percent = (full_month_spent / monthly_limit) * 100
        if raw_percent >= 100:
            budget_status = 'over'
        elif raw_percent >= 75:
            budget_status = 'warn'
        else:
            budget_status = 'ok'
    else:
        budget_percent = 0
        budget_remaining = 0
        budget_overage = 0
        budget_status = 'none'

    # ---------- PER-CATEGORY BUDGETS ----------
    # Spend per category for the full month (unfiltered)
    full_month_qs = Expense.objects.filter(
        user=request.user,
        expense_date__month=today.month,
        expense_date__year=today.year
    )
    cat_spent = defaultdict(float)
    for e in full_month_qs:
        cat_spent[e.category] += float(e.amount)

    category_budgets = []
    for cb in CategoryBudget.objects.filter(user=request.user):
        limit = float(cb.monthly_limit)
        if limit <= 0:
            continue
        spent = cat_spent.get(cb.category, 0)
        raw = (spent / limit) * 100
        pct = min(round(raw), 100)
        if raw >= 100:
            status = 'over'
        elif raw >= 75:
            status = 'warn'
        else:
            status = 'ok'
        category_budgets.append({
            'category': cb.category,
            'limit': round(limit, 2),
            'spent': round(spent, 2),
            'percent': pct,
            'remaining': round(limit - spent, 2),
            'overage': round(spent - limit, 2) if spent > limit else 0,
            'status': status,
        })

    context = {

        'today': today,

        'current_month': today.strftime("%B %Y"),

        'expenses': expenses,

        'total_spent': total_spent,

        # active filters (so template can show current state)
        'search_query': search_query,
        'category_filter': category_filter or 'All',
        'categories': CATEGORIES,

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

        # budget
        'monthly_limit': round(monthly_limit, 2),
        'full_month_spent': round(full_month_spent, 2),
        'budget_percent': budget_percent,
        'budget_remaining': budget_remaining,
        'budget_overage': budget_overage,
        'budget_status': budget_status,
        'category_budgets': category_budgets,

    }

    return render(
        request,
        'index.html',
        context
    )


def _status_from_percent(raw):
    if raw >= 100:
        return 'over'
    elif raw >= 75:
        return 'warn'
    return 'ok'


@login_required
def budget(request):

    budget_obj = Budget.objects.filter(user=request.user).first()

    if request.method == "POST":

        # ----- Overall limit -----
        limit_value = request.POST.get('monthly_limit', '0').strip()
        try:
            limit_value = float(limit_value)
            if limit_value < 0:
                limit_value = 0
        except (ValueError, TypeError):
            limit_value = 0

        if budget_obj:
            budget_obj.monthly_limit = limit_value
            budget_obj.save()
        else:
            Budget.objects.create(
                user=request.user,
                monthly_limit=limit_value
            )

        # ----- Per-category limits -----
        # Each category arrives as cat_<Category>. Blank or 0 = remove that limit.
        for cat in CATEGORIES:
            raw_val = request.POST.get(f'cat_{cat}', '').strip()
            if raw_val == '':
                # blank -> delete any existing limit for this category
                CategoryBudget.objects.filter(user=request.user, category=cat).delete()
                continue
            try:
                val = float(raw_val)
            except (ValueError, TypeError):
                val = 0
            if val <= 0:
                CategoryBudget.objects.filter(user=request.user, category=cat).delete()
            else:
                CategoryBudget.objects.update_or_create(
                    user=request.user,
                    category=cat,
                    defaults={'monthly_limit': val}
                )

        messages.success(request, "Budget updated")
        return redirect('budget')

    today = date.today()

    full_month_qs = Expense.objects.filter(
        user=request.user,
        expense_date__month=today.month,
        expense_date__year=today.year
    )

    full_month_spent = float(sum(e.amount for e in full_month_qs))

    # ----- Overall progress -----
    monthly_limit = float(budget_obj.monthly_limit) if budget_obj else 0

    if monthly_limit > 0:
        raw_percent = (full_month_spent / monthly_limit) * 100
        budget_percent = min(round(raw_percent), 100)
        budget_remaining = round(monthly_limit - full_month_spent, 2)
        budget_overage = round(full_month_spent - monthly_limit, 2) if full_month_spent > monthly_limit else 0
        budget_status = _status_from_percent(raw_percent)
    else:
        budget_percent = 0
        budget_remaining = 0
        budget_overage = 0
        budget_status = 'none'

    # ----- Per-category spend + saved limits -----
    cat_spent = defaultdict(float)
    for e in full_month_qs:
        cat_spent[e.category] += float(e.amount)

    saved_limits = {
        cb.category: float(cb.monthly_limit)
        for cb in CategoryBudget.objects.filter(user=request.user)
    }

    # Build a row for every category (for the form), with progress if a limit is set
    category_rows = []
    for cat in CATEGORIES:
        limit = saved_limits.get(cat, 0)
        spent = round(cat_spent.get(cat, 0), 2)
        if limit > 0:
            raw = (spent / limit) * 100
            row = {
                'category': cat,
                'limit': round(limit, 2),
                'spent': spent,
                'percent': min(round(raw), 100),
                'remaining': round(limit - spent, 2),
                'overage': round(spent - limit, 2) if spent > limit else 0,
                'status': _status_from_percent(raw),
                'is_set': True,
            }
        else:
            row = {
                'category': cat,
                'limit': '',
                'spent': spent,
                'percent': 0,
                'remaining': 0,
                'overage': 0,
                'status': 'none',
                'is_set': False,
            }
        category_rows.append(row)

    context = {
        'today': today,
        'current_month': today.strftime("%B %Y"),
        'monthly_limit': round(monthly_limit, 2),
        'full_month_spent': round(full_month_spent, 2),
        'budget_percent': budget_percent,
        'budget_remaining': budget_remaining,
        'budget_overage': budget_overage,
        'budget_status': budget_status,
        'category_rows': category_rows,
    }

    return render(request, 'budget.html', context)


@login_required
def edit_expense(request, id):

    # Ownership check: only the owner can edit
    expense = get_object_or_404(Expense, id=id, user=request.user)

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


@login_required
def delete_expense(request, id):

    # Ownership check: only the owner can delete
    expense = get_object_or_404(Expense, id=id, user=request.user)

    expense.delete()

    return redirect('dashboard')


@login_required
def monthly_history(request):
    today = date.today()

    try:
        selected_month = int(request.GET.get('month', today.month))
        selected_year = int(request.GET.get('year', today.year))
    except (ValueError, TypeError):
        selected_month = today.month
        selected_year = today.year

    # ---------- READ FILTERS FROM URL ----------
    search_query = request.GET.get('search', '').strip()
    category_filter = request.GET.get('category', '').strip()

    expenses = Expense.objects.filter(
        user=request.user,
        expense_date__month=selected_month,
        expense_date__year=selected_year
    )

    # Apply search
    if search_query:
        expenses = expenses.filter(item_name__icontains=search_query)

    # Apply category filter
    if category_filter and category_filter != 'All':
        expenses = expenses.filter(category=category_filter)

    expenses = expenses.order_by('expense_date')

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

        # active filters
        'search_query': search_query,
        'category_filter': category_filter or 'All',
        'categories': CATEGORIES,
    }

    return render(request, 'monthly_history.html', context)