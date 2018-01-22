from django.apps import AppConfig
from crochet import setup, run_in_reactor

from logzero import logger
from twisted.internet import reactor, task

from neo.Network.NodeLeader import NodeLeader
from neo.Implementations.Blockchains.LevelDB.LevelDBBlockchain import LevelDBBlockchain
from neo.Settings import settings
from neo.Implementations.Wallets.peewee.UserWallet import UserWallet
from neocore.Fixed8 import Fixed8
from neocore.UInt160 import UInt160
from neocore.Cryptography.Crypto import Crypto
from neo.Core.TX.Transaction import TransactionOutput,ContractTransaction,Transaction,TransactionType
from neo.Core.TX.TransactionAttribute import TransactionAttribute,TransactionAttributeUsage
from neo.Core.Helper import Helper
from neo.Core.Blockchain import Blockchain
from neo.SmartContract.ContractParameterContext import ContractParametersContext
from customer.dwolla import DwollaClient,dwolla_send_to_user
import requests
import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Logfile settings & setup
LOGFILE_FN = os.path.join(BASE_DIR, 'psp.log')
LOGFILE_MAX_BYTES = 5e7  # 50 MB
LOGFILE_BACKUP_COUNT = 3  # 3 logfiles history
settings.set_logfile(LOGFILE_FN, LOGFILE_MAX_BYTES, LOGFILE_BACKUP_COUNT)


setup()



wallet_file = 'psp_wallet.db3'
wallet_password = 'passwordpassword'
wallet_str_addr = 'AXv5hfEmQiKKiSrfSHyQXVh7XjLLFrMiw3'
wallet_addr_uint = UInt160(data=bytearray(b'\xb1\x0fg 9n~\xfb\x0e\x17\xbe\x07\x05F\x04n\x14^\xf6\xf5'))

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

        # Start `neo-python`
        blockchain = LevelDBBlockchain(settings.LEVELDB_PATH)
        Blockchain.RegisterBlockchain(blockchain)
        dbloop = task.LoopingCall(Blockchain.Default().PersistBlocks)
        dbloop.start(.1)
        NodeLeader.Instance().Start()

        # subscribe to on new block created event
        Blockchain.PersistCompleted.on_change += on_blockchain_new_block

        # open the wallet and start sync
        wallet = UserWallet.Open(wallet_file, wallet_password)
        wallet_loop = task.LoopingCall(wallet.ProcessBlocks)
        wallet_loop.start(.1)

        monitor_loop = task.LoopingCall(monitor_wallet_loop, wallet)
        monitor_loop.start(30)

        # start loop to process bank transfers that have been received
        sync_bank_transfer_loop = task.LoopingCall(process_bank_transfers)
        sync_bank_transfer_loop.start(2)

        # start loop to send out gas for bank transfers that have been received
        crypto_transfer_loop = task.LoopingCall(process_crypto_purchases, wallet)
        crypto_transfer_loop.start(3)

        # start loop to check for gas that has been sent to make sure it actually gets confirmed
        pending_crypto_tx_loop = task.LoopingCall(process_pending_blockchain_transactions)
        pending_crypto_tx_loop.start(4)


        # start loop to create bank transfers for deposits of crypto
        process_gas_received_tranfer = task.LoopingCall(process_crypto_received_bank_transfers)
        process_gas_received_tranfer.start(5)

        # every 10 minutes, refresh dwolla client token
        refresh_time = 60 * 10
        dwolla_client_refresh_loop = task.LoopingCall(refresh_dwolla_client_token)
        dwolla_client_refresh_loop.start(refresh_time)

        # every 3 minutes, update gas price
        refresh_time = 60 * 3
        price_update_looop = task.LoopingCall(update_crypto_prices)
        price_update_looop.start(refresh_time)


        # start loop to move assets sold to the system to deposit wallets into the main wallet
        refresh_time = 60
        move_deposits_to_main_wallet = task.LoopingCall(move_deposits_to_wallet)
        move_deposits_to_main_wallet.start(refresh_time)

    except Exception as e:
        logger.error("Could not start blockchain: %s " % e)


def monitor_wallet_loop(wallet):
    available_gas = wallet.GetBalance(Blockchain.SystemCoin().Hash)
    available_neo = wallet.GetBalance(Blockchain.SystemShare().Hash)
    logger.info("%s [GAS]: %s   [NEO] %s " % (wallet.Addresses[0], available_gas, available_neo))

