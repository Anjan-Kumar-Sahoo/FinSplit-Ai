"""
API URL configuration for core app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'pools', api_views.PoolViewSet)
router.register(r'members', api_views.MemberViewSet)
router.register(r'expenses', api_views.ExpenseViewSet)
router.register(r'transactions', api_views.TransactionViewSet)

# The API URLs are now determined automatically by the router
urlpatterns = [
    path('', include(router.urls)),
    
    # Custom API endpoints
    path('pools/<int:pool_id>/summary/', api_views.pool_summary, name='pool_summary'),
    path('pools/<int:pool_id>/balances/', api_views.pool_balances, name='pool_balances'),
    path('expenses/<int:expense_id>/split/', api_views.expense_split, name='expense_split'),
    path('validate-upi/', api_views.validate_upi, name='validate_upi'),
    path('send-invite/', api_views.send_invite_email, name='send_invite_email'),
]

