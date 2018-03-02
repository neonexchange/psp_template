from django.apps import AppConfig
from django.conf import settings as dj_settings

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
from neo.Core.TX.Transaction import TransactionOutput, ContractTransaction, Transaction, TransactionType
from neo.Core.TX.TransactionAttribute import TransactionAttribute, TransactionAttributeUsage
from neo.Core.Helper import Helper
from neo.Core.Blockchain import Blockchain
from neo.Wallets.utils import to_aes_key
from neo.SmartContract.ContractParameterContext import ContractParametersContext
from customer.dwolla import DwollaClient, dwolla_send_to_user, dwolla_simulate_sandbox_transfers

import requests
import os


# Logfile settings & setup
LOGFILE_FN = os.path.join(dj_settings.BASE_DIR, 'psp.log')
LOGFILE_MAX_BYTES = 5e7  # 50 MB
LOGFILE_BACKUP_COUNT = 3  # 3 logfiles history
settings.set_logfile(LOGFILE_FN, LOGFILE_MAX_BYTES, LOGFILE_BACKUP_COUNT)


# This setsup crochet to be able to run twisted
# alongside of django
setup()


# these are the settings for the main PSP wallet that holds crypto
# that it will sell to users and will receive crypto from users
wallet_file = dj_settings.PROVIDER_WALLET_FILE
wallet_password = to_aes_key(dj_settings.PROVIDER_WALLET_PASS)

wallet_str_addr = 'AJnpZkx8HE7qSYNgbzvRuKMBDfBS1x9KvS'
wallet_addr_uint = UInt160(data=bytearray(
    b'!\x168\x87\xdb\xcb\x82\x82y\x13\xd4\xc8\x07\xc1\x1f\xb45\x89\xea\r'))


class BlockchainConfig(AppConfig):
    name = 'blockchain'

    def ready(self):
        """
        When the Blockchain django app is ready, we start the blockchain
        """
        start_blockchain()

@run_in_reactor
def start_blockchain():
    """

    This method sets up the blockchain and main PSP wallet, and start a number of loops to monitor incoming/outgoing
    NEO/Gas transfers as well as transfers of fiat via dwolla

    These loops are called in the twisted reactor in an async fashion so they do not block
    any HTTP requests processed by Django

    """
    try:
        settings.setup(dj_settings.PROTOCOL_FILE)
        settings.set_log_smart_contract_events(False)

        logger.info("Data path: %s " % dj_settings.CHAIN_DIR)

        # Start `neo-python`
        blockchain = LevelDBBlockchain(dj_settings.CHAIN_DIR)
        Blockchain.RegisterBlockchain(blockchain)
        dbloop = task.LoopingCall(Blockchain.Default().PersistBlocks)
        dbloop.start(dj_settings.PERSIST_BLOCK_TIME)
        NodeLeader.Instance().Start()

        # subscribe to on new block created event
        Blockchain.PersistCompleted.on_change += on_blockchain_new_block

        # open the wallet and start sync
        wallet = UserWallet.Open(wallet_file, wallet_password)
        wallet_loop = task.LoopingCall(wallet.ProcessBlocks)
        wallet_loop.start(dj_settings.WALLET_LOOP_TIME)

        monitor_loop = task.LoopingCall(monitor_wallet_loop, wallet)
        monitor_loop.start(dj_settings.MONITOR_LOOP_TIME)

        # start loop to process bank transfers that have been received
        sync_bank_transfer_loop = task.LoopingCall(process_bank_transfers)
        sync_bank_transfer_loop.start(dj_settings.TRANSFER_LOOP_TIME)

        # start loop to send out gas for bank transfers that have been received
        crypto_transfer_loop = task.LoopingCall(
            process_crypto_purchases, wallet)
        crypto_transfer_loop.start(dj_settings.CRYPTO_TRANSFER_LOOP_TIME)

        # start loop to check for gas that has been sent to make sure it actually gets confirmed
        pending_crypto_tx_loop = task.LoopingCall(
            process_pending_blockchain_transactions)
        pending_crypto_tx_loop.start(dj_settings.PENDING_CRYPTO_TRANSFER_LOOP)

        # start loop to create bank transfers for deposits of crypto
        process_gas_received_tranfer = task.LoopingCall(
            process_crypto_received_bank_transfers)
        process_gas_received_tranfer.start(
            dj_settings.PENDING_GAS_TRANSFER_LOOP)

        # every 10 minutes, refresh dwolla client token
        dwolla_client_refresh_loop = task.LoopingCall(
            refresh_dwolla_client_token)
        dwolla_client_refresh_loop.start(dj_settings.DWOLLA_TOKEN_REFRESH_TIME)

        # every 3 minutes, update gas price
        price_update_looop = task.LoopingCall(update_crypto_prices)
        price_update_looop.start(dj_settings.CMC_UPDATE_LOOP_TIME)

        # start loop to move assets sold to the system to deposit wallets into the main wallet
        move_deposits_to_main_wallet = task.LoopingCall(
            move_deposits_to_wallet)
        move_deposits_to_main_wallet.start(dj_settings.MOVE_DEPOSITS_LOOP_TIME)

    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error("Could not start blockchain: %s " % e)


