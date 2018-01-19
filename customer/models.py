from django.db import models
from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser, PermissionsMixin
)

from django.db.models.signals import post_save
from django.dispatch import receiver
import json
from localflavor.us.models import USZipCodeField,USStateField
from django.conf import settings

from .dwolla import dwolla_create_user,dwolla_update_user,dwolla_get_url


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
    date_of_birth = models.DateField(help_text='Format YYYY-MM-DD')

    is_seller = models.BooleanField(default=False)

    objects = PSPUserManager()



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
        print("datestr: %s " % datetostr)

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

    print("dwolla sync result: %s " % dwolla_sync_result)


class ReceiveableAccount(models.Model):

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    account_id = models.CharField(max_length=128)

    def __str__(self):
        return 'Receivable Account for %s ' % self.user.last_name


    @property
    def customer_url(self):
        return self.user.dwolla_url

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
]

PURCHASE_STATUS = [
    ('pending','pending'),
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

    failure_reason = models.CharField(max_length=1024, blank=True, null=True)

    blockchain_transfer = models.OneToOneField('blockchain.BlockchainTransfer', blank=True,null=True, on_delete=models.CASCADE)


    class Meta:
        ordering = ['-date_created',]