from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from .forms import PSPUserCreationForm,PSPProfileForm,BankAccountForm,PurchaseForm
from .dwolla import *
from .models import ReceiveableAccount
import requests

def get_gas_price():
    try:
        return requests.get('https://api.coinmarketcap.com/v1/ticker/GAS/').json()[0]['price_usd']
    except Exception as e:
        print("Could not determine gas price")
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
            # <process form cleaned data>
            messages.add_message(request, messages.INFO, 'Account Created! Please sign in')

            return HttpResponseRedirect('/customer/login')

        return render(request, self.template_name, {'form': form})


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

        return render(request, self.template_name, {'form':form,'gas_price':get_gas_price()} )
