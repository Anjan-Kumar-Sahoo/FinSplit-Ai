"""
Django forms for core app.
"""
from django import forms
from django.contrib.auth.models import User
from .models import Pool, Expense, Member, UserProfile, ExpenseSplit


class UserProfileForm(forms.ModelForm):
    """Form for user profile."""
    class Meta:
        model = UserProfile
        fields = ['upi_id', 'phone_number']
        widgets = {
            'upi_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., yourname@paytm, 9876543210@ybl'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., +91 9876543210'
            }),
        }


class PoolForm(forms.ModelForm):
    """Form for creating and editing pools."""
    class Meta:
        model = Pool
        fields = ['name', 'description', 'default_split_method']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Trip to Goa, Office Lunch'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional description of the pool'
            }),
            'default_split_method': forms.Select(attrs={
                'class': 'form-control'
            }),
        }


class ExpenseForm(forms.ModelForm):
    """Form for creating and editing expenses."""
    split_equally = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = Expense
        fields = ['title', 'description', 'amount', 'paid_by', 'expense_date', 'split_method', 'receipt_image']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Dinner at restaurant, Uber ride'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Optional details about the expense'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'placeholder': '0.00'
            }),
            'paid_by': forms.Select(attrs={
                'class': 'form-control'
            }),
            'expense_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'split_method': forms.Select(attrs={
                'class': 'form-control'
            }),
            'receipt_image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        pool = kwargs.pop('pool', None)
        super().__init__(*args, **kwargs)
        
        if pool:
            # Limit paid_by choices to pool members
            self.fields['paid_by'].queryset = User.objects.filter(
                member__pool=pool,
                member__is_active=True
            )


class MemberForm(forms.Form):
    """Form for adding members to a pool."""
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'username or email'
        })
    )
    upi_id = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'member@paytm (optional)'
        })
    )

class ExpenseSplitForm(forms.ModelForm):
    """Form for custom expense splits."""
    class Meta:
        model = ExpenseSplit
        fields = ['user', 'amount', 'percentage']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.00'
            }),
            'percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.00',
                'max': '100.00'
            }),
        }


class PoolSearchForm(forms.Form):
    """Form for searching pools."""
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search pools...'
        })
    )


class TransactionForm(forms.Form):
    """Form for creating settlement transactions."""
    from_user = forms.ModelChoiceField(
        queryset=User.objects.none(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    to_user = forms.ModelChoiceField(
        queryset=User.objects.none(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0.01,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0.01'
        })
    )
    payment_method = forms.ChoiceField(
        choices=[
            ('upi', 'UPI'),
            ('cash', 'Cash'),
            ('bank_transfer', 'Bank Transfer'),
            ('other', 'Other'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Optional notes'
        })
    )
    
    def __init__(self, *args, **kwargs):
        pool = kwargs.pop('pool', None)
        super().__init__(*args, **kwargs)
        
        if pool:
            pool_members = User.objects.filter(
                member__pool=pool,
                member__is_active=True
            )
            self.fields['from_user'].queryset = pool_members
            self.fields['to_user'].queryset = pool_members

