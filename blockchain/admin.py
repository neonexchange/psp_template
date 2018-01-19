from django.contrib import admin

from blockchain.models import BlockchainTransfer


class TransferAdmin(admin.ModelAdmin):
    model = BlockchainTransfer
    list_display = ('from_address','to_address','amount','status')


admin.site.register(BlockchainTransfer, TransferAdmin)

# Register your models here.
