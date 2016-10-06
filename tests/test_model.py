import math
import string
import time

from sss import model

import hypothesis
import hypothesis.strategies as hs
import mock
import pytest

# Stock data generation strategies
symbol_strategy = hs.text(string.ascii_uppercase, min_size=3, max_size=3)
stock_type_strategy = hs.one_of(
    hs.just(model.TYPE_COMMON),
    hs.just(model.TYPE_PREFERRED)
)
last_dividend_strategy = hs.floats(min_value=0.0, allow_infinity=False)
fixed_dividend_strategy = hs.floats(min_value=0.0, max_value=100.0)
par_value_strategy = hs.floats(min_value=0.0, allow_infinity=False)
stock_price_strategy = hs.floats(min_value=0.0, allow_infinity=False)
dividend_yield_strategy = hs.floats(min_value=0.0, allow_infinity=False)

# Trade data generation strategies
timestamp_strategy = hs.floats(min_value=0.0, allow_infinity=False)
old_timestamp_strategy = (
    lambda now, decay: hs.floats(min_value=0.0, max_value=now - decay).filter(
        lambda v: v < now - decay
    )
)

# Error margin for possible test duration
ERROR_MARGIN = 4.0
new_timestamp_strategy = (
    lambda now, decay: hs.floats(
        min_value=now - decay + ERROR_MARGIN, max_value=now
    )
)
quantity_strategy = hs.integers(min_value=1)
buy_sell_strategy = hs.one_of(
    hs.just(model.TRADE_BUY),
    hs.just(model.TRADE_SELL)
)
trade_price_strategy = hs.floats(min_value=0.01, max_value=1e24)
trade_data_strategy = hs.tuples(
    quantity_strategy,
    buy_sell_strategy,
    trade_price_strategy
)


@pytest.fixture
def stock_factory():
    def build_stock():
        return model.Stock(
            symbol_strategy.example(),
            # We want to use this on a higher level, so we would need only
            # non-zero stock_price in case if there are any trade records
            stock_type_strategy.filter(lambda v: v > 0.01).example(),
            last_dividend_strategy.filter(lambda v: v > 0.01).example(),
            fixed_dividend_strategy.filter(lambda v: v > 0.01).example(),
            par_value_strategy.filter(lambda v: v > 0.01).example()
        )
    return build_stock


@pytest.fixture
def trade_factory():
    def build_trade():
        return (
            new_timestamp_strategy(
                time.time(), model.DEFAULT_TRADE_DECAY_TIME
            ).example(),
            trade_data_strategy.example()
        )
    return build_trade


@hypothesis.given(
    symbol=symbol_strategy,
    last_dividend=last_dividend_strategy,
    fixed_dividend=fixed_dividend_strategy,
    par_value=par_value_strategy
)
def test_common_stock_creation_success(symbol, last_dividend, fixed_dividend,
                                       par_value):
    stock_type = model.TYPE_COMMON
    stock = model.Stock(symbol, stock_type, last_dividend, fixed_dividend,
                        par_value)

    assert symbol == stock.symbol
    assert stock_type == stock.stock_type
    assert last_dividend == stock.last_dividend
    assert stock.fixed_dividend is None
    assert par_value == stock.par_value


@hypothesis.given(
    symbol=symbol_strategy,
    last_dividend=last_dividend_strategy,
    fixed_dividend=fixed_dividend_strategy,
    par_value=par_value_strategy
)
def test_preferred_stock_creation_success(symbol, last_dividend,
                                          fixed_dividend, par_value):
    stock_type = model.TYPE_PREFERRED
    stock = model.Stock(symbol, stock_type, last_dividend, fixed_dividend,
                        par_value)

    assert symbol == stock.symbol
    assert stock_type == stock.stock_type
    assert last_dividend == stock.last_dividend
    assert fixed_dividend == stock.fixed_dividend_percent
    assert par_value == stock.par_value


@hypothesis.given(
    symbol=hs.one_of(
        hs.text(string.ascii_lowercase, min_size=3, max_size=3),
        hs.text(string.ascii_uppercase, min_size=4),
        hs.text(string.ascii_uppercase, max_size=2),
        hs.text(string.printable, min_size=4),
        hs.text(string.printable, max_size=2)
    ),
    stock_type=stock_type_strategy,
    last_dividend=last_dividend_strategy,
    fixed_dividend=fixed_dividend_strategy,
    par_value=par_value_strategy
)
def test_stock_creation_invalid_symbol_fails(symbol, stock_type, last_dividend,
                                             fixed_dividend, par_value):
    with pytest.raises(model.ValidationError):
        model.Stock(symbol, stock_type, last_dividend, fixed_dividend,
                    par_value)


