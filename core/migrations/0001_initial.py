# Generated by Django 5.2.4 on 2025-07-10 08:39

import django.core.validators
import django.db.models.deletion
import django.utils.timezone
import uuid
from decimal import Decimal
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Member',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('joined_at', models.DateTimeField(auto_now_add=True)),
                ('is_active', models.BooleanField(default=True)),
                ('is_admin', models.BooleanField(default=False)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Member',
                'verbose_name_plural': 'Members',
            },
        ),
        migrations.CreateModel(
            name='Pool',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Name of the expense pool', max_length=100)),
                ('description', models.TextField(blank=True, help_text='Description of the pool')),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('default_split_method', models.CharField(choices=[('equal', 'Equal Split'), ('percentage', 'Percentage Split'), ('manual', 'Manual Split')], default='equal', max_length=20)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='created_pools', to=settings.AUTH_USER_MODEL)),
                ('members', models.ManyToManyField(related_name='pools', through='core.Member', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Pool',
                'verbose_name_plural': 'Pools',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddField(
            model_name='member',
            name='pool',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.pool'),
        ),
        migrations.CreateModel(
            name='Invitation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254)),
                ('upi_id', models.CharField(blank=True, max_length=100)),
                ('token', models.UUIDField(default=uuid.uuid4, unique=True)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('declined', 'Declined'), ('expired', 'Expired')], default='pending', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField()),
                ('accepted_at', models.DateTimeField(blank=True, null=True)),
                ('invited_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sent_invitations', to=settings.AUTH_USER_MODEL)),
                ('pool', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='invitations', to='core.pool')),
            ],
            options={
                'verbose_name': 'Invitation',
                'verbose_name_plural': 'Invitations',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Expense',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(help_text='What was this expense for?', max_length=200)),
                ('description', models.TextField(blank=True)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))])),
                ('expense_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('split_method', models.CharField(choices=[('equal', 'Equal Split'), ('percentage', 'Percentage Split'), ('manual', 'Manual Split')], default='equal', max_length=20)),
                ('receipt_image', models.ImageField(blank=True, null=True, upload_to='receipts/')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='created_expenses', to=settings.AUTH_USER_MODEL)),
                ('paid_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='paid_expenses', to=settings.AUTH_USER_MODEL)),
                ('pool', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='expenses', to='core.pool')),
            ],
            options={
                'verbose_name': 'Expense',
                'verbose_name_plural': 'Expenses',
                'ordering': ['-expense_date', '-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))])),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], default='pending', max_length=20)),
                ('upi_transaction_id', models.CharField(blank=True, max_length=100)),
                ('payment_method', models.CharField(choices=[('upi', 'UPI'), ('cash', 'Cash'), ('bank_transfer', 'Bank Transfer'), ('other', 'Other')], default='upi', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('notes', models.TextField(blank=True)),
                ('from_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='outgoing_transactions', to=settings.AUTH_USER_MODEL)),
                ('pool', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transactions', to='core.pool')),
                ('to_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='incoming_transactions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Transaction',
                'verbose_name_plural': 'Transactions',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('upi_id', models.CharField(help_text='Your UPI ID for receiving payments', max_length=100, validators=[django.core.validators.RegexValidator(message='Enter a valid UPI ID (e.g., user@paytm, 9876543210@ybl)', regex='^[\\w\\.-]+@[\\w\\.-]+$')])),
                ('phone_number', models.CharField(blank=True, max_length=15, validators=[django.core.validators.RegexValidator(message='Enter a valid phone number', regex='^\\+?1?\\d{9,15}$')])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'User Profile',
                'verbose_name_plural': 'User Profiles',
            },
        ),
        migrations.CreateModel(
            name='ExpenseSplit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('percentage', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('expense', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='splits', to='core.expense')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Expense Split',
                'verbose_name_plural': 'Expense Splits',
                'unique_together': {('expense', 'user')},
            },
        ),
        migrations.AlterUniqueTogether(
            name='member',
            unique_together={('user', 'pool')},
        ),
    ]
