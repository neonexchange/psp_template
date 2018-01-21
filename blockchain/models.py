from django.db import models
from customer.models import Purchase,PSPUser,ASSET_CHOICES,PURCHASE_STATUS
from neo.Core.Blockchain import Blockchain
import binascii
import json
from django.conf import settings
from logzero import logger
from neo.Implementations.Wallets.peewee.UserWallet import UserWallet
# Create your models here.
from uuid import uuid4


class DepositWallet(models.Model):

    depositor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    wallet_file = models.FilePathField()

    wallet_pass = models.CharField(max_length=64)

    start_height = models.IntegerField()

    def __str__(self):
        return "%s deposit wallet %s " % (self.depositor.email, self.wallet_file)

    @property
    def wallet(self):
        return UserWallet.Open(self.wallet_file, self.wallet_pass)

    @property
    def address(self):
        return UserWallet.ToAddress( self.wallet.GetStandardAddress().Data)

    @staticmethod
    def create(user):

        try:
            wallet_name = '%s.db3' % uuid4()
            wallet_pass = str(uuid4())
            wallet_path = '%s/%s' % (settings.WALLET_DEPOSIT_PATH, wallet_name)

            wallet = UserWallet.Create(wallet_path, wallet_pass)

            deposit_wallet = DepositWallet.objects.create(
                depositor = user,
                wallet_file = wallet_path,
                wallet_pass = wallet_pass,
                start_height = Blockchain.Default().Height
            )
            return deposit_wallet

        except Exception as e:
            logger.error("Could not create wallet %s " % e)

        return None

class BlockchainTransfer(models.Model):

    to_address = models.CharField(max_length=34)
    from_address = models.CharField(max_length=34)

    amount = models.FloatField()

    asset = models.CharField(max_length=3, choices=ASSET_CHOICES, default='GAS')

    transaction_id = models.CharField(max_length=64, blank=True, null=True)

    status = models.CharField(max_length=64, choices=PURCHASE_STATUS, default='pending')

    start_block = models.IntegerField()

    confirmed_block = models.IntegerField(blank=True,null=True)

    @property
    def transaction(self):
        if self.transaction_id:
            try:
               tx,height = Blockchain.Default().GetTransaction(self.transaction_id)
               return tx
            except Exception as e:
                logger.debug("Could not get transaction %s " % e)
        return None

    @property
    def tx_json(self):
        if self.transaction_id:

            jsn = self.transaction.ToJson()

            for attr in jsn['attributes']:
                attr_data = attr['data']
                try:
                    attr['data'] = binascii.unhexlify(attr_data).decode('utf-8')
                except Exception as e:
                    logger.debug("Could not unhex attribute data: %s %s " % (e, attr_data))

            return json.dumps(jsn, indent=4)
        return {}

    @property
    def neoscan_url(self):
        if self.transaction_id:
            return '%stransaction/%s' % (settings.NEOSCAN_URL, self.transaction_id)
        return None





