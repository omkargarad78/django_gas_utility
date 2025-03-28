# Generated by Django 5.1.7 on 2025-03-27 19:07

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_alter_user_options_user_created_at_user_updated_at_and_more'),
        ('requests', '0003_servicerequest_notes'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customer',
            name='user',
        ),
        migrations.AlterField(
            model_name='servicerequest',
            name='customer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='service_requests', to='accounts.customer'),
        ),
        migrations.RemoveField(
            model_name='supportrepresentative',
            name='user',
        ),
        migrations.AlterModelOptions(
            name='servicerequest',
            options={'ordering': ['-created_at'], 'verbose_name': 'Service Request', 'verbose_name_plural': 'Service Requests'},
        ),
        migrations.AddField(
            model_name='servicerequest',
            name='assigned_to',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_requests', to='accounts.supportrepresentative'),
        ),
        migrations.AddField(
            model_name='servicerequest',
            name='priority',
            field=models.CharField(choices=[('Low', 'Low'), ('Medium', 'Medium'), ('High', 'High'), ('Urgent', 'Urgent')], db_index=True, default='Medium', max_length=20),
        ),
        migrations.AddField(
            model_name='servicerequest',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='servicerequest',
            name='attached_file',
            field=models.FileField(blank=True, help_text='Supporting documentation or images', null=True, upload_to='service_requests/'),
        ),
        migrations.AlterField(
            model_name='servicerequest',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='servicerequest',
            name='description',
            field=models.TextField(help_text='Detailed description of the issue'),
        ),
        migrations.AlterField(
            model_name='servicerequest',
            name='service_type',
            field=models.CharField(choices=[('New Connection', 'New Connection'), ('Billing Issue', 'Billing Issue'), ('Gas Leak', 'Gas Leak'), ('Meter Problem', 'Meter Problem'), ('Other', 'Other')], help_text='Type of service requested', max_length=100),
        ),
        migrations.AlterField(
            model_name='servicerequest',
            name='status',
            field=models.CharField(choices=[('Pending', 'Pending'), ('In Progress', 'In Progress'), ('Resolved', 'Resolved')], db_index=True, default='Pending', max_length=20),
        ),
        migrations.AddIndex(
            model_name='servicerequest',
            index=models.Index(fields=['customer', 'status'], name='requests_se_custome_5984e7_idx'),
        ),
        migrations.AddIndex(
            model_name='servicerequest',
            index=models.Index(fields=['status', 'created_at'], name='requests_se_status_6f6a49_idx'),
        ),
        migrations.AddIndex(
            model_name='servicerequest',
            index=models.Index(fields=['priority', 'status'], name='requests_se_priorit_7eca41_idx'),
        ),
        migrations.DeleteModel(
            name='Customer',
        ),
        migrations.DeleteModel(
            name='SupportRepresentative',
        ),
    ]
