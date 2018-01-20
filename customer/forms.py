from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from customer.models import PSPUser,Purchase,Deposit
from neo.Core.Helper import Helper
from neocore.Cryptography.Crypto import Crypto
from localflavor.us.us_states import STATE_CHOICES
from localflavor.us.forms import USStateField
from django.forms import ValidationError

class PSPUserCreationForm(forms.ModelForm):
    """A form for creating new users. Includes all the required
    fields, plus a repeated password."""
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = PSPUser
        fields = ('email','first_name','last_name','address1','city','state','postal_code','ssn_lastfour','date_of_birth',)


    def __init__(self, *args, **kwargs):
        super(PSPUserCreationForm, self).__init__(*args, **kwargs)

        choices = list(STATE_CHOICES)
        choices[0] = ('', 'Select a State')
        self.fields['state'] = USStateField(widget=forms.Select(choices=choices))


    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class PSPUserChangeForm(forms.ModelForm):
    """A form for updating users. Includes all the fields on
    the user, but replaces the password field with admin's
    password hash display field.
    """
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = PSPUser
        fields = ('email','first_name','last_name','address1','city','state','postal_code','ssn_lastfour','date_of_birth',)

    def clean_password(self):
        # Regardless of what the user provides, return the initial value.
        # This is done here, rather than on the field, because the
        # field does not have access to the initial value
        return self.initial["password"]


class PSPProfileForm(forms.ModelForm):
    """A form for users to update their profiles.
    """
    use_required_attribute = True
    required_css_class = 'required'

    class Meta:
        model = PSPUser
        fields = ('email','first_name','last_name','address1','city','state','postal_code','ssn_lastfour','date_of_birth',)



class BankAccountForm(forms.Form):

    pass


class PurchaseForm(forms.ModelForm):

    class Meta:
        model = Purchase
        fields = ['neo_address','amount','sender_account_id',]


    def __init__(self, *args, **kwargs):
        accounts = None

        if 'accounts' in kwargs:
            accounts = kwargs.pop('accounts')

        super(PurchaseForm, self).__init__(*args, **kwargs)

        if accounts:
            choices = []
            for acct in accounts:
                choices.append( (acct['id'], acct['name']))
            self.fields['sender_account_id'] = forms.ChoiceField(choices=choices, label='Bank Account')

        self.fields['neo_address'].widget.attrs = {'placeholder':'Axxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'}


    def clean_neo_address(self):

        addr = self.cleaned_data['neo_address']

        try:
            shash = Helper.AddrStrToScriptHash(addr)
            address_output = Crypto.ToAddress(shash)

            assert address_output == addr

        except Exception as e:

            raise ValidationError("Invalid NEO Blockchain Address")

        return self.cleaned_data['neo_address']


    def clean_amount(self):
        amt = self.cleaned_data['amount']
        if amt <= 0:
            raise ValidationError('Must purchase more than 0 amount')
        return amt


class DepositForm(forms.ModelForm):

    deposit_wallet = None
    class Meta:
        model = Deposit
        fields = ['amount','receiver_account_id',]

    def __init__(self, *args, **kwargs):
        accounts = None
        self.deposit_wallet = None
        if 'accounts' in kwargs:
            accounts = kwargs.pop('accounts')
        if 'deposit_wallet' in kwargs:
            self.deposit_wallet = kwargs.pop('deposit_wallet')

        super(DepositForm, self).__init__(*args, **kwargs)

        if accounts:
            choices = []
            for acct in accounts:
                choices.append( (acct['id'], acct['name']))
            self.fields['receiver_account_id'] = forms.ChoiceField(choices=choices, label='Deposit To Bank Account:')

