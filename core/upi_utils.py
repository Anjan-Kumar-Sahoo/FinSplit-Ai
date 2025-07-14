"""
UPI utilities for FinSplit.
Handles UPI ID validation and integration with external payment APIs.
"""

import re
import requests
import threading
import logging
from django.conf import settings
from django.core.cache import cache
import json
from decimal import Decimal

logger = logging.getLogger(__name__)

# UPI ID validation regex
UPI_REGEX = re.compile(r'^[\w\.-]+@[\w\.-]+$')

# Common UPI providers
UPI_PROVIDERS = {
    'paytm': 'Paytm',
    'phonepe': 'PhonePe',
    'gpay': 'Google Pay',
    'amazonpay': 'Amazon Pay',
    'mobikwik': 'MobiKwik',
    'freecharge': 'FreeCharge',
    'airtel': 'Airtel Money',
    'jio': 'JioMoney',
    'sbi': 'SBI Pay',
    'icici': 'iMobile Pay',
    'hdfc': 'HDFC Bank',
    'axis': 'Axis Bank',
    'kotak': 'Kotak Bank',
    'ybl': 'PhonePe',
    'okhdfcbank': 'HDFC Bank',
    'okaxis': 'Axis Bank',
    'oksbi': 'SBI Pay',
    'okicici': 'ICICI Bank',
}


def validate_upi_id(upi_id):
    """
    Validate UPI ID format.
    
    Args:
        upi_id (str): UPI ID to validate
        
    Returns:
        dict: Validation result with status and details
    """
    if not upi_id:
        return {
            'valid': False,
            'error': 'UPI ID is required'
        }
    
    # Basic format validation
    if not UPI_REGEX.match(upi_id):
        return {
            'valid': False,
            'error': 'Invalid UPI ID format. Should be like user@provider'
        }
    
    # Extract provider
    try:
        username, provider = upi_id.split('@')
        
        if len(username) < 3:
            return {
                'valid': False,
                'error': 'Username part should be at least 3 characters'
            }
        
        provider_name = UPI_PROVIDERS.get(provider.lower(), provider.title())
        
        return {
            'valid': True,
            'username': username,
            'provider': provider,
            'provider_name': provider_name,
            'formatted': upi_id.lower()
        }
        
    except ValueError:
        return {
            'valid': False,
            'error': 'Invalid UPI ID format'
        }


def validate_upi_id_async(upi_id, callback=None):
    """
    Validate UPI ID asynchronously using external API.
    
    Args:
        upi_id (str): UPI ID to validate
        callback (function): Optional callback function for result
    """
    def validate():
        try:
            # First do basic validation
            basic_validation = validate_upi_id(upi_id)
            if not basic_validation['valid']:
                if callback:
                    callback(basic_validation)
                return basic_validation
            
            # Try to validate with external API (mock implementation)
            result = validate_upi_with_external_api(upi_id)
            
            if callback:
                callback(result)
            return result
            
        except Exception as e:
            error_result = {
                'valid': False,
                'error': f'Validation failed: {str(e)}'
            }
            if callback:
                callback(error_result)
            return error_result
    
    # Start validation in a separate thread
    validation_thread = threading.Thread(target=validate)
    validation_thread.daemon = True
    validation_thread.start()


def validate_upi_with_external_api(upi_id):
    """
    Validate UPI ID with external API (mock implementation).
    
    In a real implementation, this would call actual UPI validation APIs.
    """
    try:
        # Check cache first
        cache_key = f"upi_validation:{upi_id}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
        
        # Mock API call - in reality, you would call actual UPI validation service
        # For demonstration, we'll simulate an API response
        mock_api_response = {
            'status': 'success',
            'valid': True,
            'upi_id': upi_id,
            'account_exists': True,
            'provider_verified': True
        }
        
        # Simulate API delay
        import time
        time.sleep(0.5)
        
        result = {
            'valid': mock_api_response['valid'],
            'account_exists': mock_api_response.get('account_exists', False),
            'provider_verified': mock_api_response.get('provider_verified', False),
            'api_validated': True
        }
        
        # Cache the result for 1 hour
        cache.set(cache_key, result, 3600)
        
        return result
        
    except requests.RequestException as e:
        logger.error(f"UPI validation API error: {str(e)}")
        return {
            'valid': False,
            'error': 'Unable to validate with external service',
            'api_validated': False
        }
    except Exception as e:
        logger.error(f"UPI validation error: {str(e)}")
        return {
            'valid': False,
            'error': 'Validation failed',
            'api_validated': False
        }


def generate_upi_payment_link(upi_id, amount, note=None, transaction_ref=None):
    """
    Generate UPI payment link for easy payments.
    
    Args:
        upi_id (str): Recipient UPI ID
        amount (Decimal): Payment amount
        note (str): Optional payment note
        transaction_ref (str): Optional transaction reference
        
    Returns:
        str: UPI payment link
    """
    try:
        # Validate UPI ID
        validation = validate_upi_id(upi_id)
        if not validation['valid']:
            raise ValueError(f"Invalid UPI ID: {validation['error']}")
        
        # Build UPI payment URL
        upi_url = f"upi://pay?pa={upi_id}&am={amount}"
        
        if note:
            upi_url += f"&tn={note}"
        
        if transaction_ref:
            upi_url += f"&tr={transaction_ref}"
        
        # Add currency (INR)
        upi_url += "&cu=INR"
        
        return upi_url
        
    except Exception as e:
        logger.error(f"Error generating UPI payment link: {str(e)}")
        return None


