"""
URL configuration for core app.
"""
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Home and dashboard
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Pool management
    path('pools/', views.pool_list, name='pool_list'),
    path('pools/create/', views.pool_create, name='pool_create'),
    path('pools/<int:pool_id>/', views.pool_detail, name='pool_detail'),
    path('pools/<int:pool_id>/edit/', views.pool_edit, name='pool_edit'),
    path('pools/<int:pool_id>/delete/', views.pool_delete, name='pool_delete'),
    
    # Member management
    path('pools/<int:pool_id>/members/add/', views.member_add, name='member_add'),
    path('members/<int:member_id>/remove/', views.member_remove, name='member_remove'),
    
    # Expense management
    path('pools/<int:pool_id>/expenses/add/', views.expense_add, name='expense_add'),
    path('expenses/<int:expense_id>/', views.expense_detail, name='expense_detail'),
    path('expenses/<int:expense_id>/edit/', views.expense_edit, name='expense_edit'),
    path('expenses/<int:expense_id>/delete/', views.expense_delete, name='expense_delete'),
    
    # Settlement
    path('pools/<int:pool_id>/settle/', views.pool_settle, name='pool_settle'),
    path('transactions/<int:transaction_id>/mark_paid/', views.transaction_mark_paid, name='transaction_mark_paid'),
    
    # Authentication
    path('signup/', views.signup, name='signup'),
    path('profile/', views.profile, name='profile'),
    path('logout/', views.logout_view, name='logout'),
]