from django.urls import path
from . import views

app_name = 'restaurant'
urlpatterns = [
    path('', views.menu, name='menu'),
    path('cart/', views.cart_detail, name='cart'),
    path('cart/add/<int:product_id>/', views.add, name='add'),
    path('cart/update/<int:product_id>/', views.update, name='update'),
    path('cart/remove/<int:product_id>/', views.remove, name='remove'),
    path('cart/clear/', views.clear, name='clear'),
]