@hypothesis.given(
    symbol=symbol_strategy,
    stock_type=hs.one_of(
        hs.text(string.printable).filter(lambda v: v not in model.STOCK_TYPES),
        hs.just('COMMON'),
        hs.just('PREFERRED')
    ),
    last_dividend=last_dividend_strategy,
    fixed_dividend=fixed_dividend_strategy,
    par_value=par_value_strategy
)
def test_stock_creation_invalid_stock_type_fails(symbol, stock_type, last_dividend,
                                                 fixed_dividend, par_value):
    with pytest.raises(model.ValidationError):
        model.Stock(symbol, stock_type, last_dividend, fixed_dividend,
                    par_value)


@hypothesis.given(
    symbol=symbol_strategy,
    stock_type=stock_type_strategy,
    last_dividend=hs.one_of(
        hs.floats(max_value=0.0).filter(lambda v: v < 0.0),
        hs.text(string.ascii_letters)
    ),
    fixed_dividend=fixed_dividend_strategy,
    par_value=par_value_strategy
)
def test_stock_creation_invalid_last_dividend_fails(
    symbol, stock_type, last_dividend, fixed_dividend, par_value
):
    with pytest.raises(model.ValidationError):
        model.Stock(symbol, stock_type, last_dividend, fixed_dividend,
                    par_value)


@hypothesis.given(
    symbol=symbol_strategy,
    stock_type=hs.just(model.TYPE_PREFERRED),
    last_dividend=last_dividend_strategy,
    fixed_dividend=hs.one_of(
        hs.floats(max_value=0.0).filter(lambda v: v < 0.0),
        hs.floats(min_value=100.0).filter(lambda v: v > 100.0),
        hs.text(string.ascii_letters)
    ),
    par_value=par_value_strategy
)
def test_stock_creation_invalid_fixed_dividend_fails(
    symbol, stock_type, last_dividend, fixed_dividend, par_value
):
    with pytest.raises(model.ValidationError):
        model.Stock(symbol, stock_type, last_dividend, fixed_dividend,
                    par_value)


@hypothesis.given(
    symbol=symbol_strategy,
    stock_type=stock_type_strategy,
    last_dividend=last_dividend_strategy,
    fixed_dividend=fixed_dividend_strategy,
    par_value=hs.one_of(
        hs.floats(max_value=0.0).filter(lambda v: v < 0.0),
        hs.text(string.ascii_letters)
    )
)
def test_stock_creation_invalid_par_value_fails(
    symbol, stock_type, last_dividend, fixed_dividend, par_value
):
    with pytest.raises(model.ValidationError):
        model.Stock(symbol, stock_type, last_dividend, fixed_dividend,
                    par_value)


@hypothesis.given(
    symbol=symbol_strategy,
    stock_type=hs.just(model.TYPE_COMMON),
    last_dividend=last_dividend_strategy,
    fixed_dividend=fixed_dividend_strategy,
    par_value=par_value_strategy
)
def test_common_stock_fixed_dividend_success(
    symbol, stock_type, last_dividend, fixed_dividend, par_value
):
    stock = model.Stock(symbol, stock_type, last_dividend, fixed_dividend,
                        par_value)

    assert stock.fixed_dividend is None


@hypothesis.given(
    symbol=symbol_strategy,
    stock_type=hs.just(model.TYPE_PREFERRED),
    last_dividend=last_dividend_strategy,
    fixed_dividend=fixed_dividend_strategy,
    par_value=par_value_strategy
)
def test_preferred_stock_fixed_dividend_success(
    symbol, stock_type, last_dividend, fixed_dividend, par_value
):
    stock = model.Stock(symbol, stock_type, last_dividend, fixed_dividend,
                        par_value)

    expected_fixed_dividend = fixed_dividend / 100.0
    assert expected_fixed_dividend == stock.fixed_dividend


@hypothesis.given(
    symbol=symbol_strategy,
    stock_type=hs.just(model.TYPE_COMMON),
    last_dividend=last_dividend_strategy,
    fixed_dividend=fixed_dividend_strategy,
    par_value=par_value_strategy,
    stock_price=stock_price_strategy
)
def test_common_stock_dividend_yield_success(
    symbol, stock_type, last_dividend, fixed_dividend, par_value, stock_price
):
    expected_dividend_yield = (
        0.0 if not stock_price else last_dividend / stock_price
    )
    with mock.patch.object(model.Stock, 'stock_price',
                           new_callable=mock.PropertyMock) as stock_price_mock:
        stock_price_mock.return_value = stock_price
        stock = model.Stock(symbol, stock_type, last_dividend, fixed_dividend,
                            par_value)

        assert expected_dividend_yield == stock.dividend_yield


