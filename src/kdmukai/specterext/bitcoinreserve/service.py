import datetime
import json
import logging

from cryptoadvance.specter.services.service import Service, devstatus_alpha, devstatus_prod
# A SpecterError can be raised and will be shown to the user as a red banner
from cryptoadvance.specter.specter_error import SpecterError
from cryptoadvance.specter.user import User
from cryptoadvance.specter.wallet import Wallet
from flask import current_app as app
# from flask_apscheduler import APScheduler

logger = logging.getLogger(__name__)

class BitcoinReserveService(Service):
    id = "bitcoinreserve"
    name = "Bitcoin Reserve"
    icon = "bitcoinreserve/img/bitcoinreserve_icon.svg"
    logo = "bitcoinreserve/img/logo-light.svg"
    desc = "Where Europe buys Bitcoin"
    has_blueprint = True
    blueprint_module = "kdmukai.specterext.bitcoinreserve.controller"
    devstatus = devstatus_alpha
    isolated_client = False

    # TODO: As more Services are integrated, we'll want more robust categorization and sorting logic
    sort_priority = 2

    # ServiceEncryptedStorage field names for this service
    # Those will end up as keys in a json-file
    SPECTER_WALLET_ALIAS = "wallet"
    API_TOKEN = "api_token"
    LAST_TRANSACTION_TIME = "last_transaction_time"

    # def callback_after_serverpy_init_app(self, scheduler: APScheduler):
    #     def every5seconds(hello, world="world"):
    #         with scheduler.app.app_context():
    #             pass
                #print(f"Called {hello} {world} every5seconds")
        # Here you can schedule regular jobs. triggers can be one of "interval", "date" or "cron"
        # Examples:
        # interval: https://apscheduler.readthedocs.io/en/3.x/modules/triggers/interval.html
        # scheduler.add_job("every5seconds4", every5seconds, trigger='interval', seconds=5, args=["hello"])
        # Date: https://apscheduler.readthedocs.io/en/3.x/modules/triggers/date.html
        # scheduler.add_job("MyId", my_job, trigger='date', run_date=date(2009, 11, 6), args=['text'])
        # cron: https://apscheduler.readthedocs.io/en/3.x/modules/triggers/cron.html
        # sched.add_job("anotherID", job_function, trigger='cron', day_of_week='mon-fri', hour=5, minute=30, end_date='2014-05-30')
        # Maybe you should store the scheduler for later use:
        # self.scheduler = scheduler

    @classmethod
    def get_associated_wallet(cls) -> Wallet:
        """Get the Specter `Wallet` that is currently associated with this service"""
        service_data = cls.get_current_user_service_data()
        if not service_data or BitcoinReserveService.SPECTER_WALLET_ALIAS not in service_data:
            # Service is not initialized; nothing to do
            return
        try:
            return app.specter.wallet_manager.get_by_alias(
                service_data[BitcoinReserveService.SPECTER_WALLET_ALIAS]
            )
        except SpecterError as e:
            logger.debug(e)
            # Referenced an unknown wallet
            # TODO: keep ignoring or remove the unknown wallet from service_data?
            return

    @classmethod
    def set_associated_wallet(cls, wallet: Wallet):
        """Set the Specter `Wallet` that is currently associated with this Service"""
        cls.update_current_user_service_data({BitcoinReserveService.SPECTER_WALLET_ALIAS: wallet.alias})


    @classmethod
    def set_api_credentials(cls, user: User, api_token: str):
        cls.update_current_user_service_data(
            {
                BitcoinReserveService.API_TOKEN: api_token,
            }
        )
        user.add_service(BitcoinReserveService.id)

    @classmethod
    def get_api_credentials(cls) -> dict:
        service_data = cls.get_current_user_service_data()
        if BitcoinReserveService.API_TOKEN not in service_data:
            return {}

        return {
            "api_token": service_data.get(BitcoinReserveService.API_TOKEN),
        }

    @classmethod
    def remove_api_credentials(cls, user: User):
        service_data = cls.get_current_user_service_data()
        if BitcoinReserveService.API_TOKEN in service_data:
            del service_data[BitcoinReserveService.API_TOKEN]
        cls.set_current_user_service_data(service_data)
        user.remove_service(BitcoinReserveService.id)

    @classmethod
    def has_api_credentials(cls) -> bool:
        return BitcoinReserveService.get_api_credentials() != {}

    @classmethod
    def update(cls):
        from . import client as bitcoinreserve_client
        transactions = bitcoinreserve_client.get_transactions()

        # The first entry is the summary data:
        """
            {
                "total_transaction_count": 29,
                "page": 0
            },
            {
                "transaction_id": "1f88faf0-dfc4-410e-9163-7371f9aa9e30",
                "transaction_status": "DONE",
                "transaction_type": "WITHDRAWAL",
                "transaction_time": "2022-01-18 05:28:35.068650",
                "in_currency": null,
                "in_amount": "None",
                "out_currency": "SATS",
                "out_amount": "28838.00000000"
            }
        """
        last_transaction_time = BitcoinReserveService.get_current_user_service_data().get(BitcoinReserveService.LAST_TRANSACTION_TIME)
        print(f"last_transaction_time: {last_transaction_time}")
        new_last_transaction_time = datetime.datetime(2000, 1, 1).timestamp()
        for index, tx in enumerate(transactions):
            if index == 0:
                print(f"""total_transaction_count: {tx.get("total_transaction_count")}""")
                continue

            transaction_time = datetime.datetime.strptime(tx.get("transaction_time"), "%Y-%m-%d %H:%M:%S.%f").timestamp()
            print(f"transaction_time: {transaction_time}")

            if not last_transaction_time or transaction_time > last_transaction_time:
                details = bitcoinreserve_client.get_transaction(tx.get("transaction_id"))
                print(json.dumps(details, indent=4))
                new_last_transaction_time = max(new_last_transaction_time, transaction_time)
                print(f"new_last_transaction_time: {new_last_transaction_time}")
        
        if new_last_transaction_time > last_transaction_time:
            # Update our service_data to mark these transactions as already scanned
            BitcoinReserveService.update_current_user_service_data({
                BitcoinReserveService.LAST_TRANSACTION_TIME: new_last_transaction_time
            })

    @classmethod
    def on_user_login(cls):
        cls.update()
