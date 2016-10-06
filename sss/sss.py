#!/usr/bin/env python

import cli
import model


sample_stocks = [
    {
        'symbol': 'TEA',
        'stock_type': model.TYPE_COMMON,
        'last_dividend': 0,
        'fixed_dividend': None,
        'par_value': 100
    },
    {
        'symbol': 'POP',
        'stock_type': model.TYPE_COMMON,
        'last_dividend': 8,
        'fixed_dividend': None,
        'par_value': 100
    },
    {
        'symbol': 'ALE',
        'stock_type': model.TYPE_COMMON,
        'last_dividend': 23,
        'fixed_dividend': None,
        'par_value': 60
    },
    {
        'symbol': 'GIN',
        'stock_type': model.TYPE_PREFERRED,
        'last_dividend': 8,
        'fixed_dividend': 2,
        'par_value': 100
    },
    {
        'symbol': 'JOE',
        'stock_type': model.TYPE_COMMON,
        'last_dividend': 13,
        'fixed_dividend': None,
        'par_value': 250
    },
]


if __name__ == '__main__':
    stock_manager = model.StockManager()
    for stock_data in sample_stocks:
        stock_manager.add_stock(model.Stock(**stock_data))

    cli.SuperSimpleStocksShell(stock_manager)
