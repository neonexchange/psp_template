from django.http import HttpResponseRedirect,HttpResponseForbidden
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from django.views import View
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.contrib import messages
from .forms import PSPUserCreationForm,PSPProfileForm,BankAccountForm,PurchaseForm,DepositForm,CancelDepositForm
from .dwolla import *
from .models import ReceiveableAccount,Deposit
from blockchain.models import DepositWallet
import requests
from logzero import logger

def get_gas_price():
    try:
        return requests.get('https://api.coinmarketcap.com/v1/ticker/GAS/').json()[0]['price_usd']
    except Exception as e:
        logger.error("Could not determine gas price %s " % e)
    return 60.0


class TransactionView(View):
    template_name = 'account/transactions.html'

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)



class ProfileView(View):
    form_class = PSPProfileForm
    template_name = 'account/profile.html'

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        form = self.form_class(instance=request.user)
        return render(request, self.template_name, {'form': form})

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, instance=request.user)
        if form.is_valid():
            updated = form.save()
            messages.add_message(request, messages.INFO, 'Profile Updated!')

            return HttpResponseRedirect('/customer/profile/')

        return render(request, self.template_name, {'form': form})



class BankAccountListView(View):
    form_class = BankAccountForm
    template_name = 'account/bank_account_list.html'

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        form = self.form_class()
        funding_sources = dwolla_get_user_bank_accounts(request.user)
        return render(request, self.template_name, {'form': form, 'funding_sources':funding_sources})

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            # <process form cleaned data>

            return HttpResponseRedirect('/customer/accounts/')

        return render(request, self.template_name, {'form': form})



class BankAccountView(View):
    form_class = BankAccountForm
    template_name = 'account/bank_account_add.html'

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        form = self.form_class()
        funding_token = dwolla_generate_funding_source_token(request.user)
        return render(request, self.template_name, {'form': form, 'funding_token':funding_token})

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, instance=request.user)
        if form.is_valid():
            # <process form cleaned data>

            return HttpResponseRedirect('/customer/accounts/')

        return render(request, self.template_name, {'form': form})


class SignupView(View):
    form_class = PSPUserCreationForm
    template_name = 'account/signup.html'

    def get(self, request, *args, **kwargs):

        if request.user.pk:
            messages.add_message(request, messages.INFO, 'Already logged in!')
            return HttpResponseRedirect('/customer/profile')

        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            new_user = form.save()
            messages.add_message(request, messages.INFO, 'Welcome %s! Please sign in' % new_user.first_name)

            return HttpResponseRedirect('/customer/login')

        return render(request, self.template_name, {'form': form})


class SellView(View):

    template_name = 'sell.html'
    form_class = DepositForm

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):

        bank_accounts = dwolla_get_user_bank_accounts(request.user)
        has_bank_accounts = False

        if len(bank_accounts) > 0:
            has_bank_accounts = True

        can_sell = has_bank_accounts and request.user.pending_deposit is None

        form = self.form_class(accounts=bank_accounts)

        return render(request, self.template_name, {'gas_price':get_gas_price(),
                                                    'has_bank_accounts':has_bank_accounts,
                                                    'has_pending_deposit':request.user.pending_deposit,
                                                    'can_sell':can_sell,
                                                    'form':form} )


    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):

        bank_accounts = dwolla_get_user_bank_accounts(request.user)

        form = self.form_class(request.POST,accounts=bank_accounts)

        if form.is_valid():

            deposit = form.save(commit=False) # type: Deposit
            deposit.user = request.user
            deposit.sender_account_id = ReceiveableAccount.Default().customer_url
            deposit.deposit_wallet = DepositWallet.create(request.user)
            deposit.save()

            request.user.pending_deposit = deposit
            request.user.save()

            messages.add_message(request, messages.INFO, 'Crypto Sale Initiated...')
            return HttpResponseRedirect('/customer/sell/deposit/')

        has_bank_accounts = False
        if len(bank_accounts) > 0:
            has_bank_accounts = True
        can_sell = has_bank_accounts and request.user.pending_deposit is None

        return render(request, self.template_name, {'gas_price':get_gas_price(),
                                                    'has_bank_accounts':has_bank_accounts,
                                                    'has_pending_deposit':request.user.pending_deposit,
                                                    'can_sell':can_sell,
                                                    'form':form} )


class DepositCryptoView(View):
    template_name = 'deposit_crypto.html'
    form_class = DepositForm

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):

        if not request.user.pending_deposit:
            messages.add_message(request, messages.INFO, 'Please initiate a deposit before depositing crypto')
            return HttpResponseRedirect('/customer/sell/')

        deposit = request.user.pending_deposit
        deposit_wallet = deposit.deposit_wallet

        return render(request, self.template_name, {'gas_price':get_gas_price(),
                                                    'deposit':deposit,
                                                    'deposit_wallet':deposit_wallet} )

class CancelDepositCryptoView(View):
    form_class = CancelDepositForm

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):

        form = CancelDepositForm(request.POST)

        if form.is_valid():

            deposit = get_object_or_404(Deposit, pk=form.cleaned_data['deposit_id'])
            if deposit.user != request.user:
                raise PermissionDenied

            request.user.pending_deposit = None
            request.user.save()
            deposit.deposit_wallet.delete()
            deposit.delete()
            messages.add_message(request, messages.INFO, 'Deposit cancelled')

        return HttpResponseRedirect('/customer/sell')


class PurchaseView(View):

    form_class = PurchaseForm
    template_name = 'purchase.html'

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):

        bank_accounts = dwolla_get_user_bank_accounts(request.user)

        has_bank_accounts = False
        if len(bank_accounts) > 0:
            has_bank_accounts = True

        form = self.form_class(accounts=bank_accounts)

        return render(request, self.template_name, {'form':form,'gas_price':get_gas_price(),'has_bank_accounts':has_bank_accounts} )

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):

        bank_accounts = dwolla_get_user_bank_accounts(request.user)

        has_bank_accounts = False
        if len(bank_accounts) > 0:
            has_bank_accounts = True

        form = self.form_class(request.POST, accounts=bank_accounts)

        if form.is_valid():
            try:
                purchase = form.save(commit=False)
                purchase.gas_price = float(get_gas_price())
                purchase.total_gas = purchase.gas_price * purchase.amount
                purchase.total_fee = .05 * purchase.total_gas
                purchase.total = purchase.total_gas + purchase.total_fee
                purchase.user = request.user
                purchase.receiver_account_id = ReceiveableAccount.Default().customer_url

                transfer = dwolla_create_transfer(purchase)
                purchase.transfer_url = transfer.headers['location']
                purchase.save()

                messages.add_message(request, messages.INFO, 'Transfer initiated')

                return HttpResponseRedirect('/customer/transactions')
            except Exception as e:
                messages.add_message(request, messages.ERROR, 'Could not initiate purchase: %s ' % e)

        return render(request, self.template_name, {'form':form,'gas_price':get_gas_price(),'has_bank_accounts':has_bank_accounts} )