@hypothesis.given(
    symbol=symbol_strategy,
    stock_type=hs.just(model.TYPE_PREFERRED),
    last_dividend=last_dividend_strategy,
    fixed_dividend=fixed_dividend_strategy,
    par_value=par_value_strategy,
    stock_price=stock_price_strategy
)
def test_preferred_stock_dividend_yield_success(
    symbol, stock_type, last_dividend, fixed_dividend, par_value, stock_price
):
    expected_dividend_yield = (
        0.0
        if not stock_price else
        fixed_dividend / 100.0 * par_value / stock_price
    )
    with mock.patch.object(model.Stock, 'stock_price',
                           new_callable=mock.PropertyMock) as stock_price_mock:
        stock_price_mock.return_value = stock_price
        stock = model.Stock(symbol, stock_type, last_dividend, fixed_dividend,
                            par_value)

        assert expected_dividend_yield == stock.dividend_yield


@hypothesis.given(
    symbol=symbol_strategy,
    stock_type=hs.just(model.TYPE_PREFERRED),
    last_dividend=last_dividend_strategy,
    fixed_dividend=fixed_dividend_strategy,
    par_value=par_value_strategy,
    stock_price=stock_price_strategy,
    dividend_yield=dividend_yield_strategy
)
def test_stock_pe_ratio_success(
    symbol, stock_type, last_dividend, fixed_dividend, par_value, stock_price,
    dividend_yield
):
    expected_pe_ratio = (
        0.0 if not dividend_yield else stock_price / dividend_yield
    )
    with \
            mock.patch.object(
                model.Stock, 'stock_price', new_callable=mock.PropertyMock
            ) as stock_price_mock, \
            mock.patch.object(
                model.Stock, 'dividend_yield', new_callable=mock.PropertyMock
            ) as dividend_yield_mock:
        stock_price_mock.return_value = stock_price
        dividend_yield_mock.return_value = dividend_yield
        stock = model.Stock(symbol, stock_type, last_dividend, fixed_dividend,
                            par_value)

        assert expected_pe_ratio == stock.pe_ratio


def test_stock_no_trades_zero_price(stock_factory):
    stock = stock_factory()

    expected_stock_price = 0.0
    assert expected_stock_price == stock.stock_price


@hypothesis.given(
    trades=hs.lists(
        hs.tuples(
            old_timestamp_strategy(time.time(),
                                   model.DEFAULT_TRADE_DECAY_TIME),
            trade_data_strategy
        ),
        min_size=1
    )
)
def test_stock_too_old_trades_zero_price(stock_factory, trades):
    stock = stock_factory()

    # This is going to be a bit ugly. Will need to think of better way to test
    for trade in trades:
        stock._trades.append(trade)

    expected_stock_price = 0.0
    expected_trades_left = 0

    assert expected_stock_price == stock.stock_price
    assert expected_trades_left == len(stock._trades)


@hypothesis.given(
    trades=hs.lists(
        hs.tuples(
            new_timestamp_strategy(time.time(),
                                   model.DEFAULT_TRADE_DECAY_TIME),
            trade_data_strategy
        ),
        min_size=1
    )
)
def test_stock_new_trades_correct_price(stock_factory, trades):
    stock = stock_factory()

    # This is going to be a bit ugly. Will need to think of better way to test
    for trade in trades:
        stock._trades.append(trade)

    total_price = 0.0
    total_quantity = 0
    for _, (quantity, _, price) in trades:
        total_price += quantity * price
        total_quantity += quantity
    expected_stock_price = total_price / total_quantity

    assert expected_stock_price == stock.stock_price


@hypothesis.given(
    timestamp=timestamp_strategy,
    quantity=quantity_strategy,
    buy_sell=buy_sell_strategy,
    trade_price=trade_price_strategy
)
def test_stock_record_trade_success(
    stock_factory, timestamp, quantity, buy_sell, trade_price
):
    stock = stock_factory()

    stock.record_trade(timestamp, quantity, buy_sell, trade_price)

    actual_timestamp, (
        actual_quantity, actual_buy_sell, actual_trade_price
    ) = stock._trades[0]

    assert timestamp == actual_timestamp
    assert quantity == actual_quantity
    assert buy_sell == actual_buy_sell
    assert trade_price == actual_trade_price


