import cmd
import time

import model


class ExitSubcommand(Exception):
    """ An exception for exit subcommand command loop. """
    pass


class SingleStockShell(cmd.Cmd):
    def __init__(self, stock, *args, **kwargs):
        cmd.Cmd.__init__(self, *args, **kwargs)
        self._stock = stock
        self.prompt = '{symbol}> '.format(symbol=stock.symbol)
        self.cmdloop()

    def do_dividend(self, args):
        """
        Calculate the dividend yeild.
        """
        try:
            print 'Dividend yield:', self._stock.dividend_yield
        except model.NoTradesError as e:
            print e.message

    def do_pe_ratio(self, args):
        """
        Calculate the P/E ratio.
        """
        try:
            print 'P/E ratio:', self._stock.pe_ratio
        except model.StockError as e:
            print e.message

    def do_record(self, args):
        """
        Record a trade.
        Usage:
            record <quantity> <buy/sell> <price>
        """
        args = filter(None, args.split(' '))
        if len(args) != 3:
            print(
                'Provide trade data in format: <quantity> <buy/sell> <price>'
            )
            return

        try:
            self._stock.record_trade(time.time(), *args)
        except model.ValidationError as e:
            print e.message
        else:
            print 'Recorded a trade'

    def do_price(self, args):
        """
        Calculate the stock price.
        """
        try:
            print 'Stock price:', self._stock.stock_price
        except model.NoTradesError as e:
            print e.message

    def do_quit(self, args):
        """
        Quit the operations with a single stock.
        """
        print 'Quitting to all stocks'
        raise ExitSubcommand()


class SuperSimpleStocksShell(cmd.Cmd):
    def __init__(self, stock_manager, *args, **kwargs):
        cmd.Cmd.__init__(self, *args, **kwargs)

        self._stock_manager = stock_manager

        self.prompt = '> '
        self.cmdloop('Super Simple Stocks simulation started.')

    def do_single(self, args):
        """
        Operations with a single stock.
        """
        print 'Single stock'

        if not len(args):
            print 'Provide a stock symbol.'
            return

        try:
            stock = self._stock_manager.get_stock(args)
        except KeyError:
            print 'Stock "{}" is not found'.format(args)
            return

        try:
            sub_shell = SingleStockShell(stock)
        except ExitSubcommand:
            pass

    def do_all(self, args):
        """
        Calculate the GBCE All Share Index using the geometric mean of prices
        for all stocks.
        """
        try:
            print 'GBCE All Share Index:', self._stock_manager.all_share_index
        except model.NoTradesError as e:
            print e.message

    def do_quit(self, args):
        """
        Quits the simulation.
        """
        print 'Bye.'
        raise SystemExit
