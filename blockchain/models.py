from django.db import models
from customer.models import Purchase,PSPUser,ASSET_CHOICES,PURCHASE_STATUS
# Create your models here.




class BlockchainTransfer(models.Model):

    to_address = models.CharField(max_length=34)
    from_address = models.CharField(max_length=34)

    amount = models.FloatField()

    asset = models.CharField(max_length=3, choices=ASSET_CHOICES, default='GAS')

    transaction_id = models.CharField(max_length=64, blank=True, null=True)

    status = models.CharField(max_length=64, choices=PURCHASE_STATUS, default='pending')

    start_block = models.IntegerField()

    confirmed_block = models.IntegerField(blank=True,null=True)


