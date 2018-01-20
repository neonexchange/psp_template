from django.contrib import admin

from blockchain.models import BlockchainTransfer,DepositWallet


class TransferAdmin(admin.ModelAdmin):
    model = BlockchainTransfer
    list_display = ('from_address','to_address','amount','status')

class DepositWalletAdmin(admin.ModelAdmin):
    model = DepositWallet

admin.site.register(BlockchainTransfer, TransferAdmin)
admin.site.register(DepositWallet, DepositWalletAdmin)

# Register your models here.
