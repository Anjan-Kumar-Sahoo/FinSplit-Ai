"""
API views for core app using Django REST Framework.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings
import threading
import requests
from .models import Pool, Member, Expense, Transaction, ExpenseSplit
from .serializers import (
    PoolSerializer, MemberSerializer, ExpenseSerializer, 
    TransactionSerializer, ExpenseSplitSerializer
)


class PoolViewSet(viewsets.ModelViewSet):
    """ViewSet for Pool model."""
    queryset = Pool.objects.all()
    serializer_class = PoolSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'name']
    ordering = ['-created_at']
    filterset_fields = ['is_active', 'default_split_method']
    
    def get_queryset(self):
        return Pool.objects.filter(members=self.request.user)
    
    def perform_create(self, serializer):
        pool = serializer.save(created_by=self.request.user)
        # Add creator as admin member
        Member.objects.create(
            user=self.request.user,
            pool=pool,
            is_admin=True
        )


class MemberViewSet(viewsets.ModelViewSet):
    """ViewSet for Member model."""
    queryset = Member.objects.all()
    serializer_class = MemberSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = ['joined_at']
    ordering = ['-joined_at']
    filterset_fields = ['is_active', 'is_admin']
    
    def get_queryset(self):
        return Member.objects.filter(
            pool__members=self.request.user
        )


class ExpenseViewSet(viewsets.ModelViewSet):
    """ViewSet for Expense model."""
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['expense_date', 'created_at', 'amount']
    ordering = ['-expense_date', '-created_at']
    filterset_fields = ['pool', 'paid_by', 'split_method']
    
    def get_queryset(self):
        return Expense.objects.filter(
            pool__members=self.request.user
        )
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class TransactionViewSet(viewsets.ModelViewSet):
    """ViewSet for Transaction model."""
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = ['created_at', 'amount']
    ordering = ['-created_at']
    filterset_fields = ['status', 'payment_method', 'pool']
    
    def get_queryset(self):
        return Transaction.objects.filter(
            pool__members=self.request.user
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def pool_summary(request, pool_id):
    """Get summary information for a pool."""
    pool = get_object_or_404(Pool, id=pool_id, members=request.user)
    
    # Check cache first
    cache_key = f'pool_summary_{pool_id}'
    cached_summary = cache.get(cache_key)
    
    if cached_summary:
        return Response(cached_summary)
    
    # Calculate summary
    total_expenses = pool.get_total_expenses()
    member_count = pool.get_member_count()
    balances = pool.get_balances()
    
    recent_expenses = pool.expenses.order_by('-created_at')[:5]
    pending_transactions = Transaction.objects.filter(
        pool=pool,
        status='pending'
    ).count()
    
    summary = {
        'pool_id': pool.id,
        'pool_name': pool.name,
        'total_expenses': total_expenses,
        'member_count': member_count,
        'recent_expenses': ExpenseSerializer(recent_expenses, many=True).data,
        'pending_transactions': pending_transactions,
        'balances_count': len([b for b in balances.values() if b['balance'] != 0])
    }
    
    # Cache for 5 minutes
    cache.set(cache_key, summary, 300)
    
    return Response(summary)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def pool_balances(request, pool_id):
    """Get detailed balances for all members in a pool."""
    pool = get_object_or_404(Pool, id=pool_id, members=request.user)
    
    balances = pool.get_balances()
    
    # Format for API response
    formatted_balances = []
    for user_id, balance_info in balances.items():
        formatted_balances.append({
            'user_id': user_id,
            'username': balance_info['user'].username,
            'email': balance_info['user'].email,
            'paid': balance_info['paid'],
            'owes': balance_info['owes'],
            'balance': balance_info['balance'],
            'upi_id': getattr(balance_info['user'].profile, 'upi_id', '') if hasattr(balance_info['user'], 'profile') else ''
        })
    
    return Response({
        'pool_id': pool.id,
        'balances': formatted_balances
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def expense_split(request, expense_id):
    """Create or update expense splits."""
    expense = get_object_or_404(Expense, id=expense_id)
    
    # Check if user has permission to modify this expense
    if expense.created_by != request.user:
        return Response(
            {'error': 'You do not have permission to modify this expense.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    splits_data = request.data.get('splits', [])
    
    if not splits_data:
        return Response(
            {'error': 'No splits data provided.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate total amount
    total_split_amount = sum(float(split['amount']) for split in splits_data)
    if abs(total_split_amount - float(expense.amount)) > 0.01:
        return Response(
            {'error': 'Split amounts do not match expense total.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Clear existing splits
    expense.splits.all().delete()
    
    # Create new splits
    for split_data in splits_data:
        ExpenseSplit.objects.create(
            expense=expense,
            user_id=split_data['user_id'],
            amount=split_data['amount'],
            percentage=split_data.get('percentage')
        )
    
    # Clear cache
    cache.delete(f'pool_summary_{expense.pool.id}')
    
    return Response({'message': 'Expense splits updated successfully.'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def validate_upi(request):
    """Validate UPI ID (mock implementation)."""
    upi_id = request.data.get('upi_id', '')
    
    if not upi_id:
        return Response(
            {'error': 'UPI ID is required.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Mock UPI validation (in real implementation, you would call UPI API)
    # For now, just check basic format
    if '@' not in upi_id:
        return Response({
            'valid': False,
            'message': 'Invalid UPI ID format.'
        })
    
    # Simulate API call delay
    import time
    time.sleep(0.5)
    
    # Mock response
    return Response({
        'valid': True,
        'message': 'UPI ID is valid.',
        'provider': upi_id.split('@')[1] if '@' in upi_id else 'unknown'
    })


def send_email_async(subject, message, recipient_list):
    """Send email asynchronously using threading."""
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            fail_silently=False,
        )
    except Exception as e:
        print(f"Failed to send email: {e}")


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_invite_email(request):
    """Send invitation email to join a pool."""
    pool_id = request.data.get('pool_id')
    email = request.data.get('email')
    
    if not pool_id or not email:
        return Response(
            {'error': 'Pool ID and email are required.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    pool = get_object_or_404(Pool, id=pool_id, members=request.user)
    
    # Check if user is admin of the pool
    member = get_object_or_404(Member, pool=pool, user=request.user, is_admin=True)
    
    # Prepare email content
    subject = f'Invitation to join "{pool.name}" on FinSplit'
    message = f"""
    Hi there!
    
    {request.user.get_full_name() or request.user.username} has invited you to join the expense pool "{pool.name}" on FinSplit.
    
    Pool Description: {pool.description}
    
    To join this pool, please sign up at our website and use the invitation link.
    
    Best regards,
    FinSplit Team
    """
    
    # Send email asynchronously
    email_thread = threading.Thread(
        target=send_email_async,
        args=(subject, message, [email])
    )
    email_thread.start()
    
    return Response({
        'message': f'Invitation sent to {email} successfully.'
    })

