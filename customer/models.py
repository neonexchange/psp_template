from logzero import logger
from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin

from django.db.models.signals import post_save
from django.dispatch import receiver
from localflavor.us.models import USZipCodeField, USStateField
from django.conf import settings

from .dwolla import dwolla_create_user, dwolla_update_user, dwolla_get_url, DwollaClient


ASSET_CHOICES = [
    ('GAS', 'GAS'),
    ('NEO', 'NEO'),
    ('NEX', 'NEX'),
    ('RPX', 'RPX')
]

PURCHASE_STATUS = [
    ('awaiting_deposit', 'awaiting_deposit'),
    ('gas_received', 'gas_received'),
    ('pending', 'pending'),
    ('processed', 'processed'),
    ('failed', 'failed'),
    ('complete', 'complete')
]


class PSPUserManager(BaseUserManager):
    """
    PSPUSer manager is a custom user manager for customer.models.PSPUser
    """

    def create_user(self, email, first, last, address1, city, postal_code, state, ssn_lastfour, date_of_birth, password=None):
        """
        Creates and saves a User with the given email, date of
        birth and password.
        """
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            email=self.normalize_email(email),
            first_name=first,
            last_name=last,
            address1=address1,
            city=city,
            postal_code=postal_code,
            state=state,
            ssn_lastfour=ssn_lastfour,
            date_of_birth=date_of_birth
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, first_name, last_name, address1, city, postal_code, state, ssn_lastfour, date_of_birth, password):
        """
        Creates and saves a superuser with the given email, date of
        birth and password.
        """
        user = self.create_user(
            email,
            first_name, last_name, address1, city, postal_code, state, ssn_lastfour, date_of_birth,
            password=password,
        )

        user.is_admin = True
        user.save(using=self._db)
        return user


class PSPUser(AbstractBaseUser, PermissionsMixin):
    """
    PSP User is the model that represents any user on the website, whether admins or consumers. It inherits/conforms
    to the normal django user conventions

    """
    email = models.EmailField(
        verbose_name='email address',
        max_length=255,
        unique=True,
    )

    first_name = models.CharField(max_length=128)
    last_name = models.CharField(max_length=128)

    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)

    dwolla_url = models.URLField(blank=True, null=True)

    customer_type = models.CharField(max_length=32, default='personal')

    address1 = models.CharField(max_length=50)
    address2 = models.CharField(max_length=50, blank=True, null=True)
    city = models.CharField(max_length=128)
    postal_code = USZipCodeField()
    state = USStateField()
    ssn_lastfour = models.CharField(max_length=4)
    date_of_birth = models.DateField()

    is_seller = models.BooleanField(default=False)

    objects = PSPUserManager()

    pending_deposit = models.ForeignKey(
        'customer.Deposit', blank=True, null=True, on_delete=models.SET_NULL)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'address1', 'city',
                       'postal_code', 'state', 'ssn_lastfour', 'date_of_birth']

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    @property
    def is_staff(self):
        """
        Is this user a staff user?
        Returns:
            bool
        """
        return self.is_admin

    @property
    def dwolla_id(self):
        """
        Retrieve the dwolla based id for this user
        Returns:
            str
        """
        if self.dwolla_url:
            return self.dwolla_url.split('/')[-1]
        return None

    def __str__(self):
        """
        return the user's email address

        Returns:
            str
        """
        return self.email

    def get_full_name(self):
        """
        returs full name of the user

        Returns:
            str
        """
        return '%s %s ' % (self.first_name, self.last_name)

    def get_short_name(self):
        """
        Get users first name
        Returns:
            str
        """
        return self.first_name

    def to_json(self):
        """
        output this user as a json object. The format is determined by the needs
        of the dwolla api

        Returns:
            dict
        """
        datetostr = self.date_of_birth.strftime('%Y-%m-%d')

        return {
            'email': self.email,
            'firstName': self.first_name,
            'lastName': self.last_name,
            'type': self.customer_type,
            'address1': self.address1,
            'city': self.city,
            'state': self.state,
            'postalCode': self.postal_code,
            'dateOfBirth': datetostr,
            'ssn': self.ssn_lastfour
        }

    def to_update_json(self):
        """
        output of the user as json needed for dwolla to update a user
        Returns:
            dict
        """
        return {
            'email': self.email,
            'firstName': self.first_name,
            'lastName': self.last_name,
        }


