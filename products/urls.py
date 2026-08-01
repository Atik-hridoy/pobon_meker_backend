from django.urls import path
from .views import CategoryListAPIView, ProductListCreateAPIView, ProductDetailAPIView, BannerListCreateAPIView, PublicProductListAPIView, ProductReviewListCreateView

urlpatterns = [
    path('categories/', CategoryListAPIView.as_view(), name='category-list'),
    path('banners/', BannerListCreateAPIView.as_view(), name='banner-list-create'),
    path('public/', PublicProductListAPIView.as_view(), name='public-product-list'),
    path('', ProductListCreateAPIView.as_view(), name='product-list-create'),
    path('<int:pk>/', ProductDetailAPIView.as_view(), name='product-detail'),
    path('<int:pk>/reviews/', ProductReviewListCreateView.as_view(), name='product-reviews'),
]
