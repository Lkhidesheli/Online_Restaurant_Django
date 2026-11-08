"""IT Step catalog. Only successfully validated responses are cached."""
from decimal import Decimal, InvalidOperation
from urllib.parse import urlparse
import requests
from django.core.cache import cache

API_BASE = 'https://restaurant.stepprojects.ge/api'

class CatalogUnavailable(Exception):
    pass

def _get(endpoint):
    try:
        response = requests.get(f'{API_BASE}/{endpoint}', timeout=(5, 15))
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, list):
            raise ValueError('Expected list')
        return data
    except (requests.RequestException, ValueError) as exc:
        raise CatalogUnavailable('კატალოგის სერვერი დროებით მიუწვდომელია. სცადე ხელახლა.') from exc

def get_products():
    cached = cache.get('restaurant.products.v1')
    if cached is not None:
        return cached
    result = []
    try:
        for item in _get('Products/GetAll'):
            price = Decimal(str(item['price']))
            if not price.is_finite() or price < 0:
                raise ValueError('Invalid price')
            if type(item['id']) is not int or item['id'] < 1 or not isinstance(item['name'], str):
                raise ValueError('Invalid product')
            if type(item['spiciness']) is not int or not 0 <= item['spiciness'] <= 4:
                raise ValueError('Invalid spiciness')
            if type(item['nuts']) is not bool or type(item['vegeterian']) is not bool or type(item['categoryId']) is not int:
                raise ValueError('Invalid properties')
            image = item.get('image') or ''
            if not isinstance(image, str) or urlparse(image).scheme != 'https':
                image = ''
            result.append({**item, 'price': price.quantize(Decimal('.01')), 'image': image})
        if len({p['id'] for p in result}) != len(result):
            raise ValueError('Duplicate IDs')
    except (KeyError, TypeError, ValueError, InvalidOperation) as exc:
        raise CatalogUnavailable('სერვერმა არასწორი მონაცემები დააბრუნა. სცადე ხელახლა.') from exc
    cache.set('restaurant.products.v1', result, 60)
    return result

def get_categories():
    cached = cache.get('restaurant.categories.v1')
    if cached is not None:
        return cached
    data = _get('Categories/GetAll')
    if not all(isinstance(c, dict) and type(c.get('id')) is int and isinstance(c.get('name'), str) for c in data):
        raise CatalogUnavailable('კატეგორიების მონაცემები არასწორია.')
    cache.set('restaurant.categories.v1', data, 300)
    return data
