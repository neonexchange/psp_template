from logzero import logger
from django.db import models
from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser, PermissionsMixin
)

from django.db.models.signals import post_save
from django.dispatch import receiver
from localflavor.us.models import USZipCodeField,USStateField
from django.conf import settings

from .dwolla import dwolla_create_user,dwolla_update_user,dwolla_get_url,DwollaClient


class PSPUserManager(BaseUserManager):
    def create_user(self, email, first, last, address1, city, postal_code, state,ssn_lastfour, date_of_birth,password=None):
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

    def create_superuser(self, email, first_name,last_name,address1,city,postal_code,state,ssn_lastfour,date_of_birth,password):
        """
        Creates and saves a superuser with the given email, date of
        birth and password.
        """
        user = self.create_user(
            email,
            first_name,last_name,address1,city,postal_code,state,ssn_lastfour,date_of_birth,
            password=password,
        )

        user.is_admin = True
        user.save(using=self._db)
        return user


class PSPUser(AbstractBaseUser, PermissionsMixin):

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

    pending_deposit = models.ForeignKey('customer.Deposit', blank=True,null=True, on_delete=models.SET_NULL)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name','last_name','address1','city','postal_code','state','ssn_lastfour','date_of_birth']



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
        "Is the user a member of staff?"
        # Simplest possible answer: All admins are staff
        return self.is_admin

    @property
    def dwolla_id(self):
        if self.dwolla_url:
            return self.dwolla_url.split('/')[-1]
        return None

    def __str__(self):
        return self.email

    def get_full_name(self):
        return '%s %s ' % (self.first_name, self.last_name)

    def get_short_name(self):
        return self.first_name

    def to_json(self):
        datetostr = self.date_of_birth.strftime('%Y-%m-%d')

        return {
            'email':self.email,
            'firstName':self.first_name,
            'lastName':self.last_name,
            'type': self.customer_type,
            'address1':self.address1,
            'city':self.city,
            'state':self.state,
            'postalCode':self.postal_code,
            'dateOfBirth': datetostr,
            'ssn':self.ssn_lastfour
        }

    def to_update_json(self):
         return {
            'email':self.email,
            'firstName':self.first_name,
            'lastName':self.last_name,
        }

@receiver(post_save, sender=PSPUser)
def on_pspuser_saved(sender, instance, created,**kwargs):

    if instance.dwolla_url is None:

        dwolla_sync_result = dwolla_create_user(instance)
    else:
        dwolla_sync_result = dwolla_update_user(instance)

    logger.info("dwolla sync result: %s " % dwolla_sync_result)


class ReceiveableAccount(models.Model):

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    account_id = models.CharField(max_length=128)

    def __str__(self):
        return 'Receivable Account for %s ' % self.user.last_name


    @property
    def customer_url(self):
        return self.user.dwolla_url

    @property
    def funding_url(self):
        return '%s%s' % (DwollaClient.instance().funding_source_url, self.account_id)

    @staticmethod
    def Default():
        try:
            return ReceiveableAccount.objects.first()
        except Exception as e:
            pass
        return None



ASSET_CHOICES = [
    ('GAS','GAS'),
    ('NEO','NEO'),
    ('NEX','NEX'),
    ('RPX','RPX')
]

PURCHASE_STATUS = [
    ('awaiting_deposit','awaiting_deposit'),
    ('gas_received','gas_received'),
    ('pending', 'pending'),
    ('processed','processed'),
    ('failed', 'failed'),
    ('complete','complete')
]

class Purchase(models.Model):

    asset = models.CharField(choices=ASSET_CHOICES,default='GAS', max_length=3)
    amount = models.FloatField(default=1.00)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    sender_account_id = models.CharField(max_length=128)

    receiver_account_id = models.CharField(max_length=128)

    neo_address = models.CharField(max_length=34)

    gas_price = models.FloatField()

    fee = models.FloatField(default=.05)

    total_gas = models.FloatField()
    total_fee = models.FloatField()

    total = models.FloatField()

    status = models.CharField(max_length=32, choices=PURCHASE_STATUS, default='pending')

    transfer_url = models.CharField(max_length=128)

    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    failure_reason = models.CharField(max_length=1024, blank=True, null=True)

    blockchain_transfer = models.OneToOneField('blockchain.BlockchainTransfer', blank=True,null=True, on_delete=models.CASCADE)


    class Meta:
        ordering = ['-date_created',]


class Deposit(models.Model):


    amount = models.FloatField(default=1.00, blank=True,null=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING)

    sender_account_id = models.CharField(max_length=128)

    receiver_account_id = models.CharField(max_length=128)

    neo_sender_address = models.CharField(max_length=34, blank=True, null=True)


    asset = models.CharField(choices=ASSET_CHOICES,default='GAS', max_length=3)
    gas_price = models.FloatField(blank=True,null=True)
    fee = models.FloatField(default=.05)
    total_gas = models.FloatField(blank=True,null=True)
    total_fee = models.FloatField(blank=True,null=True)
    total = models.FloatField(blank=True,null=True)


    status = models.CharField(max_length=32, choices=PURCHASE_STATUS, default='awaiting_deposit')

    transfer_url = models.CharField(max_length=128, blank=True,null=True)

    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    failure_reason = models.CharField(max_length=1024, blank=True, null=True)

    blockchain_transfer = models.OneToOneField('blockchain.BlockchainTransfer', blank=True,null=True, on_delete=models.CASCADE)

    deposit_wallet = models.OneToOneField('blockchain.DepositWallet', on_delete=models.CASCADE)

    invoice_id = models.UUIDField(auto_created=True)

    class Meta:
        ordering = ['-date_created',]


    @property
    def receiver_account(self):
        url = '%s%s' % (DwollaClient.instance().funding_source_url,self.receiver_account_id)
        return dwolla_get_url(url)


    @property
    def transfer_id(self):
        if self.transfer_url:
            try:
                return self.transfer_url.split('/')[-1]
            except Exception as e:
                logger.info("Could not construct tranfer id %s " % e)
        return None