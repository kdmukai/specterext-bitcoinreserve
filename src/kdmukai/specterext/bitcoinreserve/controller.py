import logging
from flask import redirect, render_template, request, url_for, flash
from flask import current_app as app
from flask_login import login_required, current_user

from cryptoadvance.specter.services.controller import user_secret_decrypted_required
from cryptoadvance.specter.user import User
from cryptoadvance.specter.wallet import Wallet
from .service import BitcoinreserveService


logger = logging.getLogger(__name__)

bitcoinreserve_endpoint = BitcoinreserveService.blueprint

def ext():
    ''' convenience for getting the extension-object'''
    return app.specter.ext["bitcoinreserve"]


@bitcoinreserve_endpoint.route("/")
@login_required
@user_secret_decrypted_required
def index():
    return render_template(
        "bitcoinreserve/index.jinja",
    )



@bitcoinreserve_endpoint.route("/transactions")
@login_required
@user_secret_decrypted_required
def transactions():
    # The wallet currently configured for ongoing autowithdrawals
    wallet: Wallet = BitcoinreserveService.get_associated_wallet()

    return render_template(
        "bitcoinreserve/transactions.jinja",
        wallet=wallet,
        services=app.specter.service_manager.services,
    )


@bitcoinreserve_endpoint.route("/settings", methods=["GET"])
@login_required
@user_secret_decrypted_required
def settings_get():
    associated_wallet: Wallet = BitcoinreserveService.get_associated_wallet()

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
        user.add_service(BitcoinreserveService.id)
    else:
        user.remove_service(BitcoinreserveService.id)
    used_wallet_alias = request.form.get("used_wallet")
    if used_wallet_alias != None:
        wallet = current_user.wallet_manager.get_by_alias(used_wallet_alias)
        BitcoinreserveService.set_associated_wallet(wallet)
    return redirect(url_for(f"{ BitcoinreserveService.get_blueprint_name()}.settings_get"))
