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
from neo.Core.TX.Transaction import TransactionOutput,ContractTransaction
from neo.Core.Helper import Helper
from neo.Core.Blockchain import Blockchain
from neo.SmartContract.ContractParameterContext import ContractParametersContext
import json

setup()



wallet_file = 'psp_wallet.db3'
wallet_password = 'passwordpassword'


class BlockchainConfig(AppConfig):
    name = 'blockchain'

    def ready(self):
        print("init Blockchain!!")
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

        wallet = UserWallet.Open(wallet_file, wallet_password)
        wallet_loop = task.LoopingCall(wallet.ProcessBlocks)
        wallet_loop.start(.1)

        update = task.LoopingCall(update_loop, wallet)
        update.start(30)
        print("Starting blockchain!!")

        transfer_loop = task.LoopingCall(process_transfers, wallet)
        transfer_loop.start(20)

    except Exception as e:
        print("Could not start blockchain: %s " % e)

def update_loop(wallet):
    print("Current Height %s " % Blockchain.Default().Height)
    print("wallet: %s " % json.dumps(wallet.ToJson(), indent=4))



def process_transfers(wallet):
    from customer.models import Purchase
    from customer.dwolla import dwolla_get_url
    from .models import BlockchainTransfer

    current_height = Blockchain.Default().Height
    # loop through incomplete purchases
    for purchase in Purchase.objects.filter(status='pending'):
        try:
            transfer = dwolla_get_url(purchase.transfer_url)
            if transfer['status'] != purchase.status:
                print("change status!!!")
                purchase.status = transfer['status']
                purchase.save()
        except Exception as e:
            print("could not process transfer %s " % e)

    print("process transfers..")
    if len(NodeLeader.Instance().Peers) < 1:
        print("Not connected yet")
        return

    for purchase in Purchase.objects.filter(status='processed', blockchain_transfer__amount__isnull=True):
        print("looking over purchase %s " % purchase)
        try:
            transaction = create_transaction(wallet, purchase)
        except Exception as e:
            print("could not create transaction %s " % e)

        if transaction:
            print("creating transfer1111")
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


    for transfer in BlockchainTransfer.objects.filter(status='pending'):
        print("looknig for transaction id %s " % transfer.transaction_id)
        txid,height = Blockchain.Default().GetTransaction(transfer.transaction_id)
        if txid is not None:
            print("TX ID %s, height %s " % (txid, height))
            transfer.status = 'complete'
            transfer.confirmed_block = height
            transfer.save()


def create_transaction(wallet, purchase):


    asset_id = Blockchain.Default().SystemCoin().Hash
    amount = Fixed8.FromDecimal(purchase.amount)
    print("amount: %s %s " % (amount.ToString(), amount.value))

    to_script_hash = Helper.AddrStrToScriptHash(purchase.neo_address)
    print("to script hash %s " % to_script_hash)
    output = TransactionOutput(
        AssetId=asset_id,
        Value=amount,
        script_hash=to_script_hash,
    )

    tx = ContractTransaction()
    tx.outputs = [output]
    tx = wallet.MakeTransaction(tx)
    print("hello11")
    context = ContractParametersContext(tx)
    wallet.Sign(context)
    print("hello...")
    if context.Completed:
        print("Hellooo")
        tx.scripts = context.GetScripts()

        #            print("will send tx: %s " % json.dumps(tx.ToJson(),indent=4))

        relayed = NodeLeader.Instance().Relay(tx)
        print("elayed?? %s" % relayed)
        if relayed:

            wallet.SaveTransaction(tx)

            return tx

    return None