@receiver(post_save, sender=PSPUser)
def on_pspuser_saved(sender, instance, created, **kwargs):
    """
    When a PSP user is saved, we check to see if they are associatde with the dwolla system ( dwolla_url )
    if not, we will create a dwolla user

    Args:
        sender (customer.models.PSPUser): the model class that sends this event
        instance (customer.models.PSPUser): the instance of the model associated with this event
        created (bool): whether this instance has just been created
        **kwargs:

    """
    if instance.dwolla_url is None:

        dwolla_sync_result = dwolla_create_user(instance)
    else:
        dwolla_sync_result = dwolla_update_user(instance)

    logger.info("dwolla sync result: %s " % dwolla_sync_result)


class ReceiveableAccount(models.Model):
    """
    This is a model used to represent the main PSP user and associate them with their main
    bank account in dwolla

    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)

    account_id = models.CharField(max_length=128)

    def __str__(self):
        return 'Receivable Account for %s ' % self.user.last_name

    @property
    def customer_url(self):
        """
        The url for the receivable account customer dwolla account
        Returns:
            str
        """
        return self.user.dwolla_url

    @property
    def funding_url(self):
        """
        The url for the receivable account customer funding dwolla account

        Returns:
            str
        """
        return '%s%s' % (DwollaClient.instance().funding_source_url, self.account_id)

    @staticmethod
    def Default():
        """
        There should only be one, so this is kind of a singleton for retrieving it
        Returns:
            customer.models.ReceivableAccount
        """
        try:
            return ReceiveableAccount.objects.first()
        except Exception as e:
            pass
        return None


class Purchase(models.Model):
    """
    A Purchase represents when a user sends fiat to the ReceivableAccount
    """
    asset = models.CharField(choices=ASSET_CHOICES,
                             default='GAS', max_length=3)
    amount = models.FloatField(default=1.00)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)

    sender_account_id = models.CharField(max_length=128)

    receiver_account_id = models.CharField(max_length=128)

    neo_address = models.CharField(max_length=34)

    gas_price = models.FloatField()

    fee = models.FloatField(default=.05)

    total_gas = models.FloatField()
    total_fee = models.FloatField()

    total = models.FloatField()

    status = models.CharField(
        max_length=32, choices=PURCHASE_STATUS, default='pending')

    transfer_url = models.CharField(max_length=128)

    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    failure_reason = models.CharField(max_length=1024, blank=True, null=True)

    blockchain_transfer = models.OneToOneField(
        'blockchain.BlockchainTransfer', blank=True, null=True, on_delete=models.CASCADE)

    class Meta:
        ordering = ['-date_created', ]


class Deposit(models.Model):
    """
    A deposit is for persisting when a user deposits crypto into the system in exchange for fiat
    """

    amount = models.FloatField(default=1.00, blank=True, null=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.DO_NOTHING)

    sender_account_id = models.CharField(max_length=128)

    receiver_account_id = models.CharField(max_length=128)

    neo_sender_address = models.CharField(max_length=34, blank=True, null=True)

    asset = models.CharField(choices=ASSET_CHOICES,
                             default='GAS', max_length=3)
    gas_price = models.FloatField(blank=True, null=True)
    fee = models.FloatField(default=.05)
    total_gas = models.FloatField(blank=True, null=True)
    total_fee = models.FloatField(blank=True, null=True)
    total = models.FloatField(blank=True, null=True)

    status = models.CharField(
        max_length=32, choices=PURCHASE_STATUS, default='awaiting_deposit')

    transfer_url = models.CharField(max_length=128, blank=True, null=True)

    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    failure_reason = models.CharField(max_length=1024, blank=True, null=True)

    blockchain_transfer = models.OneToOneField(
        'blockchain.BlockchainTransfer', blank=True, null=True, on_delete=models.CASCADE)

    deposit_wallet = models.OneToOneField(
        'blockchain.DepositWallet', on_delete=models.CASCADE)

    invoice_id = models.UUIDField(auto_created=True)

    class Meta:
        ordering = ['-date_created', ]

    @property
    def receiver_account(self):
        """
        The dwolla url of the reciever of this Deposit

        Returns:
            str
        """
        url = '%s%s' % (DwollaClient.instance(
        ).funding_source_url, self.receiver_account_id)
        return dwolla_get_url(url)

    @property
    def transfer_id(self):
        """
        The url of the dwolla transfer associated with this deposit

        Returns:
            str
        """
        if self.transfer_url:
            try:
                return self.transfer_url.split('/')[-1]
            except Exception as e:
                logger.info("Could not construct tranfer id %s " % e)
        return None
