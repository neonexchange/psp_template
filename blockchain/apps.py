from django.apps import AppConfig
from crochet import setup, run_in_reactor

from logzero import logger
from twisted.internet import reactor, task

from neo.Network.NodeLeader import NodeLeader
from neo.Core.Blockchain import Blockchain
from neo.Implementations.Blockchains.LevelDB.LevelDBBlockchain import LevelDBBlockchain
from neo.Settings import settings
from neocore.Fixed8 import Fixed8
from neo.Implementations.Wallets.peewee.UserWallet import UserWallet
from neocore.Fixed8 import Fixed8
from neocore.Cryptography.Crypto import Crypto
from neo.Core.TX.Transaction import TransactionOutput,ContractTransaction,Transaction,TransactionType
from neo.Core.TX.TransactionAttribute import TransactionAttribute,TransactionAttributeUsage
from neo.Core.Helper import Helper
from neo.Core.Blockchain import Blockchain
from neo.Core.Block import Block
from neo.SmartContract.ContractParameterContext import ContractParametersContext
from customer.dwolla import DwollaClient

import json
import pdb
import binascii

setup()



wallet_file = 'psp_wallet.db3'
wallet_password = 'passwordpassword'


class BlockchainConfig(AppConfig):
    name = 'blockchain'

    def ready(self):
        logger.info("init Blockchain!!")
        start_blockchain()


@run_in_reactor
def start_blockchain():

    try:
        settings.setup('protocol.nex.json')
        settings.set_log_smart_contract_events(False)

        blockchain = LevelDBBlockchain(settings.LEVELDB_PATH)
        Blockchain.RegisterBlockchain(blockchain)
        dbloop = task.LoopingCall(Blockchain.Default().PersistBlocks)
        dbloop.start(.1)
        NodeLeader.Instance().Start()

        Blockchain.PersistCompleted.on_change += on_blockchain_new_block

        wallet = UserWallet.Open(wallet_file, wallet_password)
        wallet_loop = task.LoopingCall(wallet.ProcessBlocks)
        wallet_loop.start(.1)


        sync_bank_transfer_loop = task.LoopingCall(process_bank_transfers)
        sync_bank_transfer_loop.start(2)

        crypto_transfer_loop = task.LoopingCall(process_crypto_purchases, wallet)
        crypto_transfer_loop.start(3)

        pending_crypto_tx_loop = task.LoopingCall(process_pending_blockchain_transactions)
        pending_crypto_tx_loop.start(4)

        # every 10 minutes, refresh dwolla client token
        refresh_time = 60 * 10
        dwolla_client_refresh_loop = task.LoopingCall(refresh_dwolla_client_token)
        dwolla_client_refresh_loop.start(refresh_time)


    except Exception as e:
        logger.error("Could not start blockchain: %s " % e)




def process_bank_transfers():
    from customer.models import Purchase
    from customer.dwolla import dwolla_get_url

    # loop through incomplete purchases
    for purchase in Purchase.objects.filter(status='pending'):
        try:
            transfer = dwolla_get_url(purchase.transfer_url)
            # if this transfer status has changed, update the database status
            if transfer['status'] != purchase.status:
                purchase.status = transfer['status']
                purchase.save()
        except Exception as e:
            logger.error("could not process transfer %s " % e)


def process_crypto_purchases(wallet):

    from customer.models import Purchase
    from .models import BlockchainTransfer

    # below here requires the blockchain.  If there are no connected peers we won't do anything
    if len(NodeLeader.Instance().Peers) < 1:
        logger.info("Not connected yet")
        return

    current_height = Blockchain.Default().Height

    # loop though the purchases that are processed and the ones that dont have a blockchain
    # transfer associated with them
    for purchase in Purchase.objects.filter(status='processed', blockchain_transfer__amount__isnull=True):

        try:
            # we try to create a transaction with the purchase information
            transaction = create_transaction(wallet, purchase)
        except Exception as e:
            logger.info("could not create transaction %s " % e)

        # if the transaction was created we make BlockchainTransfer model object
        if transaction:
            bc = BlockchainTransfer.objects.create(
                to_address = purchase.neo_address,
                from_address = UserWallet.ToAddress( wallet.GetStandardAddress().Data),
                amount = purchase.amount,
                asset = 'GAS',
                transaction_id = transaction.Hash.ToString(),
                status='pending',
                start_block = current_height
            )
            purchase.blockchain_transfer = bc
            purchase.save()


