'''
EXAMPLE AUTO TRADER

These are simple bots that illustrate the Optibook API and some simple trading concepts. These bots will not make a profit.

This is an example bot that trades a single instrument.
All it does is to randomly insert either a BID or an ASK every 5 seconds.
The price at which it inserts is equal to the opposite side of the order book.
Thus, if the best bid in the order book is currently 90, it will send a sell order for price 90.
If the best ask in the order book is 91, it will send a buy order for price 91.

The order type this bot uses is IOC (immediate or cancel). This means that if the order does not
immediately trade, it will not be visible to others in the order book. Instead, it will be cancelled automatically.
'''
import logging
import time
from typing import List
from optibook import common_types as t
from optibook import ORDER_TYPE_IOC, ORDER_TYPE_LIMIT, SIDE_ASK, SIDE_BID
from optibook.exchange_responses import InsertOrderResponse
from optibook.synchronous_client import Exchange
import random
import json

logging.getLogger('client').setLevel('ERROR')
logger = logging.getLogger(__name__)

INSTRUMENT_ID = 'SMALL_CHIPS'


def print_report(e: Exchange):
    pnl = e.get_pnl()
    positions = e.get_positions()
    my_trades = e.poll_new_trades(INSTRUMENT_ID)
    all_market_trades = e.poll_new_trade_ticks(INSTRUMENT_ID)
    logger.info(f'I have done {len(my_trades)} trade(s) in {INSTRUMENT_ID} since the last report. There have been {len(all_market_trades)} market trade(s) in total in {INSTRUMENT_ID} since the last report.')
    logger.info(f'My PNL is: {pnl:.2f}')
    logger.info(f'My current positions are: {json.dumps(positions, indent=3)}')
    logger.info("orders: " + e.get_outstanding_orders(INSTRUMENT_ID))

def print_order_response(order_response: InsertOrderResponse):
    if order_response.success:
        logger.info(f"Inserted order successfully, order_id='{order_response.order_id}'")
    else:
        logger.info(f"Unable to insert order with reason: '{order_response.success}'")


def trade_cycle(e: Exchange):
    # this is the main bot logic which gets called every 5 seconds
    # fetch the current order book

    tradable_instruments = e.get_instruments()

    # first we verify that the instrument we wish to trade actually exists
    if INSTRUMENT_ID not in tradable_instruments:
        logger.info(f"Unable to trade because instrument '{INSTRUMENT_ID}' does not exist")
        return

    # then we make sure that the instrument is not currently paused
    if tradable_instruments[INSTRUMENT_ID].paused:
        logger.info(f"Skipping cycle because instrument '{INSTRUMENT_ID}' is paused, will try again in the next cycle.")
        return

    # Get the latest order book
    book = e.get_last_price_book(INSTRUMENT_ID)
    position = e.get_positions()[INSTRUMENT_ID]

    # verify that the book exists and that it has at least one bid and ask
    if book and book.bids and book.asks:
        # now randomly either shoot a BID (buy order) or an ASK (sell order)
        if book.bids[0].price > 117.5 and position > 0:
            response: InsertOrderResponse = e.insert_order(INSTRUMENT_ID, price=book.bids[0].price + 0.1, volume=min(20, position), side=SIDE_ASK, order_type=ORDER_TYPE_IOC)
            print_order_response(response)
        elif book.asks[0].price < 117 and position < 30:
            response: InsertOrderResponse = e.insert_order(INSTRUMENT_ID, price=book.asks[0].price - 0.1, volume=20, side=SIDE_BID, order_type=ORDER_TYPE_IOC)
            print_order_response(response)

        # now look at whether you successfully inserted an order or not.
        # note: If you send invalid information, such as in instrument which does not exist, you will be disconnected
        
    else:
        logger.info(f"No top bid/ask or no book at all for the instrument '{INSTRUMENT_ID}'")

    print_report(e)


def main():
    exchange = Exchange()
    exchange.connect()

    # you can also define host/user/pass yourself
    # when not defined, it is taken from ~/.optibook file if it exists
    # if that file does not exists, an error is thrown
    #exchange = Exchange(host='host-to-connect-to', info_port=7001, exec_port=8001, username='your-username', password='your-password')
    #exchange.connect()

    sleep_duration_sec = 8
    while True:
        trade_cycle(exchange)
        logger.info(f'Iteration complete. Sleeping for {sleep_duration_sec} seconds')
        time.sleep(sleep_duration_sec)


if __name__ == '__main__':
    main()