def monitor_wallet_loop(wallet):
    """
    This is a basic loop to monitor the PSP wallet and log the current balance.
    One thing that could be added here is to set some type of system event
    Indicating that more crypto is needed to be purchased or something

    This loop also calls the dwolla 'simulate transfers' method which runs
    any pending bank transfers

    Args:
        wallet (neo.Implementations.Wallets.peewee.UserWallet.UserWallet): The user wallet of the PSP

    """
    available_gas = wallet.GetBalance(Blockchain.SystemCoin().Hash)
    available_neo = wallet.GetBalance(Blockchain.SystemShare().Hash)
    logger.info("[%s] %s [GAS]: %s   [NEO] %s " % (
        Blockchain.Default().Height, wallet.Addresses[0], available_gas, available_neo))

    try:
        num_transfers = dwolla_simulate_sandbox_transfers().body['total']
        logger.info("Processed %s transfers" % num_transfers)
    except Exception as e:
        logger.info("Could not process transfers %s " % e)
        DwollaClient.instance().refresh()


def process_bank_transfers():
    """
    Loop through any purchase or deposits that are pending.  If their status has changed
    We update our model instance representing that purchase/deposit accordingly

    """
    from customer.models import Purchase, Deposit
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
    """
    This method loops through all dwolla purchase objects that are in the ``processed`` state.  If they are
    and they don't have a BlockchainTransfer model object associated with them, then we will create one
    and initiate a transaction of crypto from the PSP wallet to the user who has just purchased crypto.

    Args:
        wallet (neo.Implementations.Wallets.peewee.UserWallet.UserWallet): The user wallet of the PSP
    """
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

        # we try to create a transaction with the purchase information
        transaction = create_transaction(wallet, purchase)

        # if the transaction was created we make BlockchainTransfer model object
        if transaction:
            bc = BlockchainTransfer.objects.create(
                to_address=purchase.neo_address,
                from_address=UserWallet.ToAddress(
                    wallet.GetStandardAddress().Data),
                amount=purchase.amount,
                asset='GAS',
                transaction_id=transaction.Hash.ToString(),
                status='pending',
                start_block=current_height
            )
            purchase.blockchain_transfer = bc
            purchase.save()


def process_pending_blockchain_transactions():
    """
    Loop through any BlockchainTransfer objects that are pending.  If the transfer's transaction id has been
    found on the blockchain, we know that the transfer of crypto is complete.  In that case we can
    mark the BlockchainTransfer model instance as complete.
    """
    from .models import BlockchainTransfer

    # Loop through BlockchainTransfer model objects that haven't been
    # confirmed on the blockchain, and check if they've been synced
    # if so, we'll mark the BlockchainTransfer as complete and save the current block
    for transfer in BlockchainTransfer.objects.filter(status='pending'):
        txid, height = Blockchain.Default().GetTransaction(transfer.transaction_id)
        if txid is not None:
            transfer.status = 'complete'
            transfer.confirmed_block = height
            transfer.save()


def create_transaction(wallet, purchase):
    """
    creates a transaction of crypto from the PSP wallet to a user who has paid in fiat

    Note: Ideally this will be done for more than 1 tx at a time.. would have a basket of tx ready to go
    and then they will all go out in one TX with all the outputs.  Then the system wont have to wait
    for the TX to clear to get its change back before doing the next batch

    Args:
        wallet (neo.Implementations.Wallets.peewee.UserWallet.UserWallet): The user wallet of the PSP
        purchase (blockchain.models.Purchase): A purchase object representing a user wishing to purchase crypto

    Returns:
        neo.Core.TX.Transaction.Transaction: A transaction from the PSP to the user who has purchased crypto
    """
    try:
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
            TransactionAttribute(
                TransactionAttributeUsage.Remark1, b'Sent by Payment Service Provider'),
            TransactionAttribute(TransactionAttributeUsage.Remark2, ('Purchase Price USD %0.2f' % (
                purchase.total,)).encode('utf-8'))
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

    except Exception as e:
        print("Could not create transaction %s " % e)


def refresh_dwolla_client_token():
    """
    Every 10 minutes or so you want to refresh your dwolla token
    """
    logger.info("Refreshing Dwolla client token")
    DwollaClient.instance().refresh()


def update_crypto_prices():
    """
    We monitor prices from CMC and upate them in a local model
    """

    from blockchain.models import Price
    req = requests.get(
        'https://api.coinmarketcap.com/v1/ticker/?limit=0', json=True)
    prices_wanted = ['NEO', 'GAS', 'RPX', ]
    for item in req.json():
        if item['symbol'] in prices_wanted:
            symbol = item['symbol']
            usd_price = item['price_usd']
            price, created = Price.objects.get_or_create(asset=symbol)
            price.usd = usd_price
            price.save()