@hypothesis.given(
    timestamp=hs.one_of(
        hs.floats(max_value=0.0).filter(lambda v: v < 0.0),
        hs.text(string.ascii_letters)
    ),
    quantity=quantity_strategy,
    buy_sell=buy_sell_strategy,
    trade_price=trade_price_strategy
)
def test_stock_record_invalid_timestamp_fails(
    stock_factory, timestamp, quantity, buy_sell, trade_price
):
    stock = stock_factory()

    with pytest.raises(model.ValidationError):
        stock.record_trade(timestamp, quantity, buy_sell, trade_price)


@hypothesis.given(
    timestamp=timestamp_strategy,
    quantity=hs.one_of(
        hs.integers(max_value=0),
        hs.text(string.ascii_letters)
    ),
    buy_sell=buy_sell_strategy,
    trade_price=trade_price_strategy
)
def test_stock_record_invalid_quantity_fails(
    stock_factory, timestamp, quantity, buy_sell, trade_price
):
    stock = stock_factory()

    with pytest.raises(model.ValidationError):
        stock.record_trade(timestamp, quantity, buy_sell, trade_price)


@hypothesis.given(
    timestamp=timestamp_strategy,
    quantity=quantity_strategy,
    buy_sell=hs.one_of(
        hs.text(string.printable).filter(lambda v: v not in model.TRADE_TYPES),
        hs.just('BUY'),
        hs.just('SELL')
    ),
    trade_price=trade_price_strategy
)
def test_stock_record_invalid_buy_sell_fails(
    stock_factory, timestamp, quantity, buy_sell, trade_price
):
    stock = stock_factory()

    with pytest.raises(model.ValidationError):
        stock.record_trade(timestamp, quantity, buy_sell, trade_price)


@hypothesis.given(
    timestamp=timestamp_strategy,
    quantity=quantity_strategy,
    buy_sell=buy_sell_strategy,
    trade_price=hs.one_of(
        hs.floats(max_value=0.0).filter(lambda v: v < 0.0),
        hs.text(string.ascii_letters)
    )
)
def test_stock_record_invalid_trade_price_fails(
    stock_factory, timestamp, quantity, buy_sell, trade_price
):
    stock = stock_factory()

    with pytest.raises(model.ValidationError):
        stock.record_trade(timestamp, quantity, buy_sell, trade_price)


def test_stock_manager_create_success():
    stock_manager = model.StockManager()

    assert not len(stock_manager._stocks)


def test_stock_manager_add_stock_wrong_type_fails():
    stock_manager = model.StockManager()

    with pytest.raises(model.StockError):
        stock_manager.add_stock({})


def test_stock_manager_add_get_stock_success(stock_factory):
    stock_manager = model.StockManager()
    stock = stock_factory()

    stock_manager.add_stock(stock)
    actual_stock = stock_manager.get_stock(stock.symbol)

    assert stock == actual_stock


def test_stock_manager_all_share_index_no_data_returns_zero(stock_factory):
    stock_manager = model.StockManager()
    stock = stock_factory()
    stock_manager.add_stock(stock)

    expected_all_share_index = 0.0
    assert expected_all_share_index == stock_manager.all_share_index


def test_stock_manager_all_share_index_success(stock_factory, trade_factory):
    stock_manager = model.StockManager()
    stock1 = stock_factory()
    stock2 = stock_factory()
    for stock in (stock1, stock2):
        stock_manager.add_stock(stock)
        timestamp, (quantity, buy_sell, trade_price) = trade_factory()
        stock.record_trade(timestamp, quantity, buy_sell, trade_price)

    expected_all_share_index = math.sqrt(
        stock1.stock_price * stock2.stock_price
    )
    assert expected_all_share_index == stock_manager.all_share_index


def test_stock_manager_all_share_index_stocks_without_data_ignored(
    stock_factory, trade_factory
):
    stock_manager = model.StockManager()
    stock1 = stock_factory()
    stock2 = stock_factory()
    for stock in (stock1, stock2):
        stock_manager.add_stock(stock)
    timestamp, (quantity, buy_sell, trade_price) = trade_factory()
    stock1.record_trade(timestamp, quantity, buy_sell, trade_price)

    expected_all_share_index = stock1.stock_price
    assert expected_all_share_index == stock_manager.all_share_index
