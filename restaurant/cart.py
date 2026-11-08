from decimal import Decimal

MAX_QUANTITY = 99

def read_cart(session):
    raw = session.get('cart', {})
    if not isinstance(raw, dict):
        return {}
    return {key: quantity for key, quantity in raw.items() if isinstance(key, str) and key.isascii() and key.isdigit() and int(key) > 0 and type(quantity) is int and 1 <= quantity <= MAX_QUANTITY}

def write_cart(session, cart):
    session['cart'] = cart

def cart_context(session, products):
    cart = read_cart(session)
    available = {str(p['id']): p for p in products}
    valid = {key: qty for key, qty in cart.items() if key in available}
    removed = len(valid) != len(cart)
    if removed:
        write_cart(session, valid)
    items = [{**available[key], 'quantity': qty, 'subtotal': available[key]['price'] * qty} for key, qty in valid.items()]
    return {'cart_items': items, 'total_price': sum((item['subtotal'] for item in items), Decimal('0.00')), 'total_quantity':sum(valid.values()), 'removed':removed}
