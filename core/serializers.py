"""
Django REST Framework serializers for core app.
"""
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Pool, Member, Expense, Transaction, ExpenseSplit, UserProfile, Invitation


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    upi_id = serializers.CharField(source='profile.upi_id', read_only=True)
    phone_number = serializers.CharField(source='profile.phone_number', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'upi_id', 'phone_number']
        read_only_fields = ['id']


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile model."""
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ['id', 'username', 'email', 'upi_id', 'phone_number', 'created_at', 'updated_at']
        read_only_fields = ['id', 'username', 'email', 'created_at', 'updated_at']


class MemberSerializer(serializers.ModelSerializer):
    """Serializer for Member model."""
    user = UserSerializer(read_only=True)
    pool_name = serializers.CharField(source='pool.name', read_only=True)
    
    class Meta:
        model = Member
        fields = ['id', 'user', 'pool', 'pool_name', 'joined_at', 'is_active', 'is_admin']
        read_only_fields = ['id', 'joined_at']


class PoolSerializer(serializers.ModelSerializer):
    """Serializer for Pool model."""
    created_by = UserSerializer(read_only=True)
    members = UserSerializer(many=True, read_only=True)
    member_count = serializers.SerializerMethodField()
    total_expenses = serializers.SerializerMethodField()
    
    class Meta:
        model = Pool
        fields = [
            'id', 'name', 'description', 'created_by', 'members', 'is_active',
            'created_at', 'updated_at', 'default_split_method', 'member_count', 'total_expenses'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']
    
    def get_member_count(self, obj):
        return obj.get_member_count()
    
    def get_total_expenses(self, obj):
        return obj.get_total_expenses()


class ExpenseSplitSerializer(serializers.ModelSerializer):
    """Serializer for ExpenseSplit model."""
    user = UserSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = ExpenseSplit
        fields = ['id', 'user', 'user_id', 'amount', 'percentage']
        read_only_fields = ['id']


class ExpenseSerializer(serializers.ModelSerializer):
    """Serializer for Expense model."""
    paid_by = UserSerializer(read_only=True)
    paid_by_id = serializers.IntegerField(write_only=True)
    created_by = UserSerializer(read_only=True)
    pool_name = serializers.CharField(source='pool.name', read_only=True)
    splits = ExpenseSplitSerializer(many=True, read_only=True)
    split_summary = serializers.SerializerMethodField()
    
    class Meta:
        model = Expense
        fields = [
            'id', 'pool', 'pool_name', 'title', 'description', 'amount',
            'paid_by', 'paid_by_id', 'created_by', 'expense_date', 'created_at',
            'updated_at', 'split_method', 'receipt_image', 'splits', 'split_summary'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']
    
    def get_split_summary(self, obj):
        return obj.get_split_summary()


class TransactionSerializer(serializers.ModelSerializer):
    """Serializer for Transaction model."""
    from_user = UserSerializer(read_only=True)
    from_user_id = serializers.IntegerField(write_only=True)
    to_user = UserSerializer(read_only=True)
    to_user_id = serializers.IntegerField(write_only=True)
    pool_name = serializers.CharField(source='pool.name', read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'pool', 'pool_name', 'from_user', 'from_user_id', 'to_user', 'to_user_id',
            'amount', 'status', 'upi_transaction_id', 'payment_method', 'created_at',
            'completed_at', 'notes'
        ]
        read_only_fields = ['id', 'created_at', 'completed_at']


class InvitationSerializer(serializers.ModelSerializer):
    """Serializer for Invitation model."""
    invited_by = UserSerializer(read_only=True)
    pool_name = serializers.CharField(source='pool.name', read_only=True)
    is_expired = serializers.SerializerMethodField()
    
    class Meta:
        model = Invitation
        fields = [
            'id', 'pool', 'pool_name', 'invited_by', 'email', 'upi_id',
            'token', 'status', 'created_at', 'expires_at', 'accepted_at', 'is_expired'
        ]
        read_only_fields = ['id', 'invited_by', 'token', 'created_at', 'accepted_at']
    
    def get_is_expired(self, obj):
        return obj.is_expired()


class PoolBalanceSerializer(serializers.Serializer):
    """Serializer for pool balance information."""
    user_id = serializers.IntegerField()
    username = serializers.CharField()
    email = serializers.EmailField()
    paid = serializers.DecimalField(max_digits=10, decimal_places=2)
    owes = serializers.DecimalField(max_digits=10, decimal_places=2)
    balance = serializers.DecimalField(max_digits=10, decimal_places=2)
    upi_id = serializers.CharField()


class PoolSummarySerializer(serializers.Serializer):
    """Serializer for pool summary information."""
    pool_id = serializers.IntegerField()
    pool_name = serializers.CharField()
    total_expenses = serializers.DecimalField(max_digits=10, decimal_places=2)
    member_count = serializers.IntegerField()
    recent_expenses = ExpenseSerializer(many=True)
    pending_transactions = serializers.IntegerField()
    balances_count = serializers.IntegerField()


class UPIValidationSerializer(serializers.Serializer):
    """Serializer for UPI validation request."""
    upi_id = serializers.CharField(max_length=100)


class UPIValidationResponseSerializer(serializers.Serializer):
    """Serializer for UPI validation response."""
    valid = serializers.BooleanField()
    message = serializers.CharField()
    provider = serializers.CharField(required=False)


class InviteEmailSerializer(serializers.Serializer):
    """Serializer for sending invitation emails."""
    pool_id = serializers.IntegerField()
    email = serializers.EmailField()
    message = serializers.CharField(required=False)

