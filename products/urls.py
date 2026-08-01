from django.urls import path
from .views import CategoryListCreateAPIView, ProductListCreateAPIView, ProductDetailAPIView, BannerListCreateAPIView, PublicProductListAPIView, ProductReviewListCreateView, BestSellingProductsAPIView

urlpatterns = [
    path('categories/', CategoryListCreateAPIView.as_view(), name='category-list-create'),
    path('banners/', BannerListCreateAPIView.as_view(), name='banner-list-create'),
    path('public/', PublicProductListAPIView.as_view(), name='public-product-list'),
    path('best-sellers/', BestSellingProductsAPIView.as_view(), name='best-sellers'),
    path('', ProductListCreateAPIView.as_view(), name='product-list-create'),
    path('<int:pk>/', ProductDetailAPIView.as_view(), name='product-detail'),
    path('<int:pk>/reviews/', ProductReviewListCreateView.as_view(), name='product-reviews'),
]
