import collections
import math
import operator
import re
import time


TYPE_COMMON = 'common'
TYPE_PREFERRED = 'preferred'
STOCK_TYPES = (TYPE_COMMON, TYPE_PREFERRED)

TRADE_BUY = 'buy'
TRADE_SELL = 'sell'
TRADE_TYPES = (TRADE_BUY, TRADE_SELL)

DEFAULT_TRADE_DECAY_TIME = 15 * 60  # 15 minutes


class StockError(Exception):
    pass


class ValidationError(Exception):
    pass


class Stock(object):
    _SYMBOL_PATTERN = re.compile(r'^[A-Z]{3}$')

    def __init__(self, symbol, stock_type, last_dividend, fixed_dividend,
                 par_value, trades_cache_decay_time=DEFAULT_TRADE_DECAY_TIME):
        symbol, stock_type, last_dividend, fixed_dividend, par_value = (
            self._validate(
                symbol, stock_type, last_dividend, fixed_dividend, par_value
            )
        )
        self._symbol = symbol
        self._stock_type = stock_type
        self._last_dividend = last_dividend
        self._fixed_dividend = fixed_dividend
        self._par_value = par_value
        self._trades_cache_decay_time = trades_cache_decay_time

        self._trades = collections.deque()

    def _validate(self, symbol, stock_type, last_dividend, fixed_dividend,
                  par_value):
        errors = []

        # Validate symbol
        if self._SYMBOL_PATTERN.match(symbol) is None:
            errors.append('"{}" is invalid symbol'.format(symbol))

        if stock_type not in STOCK_TYPES:
            errors.append(
                'stock_type should be one of ({})'.format(
                    ', '.join(STOCK_TYPES)
                )
            )

        try:
            last_dividend = float(last_dividend)
            if last_dividend < 0.0:
                raise ValueError
        except ValueError:
            errors.append('last_dividend should be a non-negative number')

        try:
            if stock_type == TYPE_PREFERRED:
                fixed_dividend = float(fixed_dividend)
                if fixed_dividend < 0.0 or fixed_dividend > 100.0:
                    raise ValueError
            else:
                fixed_dividend = None
        except ValueError:
            errors.append(
                'fixed_dividend should be a number in the interval [0, 100]'
            )

        try:
            par_value = float(par_value)
            if par_value < 0.0:
                raise ValueError
        except ValueError:
            errors.append('par_value should be a non-negative number')

        if errors:
            raise ValidationError('\n'.join(errors))

        return symbol, stock_type, last_dividend, fixed_dividend, par_value

    def _validate_trade(self, timestamp, quantity, buy_sell, price):
        errors = []

        try:
            timestamp = float(timestamp)
            if timestamp < 0.0:
                raise ValueError
            if self._trades and self._trades[-1][0] > timestamp:
                raise ValueError
        except ValueError:
            errors.append(
                'timestamp should be a non-negative number of second since '
                'epoch. timestamp cannot be less than timestamp of last '
                'recorded trade'
            )

        try:
            quantity = int(quantity)
            if quantity < 1:
                raise ValueError
        except ValueError:
            errors.append('quantity should be a positive integer number')

        if buy_sell not in TRADE_TYPES:
            errors.append(
                'buy_sell should be one of ({})'.format(
                    ', '.join(TRADE_TYPES)
                )
            )

        try:
            price = float(price)
            if price <= 0.0:
                raise ValueError
        except ValueError:
            errors.append('price should be a positive number')

        if errors:
            raise ValidationError('\n'.join(errors))

        return timestamp, quantity, buy_sell, price

    @property
    def symbol(self):
        return self._symbol

    @property
    def stock_type(self):
        return self._stock_type

    @property
    def last_dividend(self):
        return self._last_dividend

    @property
    def fixed_dividend(self):
        return self._fixed_dividend and self._fixed_dividend / 100.0

    @property
    def fixed_dividend_percent(self):
        return self._fixed_dividend

    @property
    def par_value(self):
        return self._par_value

    @property
    def dividend_yield(self):
        if self.stock_price == 0.0:
            return 0.0
        if self._stock_type == TYPE_COMMON:
            return self.last_dividend / self.stock_price
        else:
            return self.fixed_dividend * self.par_value / self.stock_price

    @property
    def pe_ratio(self):
        dividend_yield = self.dividend_yield
        if dividend_yield == 0.0:
            return 0.0
        return self.stock_price / self.dividend_yield

    @property
    def stock_price(self):
        now = time.time()
        relevant_since = now - self._trades_cache_decay_time
        while self._trades and self._trades[0][0] < relevant_since:
            self._trades.popleft()

        if not self._trades:
            return 0.0

        _, trades = zip(*self._trades)
        quantities, _, prices = zip(*trades)
        total_price = sum(map(operator.mul, prices, quantities))
        total_quantity = sum(quantities)

        return total_price / total_quantity

    def record_trade(self, timestamp, quantity, buy_sell, price):
        timestamp, quantity, buy_sell, price = self._validate_trade(
            timestamp, quantity, buy_sell, price
        )
        self._trades.append((timestamp, (quantity, buy_sell, price)))


class StockManager(object):
    def __init__(self):
        self._stocks = {}

    @property
    def all_share_index(self):
        significant_stock_values = filter(
            lambda v: v.stock_price, self._stocks.values()
        )
        if not significant_stock_values:
            return 0.0

        return math.pow(
            reduce(
                operator.mul,
                map(operator.attrgetter('stock_price'),
                    significant_stock_values)
            ),
            1.0 / len(significant_stock_values)
        )

    def add_stock(self, stock):
        if not isinstance(stock, Stock):
            raise StockError('stock argument should be of Stock type')

        self._stocks[stock.symbol] = stock

    def get_stock(self, symbol):
        return self._stocks[symbol]
