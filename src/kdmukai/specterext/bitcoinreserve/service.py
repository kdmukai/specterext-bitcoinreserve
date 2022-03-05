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
    API_CLIENT_ID = "client_id"
    API_CLIENT_SECRET = "client_secret"

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
    def set_api_credentials(cls, user: User, client_id: str, client_secret: str):
        cls.update_current_user_service_data(
            {
                BitcoinReserveService.API_CLIENT_ID: client_id,
                BitcoinReserveService.API_CLIENT_SECRET: client_secret,
            }
        )
        user.add_service(BitcoinReserveService.id)

    @classmethod
    def get_api_credentials(cls, client_id: str, client_secret: str) -> dict:
        service_data = cls.get_current_user_service_data()
        if (
            not BitcoinReserveService.API_CLIENT_ID in service_data
            or BitcoinReserveService.API_CLIENT_SECRET not in service_data
        ):
            return {}

        return {
            "client_id": service_data.get(BitcoinReserveService.API_CLIENT_ID),
            "client_secret": service_data.get(BitcoinReserveService.API_CLIENT_SECRET),
        }

    @classmethod
    def remove_api_credentials(cls, user: User):
        service_data = cls.get_current_user_service_data()
        if BitcoinReserveService.API_CLIENT_ID in service_data:
            del service_data[BitcoinReserveService.API_CLIENT_ID]
        if BitcoinReserveService.API_CLIENT_SECRET in service_data:
            del service_data[BitcoinReserveService.API_CLIENT_SECRET]
        cls.set_current_user_service_data(service_data)
        user.remove_service(BitcoinReserveService.id)

    @classmethod
    def has_api_credentials(cls) -> bool:
        return BitcoinReserveService.get_api_credentials() != {}

    @classmethod
    def update(cls):
        from . import client as bitcoinreserve_client

        results = bitcoinreserve_client.get_orders()

    @classmethod
    def on_user_login(cls):
        cls.update()