def on_blockchain_new_block(block):
    """
    on each block, we loop through all the tx.  If any of them have the an identifier
    in the TX Attribute (TXAttrubuteUsage.REMARK3), we'll take a closer look at it
    Args:
        block (neo.Core.Block.Block): a newly created block
    """

    contract_tx_type = int.from_bytes(
        TransactionType.ContractTransaction, 'little')
    for tx in block.FullTransactions:
        if tx.Type == contract_tx_type:
            if len(tx.Attributes) > 0:
                for attr in tx.Attributes:
                    if attr.Usage == TransactionAttributeUsage.Remark3:
                        process_possible_transaction_match(tx)


def process_possible_transaction_match(transaction):
    """
    Take a look this transaction.  If it has a TransactionAttributeUsage.Remark3, we look at that remark.
    If that remark matches a an invoice ID in our system, then we create a Deposit model out of it
    And check the deposit

    Args:
        transaction (neo.Core.TX.Transaction.Transaction): a transaction with attributes that we are interested in
    """
    from customer.models import Deposit

    for attr in transaction.Attributes:
        if attr.Usage == TransactionAttributeUsage.Remark3:
            try:
                invoice_id = attr.Data.decode('utf-8')
                deposit = Deposit.objects.get(
                    invoice_id=invoice_id, status='awaiting_deposit')
                check_deposit_and_tx(deposit, transaction)
            except Deposit.DoesNotExist:
                logger.info(
                    "Could not find deposit with invoice %s " % attr.Data)
            except Exception as e:
                logger.info("Could not generate deposit/tx %s %s" %
                            (attr.Data, e))


def check_deposit_and_tx(deposit, transaction):
    """

    Checks the deposit object and compares with the transaction in which the PSP wallet received GAS/NEO
    If the deposit is greater than zero, we create a BlockchainTransfer object to represent it
    and use the current NEO/Gas price to calculate the amount of fiat owed to the depositor
    based on the amount of GAS/NEO received and the current price.

    Args:
        deposit (blockchain.models.Deposit): The Deposit model instance to check
        transaction (neo.Core.TX.Transaction.Transaction): The transaction associated with the the deposit

    """
    from blockchain.models import BlockchainTransfer, Price
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
                to_address=deposit.deposit_wallet.address,
                from_address=Crypto.ToAddress(sender_addr),
                amount=amount,
                transaction_id=transaction.Hash.ToString(),
                status='gas_received',
                start_block=current_block,
                confirmed_block=current_block
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
    """

    For any deposits the PSP has received from a user that have a receieved status, we will start
    a dwolla transfer of fiat to that user

    """
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
    """

    Once crypto has been deposited to has been deposited to a wallet, we transfer
    that deposit of the temporary wallet to the main PSP wallet.  After that is complete
    we can mark that transfer as pending, waiting for it to finish on the chain

    """
    from blockchain.models import DepositWallet, BlockchainTransfer

    if len(NodeLeader.Instance().Peers) < 1:
        return

    to_move = DepositWallet.next_available_for_retrieval()  # type:DepositWallet

    if to_move:

        wallet = UserWallet.Open(
            to_move.wallet_file, to_aes_key(to_move.wallet_pass))
        transfer = to_move.transfer

        tx, height = Blockchain.Default().GetTransaction(transfer.transaction_id)
        block = Blockchain.Default().GetBlockByHeight(height)
        wallet.ProcessNewBlock(block)

        move_tx = create_move_to_main_tx(wallet, transfer, to_move.deposit)

        if move_tx:
            try:
                bc_transfer = BlockchainTransfer.objects.create(
                    to_address=wallet_str_addr,
                    from_address=to_move.address,
                    amount=transfer.amount,
                    transaction_id=move_tx.Hash.ToString(),
                    status='pending',
                    start_block=Blockchain.Default().Height,
                )
                to_move.transfer_to_main = bc_transfer
                to_move.save()
            except Exception as e:
                logger.error(
                    "Could not transfer funds from deposit wallet %s" % e)

        wallet.Close()


def create_move_to_main_tx(deposit_wallet, transfer, deposit):
    """
    Creates a transaction to move Neo/Gas from a temporary 'deposit wallet' to the main PSP wallet

    Args:
        deposit_wallet (neo.Implementations.Wallets.peewee.UserWallet.UserWallet): the wallet to transfer NEO/Gas out of
        transfer (blockchain.models.BlockchainTransfer): the transfer object representing the transfer of NEO/Gas for fiat
        deposit (customer.models.Deposit): The deposit

    Returns:
        neo.Core.TX.Transaction.Transaction: the transaction to move NEO/Gas
    """
    tx = ContractTransaction()

    amount = Fixed8.FromDecimal(transfer.amount)
    tx.outputs = [TransactionOutput(
        AssetId=Blockchain.SystemCoin().Hash,
        Value=amount,
        script_hash=wallet_addr_uint,
    )]

    # annotate the tx with attributes to make invoice tracking easier
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
