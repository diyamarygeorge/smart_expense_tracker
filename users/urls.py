from django.urls import path

from . import views


urlpatterns = [

    path('', views.home, name='home'),

    path('login/', views.login_user, name='login'),

    path('register/', views.register_user, name='register'),

    path('logout/', views.logout_user, name='logout'),
    
    path('dashboard/',views.dashboard,name='dashboard'),
    
    path('edit-expense/<int:id>/',views.edit_expense,name='edit_expense'),

    path('delete-expense/<int:id>/',views.delete_expense,name='delete_expense'),
    
    path('monthly-history/',views.monthly_history,name='monthly_history'),

    path('budget/',views.budget,name='budget'),

    path('parse-expense/',views.parse_expense_view,name='parse_expense'),

    path('categorize/',views.categorize_view,name='categorize'),

]