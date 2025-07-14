"""
Views for core app.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q
import logging
from django.contrib.auth.models import User
from .models import Pool, Member, Expense, Transaction, UserProfile
from .forms import PoolForm, ExpenseForm, MemberForm, UserProfileForm

logger = logging.getLogger(__name__)


def home(request):
    """Home page view."""
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    return render(request, 'core/home.html')


@login_required
def dashboard(request):
    """User dashboard showing pools and recent activity."""
    user_pools = Pool.objects.filter(members=request.user, is_active=True)
    recent_expenses = Expense.objects.filter(
        pool__in=user_pools
    ).order_by('-created_at')[:10]
    
    pending_transactions = Transaction.objects.filter(
        Q(from_user=request.user) | Q(to_user=request.user),
        status='pending'
    )
    
    context = {
        'pools': user_pools,
        'recent_expenses': recent_expenses,
        'pending_transactions': pending_transactions,
    }
    return render(request, 'core/dashboard.html', context)


@login_required
def pool_list(request):
    """List all pools for the user."""
    pools = Pool.objects.filter(members=request.user, is_active=True)
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        pools = pools.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(pools, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
    }
    return render(request, 'core/pool_list.html', context)


@login_required
def pool_create(request):
    """Create a new pool."""
    if request.method == 'POST':
        form = PoolForm(request.POST)
        if form.is_valid():
            pool = form.save(commit=False)
            pool.created_by = request.user
            pool.save()
            
            # Add creator as admin member
            Member.objects.create(
                user=request.user,
                pool=pool,
                is_admin=True
            )
            
            messages.success(request, f'Pool "{pool.name}" created successfully!')
            return redirect('core:pool_detail', pool_id=pool.id)
    else:
        form = PoolForm()
    
    return render(request, 'core/pool_form.html', {'form': form, 'title': 'Create Pool'})


@login_required
def pool_detail(request, pool_id):
    """Pool detail view with expenses and members."""
    from .cache_utils import get_cached_pool_balances, get_cached_pool_summary
    
    pool = get_object_or_404(Pool, id=pool_id, members=request.user)
    
    # Get expenses with pagination
    expenses = pool.expenses.all()
    paginator = Paginator(expenses, 10)
    page_number = request.GET.get('page')
    expenses_page = paginator.get_page(page_number)
    
    # Get members
    members = pool.members.filter(member__is_active=True)
    
    # Get cached balances for better performance
    try:
        balances = get_cached_pool_balances(pool_id)
    except:
        # Fallback to model method if caching fails
        balances = pool.get_balances()
    
    # Get pending transactions
    transactions = Transaction.objects.filter(
        pool=pool,
        status='pending'
    )
    
    # Get cached pool summary
    try:
        pool_summary = get_cached_pool_summary(pool_id)
        total_expenses = pool_summary['total_expenses'] if pool_summary else pool.get_total_expenses()
    except:
        total_expenses = pool.get_total_expenses()
    
    context = {
        'pool': pool,
        'expenses_page': expenses_page,
        'members': members,
        'balances': balances,
        'transactions': transactions,
        'total_expenses': total_expenses,
    }
    return render(request, 'core/pool_detail.html', context)


@login_required
def pool_edit(request, pool_id):
    """Edit pool details."""
    pool = get_object_or_404(Pool, id=pool_id, created_by=request.user)
    
    if request.method == 'POST':
        form = PoolForm(request.POST, instance=pool)
        if form.is_valid():
            form.save()
            messages.success(request, 'Pool updated successfully!')
            return redirect('core:pool_detail', pool_id=pool.id)
    else:
        form = PoolForm(instance=pool)
    
    return render(request, 'core/pool_form.html', {'form': form, 'title': 'Edit Pool', 'pool': pool})


@login_required
def pool_delete(request, pool_id):
    """Delete a pool."""
    pool = get_object_or_404(Pool, id=pool_id, created_by=request.user)
    
    if request.method == 'POST':
        pool.is_active = False
        pool.save()
        messages.success(request, f'Pool "{pool.name}" deleted successfully!')
        return redirect('core:pool_list')
    
    return render(request, 'core/pool_confirm_delete.html', {'pool': pool})


@login_required
def member_add(request, pool_id):
    """Add a member to the pool."""
    pool = get_object_or_404(Pool, id=pool_id)
    
    # Check if user is admin of the pool or creator
    try:
        member = Member.objects.get(pool=pool, user=request.user, is_admin=True)
    except Member.DoesNotExist:
        if pool.created_by != request.user:
            messages.error(request, 'You do not have permission to add members to this pool.')
            return redirect('core:pool_detail', pool_id=pool.id)
    
    if request.method == 'POST':
        form = MemberForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            upi_id = form.cleaned_data.get('upi_id', '')
            
            try:
                # Try to find user by username
                user_to_add = User.objects.get(username=username)
                
                # Check if user is already a member
                if Member.objects.filter(pool=pool, user=user_to_add).exists():
                    messages.warning(request, f'{username} is already a member of this pool.')
                else:
                    # Add user as member
                    Member.objects.create(
                        pool=pool,
                        user=user_to_add,
                        is_admin=False,
                        is_active=True
                    )
                    
                    # Update user's UPI ID if provided
                    if upi_id:
                        profile, created = UserProfile.objects.get_or_create(user=user_to_add)
                        profile.upi_id = upi_id
                        profile.save()
                    
                    messages.success(request, f'{username} has been added to the pool successfully!')
                    
                    # Send invitation email if email utils are working
                    try:
                        from .email_utils import send_pool_invite_email
                        send_pool_invite_email(request.user, pool, user_to_add.email)
                    except:
                        pass  # Email sending is optional
                        
                return redirect('core:pool_detail', pool_id=pool.id)
                
            except User.DoesNotExist:
                messages.error(request, f'User "{username}" not found. Please make sure they have registered on FinSplit.')
                
    else:
        form = MemberForm()
    
    return render(request, 'core/member_form.html', {'form': form, 'pool': pool})


@login_required
def member_remove(request, member_id):
    """Remove a member from the pool."""
    member = get_object_or_404(Member, id=member_id)
    pool = member.pool
    
    # Check permissions
    requesting_member = get_object_or_404(Member, pool=pool, user=request.user, is_admin=True)
    
    if request.method == 'POST':
        member.is_active = False
        member.save()
        messages.success(request, f'{member.user.username} removed from pool.')
        return redirect('core:pool_detail', pool_id=pool.id)
    
    return render(request, 'core/member_confirm_remove.html', {'member': member})


@login_required
def expense_add(request, pool_id):
    """Add an expense to the pool."""
    from .email_utils import send_expense_notification_email
    from .cache_utils import invalidate_pool_cache
    
    pool = get_object_or_404(Pool, id=pool_id, members=request.user)
    
    if request.method == 'POST':
        form = ExpenseForm(request.POST, request.FILES, pool=pool)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.pool = pool
            expense.created_by = request.user
            expense.save()
            
            # Create expense splits based on the split method
            create_expense_splits(expense, request.POST)
            
            # Invalidate cache for this pool
            invalidate_pool_cache(pool_id)
            
            # Send email notifications to pool members (async)
            try:
                pool_members = pool.members.exclude(id=request.user.id)
                send_expense_notification_email(expense, pool_members)
            except Exception as e:
                # Don't fail the request if email sending fails
                logger.warning(f"Failed to send expense notification emails: {str(e)}")
            
            messages.success(request, 'Expense added successfully!')
            return redirect('core:pool_detail', pool_id=pool.id)
    else:
        form = ExpenseForm(pool=pool)
    
    return render(request, 'core/expense_form.html', {'form': form, 'pool': pool, 'title': 'Add Expense'})


def create_expense_splits(expense, post_data):
    """Create expense splits based on the split method."""
    from .models import ExpenseSplit
    from decimal import Decimal
    
    # Get pool members
    pool_members = expense.pool.members.filter(member__is_active=True)
    
    if expense.split_method == 'equal':
        # Equal split among all active members
        split_amount = expense.amount / pool_members.count()
        for member in pool_members:
            ExpenseSplit.objects.create(
                expense=expense,
                user=member,
                amount=split_amount,
                percentage=(split_amount / expense.amount * 100)
            )
    
    elif expense.split_method == 'percentage':
        # Percentage-based split (would need additional form handling)
        # For now, default to equal split
        split_amount = expense.amount / pool_members.count()
        for member in pool_members:
            ExpenseSplit.objects.create(
                expense=expense,
                user=member,
                amount=split_amount,
                percentage=(split_amount / expense.amount * 100)
            )
    
    elif expense.split_method == 'manual':
        # Manual split (would need additional form handling)
        # For now, default to equal split
        split_amount = expense.amount / pool_members.count()
        for member in pool_members:
            ExpenseSplit.objects.create(
                expense=expense,
                user=member,
                amount=split_amount,
                percentage=(split_amount / expense.amount * 100)
            )


@login_required
def expense_detail(request, expense_id):
    """Expense detail view."""
    expense = get_object_or_404(Expense, id=expense_id)
    
    # Check if user has access to this expense
    get_object_or_404(Member, pool=expense.pool, user=request.user, is_active=True)
    
    splits = expense.splits.all()
    
    context = {
        'expense': expense,
        'splits': splits,
        'split_summary': expense.get_split_summary(),
    }
    return render(request, 'core/expense_detail.html', context)


@login_required
def expense_edit(request, expense_id):
    """Edit an expense."""
    expense = get_object_or_404(Expense, id=expense_id, created_by=request.user)
    
    if request.method == 'POST':
        form = ExpenseForm(request.POST, request.FILES, instance=expense, pool=expense.pool)
        if form.is_valid():
            form.save()
            messages.success(request, 'Expense updated successfully!')
            return redirect('core:expense_detail', expense_id=expense.id)
    else:
        form = ExpenseForm(instance=expense, pool=expense.pool)
    
    return render(request, 'core/expense_form.html', {'form': form, 'expense': expense, 'title': 'Edit Expense'})


@login_required
def expense_delete(request, expense_id):
    """Delete an expense."""
    expense = get_object_or_404(Expense, id=expense_id, created_by=request.user)
    
    if request.method == 'POST':
        pool_id = expense.pool.id
        expense.delete()
        messages.success(request, 'Expense deleted successfully!')
        return redirect('core:pool_detail', pool_id=pool_id)
    
    return render(request, 'core/expense_confirm_delete.html', {'expense': expense})


@login_required
def pool_settle(request, pool_id):
    """Settlement view for the pool."""
    pool = get_object_or_404(Pool, id=pool_id, members=request.user)
    
    balances = pool.get_balances()
    
    # Calculate optimal settlements (simplified algorithm)
    settlements = []
    creditors = []  # People who are owed money
    debtors = []    # People who owe money
    
    for user_id, balance_info in balances.items():
        if balance_info['balance'] > 0:
            creditors.append((balance_info['user'], balance_info['balance']))
        elif balance_info['balance'] < 0:
            debtors.append((balance_info['user'], abs(balance_info['balance'])))
    
    # Simple settlement algorithm
    for debtor, debt_amount in debtors:
        for creditor, credit_amount in creditors:
            if debt_amount > 0 and credit_amount > 0:
                settlement_amount = min(debt_amount, credit_amount)
                
                # Create a Transaction object for the suggested settlement
                transaction = Transaction.objects.create(
                    pool=pool,
                    from_user=debtor,
                    to_user=creditor,
                    amount=settlement_amount,
                    status='pending' # New transactions are pending by default
                )
                
                settlements.append({
                    'from_user': debtor,
                    'to_user': creditor,
                    'amount': settlement_amount,
                    'id': transaction.id # Pass the transaction ID to the template
                })
                debt_amount -= settlement_amount
                credit_amount -= settlement_amount
    
    for transaction in pool.transactions.all():
        transaction.is_involved = (request.user == transaction.from_user or request.user == transaction.to_user)
    
    context = {
        'pool': pool,
        'balances': balances,
        'settlements': settlements,
        'transactions': pool.transactions.all(), # Pass all transactions with the new flag
    }
    return render(request, 'core/pool_settle.html', context)


@login_required
def transaction_mark_paid(request, transaction_id):
    """Mark a transaction as settled - only creditor can do this."""
    transaction = get_object_or_404(Transaction, id=transaction_id)
    
    if request.method == 'POST':
        if not transaction.can_be_settled_by(request.user):
            if request.user == transaction.from_user:
                messages.error(request, 'Only the person receiving money can mark a transaction as settled.')
            else:
                messages.error(request, 'You are not authorized to settle this transaction.')
            return redirect("core:pool_settle", pool_id=transaction.pool.id)
        
        try:
            transaction.mark_settled(request.user)
            messages.success(request, f'Transaction of ₹{transaction.amount} from {transaction.from_user.username} has been marked as settled!')
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, 'An error occurred while settling the transaction.')
            
        return redirect('core:pool_settle', pool_id=transaction.pool.id)
    
    return render(request, 'core/transaction_confirm_paid.html', {'transaction': transaction})

def signup(request):
    """User signup view."""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        profile_form = UserProfileForm(request.POST)
        
        if form.is_valid() and profile_form.is_valid():
            user = form.save()
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()
            
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('core:dashboard')
    else:
        form = UserCreationForm()
        profile_form = UserProfileForm()
    
    return render(request, 'registration/signup.html', {
        'form': form,
        'profile_form': profile_form
    })


@login_required
def profile(request):
    """User profile view."""
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('core:profile')
    else:
        form = UserProfileForm(instance=profile)
    
    return render(request, 'core/profile.html', {'form': form})



from django.contrib.auth import logout
from django.urls import reverse

def logout_view(request):
    logout(request)
    return redirect(reverse('login'))