def process_pending_blockchain_transactions():

    from .models import BlockchainTransfer

    # Loop through BlockchainTransfer model objects that haven't been
    # confirmed on the blockchain, and check if they've been synced
    # if so, we'll mark the BlockchainTransfer as complete and save the current block
    for transfer in BlockchainTransfer.objects.filter(status='pending'):
        txid,height = Blockchain.Default().GetTransaction(transfer.transaction_id)
        if txid is not None:
            transfer.status = 'complete'
            transfer.confirmed_block = height
            transfer.save()



def create_transaction(wallet, purchase):

    asset_id = Blockchain.Default().SystemCoin().Hash
    amount = Fixed8.FromDecimal(purchase.amount)

    to_script_hash = Helper.AddrStrToScriptHash(purchase.neo_address)

    output = TransactionOutput(
        AssetId=asset_id,
        Value=amount,
        script_hash=to_script_hash,
    )

    tx = ContractTransaction()
    tx.outputs = [output]
    tx = wallet.MakeTransaction(tx)

    tx.Attributes = [
        TransactionAttribute(TransactionAttributeUsage.Remark1, b'Sent by Payment Service Provider'),
        TransactionAttribute(TransactionAttributeUsage.Remark2, ('Purchase Price USD %0.2f' % (purchase.total,)).encode('utf-8'))
    ]

    context = ContractParametersContext(tx)

    wallet.Sign(context)

    if context.Completed:
        tx.scripts = context.GetScripts()
        relayed = NodeLeader.Instance().Relay(tx)
        if relayed:
            wallet.SaveTransaction(tx)
            return tx

    return None


def refresh_dwolla_client_token():
    logger.info("Refreshing Dwolla client token")
    DwollaClient.instance().refresh()




def on_blockchain_new_block(block):
    print("on blockchain new block! %s " % block.Index)
    contract_tx_type = int.from_bytes(TransactionType.ContractTransaction, 'little')
    for tx in block.FullTransactions:
        if tx.Type == contract_tx_type:
            if len(tx.Attributes) > 0:
                for attr in tx.Attributes:
                    if attr.Usage == TransactionAttributeUsage.Remark3:
                        process_possible_transaction_match(tx)

def process_possible_transaction_match(transaction):
    from customer.models import Deposit

    for attr in transaction.Attributes:
        if attr.Usage == TransactionAttributeUsage.Remark3:
            try:
                invoice_id = attr.Data.decode('utf-8')
                deposit = Deposit.objects.get(invoice_id=invoice_id, status='pending')
                check_deposit_and_tx(deposit, transaction)
            except Deposit.DoesNotExist:
                logger.info("Could not find deposit with invoice %s " % attr.Data)
            except Exception as e:
                logger.info("Could not decode data into utf-8 %s %s" % (attr.Data,e))


def check_deposit_and_tx(deposit, transaction):

    from blockchain.models import BlockchainTransfer

    deposit_total = Fixed8.Zero()
    sender_addr = transaction.G
    for output in transaction.outputs:

        if output.ScriptHash == deposit.deposit_wallet.wallet.GetStandardAddress():
            deposit_total += output.Value
        else:
            sender_addr = output.ScriptHash

    if deposit_total > Fixed8.Zero():

        current_block = Blockchain.Default().Height
        amount = deposit_total.value / Fixed8.D
        try:
            bc_transfer = BlockchainTransfer.objects.create(
                to_address = deposit.deposit_wallet.address,
                from_address = Crypto.ToAddress(sender_addr),
                amount = amount,
                transaction_id = transaction.Hash.ToString(),
                status = 'gas_received',
                start_block = current_block,
                confirmed_block = current_block
            )
            deposit.status = 'gas_received'
            deposit.blockchain_transfer = bc_transfer
            deposit.neo_sender_address = bc_transfer.from_address
            deposit.amount = amount
            deposit.save()
        except Exception as e:
            logger.error("Could not create transfer... %s " % e)