def create_payment_request(from_user, to_user, amount, pool, description=None):
    """
    Create a payment request between users.
    
    Args:
        from_user: User who needs to pay
        to_user: User who will receive payment
        amount: Payment amount
        pool: Pool associated with payment
        description: Optional payment description
        
    Returns:
        dict: Payment request details
    """
    try:
        # Validate recipient UPI ID
        if not to_user.profile.upi_id:
            return {
                'success': False,
                'error': 'Recipient does not have a UPI ID configured'
            }
        
        validation = validate_upi_id(to_user.profile.upi_id)
        if not validation['valid']:
            return {
                'success': False,
                'error': f"Recipient UPI ID is invalid: {validation['error']}"
            }
        
        # Generate payment link
        note = description or f"FinSplit payment for {pool.name}"
        transaction_ref = f"FS{pool.id}{from_user.id}{to_user.id}"
        
        payment_link = generate_upi_payment_link(
            upi_id=to_user.profile.upi_id,
            amount=amount,
            note=note,
            transaction_ref=transaction_ref
        )
        
        if not payment_link:
            return {
                'success': False,
                'error': 'Failed to generate payment link'
            }
        
        return {
            'success': True,
            'payment_link': payment_link,
            'recipient_upi': to_user.profile.upi_id,
            'amount': float(amount),
            'note': note,
            'transaction_ref': transaction_ref,
            'recipient_name': to_user.get_full_name() or to_user.username
        }
        
    except Exception as e:
        logger.error(f"Error creating payment request: {str(e)}")
        return {
            'success': False,
            'error': 'Failed to create payment request'
        }


def get_upi_provider_info(upi_id):
    """
    Get information about UPI provider.
    
    Args:
        upi_id (str): UPI ID to analyze
        
    Returns:
        dict: Provider information
    """
    validation = validate_upi_id(upi_id)
    if not validation['valid']:
        return None
    
    provider = validation['provider'].lower()
    provider_name = UPI_PROVIDERS.get(provider, provider.title())
    
    # Provider-specific information
    provider_info = {
        'provider_code': provider,
        'provider_name': provider_name,
        'is_bank': provider in ['sbi', 'icici', 'hdfc', 'axis', 'kotak', 'okhdfcbank', 'okaxis', 'oksbi', 'okicici'],
        'is_wallet': provider in ['paytm', 'phonepe', 'mobikwik', 'freecharge', 'amazonpay'],
        'is_telecom': provider in ['airtel', 'jio'],
        'supports_qr': True,  # Most UPI providers support QR codes
        'supports_link': True,  # Most UPI providers support payment links
    }
    
    return provider_info


def bulk_validate_upi_ids(upi_ids):
    """
    Validate multiple UPI IDs in bulk.
    
    Args:
        upi_ids (list): List of UPI IDs to validate
        
    Returns:
        dict: Validation results for each UPI ID
    """
    results = {}
    
    def validate_single(upi_id):
        results[upi_id] = validate_upi_id(upi_id)
    
    # Use threading for concurrent validation
    threads = []
    for upi_id in upi_ids:
        thread = threading.Thread(target=validate_single, args=(upi_id,))
        thread.daemon = True
        thread.start()
        threads.append(thread)
    
    # Wait for all validations to complete
    for thread in threads:
        thread.join()
    
    return results


def get_payment_statistics(user):
    """
    Get payment statistics for a user.
    
    Args:
        user: User object
        
    Returns:
        dict: Payment statistics
    """
    try:
        from .models import Transaction
        
        # Get user's transactions
        sent_transactions = Transaction.objects.filter(from_user=user)
        received_transactions = Transaction.objects.filter(to_user=user)
        
        stats = {
            'total_sent': sent_transactions.count(),
            'total_received': received_transactions.count(),
            'amount_sent': sum(t.amount for t in sent_transactions),
            'amount_received': sum(t.amount for t in received_transactions),
            'pending_sent': sent_transactions.filter(status='pending').count(),
            'pending_received': received_transactions.filter(status='pending').count(),
            'completed_sent': sent_transactions.filter(status='completed').count(),
            'completed_received': received_transactions.filter(status='completed').count(),
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting payment statistics: {str(e)}")
        return {}


# UPI QR Code generation (would require additional libraries in production)
def generate_upi_qr_data(upi_id, amount, note=None):
    """
    Generate UPI QR code data.
    
    Args:
        upi_id (str): UPI ID
        amount (Decimal): Amount
        note (str): Optional note
        
    Returns:
        str: QR code data string
    """
    payment_link = generate_upi_payment_link(upi_id, amount, note)
    return payment_link  # In production, you'd generate actual QR code image

