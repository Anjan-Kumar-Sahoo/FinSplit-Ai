"""
Django admin configuration for core app.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.urls import reverse
from .models import (
    UserProfile, Pool, Member, Expense, ExpenseSplit, 
    Transaction, Invitation
)


# Inline admin classes
class UserProfileInline(admin.StackedInline):
    """Inline admin for UserProfile."""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fields = ['upi_id', 'phone_number']


class MemberInline(admin.TabularInline):
    """Inline admin for Pool members."""
    model = Member
    extra = 0
    fields = ['user', 'is_admin', 'is_active', 'joined_at']
    readonly_fields = ['joined_at']


class ExpenseSplitInline(admin.TabularInline):
    """Inline admin for Expense splits."""
    model = ExpenseSplit
    extra = 0
    fields = ['user', 'amount', 'percentage']


# Extend User admin
class UserAdmin(BaseUserAdmin):
    """Extended User admin with profile information."""
    inlines = (UserProfileInline,)
    list_display = ['username', 'email', 'first_name', 'last_name', 'get_upi_id', 'is_staff', 'date_joined']
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'date_joined']
    
    def get_upi_id(self, obj):
        """Get UPI ID from profile."""
        try:
            return obj.profile.upi_id
        except UserProfile.DoesNotExist:
            return '-'
    get_upi_id.short_description = 'UPI ID'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin for UserProfile model."""
    list_display = ['user', 'upi_id', 'phone_number', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'user__email', 'upi_id', 'phone_number']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Pool)
class PoolAdmin(admin.ModelAdmin):
    """Admin for Pool model."""
    list_display = ['name', 'created_by', 'get_member_count', 'get_total_expenses', 'is_active', 'created_at']
    list_filter = ['is_active', 'default_split_method', 'created_at']
    search_fields = ['name', 'description', 'created_by__username']
    readonly_fields = ['created_at', 'updated_at', 'get_total_expenses', 'get_member_count']
    inlines = [MemberInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'created_by')
        }),
        ('Settings', {
            'fields': ('default_split_method', 'is_active')
        }),
        ('Statistics', {
            'fields': ('get_total_expenses', 'get_member_count'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_member_count(self, obj):
        """Get member count."""
        return obj.get_member_count()
    get_member_count.short_description = 'Members'
    
    def get_total_expenses(self, obj):
        """Get total expenses."""
        return f"₹{obj.get_total_expenses()}"
    get_total_expenses.short_description = 'Total Expenses'


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    """Admin for Member model."""
    list_display = ['user', 'pool', 'is_admin', 'is_active', 'joined_at']
    list_filter = ['is_admin', 'is_active', 'joined_at']
    search_fields = ['user__username', 'pool__name']
    readonly_fields = ['joined_at']
    
    fieldsets = (
        ('Member Information', {
            'fields': ('user', 'pool')
        }),
        ('Permissions', {
            'fields': ('is_admin', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('joined_at',)
        }),
    )


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    """Admin for Expense model."""
    list_display = ['title', 'pool', 'amount', 'paid_by', 'created_by', 'expense_date', 'split_method']
    list_filter = ['split_method', 'expense_date', 'created_at', 'pool']
    search_fields = ['title', 'description', 'paid_by__username', 'pool__name']
    readonly_fields = ['created_at', 'updated_at', 'get_split_summary']
    inlines = [ExpenseSplitInline]
    date_hierarchy = 'expense_date'
    
    fieldsets = (
        ('Expense Details', {
            'fields': ('title', 'description', 'amount', 'pool')
        }),
        ('Payment Information', {
            'fields': ('paid_by', 'created_by', 'expense_date')
        }),
        ('Split Configuration', {
            'fields': ('split_method',)
        }),
        ('Receipt', {
            'fields': ('receipt_image',),
            'classes': ('collapse',)
        }),
        ('Split Summary', {
            'fields': ('get_split_summary',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_split_summary(self, obj):
        """Get formatted split summary."""
        summary = obj.get_split_summary()
        html = f"<strong>Total: ₹{summary['total_amount']}</strong><br>"
        html += f"Split among {summary['split_count']} members:<br>"
        for split in summary['splits']:
            html += f"• {split['user']}: ₹{split['amount']} ({split['percentage']:.1f}%)<br>"
        return format_html(html)
    get_split_summary.short_description = 'Split Summary'


@admin.register(ExpenseSplit)
class ExpenseSplitAdmin(admin.ModelAdmin):
    """Admin for ExpenseSplit model."""
    list_display = ['expense', 'user', 'amount', 'percentage']
    list_filter = ['expense__pool', 'expense__expense_date']
    search_fields = ['expense__title', 'user__username']
    
    fieldsets = (
        ('Split Information', {
            'fields': ('expense', 'user')
        }),
        ('Amount Details', {
            'fields': ('amount', 'percentage')
        }),
    )


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """Admin for Transaction model."""
    list_display = ['from_user', 'to_user', 'amount', 'status', 'payment_method', 'pool', 'created_at']
    list_filter = ['status', 'payment_method', 'created_at', 'pool']
    search_fields = ['from_user__username', 'to_user__username', 'pool__name', 'upi_transaction_id']
    readonly_fields = ['created_at', 'completed_at']
    
    fieldsets = (
        ('Transaction Details', {
            'fields': ('pool', 'from_user', 'to_user', 'amount')
        }),
        ('Payment Information', {
            'fields': ('payment_method', 'upi_transaction_id', 'status')
        }),
        ('Additional Information', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_completed', 'mark_cancelled']
    
    def mark_completed(self, request, queryset):
        """Mark selected transactions as completed."""
        updated = queryset.filter(status='pending').update(status='completed')
        self.message_user(request, f'{updated} transactions marked as completed.')
    mark_completed.short_description = 'Mark selected transactions as completed'
    
    def mark_cancelled(self, request, queryset):
        """Mark selected transactions as cancelled."""
        updated = queryset.filter(status='pending').update(status='cancelled')
        self.message_user(request, f'{updated} transactions marked as cancelled.')
    mark_cancelled.short_description = 'Mark selected transactions as cancelled'


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    """Admin for Invitation model."""
    list_display = ['email', 'pool', 'invited_by', 'status', 'created_at', 'expires_at', 'is_expired']
    list_filter = ['status', 'created_at', 'expires_at']
    search_fields = ['email', 'pool__name', 'invited_by__username']
    readonly_fields = ['token', 'created_at', 'accepted_at', 'is_expired']
    
    fieldsets = (
        ('Invitation Details', {
            'fields': ('pool', 'invited_by', 'email', 'upi_id')
        }),
        ('Status', {
            'fields': ('status', 'token')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'expires_at', 'accepted_at', 'is_expired')
        }),
    )
    
    def is_expired(self, obj):
        """Check if invitation is expired."""
        return obj.is_expired()
    is_expired.boolean = True
    is_expired.short_description = 'Expired'


# Unregister the default User admin and register our custom one
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# Customize admin site headers
admin.site.site_header = 'FinSplit Administration'
admin.site.site_title = 'FinSplit Admin'
admin.site.index_title = 'Welcome to FinSplit Administration'

