from django.urls import path, include

from django.contrib.auth import views
from .views import ProfileView, SignupView, BankAccountView, BankAccountListView, PurchaseView, TransactionView, SellView, DepositCryptoView, CancelDepositCryptoView
from django.urls import path

urlpatterns = [

    path('login/', views.LoginView.as_view(template_name='account/login.html'), name='login'),
    path('logout/', views.LogoutView.as_view(template_name='account/logout.html'), name='logout'),

    path('password_change/', views.PasswordChangeView.as_view(template_name='account/password_change.html',
                                                              success_url='/customer/profile/'), name='password_change'),
    path('password_change/done/', views.PasswordChangeDoneView.as_view(
        template_name='account/password_reset_done.html'), name='password_change_done'),

    path('password_reset/', views.PasswordResetView.as_view(
        template_name='account/password_reset.html'), name='password_reset'),
    path('password_reset/done/', views.PasswordResetDoneView.as_view(
        template_name='account/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', views.PasswordResetConfirmView.as_view(
        template_name='account/password_reset_from_key.html'), name='password_reset_confirm'),
    path('reset/done/', views.PasswordResetCompleteView.as_view(
        template_name='account/password_reset_from_key_done.html'), name='password_reset_complete'),

    path('profile/', ProfileView.as_view(), name='profile'),
    path('signup/', SignupView.as_view(), name='signup'),

    path('accounts/', BankAccountListView.as_view(), name='bank_accounts'),

    path('accounts/create/', BankAccountView.as_view(),
         name='bank_accounts_create'),

    #    path('accounts/transfer/', TransferView.as_view(), name='bank_account_transfer'),

    path('purchase/', PurchaseView.as_view(), name='purchase'),

    path('sell/', SellView.as_view(), name='sell'),
    path('sell/deposit/', DepositCryptoView.as_view(), name='deposit-crypto'),
    path('sell/deposit/cancel', CancelDepositCryptoView.as_view(),
         name='deposit-crypto-cancel'),

    path('transactions/', TransactionView.as_view(), name='transactions'),
]
