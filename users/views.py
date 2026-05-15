from django.shortcuts import render, redirect

from django.contrib.auth.models import User

from django.contrib.auth import authenticate, login, logout

from django.contrib import messages



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

            return redirect('home')

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