# Generated by Django 2.0 on 2018-01-21 18:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0021_auto_20180121_1642'),
    ]

    operations = [
        migrations.AlterField(
            model_name='deposit',
            name='status',
            field=models.CharField(choices=[('awaiting_deposit', 'awaiting_deposit'), ('gas_received', 'gas_received'), ('pending', 'pending'), (
                'processed', 'processed'), ('failed', 'failed'), ('complete', 'complete')], default='awaiting_deposit', max_length=32),
        ),
        migrations.AlterField(
            model_name='purchase',
            name='status',
            field=models.CharField(choices=[('awaiting_deposit', 'awaiting_deposit'), ('gas_received', 'gas_received'), ('pending', 'pending'), (
                'processed', 'processed'), ('failed', 'failed'), ('complete', 'complete')], default='pending', max_length=32),
        ),
    ]
