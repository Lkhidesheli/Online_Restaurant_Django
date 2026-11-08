from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET, require_POST
from . import api
from .cart import cart_context, read_cart, write_cart
from .forms import FilterForm, QuantityForm

def wants_json(request):
    return request.headers.get('Accept') == 'application/json'

def failure(request, message, status=400):
    if wants_json(request):
        return JsonResponse({'error': message}, status=status)
    return render(request, 'restaurant/error.html', {'error': message}, status=status)

def result(request, message, products=None, destination='restaurant:cart'):
    if wants_json(request):
        data = {'message': message, 'cart_count': sum(read_cart(request.session).values())}
        if products is not None:
            context = cart_context(request.session, products)
            data['cart_count'] = context['total_quantity']
            data['html'] = render_to_string('restaurant/_cart.html', context, request=request)
        return JsonResponse(data)
    messages.success(request, message)
    return redirect(destination)

@require_GET
def menu(request):
    try:
        categories, products = api.get_categories(), api.get_products()
    except api.CatalogUnavailable as exc:
        return render(request, 'restaurant/menu.html', {'error':str(exc)}, status=503)
    form = FilterForm(request.GET, categories=categories)
    if not form.is_valid():
        return render(request, 'restaurant/menu.html', {'filter_form':form, 'products':[], 'invalid_filters':True}, status=400)
    for key, value in form.cleaned_data.items():
        if value != '':
            products = [p for p in products if (str(p[key]).lower() if type(p[key]) is bool else str(p[key])) == value]
    return render(request, 'restaurant/menu.html', {'filter_form':form, 'products':products})

@require_GET
def cart_detail(request):
    try:
        context = cart_context(request.session, api.get_products())
    except api.CatalogUnavailable as exc:
        return render(request, 'restaurant/cart.html', {'error':str(exc)}, status=503)
    if context['removed']:
        messages.info(request, 'მენიუდან ამოღებული კერძები კალათიდან წაიშალა.')
    return render(request, 'restaurant/cart.html', context)

@require_POST
def add(request, product_id):
    try:
        products = api.get_products()
    except api.CatalogUnavailable as exc:
        return failure(request, str(exc), 503)
    product = next((p for p in products if p['id'] == product_id), None)
    if product is None:
        return failure(request, 'კერძი ვერ მოიძებნა.', 404)
    cart = read_cart(request.session)
    key = str(product_id)
    if cart.get(key, 0) >= 99:
        return failure(request, 'ერთი კერძის მაქსიმალური რაოდენობაა 99.')
    cart[key] = cart.get(key, 0) + 1
    write_cart(request.session, cart)
    return result(request, f'{product["name"]} დაემატა კალათაში', destination='restaurant:menu')

@require_POST
def update(request, product_id):
    form = QuantityForm(request.POST)
    if not form.is_valid():
        return failure(request, ' '.join(form.errors['quantity']))
    cart = read_cart(request.session)
    key = str(product_id)
    if key not in cart:
        return failure(request, 'ეს კერძი კალათაში არ არის.', 404)
    try:
        products = api.get_products()
    except api.CatalogUnavailable as exc:
        return failure(request, str(exc), 503)
    if not any(p['id'] == product_id for p in products):
        return failure(request, 'კერძი მენიუში აღარ არის. განაახლე კალათა.', 404)
    cart[key] = form.cleaned_data['quantity']
    write_cart(request.session, cart)
    return result(request, 'რაოდენობა განახლდა.', products)

@require_POST
def remove(request, product_id):
    # An API outage must not prevent the visitor from removing a saved item.
    cart = read_cart(request.session)
    cart.pop(str(product_id), None)
    write_cart(request.session, cart)
    try:
        products = api.get_products()
    except api.CatalogUnavailable:
        if wants_json(request):
            return JsonResponse({'reload':True})
        return redirect('restaurant:cart')
    return result(request, 'კერძი წაიშალა.', products)

@require_POST
def clear(request):
    write_cart(request.session, {})
    return result(request, 'კალათა გასუფთავდა.', [])
