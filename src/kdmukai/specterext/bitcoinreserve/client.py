import json
import logging
import requests

from decimal import Decimal
from flask import current_app as app
from werkzeug.wrappers import auth

from kdmukai.specterext.bitcoinreserve.service import BitcoinReserveService


logger = logging.getLogger(__name__)


class BitcoinReserveApiException(Exception):
    pass


def authenticated_request(
    endpoint: str, method: str = "GET", json_payload: dict = {}
) -> dict:
    logger.debug(f"{method} endpoint: {endpoint}")

    api_token = BitcoinReserveService.get_api_credentials().get("api_token")

    # Must explicitly set User-Agent; Swan firewall blocks all requests with "python".
    auth_header = {
        "User-Agent": "Specter Desktop",
        "Authorization": "Token " + api_token,
    }

    url = url=app.config.get("BITCOIN_RESERVE_API_URL") + endpoint
    logger.debug(url)
    logger.debug(auth_header)

    try:
        response = requests.request(
            method=method,
            url=url,
            headers=auth_header,
            json=json_payload,
        )
        if response.status_code != 200:
            raise BitcoinReserveApiException(f"{response.status_code}: {response.text}")
        print(json.dumps(response.json(), indent=4))
        return response.json()
    except Exception as e:
        # TODO: tighten up expected Exceptions
        logger.exception(e)
        logger.error(
            f"endpoint: {endpoint} | method: {method} | payload: {json.dumps(json_payload, indent=4)}"
        )
        logger.error(f"{response.status_code}: {response.text}")
        raise e


"""
"User Balance": /user/balance/
EXAMPLE:
curl -X GET http://46.101.227.39/user/balance/
OUTPUT:
{
    "balance_eur": "0.00000000"
}
"""


def get_fiat_balances():
    return authenticated_request("/user/balance")


"""
"Create Quote": /user/order/quote/
EXAMPLE:
curl -d '{"fiat_currency":"EUR", "fiat_deliver_amount":"10000", "withdrawal_address":"bc1qjg53lww9jrm506dj0g0szmk4pxt6f55x8dncuv", "withdrawal_method":"ONCHAIN"}' -H "Content-Type: application/json" -X POST http://46.101.227.39/user/order/quote/
OUTPUT:
{
    "quote_id": "9b787187-1fc2-475d-b495-0b9df5ed270e",
    "bitcoin_receive_amount": 0.26516569,
    "trade_fee_currency": "EUR",
    "trade_fee_amount": 195.0,
    "expiration_time_utc": 1641867612.480406
}
"""


def create_quote(
    fiat_amount: Decimal, withdrawal_address: str, fiat_currency: str = "EUR"
):
    return authenticated_request(
        "/user/order/quote",
        method="POST",
        json_payload={
            "fiat_currency": fiat_currency,
            "fiat_deliver_amount": fiat_amount,
            "withdrawal_address": withdrawal_address,
            "withdrawal_method": "ONCHAIN",
        },
    )


"""
"Confirm Order": /user/order/confirm/
EXAMPLE:
curl -d '{"quote_id":"9b787187-1fc2-475d-b495-0b9df5ed270e"}' -H "Content-Type: application/json" -X POST http://46.101.227.39/user/order/confirm/
OUTPUT: 
{
    "order_id": "d9160a5a-e23f-4f76-9327-330e2afda736",
    "order_status": "COMPLETE",
    "bitcoin_receive_amount": 0.26516569,
    "trade_fee_currency": "EUR",
    "trade_fee_amount": 195.0,
    "withdrawal_address": "bc1qjg53lww9jrm506dj0g0szmk4pxt6f55x8dncuv",
    "withdrawal_status": "INITIATED",
    "withdrawal_method": "ONCHAIN",
    "withdrawal_fee": 0.0,
    "withdrawal_eta": 1641953991.115419
}
"""


def confirm_order(quote_id: str):
    return authenticated_request(
        "/user/order/confirm", method="POST", json_payload={"quote_id": quote_id}
    )


"""
"Order Status": /user/order/status/
EXAMPLE:
curl -d '{"order_id":"d9160a5a-e23f-4f76-9327-330e2afda736"}' -H "Content-Type: application/json" -X GET http://46.101.227.39/user/order/status/
OUTPUT:
{
    "order_status": "COMPLETE",
    "bitcoin_receive_amount": 0.26516569,
    "quote_id": "9b787187-1fc2-475d-b495-0b9df5ed270e",
    "trade_fee_currency": "EUR",
    "trade_fee_amount": 195.0,
    "withdrawals": {
        "withdrawal_number": 0,
        "withdrawal_status": "INITIATED",
        "withdrawal_address": "bc1qjg53lww9jrm506dj0g0szmk4pxt6f55x8dncuv",
        "withdrawal_method": "ONCHAIN",
        "withdrawal_fee": 0.0,
        "withdrawal_eta": 1641953991.115419,
        "withdrawal_identifier": null
    }
}
"""


def get_order_status(order_id: str):
    return authenticated_request(
        "/user/order/status", method="GET", json_payload={"order_id": order_id}
    )


def get_transactions(page_num: int = 0) -> list:
    """
        First entry is the summary data:
        [
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
            },
            {...},
        ]
    """
    return authenticated_request(f"/api/user/transactions/{page_num}")


def get_transaction(transaction_id: str) -> dict:
    """
        {
            "transaction_type": "MARKET BUY",
            "transaction_id": "31ffc3b6-9b9f-41db-ad6d-b636b69ae63d",
            "transaction_status": "COMPLETE",
            "sats_bought": "147810",
            "fiat_spent": "50.00",
            "fiat_currency": "EUR",
            "withdrawals": {
                "transaction_type": "WITHDRAWAL",
                "transaction_id": "a9ab0eca-eb9a-4e6e-a692-8531356dd674",
                "withdrawal_serial_number": 0,
                "withdrawal_status": "DONE",
                "withdrawal_address": "bc1qsst0m3pn9adnl68wuhd9h727eu09rnn0nqes2u",
                "withdrawal_fee": "0",
                "withdrawal_currency": "SATS",
                "withdrawal_identifier": "ab4be723b1b11334fde4317c54fad91d583a1570958f78a486a3d4b4d32d7bc1"
            }
        }
    """
    return authenticated_request(f"/api/user/transaction/{transaction_id}")
