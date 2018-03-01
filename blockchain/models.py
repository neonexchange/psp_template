from django.db import models
from customer.models import Purchase, PSPUser, ASSET_CHOICES, PURCHASE_STATUS
from neo.Core.Blockchain import Blockchain
import binascii
import json
from django.conf import settings
from logzero import logger
from neo.Implementations.Wallets.peewee.UserWallet import UserWallet
# Create your models here.
from uuid import uuid4
from neo.Wallets.utils import to_aes_key


class Price(models.Model):
    """
    This is a class to represent fiat values of different crypto currencies
    """
    asset = models.CharField(max_length=3, choices=ASSET_CHOICES, unique=True)
    usd = models.FloatField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '[%s] $%0.2f  at %s' % (self.asset, float(self.usd), self.updated_at)


class DepositWallet(models.Model):
    """
    A deposit wallet is used to represent a 'temporary' wallet that a user deposits crypto into
    this wallet is monitored so that when a user finishes a deposit, the system
    can send them fiat in exchange

    """
    depositor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    wallet_file = models.FilePathField()

    wallet_pass = models.CharField(max_length=64)

    start_height = models.IntegerField()

    transfer = models.OneToOneField(
        'blockchain.BlockchainTransfer', blank=True, null=True, on_delete=models.SET_NULL)

    transfer_to_main = models.OneToOneField(
        'blockchain.BlockchainTransfer', related_name='main_transfer', blank=True, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return "%s deposit wallet %s " % (self.depositor.email, self.wallet_file)

    @property
    def wallet(self):
        """

        Returns:
            neo.Implementations.Wallets.peewee.UserWallet.UserWallet
        """
        return UserWallet.Open(self.wallet_file, to_aes_key(self.wallet_pass))

    @property
    def address(self):
        """
        The bytearray of the address of this wallet

        Returns:
            bytearray
        """
        return UserWallet.ToAddress(self.wallet.GetStandardAddress().Data)

    @staticmethod
    def next_available_for_retrieval():
        """
        Retrieves the next deposit wallet that can be processed

        Returns:
            blockchain.models.DepositWallet
        """
        available = DepositWallet.objects.filter(
            transfer__isnull=False, transfer_to_main__isnull=True)
        if available.count():
            return available.first()
        return None

    @staticmethod
    def create(user):
        """
        Creates a DepositWallet instance for a user
        Args:
            user (customer.models.PSPUser): The user to create the DepositWallet for

        Returns:
            blockchain.models.DepositWallet
        """
        try:
            wallet_name = '%s.db3' % uuid4()
            wallet_pass = str(uuid4())
            wallet_path = '%s/%s' % (settings.WALLET_DEPOSIT_PATH, wallet_name)

            wallet = UserWallet.Create(wallet_path, to_aes_key(wallet_pass))
            deposit_wallet = DepositWallet.objects.create(
                depositor=user,
                wallet_file=wallet_path,
                wallet_pass=wallet_pass,
                start_height=Blockchain.Default().Height
            )
            return deposit_wallet

        except Exception as e:
            logger.error("Could not create wallet %s " % e)

        return None


class BlockchainTransfer(models.Model):
    """
    This model represents a transfer of crypto from one address to another.  This is used for both
    when a user has purchased crypto and also when they are selling crypto.

    """
    to_address = models.CharField(max_length=34)
    from_address = models.CharField(max_length=34)

    amount = models.FloatField()

    asset = models.CharField(
        max_length=3, choices=ASSET_CHOICES, default='GAS')

    transaction_id = models.CharField(max_length=64, blank=True, null=True)

    status = models.CharField(
        max_length=64, choices=PURCHASE_STATUS, default='pending')

    start_block = models.IntegerField()

    confirmed_block = models.IntegerField(blank=True, null=True)

    @property
    def transaction(self):
        """
        the transaction on the blockchain that is associated with this model instance

        Returns:
            neo.Core.TX.Transaction.Transaction
        """
        if self.transaction_id:
            try:
                tx, height = Blockchain.Default().GetTransaction(self.transaction_id)
                return tx
            except Exception as e:
                print("Could not get transaction %s " % e)
        return None

    @property
    def tx_json(self):
        """
        A json representation of the transaction associated with this model instance
        Returns:
            dict
        """
        if self.transaction:

            jsn = self.transaction.ToJson()

            for attr in jsn['attributes']:
                attr_data = attr['data']
                try:
                    attr['data'] = binascii.unhexlify(
                        attr_data).decode('utf-8')
                except Exception as e:
                    logger.debug(
                        "Could not unhex attribute data: %s %s " % (e, attr_data))

            return json.dumps(jsn, indent=4)

        return {}

    @property
    def neoscan_url(self):
        """
        the url on neo-scan where the transaction associated with this model instance can be viewed
        Returns:
            str
        """
        if self.transaction_id:
            return '%stransaction/%s' % (settings.NEOSCAN_URL, self.transaction_id)
        return None