def process_bank_transfers():
    from customer.models import Purchase,Deposit
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

    # loop through incomplete deposits
    for deposit in Deposit.objects.filter(status='pending'):
        try:
            transfer = dwolla_get_url(deposit.transfer_url)
            if transfer['status'] != deposit.status:
                deposit.status = transfer['status']
                deposit.save()
                deposit.user.pending_deposit = None
                deposit.user.save()
        except Exception as e:
            logger.error("Could not process deposit transfer %s " % e)

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


def update_crypto_prices():
    from blockchain.models import Price
    req = requests.get('https://api.coinmarketcap.com/v1/ticker/?limit=0', json=True)
    prices_wanted = ['NEO', 'GAS', 'RPX', ]
    for item in req.json():
        if item['symbol'] in prices_wanted:
            symbol = item['symbol']
            usd_price = item['price_usd']
            price,created = Price.objects.get_or_create(asset=symbol)
            price.usd = usd_price
            price.save()

def on_blockchain_new_block(block):
#    print("on blockchain new block! %s " % block.Index)
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
                deposit = Deposit.objects.get(invoice_id=invoice_id, status='awaiting_deposit')
                check_deposit_and_tx(deposit, transaction)
            except Deposit.DoesNotExist:
                logger.info("Could not find deposit with invoice %s " % attr.Data)
            except Exception as e:
                logger.info("Could not generate deposit/tx %s %s" % (attr.Data,e))


def check_deposit_and_tx(deposit, transaction):

    from blockchain.models import BlockchainTransfer,Price
    price_gas = float(Price.objects.get(asset='GAS').usd)
    deposit_total = Fixed8.Zero()
    sender_addr = None
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
            deposit.gas_price = price_gas
            deposit.total_gas = price_gas * amount
            deposit.total_fee = deposit.fee * deposit.total_gas
            deposit.total = deposit.total_gas - deposit.total_fee
            deposit.deposit_wallet.transfer = bc_transfer
            deposit.deposit_wallet.save()
            deposit.save()
        except Exception as e:
            logger.error("Could not create transfer... %s " % e)



def process_crypto_received_bank_transfers():
    from customer.models import Deposit
    for deposit in Deposit.objects.filter(status='gas_received'):
        try:
            transfer = dwolla_send_to_user(deposit)
            deposit.transfer_url = transfer.headers['location']
            deposit.status = 'pending'
            deposit.save()
        except Exception as e:
            logger.error("Could not create transfer %s " % e)



def move_deposits_to_wallet():

    from blockchain.models import DepositWallet,BlockchainTransfer

    if len(NodeLeader.Instance().Peers) < 1:
        return

    to_move = DepositWallet.next_available_for_retrieval() # type:DepositWallet

    if to_move:

        print("deposit to move %s %s " % (to_move, to_move.transfer))

        wallet = UserWallet.Open(to_move.wallet_file, to_move.wallet_pass)
        transfer = to_move.transfer

        tx, height = Blockchain.Default().GetTransaction(transfer.transaction_id)
        block = Blockchain.Default().GetBlockByHeight(height)
        wallet.ProcessNewBlock(block)

        move_tx = create_move_to_main_tx(wallet,transfer,to_move.deposit)

        if move_tx:
            print("move tx!")
            try:
                bc_transfer = BlockchainTransfer.objects.create(
                    to_address = wallet_str_addr,
                    from_address = to_move.address,
                    amount = transfer.amount,
                    transaction_id = move_tx.Hash.ToString(),
                    status = 'pending',
                    start_block = Blockchain.Default().Height,
                )
                to_move.transfer_to_main = bc_transfer
                to_move.save()
            except Exception as e:
                logger.error("Could not transfer funds from deposit wallet %s" % e)

        wallet.Close()

def create_move_to_main_tx(deposit_wallet, transfer, deposit):
    tx = ContractTransaction()

    amount = Fixed8.FromDecimal(transfer.amount)
    tx.outputs = [TransactionOutput(
        AssetId=Blockchain.SystemCoin().Hash,
        Value=amount,
        script_hash=wallet_addr_uint,
    )]
    tx.Attributes = [
        TransactionAttribute(TransactionAttributeUsage.Remark1,
        ('For deposit invoice %s' % deposit.invoice_id).encode('utf-8')),
        TransactionAttribute(TransactionAttributeUsage.Remark2,
        ('Sale price USD %0.2f ' % deposit.total).encode('utf-8'))
    ]

    tx = deposit_wallet.MakeTransaction(tx)
    context = ContractParametersContext(tx)
    deposit_wallet.Sign(context)

    if context.Completed:
        tx.scripts = context.GetScripts()
        relayed = NodeLeader.Instance().Relay(tx)
        if relayed:
            deposit_wallet.SaveTransaction(tx)
            return tx

    return None
