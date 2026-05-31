from django.shortcuts import render, redirect

from django.contrib.auth.models import User

from django.contrib.auth import authenticate, login, logout

from django.contrib import messages
from datetime import date
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
    )
    

    total_spent = sum(
        expense.amount
        for expense in expenses
    )

    context = {

        'today': today,

        'current_month': today.strftime("%B %Y"),

        'expenses': expenses,

        'total_spent': total_spent

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

    return render( request, 'monthly_history.html')