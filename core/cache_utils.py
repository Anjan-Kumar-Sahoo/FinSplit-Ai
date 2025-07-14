"""
Caching utilities for FinSplit.
Implements caching for expensive operations like pool summaries and balance calculations.
"""

from django.core.cache import cache
from django.conf import settings
from functools import wraps
import hashlib
import json
import logging
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)

# Cache timeout settings (in seconds)
CACHE_TIMEOUTS = {
    'pool_summary': 300,      # 5 minutes
    'user_balance': 180,      # 3 minutes
    'pool_balances': 300,     # 5 minutes
    'expense_splits': 600,    # 10 minutes
    'user_pools': 120,        # 2 minutes
    'pool_members': 300,      # 5 minutes
    'api_response': 60,       # 1 minute
}


def generate_cache_key(prefix, *args, **kwargs):
    """Generate a unique cache key based on prefix and arguments."""
    # Create a string representation of all arguments
    key_data = {
        'args': args,
        'kwargs': sorted(kwargs.items())
    }
    key_string = json.dumps(key_data, sort_keys=True, default=str)
    
    # Create a hash of the key string
    key_hash = hashlib.md5(key_string.encode()).hexdigest()
    
    return f"finsplit:{prefix}:{key_hash}"


def cache_result(cache_key_prefix, timeout=None):
    """Decorator to cache function results."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = generate_cache_key(cache_key_prefix, *args, **kwargs)
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_timeout = timeout or CACHE_TIMEOUTS.get(cache_key_prefix, 300)
            cache.set(cache_key, result, cache_timeout)
            logger.debug(f"Cache set for {cache_key} with timeout {cache_timeout}")
            
            return result
        return wrapper
    return decorator


def invalidate_cache_pattern(pattern):
    """Invalidate all cache keys matching a pattern."""
    try:
        # This is a simplified version - in production, you might want to use Redis
        # with pattern matching or maintain a list of cache keys
        cache.clear()  # For now, clear all cache
        logger.info(f"Cache cleared for pattern: {pattern}")
    except Exception as e:
        logger.error(f"Failed to invalidate cache pattern {pattern}: {str(e)}")


def invalidate_pool_cache(pool_id):
    """Invalidate all cache entries related to a specific pool."""
    patterns = [
        f"finsplit:pool_summary:*{pool_id}*",
        f"finsplit:pool_balances:*{pool_id}*",
        f"finsplit:pool_members:*{pool_id}*",
        f"finsplit:user_balance:*{pool_id}*",
    ]
    
    for pattern in patterns:
        invalidate_cache_pattern(pattern)


def invalidate_user_cache(user_id):
    """Invalidate all cache entries related to a specific user."""
    patterns = [
        f"finsplit:user_pools:*{user_id}*",
        f"finsplit:user_balance:*{user_id}*",
    ]
    
    for pattern in patterns:
        invalidate_cache_pattern(pattern)


# Cached functions for expensive operations

@cache_result('pool_summary')
def get_cached_pool_summary(pool_id):
    """Get cached pool summary including total expenses, member count, etc."""
    from .models import Pool
    
    try:
        pool = Pool.objects.get(id=pool_id)
        
        summary = {
            'total_expenses': float(pool.get_total_expenses()),
            'member_count': pool.get_member_count(),
            'expense_count': pool.expenses.count(),
            'last_expense_date': pool.expenses.order_by('-expense_date').first().expense_date if pool.expenses.exists() else None,
            'created_at': pool.created_at,
        }
        
        return summary
    except Exception as e:
        logger.error(f"Error getting pool summary for pool {pool_id}: {str(e)}")
        return None


@cache_result('pool_balances')
def get_cached_pool_balances(pool_id):
    """Get cached balance calculations for all pool members."""
    from .models import Pool
    
    try:
        pool = Pool.objects.get(id=pool_id)
        balances = {}
        
        for member in pool.members.all():
            # Calculate what user paid
            paid_amount = sum(
                expense.amount for expense in pool.expenses.filter(paid_by=member)
            )
            
            # Calculate what user owes
            owed_amount = Decimal('0')
            for expense in pool.expenses.all():
                splits = expense.splits.filter(user=member)
                if splits.exists():
                    owed_amount += sum(split.amount for split in splits)
            
            balance = paid_amount - owed_amount
            
            balances[member.id] = {
                'user_id': member.id,
                'username': member.username,
                'paid': float(paid_amount),
                'owes': float(owed_amount),
                'balance': float(balance),
            }
        
        return balances
    except Exception as e:
        logger.error(f"Error getting pool balances for pool {pool_id}: {str(e)}")
        return {}


@cache_result('user_balance')
def get_cached_user_balance(user_id, pool_id):
    """Get cached balance for a specific user in a specific pool."""
    from .models import Pool, User
    
    try:
        user = User.objects.get(id=user_id)
        pool = Pool.objects.get(id=pool_id)
        
        # Calculate what user paid
        paid_amount = sum(
            expense.amount for expense in pool.expenses.filter(paid_by=user)
        )
        
        # Calculate what user owes
        owed_amount = Decimal('0')
        for expense in pool.expenses.all():
            splits = expense.splits.filter(user=user)
            if splits.exists():
                owed_amount += sum(split.amount for split in splits)
        
        balance = paid_amount - owed_amount
        
        return {
            'paid': float(paid_amount),
            'owes': float(owed_amount),
            'balance': float(balance),
        }
    except Exception as e:
        logger.error(f"Error getting user balance for user {user_id} in pool {pool_id}: {str(e)}")
        return {'paid': 0, 'owes': 0, 'balance': 0}


@cache_result('user_pools')
def get_cached_user_pools(user_id):
    """Get cached list of pools for a user."""
    from .models import Pool, User
    
    try:
        user = User.objects.get(id=user_id)
        pools = Pool.objects.filter(members=user).values(
            'id', 'name', 'description', 'created_at', 'created_by__username'
        )
        
        return list(pools)
    except Exception as e:
        logger.error(f"Error getting user pools for user {user_id}: {str(e)}")
        return []


@cache_result('pool_members')
def get_cached_pool_members(pool_id):
    """Get cached list of pool members."""
    from .models import Pool
    
    try:
        pool = Pool.objects.get(id=pool_id)
        members = pool.members.values(
            'id', 'username', 'email', 'first_name', 'last_name'
        )
        
        return list(members)
    except Exception as e:
        logger.error(f"Error getting pool members for pool {pool_id}: {str(e)}")
        return []


# Cache warming functions

def warm_pool_cache(pool_id):
    """Pre-populate cache for a pool."""
    logger.info(f"Warming cache for pool {pool_id}")
    
    # Warm up pool summary
    get_cached_pool_summary(pool_id)
    
    # Warm up pool balances
    get_cached_pool_balances(pool_id)
    
    # Warm up pool members
    get_cached_pool_members(pool_id)
    
    logger.info(f"Cache warmed for pool {pool_id}")


def warm_user_cache(user_id):
    """Pre-populate cache for a user."""
    logger.info(f"Warming cache for user {user_id}")
    
    # Warm up user pools
    user_pools = get_cached_user_pools(user_id)
    
    # Warm up user balances for each pool
    for pool in user_pools:
        get_cached_user_balance(user_id, pool['id'])
    
    logger.info(f"Cache warmed for user {user_id}")


# Cache statistics and monitoring

def get_cache_stats():
    """Get cache statistics."""
    try:
        # This would depend on your cache backend
        # For memcached or Redis, you could get actual stats
        return {
            'backend': settings.CACHES['default']['BACKEND'],
            'status': 'active',
            'timeouts': CACHE_TIMEOUTS,
        }
    except Exception as e:
        logger.error(f"Error getting cache stats: {str(e)}")
        return {'status': 'error', 'error': str(e)}


# Cache middleware for API responses

class APICacheMiddleware:
    """Middleware to cache API responses."""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Check if this is an API request
        if request.path.startswith('/api/') and request.method == 'GET':
            cache_key = generate_cache_key('api_response', request.path, request.GET.dict())
            
            # Try to get cached response
            cached_response = cache.get(cache_key)
            if cached_response:
                logger.debug(f"API cache hit for {request.path}")
                return cached_response
        
        response = self.get_response(request)
        
        # Cache successful GET responses
        if (request.path.startswith('/api/') and 
            request.method == 'GET' and 
            response.status_code == 200):
            
            cache_key = generate_cache_key('api_response', request.path, request.GET.dict())
            cache.set(cache_key, response, CACHE_TIMEOUTS['api_response'])
            logger.debug(f"API response cached for {request.path}")
        
        return response

