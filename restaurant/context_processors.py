from .cart import read_cart

def cart_count(request):
    return {'cart_count': sum(read_cart(request.session).values())}
