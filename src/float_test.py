from float_utils import *
from decimal import *

xx = [
    # uni, pre, dto, importe_odoo
    [30, 0.35, 25, 7.87],
    [95, 1.23, 30, 81.8],
    [41, 0.35, 30, 10.04],
    [25, 0.57, 34, 9.40],
    [9, 3.15, 30, 19.84],
    [71, 0.35, 30, 17.39],
    [70, 0.35, 25, 18.37],
    [1, 7.3,  35,  4.75],
    [15, 0.75, 30,  7.87],
    [70, 0.35, 25, 18.37],
    [250, 1.85, 33, 309.87],
]
lines = [
    {'qty': 30.0, 'price': 0.35, 'dto': 25.0, 'amount': 7.87},
    {'qty': 95.0, 'price': 1.23, 'dto': 30.0, 'amount': 81.8},
    {'qty': 41.0, 'price': 0.35, 'dto': 30.0, 'amount': 10.04},
    {'qty': 25.0, 'price': 0.57, 'dto': 34.0, 'amount': 9.40},
    {'qty': 9.0, 'price': 3.15, 'dto': 30.0, 'amount': 19.84},
    {'qty': 71.0, 'price': 0.35, 'dto': 30.0, 'amount': 17.39},
    {'qty': 70.0, 'price': 0.35, 'dto': 25.0, 'amount': 18.37},
    {'qty': 1.0, 'price': 7.3, 'dto': 35.0, 'amount': 4.75},
    {'qty': 15.0, 'price': 0.75, 'dto': 30.0, 'amount': 7.87},
    {'qty': 70.0, 'price': 0.35, 'dto': 25.0, 'amount': 18.37},
    {'qty': 250.0, 'price': 1.85, 'dto': 33.0, 'amount': 309.87},
]

for x in lines:
    total1 = x['price'] * (1 - (x['dto'] or 0.0) / 100) * x['qty']

    total2 = (x['qty'] *  x['price']) -  (x['qty'] *  x['price'] * x['dto'] / 100.0)

    tr1 = float_round(total1, 2)
    tr2 = float_round(total2, 2)

    tr1 = float_repr(tr1, 2)
    tr2 = float_repr(tr2, 2)

    # rounding = 0.010000  # Es el campo rounding de la tabla res_currency, este es el del EURO
    # print "%s\t=>\t%s\t:%f" % (x['amount'], float_round(total, precision_rounding=rounding), total)
    print "%s\t => \t%s \t%s \t:%f \t:%f" % (x['amount'], tr1, tr2, total1, total2)

print "...................."

for [qty, price, dto, amount] in xx:
    qty = float(qty)
    price = float(price)
    dto = float(dto)

    total1 = price * (1 - dto / 100.0) * qty

    total2 = qty * price - (qty * price * dto / 100.0)

    tr1 = float_round(total1, 2)
    tr2 = float_round(total2, 2)

    tr1 = float_repr(tr1, 2)
    tr2 = float_repr(tr2, 2)

    print "%s\t => \t%s \t%s \t:%f \t:%f" % (amount, tr1, tr2, total1, total2)

for [qty, price, dto, amount] in xx:
    qty = float(qty)
    price = float(price)
    dto = float(dto)

    total1 = Decimal(price * (1 - dto / 100.0) * qty)
    total2 = Decimal(qty * price - (qty * price * dto / 100.0))

    # https://pyformat.info
    print '{:>52}'.format(total1), '{:>52}'.format(total2)

print "Decimal......"
for [qty, price, dto, amount] in xx:
    qty = Decimal(qty)
    price = Decimal(price)
    dto = Decimal(dto)

    total1 = Decimal(price * (Decimal(1) - dto / Decimal(100.0)) * qty).quantize(Decimal("0.01"), ROUND_HALF_DOWN)
    total2 = Decimal(qty * price - (qty * price * dto / Decimal(100.0))).quantize(Decimal("0.01"), ROUND_HALF_DOWN)

    print total1, "\t", total2


