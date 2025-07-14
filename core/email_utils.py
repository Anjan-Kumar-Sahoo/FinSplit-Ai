"""
Email utility functions for FinSplit.
Handles sending invites, expense summaries, and notifications.
"""

import threading
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.contrib.auth.models import User
from .models import Pool, Expense, Member
import logging

logger = logging.getLogger(__name__)


def send_email_async(subject, message, from_email, recipient_list, html_message=None):
    """Send email asynchronously using threading."""
    def send_email():
        try:
            if html_message:
                email = EmailMultiAlternatives(subject, message, from_email, recipient_list)
                email.attach_alternative(html_message, "text/html")
                email.send()
            else:
                send_mail(subject, message, from_email, recipient_list)
            logger.info(f"Email sent successfully to {recipient_list}")
        except Exception as e:
            logger.error(f"Failed to send email to {recipient_list}: {str(e)}")
    
    # Start email sending in a separate thread
    email_thread = threading.Thread(target=send_email)
    email_thread.daemon = True
    email_thread.start()


def send_pool_invite_email(inviter, pool, invited_email):
    """Send pool invitation email to a user."""
    subject = f"You've been invited to join '{pool.name}' on FinSplit"
    
    context = {
        'pool': pool,
        'invited_email': invited_email,
        'inviter': inviter,
        'site_name': 'FinSplit',
        'login_url': f"{settings.SITE_URL}/auth/login/" if hasattr(settings, 'SITE_URL') else 'http://localhost:8000/auth/login/'
    }
    
    # Render HTML email template
    html_message = render_to_string('emails/pool_invite.html', context)
    plain_message = strip_tags(html_message)
    
    send_email_async(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[invited_email],
        html_message=html_message
    )


def send_expense_notification_email(expense, members):
    """Send expense notification email to pool members."""
    subject = f"New expense added: {expense.title}"
    
    context = {
        'expense': expense,
        'pool': expense.pool,
        'site_name': 'FinSplit',
        'pool_url': f"{settings.SITE_URL}/pools/{expense.pool.id}/" if hasattr(settings, 'SITE_URL') else f'http://localhost:8000/pools/{expense.pool.id}/'
    }
    
    # Render HTML email template
    html_message = render_to_string('emails/expense_notification.html', context)
    plain_message = strip_tags(html_message)
    
    # Send to all members except the one who created the expense
    recipient_emails = [member.email for member in members if member != expense.created_by and member.email]
    
    if recipient_emails:
        send_email_async(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_emails,
            html_message=html_message
        )


def send_expense_summary_email(pool, user):
    """Send expense summary email for a pool."""
    subject = f"Expense Summary for '{pool.name}'"
    
    # Calculate user's balance and expenses
    user_expenses = pool.expenses.filter(paid_by=user)
    user_splits = []
    
    for expense in pool.expenses.all():
        splits = expense.splits.filter(user=user)
        if splits.exists():
            user_splits.extend(splits)
    
    total_paid = sum(expense.amount for expense in user_expenses)
    total_owed = sum(split.amount for split in user_splits)
    balance = total_paid - total_owed
    
    context = {
        'pool': pool,
        'user': user,
        'user_expenses': user_expenses,
        'user_splits': user_splits,
        'total_paid': total_paid,
        'total_owed': total_owed,
        'balance': balance,
        'site_name': 'FinSplit',
        'pool_url': f"{settings.SITE_URL}/pools/{pool.id}/" if hasattr(settings, 'SITE_URL') else f'http://localhost:8000/pools/{pool.id}/'
    }
    
    # Render HTML email template
    html_message = render_to_string('emails/expense_summary.html', context)
    plain_message = strip_tags(html_message)
    
    send_email_async(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message
    )


