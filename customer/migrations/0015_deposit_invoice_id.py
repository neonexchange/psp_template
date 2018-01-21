# Generated by Django 2.0 on 2018-01-21 02:15

from django.db import migrations, models
from uuid import uuid4

class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0014_pspuser_pending_deposit'),
    ]

    operations = [
        migrations.AddField(
            model_name='deposit',
            name='invoice_id',
            field=models.UUIDField(auto_created=True, default=uuid4()),
            preserve_default=False,
        ),
    ]
