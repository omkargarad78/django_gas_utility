# Generated by Django 5.1.7 on 2025-03-27 19:07

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='user',
            options={'ordering': ['-date_joined'], 'verbose_name': 'User', 'verbose_name_plural': 'Users'},
        ),
        migrations.AddField(
            model_name='user',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='user',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(choices=[('customer', 'Customer'), ('support_staff', 'Support Staff')], default='customer', help_text="Determines the user's permissions and access level", max_length=20, verbose_name='User Role'),
        ),
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone_number', models.CharField(blank=True, help_text="Customer's phone number for contact purposes", max_length=15, null=True)),
                ('address', models.TextField(blank=True, help_text="Customer's address for service visits", null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='customer_profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Customer',
                'verbose_name_plural': 'Customers',
                'indexes': [models.Index(fields=['user'], name='accounts_cu_user_id_4678a9_idx')],
            },
        ),
        migrations.CreateModel(
            name='SupportRepresentative',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('department', models.CharField(blank=True, help_text='Department the support representative belongs to', max_length=100, null=True)),
                ('employee_id', models.CharField(blank=True, help_text='Employee ID for internal reference', max_length=50, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='support_profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Support Representative',
                'verbose_name_plural': 'Support Representatives',
                'indexes': [models.Index(fields=['user'], name='accounts_su_user_id_45e338_idx')],
            },
        ),
    ]