def send_settlement_reminder_email(transaction):
    """Send settlement reminder email."""
    subject = f"Settlement Reminder: ₹{transaction.amount} to {transaction.to_user.username}"
    
    context = {
        'transaction': transaction,
        'pool': transaction.pool,
        'site_name': 'FinSplit',
        'pool_url': f"{settings.SITE_URL}/pools/{transaction.pool.id}/settle/" if hasattr(settings, 'SITE_URL') else f'http://localhost:8000/pools/{transaction.pool.id}/settle/'
    }
    
    # Render HTML email template
    html_message = render_to_string('emails/settlement_reminder.html', context)
    plain_message = strip_tags(html_message)
    
    send_email_async(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[transaction.from_user.email],
        html_message=html_message
    )


def send_weekly_summary_email(user):
    """Send weekly summary email to user."""
    subject = "Your Weekly FinSplit Summary"
    
    # Get user's pools and recent activity
    user_pools = Pool.objects.filter(members=user)
    recent_expenses = Expense.objects.filter(
        pool__in=user_pools,
        created_at__gte=timezone.now() - timedelta(days=7)
    ).order_by('-created_at')
    
    context = {
        'user': user,
        'user_pools': user_pools,
        'recent_expenses': recent_expenses,
        'site_name': 'FinSplit',
        'dashboard_url': f"{settings.SITE_URL}/dashboard/" if hasattr(settings, 'SITE_URL') else 'http://localhost:8000/dashboard/'
    }
    
    # Render HTML email template
    html_message = render_to_string('emails/weekly_summary.html', context)
    plain_message = strip_tags(html_message)
    
    send_email_async(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message
    )


# Bulk email functions
def send_bulk_expense_notifications(expense):
    """Send expense notifications to all pool members."""
    pool_members = expense.pool.members.exclude(id=expense.created_by.id)
    send_expense_notification_email(expense, pool_members)


def send_bulk_settlement_reminders(pool):
    """Send settlement reminders to all users with pending transactions."""
    pending_transactions = pool.transactions.filter(status='pending')
    
    for transaction in pending_transactions:
        send_settlement_reminder_email(transaction)


# Email template validation
def validate_email_templates():
    """Validate that all required email templates exist."""
    required_templates = [
        'emails/pool_invite.html',
        'emails/expense_notification.html',
        'emails/expense_summary.html',
        'emails/settlement_reminder.html',
        'emails/weekly_summary.html'
    ]
    
    missing_templates = []
    
    for template in required_templates:
        try:
            render_to_string(template, {})
        except:
            missing_templates.append(template)
    
    if missing_templates:
        logger.warning(f"Missing email templates: {missing_templates}")
        return False
    
    return True



def send_settlement_confirmation_email(transaction):
    """Send settlement confirmation email to both parties."""
    try:
        subject = f"Settlement Confirmed - {transaction.pool.name}"
        
        # Email to the payer (from_user)
        payer_context = {
            'transaction': transaction,
            'recipient_name': transaction.from_user.first_name or transaction.from_user.username,
            'is_payer': True,
        }
        payer_html_content = render_to_string('emails/settlement_confirmation.html', payer_context)
        
        def send_payer_email():
            send_mail(
                subject=subject,
                message=f"Your payment of ₹{transaction.amount} to {transaction.to_user.username} has been confirmed as settled.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[transaction.from_user.email],
                html_message=payer_html_content,
                fail_silently=True,
            )
        
        # Email to the payee (to_user)
        payee_context = {
            'transaction': transaction,
            'recipient_name': transaction.to_user.first_name or transaction.to_user.username,
            'is_payer': False,
        }
        payee_html_content = render_to_string('emails/settlement_confirmation.html', payee_context)
        
        def send_payee_email():
            send_mail(
                subject=subject,
                message=f"You have confirmed receipt of ₹{transaction.amount} from {transaction.from_user.username}.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[transaction.to_user.email],
                html_message=payee_html_content,
                fail_silently=True,
            )
        
        # Send emails in separate threads
        threading.Thread(target=send_payer_email).start()
        threading.Thread(target=send_payee_email).start()
        
        logger.info(f"Settlement confirmation emails sent for transaction {transaction.id}")
        
    except Exception as e:
        logger.error(f"Failed to send settlement confirmation emails for transaction {transaction.id}: {str(e)}")

