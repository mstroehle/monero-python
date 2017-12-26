import argparse
from decimal import Decimal
import logging
import pprint
import random
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

from monero.backends.jsonrpc import JSONRPCWallet
from monero import exceptions
from monero import Address, Wallet, as_monero

def get_wallet():
    argsparser = argparse.ArgumentParser(description="Display wallet contents")
    argsparser.add_argument('--host', dest='host', default='127.0.0.1', help="Wallet RPC host")
    argsparser.add_argument('--port', dest='port', default='18082', help="Wallet RPC port")
    argsparser.add_argument('-u', dest='user', default='', help="Wallet RPC user")
    argsparser.add_argument('-p', dest='password', default='', help="Wallet RPC password")
    argsparser.add_argument('-v', dest='verbosity', action='count', default=0,
        help="Verbosity (repeat to increase; -v for INFO, -vv for DEBUG")
    args = argsparser.parse_args()
    level = logging.WARNING
    if args.verbosity == 1:
        level = logging.INFO
    elif args.verbosity > 1:
        level = logging.DEBUG
    logging.basicConfig(level=level, format="%(asctime)-15s %(message)s")
    return Wallet(JSONRPCWallet(
        host=args.host, port=args.port,
        user=args.user,
        password=args.password))

_TXHDR = "timestamp         height  id/hash                                                     " \
    "         amount         fee           payment_id"

def tx2str(tx):
    return "{time} {height} {fullid} {amount:17.12f} {fee:13.12f} {payment_id}".format(
        time=tx['timestamp'].strftime("%d-%m-%y %H:%M:%S"),
        shortid="[{}...]".format(tx['id'][:32]),
        fullid=tx['id'],
        **tx)

w = get_wallet()
print(
    "Master address: {addr}\n" \
    "Balance: {total:16.12f} ({unlocked:16.12f} unlocked)".format(
        addr=w.get_address(),
        total=w.get_balance(),
        unlocked=w.get_balance(unlocked=True)))

if len(w.accounts) > 1:
    print("\nWallet has {num} account(s):".format(num=len(w.accounts)))
    for acc in w.accounts:
        print("\nAccount {idx:02d}:".format(idx=acc.index))
        print("Balance: {total:16.12f} ({unlocked:16.12f} unlocked)".format(
            total=acc.get_balance(),
            unlocked=acc.get_balance(unlocked=True)))
        addresses = acc.get_addresses()
        print("{num:2d} address(es):".format(num=len(addresses)))
        print("\n".join(map(str, addresses)))
        ins = acc.get_payments_in()
        if ins:
            print("\nIncoming payments:")
            print(_TXHDR)
            for tx in ins:
                print(tx2str(tx))
        outs = acc.get_payments_out()
        if outs:
            print("\nOutgoing transfers:")
            print(_TXHDR)
            for tx in outs:
                print(tx2str(tx))
else:
    ins = w.get_payments_in()
    if ins:
        print("\nIncoming payments:")
        print(_TXHDR)
        for tx in ins:
            print(tx2str(tx))
    outs = w.get_payments_out()
    if outs:
        print("\nOutgoing transfers:")
        print(_TXHDR)
        for tx in outs:
            print(tx2str(tx))
