import logging
from flask import redirect, render_template, request, url_for, flash
from flask import current_app as app
from flask_login import login_required, current_user
from functools import wraps

from cryptoadvance.specter.services.controller import user_secret_decrypted_required
from cryptoadvance.specter.services.service_encrypted_storage import ServiceEncryptedStorageError
from cryptoadvance.specter.user import User
from cryptoadvance.specter.wallet import Wallet

from kdmukai.specterext.bitcoinreserve.client import BitcoinReserveApiException
from .service import BitcoinReserveService


logger = logging.getLogger(__name__)

bitcoinreserve_endpoint = BitcoinReserveService.blueprint

def ext():
    ''' convenience for getting the extension-object'''
    return app.specter.ext["bitcoinreserve"]



def api_key_required(func):
    """Refresh token needed for any endpoint that interacts with Swan API"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            if not BitcoinReserveService.has_api_credentials():
                logger.debug(f"No API credentials, redirecting to set API key")
                return redirect(
                    url_for(f"{BitcoinReserveService.get_blueprint_name()}.set_api_key")
                )
        except ServiceEncryptedStorageError as e:
            logger.debug(repr(e))
            flash("Re-login required to access your protected services data")

            # Use Flask's built-in re-login w/automatic redirect back to calling page
            return app.login_manager.unauthorized()
        return func(*args, **kwargs)

    return wrapper



@bitcoinreserve_endpoint.route("/")
@login_required
@user_secret_decrypted_required
def index():
    return render_template(
        "bitcoinreserve/index.jinja",
    )



@bitcoinreserve_endpoint.route("/set_api_key", methods=["GET", "POST"])
@login_required
@user_secret_decrypted_required
def set_api_key():
    if request.method == "POST":
        client_id = request.form.get("client_id")
        client_secret = request.form.get("client_secret")
        BitcoinReserveService.set_api_credentials(
            user=app.specter.user_manager.get_user(),
            client_id=client_id,
            client_secret=client_secret,
        )

        try:
            BitcoinReserveService.update()
            return redirect(
                url_for(f"{BitcoinReserveService.get_blueprint_name()}.history")
            )
        except BitcoinReserveApiException as e:
            logger.debug(repr(e))
            flash(_("Error: {e}"), category="error")

    return render_template(
        "bitcoinreserve/set_api_key.jinja",
    )



@bitcoinreserve_endpoint.route("/transactions")
@login_required
@user_secret_decrypted_required
def transactions():
    # The wallet currently configured for ongoing autowithdrawals
    wallet: Wallet = BitcoinReserveService.get_associated_wallet()

    return render_template(
        "bitcoinreserve/transactions.jinja",
        wallet=wallet,
        services=app.specter.service_manager.services,
    )




@bitcoinreserve_endpoint.route("/flash_buy")
@login_required
@api_key_required
def flash_buy():
    return render_template(
        "bitcoinreserve/index.jinja",
    )



@bitcoinreserve_endpoint.route("/settings", methods=["GET"])
@login_required
@user_secret_decrypted_required
def settings_get():
    associated_wallet: Wallet = BitcoinReserveService.get_associated_wallet()

    # Get the user's Wallet objs, sorted by Wallet.name
    wallet_names = sorted(current_user.wallet_manager.wallets.keys())
    wallets = [current_user.wallet_manager.wallets[name] for name in wallet_names]

    return render_template(
        "bitcoinreserve/settings.jinja",
        associated_wallet=associated_wallet,
        wallets=wallets,
        cookies=request.cookies,
    )



@bitcoinreserve_endpoint.route("/settings", methods=["POST"])
@login_required
@user_secret_decrypted_required
def settings_post():
    show_menu = request.form["show_menu"]
    user = app.specter.user_manager.get_user()
    if show_menu == "yes":
        user.add_service(BitcoinReserveService.id)
    else:
        user.remove_service(BitcoinReserveService.id)
    used_wallet_alias = request.form.get("used_wallet")
    if used_wallet_alias != None:
        wallet = current_user.wallet_manager.get_by_alias(used_wallet_alias)
        BitcoinReserveService.set_associated_wallet(wallet)
    return redirect(url_for(f"{ BitcoinReserveService.get_blueprint_name()}.settings_get"))
