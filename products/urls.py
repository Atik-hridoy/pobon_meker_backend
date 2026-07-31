from django.urls import path
from .views import CategoryListAPIView, ProductListCreateAPIView, ProductDetailAPIView, BannerListCreateAPIView

urlpatterns = [
    path('categories/', CategoryListAPIView.as_view(), name='category-list'),
    path('banners/', BannerListCreateAPIView.as_view(), name='banner-list-create'),
    path('', ProductListCreateAPIView.as_view(), name='product-list-create'),
    path('<int:pk>/', ProductDetailAPIView.as_view(), name='product-detail'),
]
