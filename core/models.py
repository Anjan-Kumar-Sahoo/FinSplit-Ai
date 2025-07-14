"""
Django models for FinSplit application.
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, RegexValidator
from django.utils import timezone
from decimal import Decimal
import uuid


class UserProfile(models.Model):
    """Extended user profile with UPI information."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    upi_id = models.CharField(
        max_length=100, 
        validators=[
            RegexValidator(
                regex=r'^[\w\.-]+@[\w\.-]+$',
                message='Enter a valid UPI ID (e.g., user@paytm, 9876543210@ybl)'
            )
        ],
        help_text='Your UPI ID for receiving payments'
    )
    phone_number = models.CharField(
        max_length=15,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message='Enter a valid phone number'
            )
        ],
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.upi_id}"

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"


class Pool(models.Model):
    """A group/pool for expense sharing."""
    name = models.CharField(max_length=100, help_text='Name of the expense pool')
    description = models.TextField(blank=True, help_text='Description of the pool')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_pools')
    members = models.ManyToManyField(User, through='Member', related_name='pools')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Pool settings
    default_split_method = models.CharField(
        max_length=20,
        choices=[
            ('equal', 'Equal Split'),
            ('percentage', 'Percentage Split'),
            ('manual', 'Manual Split'),
        ],
        default='equal'
    )

    def __str__(self):
        return self.name

    def get_total_expenses(self):
        """Calculate total expenses in this pool."""
        return self.expenses.aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')

    def get_member_count(self):
        """Get number of active members in the pool."""
        return self.members.filter(member__is_active=True).count()

    def get_balances(self):
        """Calculate balances for all members in the pool."""
        balances = {}
        members = self.members.filter(member__is_active=True)
        
        for member in members:
            balances[member.id] = {
                'user': member,
                'paid': Decimal('0.00'),
                'owes': Decimal('0.00'),
                'balance': Decimal('0.00')
            }
        
        # Calculate what each member paid
        for expense in self.expenses.all():
            if expense.paid_by.id in balances:
                balances[expense.paid_by.id]['paid'] += expense.amount
        
        # Calculate what each member owes
        for expense in self.expenses.all():
            splits = expense.splits.all()
            for split in splits:
                if split.user.id in balances:
                    balances[split.user.id]['owes'] += split.amount
        
        # Calculate net balance (positive means they are owed money, negative means they owe money)
        for member_id in balances:
            balances[member_id]['balance'] = balances[member_id]['paid'] - balances[member_id]['owes']
        
        return balances

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Pool"
        verbose_name_plural = "Pools"


class Member(models.Model):
    """Membership relationship between User and Pool."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    pool = models.ForeignKey(Pool, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} in {self.pool.name}"

    class Meta:
        unique_together = ['user', 'pool']
        verbose_name = "Member"
        verbose_name_plural = "Members"


class Expense(models.Model):
    """An expense entry in a pool."""
    pool = models.ForeignKey(Pool, on_delete=models.CASCADE, related_name='expenses')
    title = models.CharField(max_length=200, help_text='What was this expense for?')
    description = models.TextField(blank=True)
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    paid_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='paid_expenses')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_expenses')
    
    # Expense metadata
    expense_date = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Split method for this expense
    split_method = models.CharField(
        max_length=20,
        choices=[
            ('equal', 'Equal Split'),
            ('percentage', 'Percentage Split'),
            ('manual', 'Manual Split'),
        ],
        default='equal'
    )
    
    # Receipt/proof
    receipt_image = models.ImageField(upload_to='receipts/', blank=True, null=True)
    
    def __str__(self):
        return f"{self.title} - ₹{self.amount}"

    def get_split_summary(self):
        """Get summary of how this expense is split."""
        splits = self.splits.all()
        return {
            'total_amount': self.amount,
            'split_count': splits.count(),
            'splits': [
                {
                    'user': split.user.username,
                    'amount': split.amount,
                    'percentage': (split.amount / self.amount * 100) if self.amount > 0 else 0
                }
                for split in splits
            ]
        }

    class Meta:
        ordering = ['-expense_date', '-created_at']
        verbose_name = "Expense"
        verbose_name_plural = "Expenses"


class ExpenseSplit(models.Model):
    """How an expense is split among members."""
    expense = models.ForeignKey(Expense, on_delete=models.CASCADE, related_name='splits')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))]
    )

    def __str__(self):
        return f"{self.user.username} owes ₹{self.amount} for {self.expense.title}"

    class Meta:
        unique_together = ['expense', 'user']
        verbose_name = "Expense Split"
        verbose_name_plural = "Expense Splits"


class Transaction(models.Model):
    """Settlement transactions between users."""
    pool = models.ForeignKey(Pool, on_delete=models.CASCADE, related_name='transactions')
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='outgoing_transactions')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='incoming_transactions')
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    # Transaction status
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Payment details
    upi_transaction_id = models.CharField(max_length=100, blank=True)
    payment_method = models.CharField(
        max_length=20,
        choices=[
            ('upi', 'UPI'),
            ('cash', 'Cash'),
            ('bank_transfer', 'Bank Transfer'),
            ('other', 'Other'),
        ],
        default='upi'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    settled_at = models.DateTimeField(null=True, blank=True)
    
    # Settlement status
    is_settled = models.BooleanField(default=False)
    
    # Notes
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.from_user.username} → {self.to_user.username}: ₹{self.amount}"

    def mark_completed(self):
        """Mark transaction as completed."""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()

    def mark_settled(self, settled_by_user):
        """Mark transaction as settled by the creditor."""
        if settled_by_user != self.to_user:
            raise ValueError("Only the creditor can mark a transaction as settled")
        
        self.is_settled = True
        self.settled_at = timezone.now()
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()
        
        # Send notification email if available
        try:
            from .email_utils import send_settlement_confirmation_email
            send_settlement_confirmation_email(self)
        except:
            pass  # Email sending is optional

    def can_be_settled_by(self, user):
        """Check if a user can settle this transaction."""
        return user == self.to_user and self.status == 'pending' and not self.is_settled

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"


class Invitation(models.Model):
    """Invitations sent to join pools."""
    pool = models.ForeignKey(Pool, on_delete=models.CASCADE, related_name='invitations')
    invited_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_invitations')
    email = models.EmailField()
    upi_id = models.CharField(max_length=100, blank=True)
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('expired', 'Expired'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Invitation to {self.email} for {self.pool.name}"

    def is_expired(self):
        """Check if invitation has expired."""
        return timezone.now() > self.expires_at

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Invitation"
        verbose_name_plural = "Invitations"

