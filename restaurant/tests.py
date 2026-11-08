from decimal import Decimal
from unittest.mock import Mock, patch
from django.core.cache import cache
from django.test import Client, TestCase, SimpleTestCase, override_settings
from django.urls import reverse
from . import api

PRODUCTS = [
    {'id':1,'name':'Salad','price':Decimal('9.50'),'image':'https://example.com/salad.png','spiciness':0,'nuts':False,'vegeterian':True,'categoryId':1},
    {'id':2,'name':'Chicken','price':Decimal('14.00'),'image':'https://example.com/chicken.png','spiciness':4,'nuts':True,'vegeterian':False,'categoryId':2},
]
CATEGORIES = [{'id':1,'name':'Salads'},{'id':2,'name':'Chicken-Dishes'}]

@override_settings(STORAGES={'default':{'BACKEND':'django.core.files.storage.FileSystemStorage'},'staticfiles':{'BACKEND':'django.contrib.staticfiles.storage.StaticFilesStorage'}})
class RestaurantTests(TestCase):
    def setUp(self):
        patcher = patch('restaurant.api.get_products', return_value=PRODUCTS)
        self.products_mock = patcher.start(); self.addCleanup(patcher.stop)
        patcher = patch('restaurant.api.get_categories', return_value=CATEGORIES)
        patcher.start(); self.addCleanup(patcher.stop)

    def test_menu_renders_all_required_attributes(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code,200)
        self.assertContains(response, 'Salad')
        self.assertContains(response, 'სიცხარე 0/4')
        self.assertContains(response, 'ნიგვზიანი: არა')
        self.assertContains(response, 'ვეგეტარიანული: კი')

    def test_combined_filters_include_zero_and_false(self):
        response = self.client.get('/', {'categoryId':'1','spiciness':'0','nuts':'false','vegeterian':'true'})
        self.assertEqual([p['id'] for p in response.context['products']], [1])
        response = self.client.get('/', {'nuts':'true','vegeterian':'false'})
        self.assertEqual([p['id'] for p in response.context['products']], [2])
        response = self.client.get('/', {'categoryId':'1','spiciness':'4'})
        self.assertEqual(response.context['products'], [])

    def test_invalid_filter_rejected(self):
        self.assertEqual(self.client.get('/', {'spiciness':'9'}).status_code,400)
        self.assertEqual(self.client.get('/', {'nuts':'maybe'}).status_code,400)

    def test_cart_prices_are_server_sourced_and_persist(self):
        self.client.post(reverse('restaurant:add', args=[1]), {'price':'0.01','name':'Forged'})
        self.client.post(reverse('restaurant:add', args=[1]))
        self.client.post(reverse('restaurant:add', args=[2]))
        response = self.client.get(reverse('restaurant:cart'))
        self.assertEqual(response.context['total_price'], Decimal('33.00'))
        self.assertEqual(response.context['total_quantity'],3)
        self.assertEqual(self.client.session['cart'], {'1':2,'2':1})
        self.assertNotContains(response,'Forged')
        self.assertEqual(Client().get(reverse('restaurant:cart')).context['total_quantity'],0)

    def test_quantity_update_and_ajax_total(self):
        self.client.post(reverse('restaurant:add', args=[1]))
        response = self.client.post(reverse('restaurant:update', args=[1]), {'quantity':'3'}, HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json()['cart_count'],3)
        self.assertIn('28.50',response.json()['html'])
        for invalid in ['0','-1','100','1.5','hello','']:
            with self.subTest(invalid=invalid):
                self.assertEqual(self.client.post(reverse('restaurant:update',args=[1]),{'quantity':invalid}).status_code,400)
                self.assertEqual(self.client.session['cart']['1'],3)

    def test_maximum_and_missing_product(self):
        session = self.client.session; session['cart']={'1':99}; session.save()
        self.assertEqual(self.client.post(reverse('restaurant:add',args=[1])).status_code,400)
        self.assertEqual(self.client.post(reverse('restaurant:add',args=[999])).status_code,404)
        self.assertEqual(self.client.post(reverse('restaurant:update',args=[2]),{'quantity':1}).status_code,404)

    def test_remove_clear_and_method_safety(self):
        self.client.post(reverse('restaurant:add', args=[1]))
        for name, args in [('add',[1]),('update',[1]),('remove',[1]),('clear',[])]:
            self.assertEqual(self.client.get(reverse('restaurant:'+name,args=args)).status_code,405)
        self.client.post(reverse('restaurant:remove',args=[1]))
        self.assertEqual(self.client.session['cart'],{})
        self.client.post(reverse('restaurant:add',args=[2]))
        self.client.post(reverse('restaurant:clear'))
        self.assertContains(self.client.get(reverse('restaurant:cart')),'კალათა ჯერ ცარიელია')

    def test_csrf_required(self):
        client=Client(enforce_csrf_checks=True)
        self.assertEqual(client.post(reverse('restaurant:add',args=[1])).status_code,403)
        client.get('/')
        token=client.cookies['csrftoken'].value
        self.assertEqual(client.post(reverse('restaurant:add',args=[1]),{'csrfmiddlewaretoken':token}).status_code,302)

    def test_outage_preserves_cart_and_clear_still_works(self):
        self.client.post(reverse('restaurant:add',args=[1]))
        self.products_mock.side_effect=api.CatalogUnavailable('Unavailable')
        self.assertEqual(self.client.get('/').status_code,503)
        self.assertEqual(self.client.get(reverse('restaurant:cart')).status_code,503)
        self.assertEqual(self.client.post(reverse('restaurant:update',args=[1]),{'quantity':3}).status_code,503)
        self.assertEqual(self.client.session['cart'],{'1':1})
        self.client.post(reverse('restaurant:clear'))
        self.assertEqual(self.client.session['cart'],{})

    def test_deleted_catalog_item_is_removed(self):
        session=self.client.session; session['cart']={'999':1,'1':2}; session.save()
        response=self.client.get(reverse('restaurant:cart'))
        self.assertEqual(response.context['total_price'],Decimal('19.00'))
        self.assertEqual(self.client.session['cart'],{'1':2})

    def test_names_are_escaped(self):
        self.products_mock.return_value=[{**PRODUCTS[0],'name':'<script>alert(1)</script>'}]
        response=self.client.get('/')
        self.assertContains(response,'&lt;script&gt;')
        self.assertNotContains(response,'<script>alert(1)</script>')

class ApiTests(SimpleTestCase):
    def setUp(self): cache.clear()

    @patch('restaurant.api.requests.get')
    def test_invalid_price_not_cached(self,get):
        response=Mock(); response.json.return_value=[{**PRODUCTS[0],'price':'NaN'}]; get.return_value=response
        with self.assertRaises(api.CatalogUnavailable): api.get_products()
        self.assertIsNone(cache.get('restaurant.products.v1'))

    @patch('restaurant.api.requests.get')
    def test_success_is_cached_and_uses_decimal(self,get):
        response=Mock(); response.json.return_value=[{**PRODUCTS[0],'price':9.5}]; get.return_value=response
        self.assertEqual(api.get_products()[0]['price'],Decimal('9.50'))
        api.get_products(); self.assertEqual(get.call_count,1)

    @patch('restaurant.api.requests.get')
    def test_transport_failure(self,get):
        import requests
        get.side_effect=requests.Timeout()
        with self.assertRaises(api.CatalogUnavailable): api.get_products()
