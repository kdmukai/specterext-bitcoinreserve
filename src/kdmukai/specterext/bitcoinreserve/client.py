import json
import logging
import requests

from decimal import Decimal
from flask import app
from werkzeug.wrappers import auth

from kdmukai.specterext.bitcoinreserve.service import BitcoinReserveService


logger = logging.getLogger(__name__)


class BitcoinReserveApiException(Exception):
    pass


def authenticated_request(
    endpoint: str, method: str = "GET", json_payload: dict = {}
) -> dict:
    logger.debug(f"{method} endpoint: {endpoint}")

    api_keys = BitcoinReserveService.get_api_credentials()

    # Must explicitly set User-Agent; Swan firewall blocks all requests with "python".
    auth_header = {
        "User-Agent": "Specter Desktop",
    }
    try:
        response = requests.request(
            method=method,
            url=app.config.get("BITCOIN_RESERVE_API_URL") + endpoint,
            headers=auth_header,
            json=json_payload,
        )
        if response.status_code != 200:
            raise BitcoinReserveApiException(f"{response.status_code}: {response.text}")
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


"""
"Order History": /user/orders/
EXAMPLE:
curl -X GET http://46.101.227.39/user/orders/
OUTPUT:
[
    {
        "order_id": "ff651131-7934-4833-be5a-0f7a0b7b4b5e",
        "order_status": "COMPLETE",
        "quote_id": "67dcd074-d462-48e5-a38f-25568af17a4d",
        "trade_fee_currency": "EUR",
        "trade_fee_amount": 30.0,
        "withdrawals": {
            "withdrawal_number": 0,
            "withdrawal_status": "INITIATED",
            "withdrawal_address": "bc1qjg53lww9jrm506dj0g0szmk4pxt6f55x8dncuv",
            "withdrawal_method": "ONCHAIN",
            "withdrawal_fee": 0.0,
            "withdrawal_eta": 1641580420.89475,
            "withdrawal_identifier": null
        }
    },
    {
        "order_id": "c1f13466-a58f-4df1-b76a-45a59136675b",
        "order_status": "COMPLETE",
        "quote_id": "0d610e67-3090-4ed4-ba6f-a42f5e63ec15",
        "trade_fee_currency": "EUR",
        "trade_fee_amount": 15.0,
        "withdrawals": {
            "withdrawal_number": 0,
            "withdrawal_status": "INITIATED",
            "withdrawal_address": "3NUNxvYdD3ifmMuVLF3uhVAx977GrHykUc",
            "withdrawal_method": "ONCHAIN",
            "withdrawal_fee": 0.0,
            "withdrawal_eta": 1641580580.193506,
            "withdrawal_identifier": "94a9e6d5b08435e0bb04cc94847812970749f40d909e5c83d29097559bd320f8"
        }
    },
    {
        "order_id": "f46b47fe-7164-4623-8d04-77ce9086c1f6",
        "order_status": "COMPLETE",
        "quote_id": "003e6246-2ef4-42ed-805e-38788aac9ce5",
        "trade_fee_currency": "EUR",
        "trade_fee_amount": 234.0,
        "withdrawals": {
            "withdrawal_number": 0,
            "withdrawal_status": "INITIATED",
            "withdrawal_address": "bc1qtt04zfgjxg7lpqhk9vk8hnmnwf88ucwww5arsd",
            "withdrawal_method": "ONCHAIN",
            "withdrawal_fee": 0.0,
            "withdrawal_eta": 1641580711.972974,
            "withdrawal_identifier": null
        }
    },
    {
        "order_id": "a19d417f-5607-4db9-8988-3f049768908f",
        "order_status": "COMPLETE",
        "quote_id": "886e9065-8c1a-4755-a846-4dc5348f69a1",
        "trade_fee_currency": "EUR",
        "trade_fee_amount": 149.5,
        "withdrawals": {
            "withdrawal_number": 0,
            "withdrawal_status": "INITIATED",
            "withdrawal_address": "bc1qjg53lww9jrm506dj0g0szmk4pxt6f55x8dncuv",
            "withdrawal_method": "ONCHAIN",
            "withdrawal_fee": 0.0,
            "withdrawal_eta": 1641918044.398311,
            "withdrawal_identifier": null
        }
    },
    {
        "order_id": "ada3b445-268f-4b19-8be9-1813d2049107",
        "order_status": "COMPLETE",
        "quote_id": "886e9065-8c1a-4755-a846-4dc5348f69a1",
        "trade_fee_currency": "EUR",
        "trade_fee_amount": 149.5,
        "withdrawals": {
            "withdrawal_number": 0,
            "withdrawal_status": "INITIATED",
            "withdrawal_address": "bc1qjg53lww9jrm506dj0g0szmk4pxt6f55x8dncuv",
            "withdrawal_method": "ONCHAIN",
            "withdrawal_fee": 0.0,
            "withdrawal_eta": 1641918060.721925,
            "withdrawal_identifier": null
        }
    },
    {
        "order_id": "39e70c45-429a-401d-a04f-7954b1e5763b",
        "order_status": "COMPLETE",
        "quote_id": "e80f9f82-d317-451e-9626-e95f4a3ef9d4",
        "trade_fee_currency": "EUR",
        "trade_fee_amount": 149.5,
        "withdrawals": {
            "withdrawal_number": 0,
            "withdrawal_status": "INITIATED",
            "withdrawal_address": "bc1qjg53lww9jrm506dj0g0szmk4pxt6f55x8dncuv",
            "withdrawal_method": "ONCHAIN",
            "withdrawal_fee": 0.0,
            "withdrawal_eta": 1641918081.47717,
            "withdrawal_identifier": null
        }
    },
    {
        "order_id": "64b25003-f86f-4efe-8f12-25e081997f94",
        "order_status": "COMPLETE",
        "quote_id": "9bf167ef-fe91-4aa0-84ae-4e776cb18964",
        "trade_fee_currency": "EUR",
        "trade_fee_amount": 232.5323,
        "withdrawals": {
            "withdrawal_number": 0,
            "withdrawal_status": "INITIATED",
            "withdrawal_address": "bc1qjg53lww9jrm506dj0g0szmk4pxt6f55x8dncuv",
            "withdrawal_method": "ONCHAIN",
            "withdrawal_fee": 0.0,
            "withdrawal_eta": 1641926345.437326,
            "withdrawal_identifier": null
        }
    }
]
"""


def get_orders():
    return authenticated_request("/user/orders")
