from django.urls import path
from .views import TrackProductView, MyRecentlyViewedView, ToggleWishlistView, MyWishlistView, UserRecommendationsView

urlpatterns = [
    path('track-view/', TrackProductView.as_view(), name='track_view'),
    path('recently-viewed/', MyRecentlyViewedView.as_view(), name='recently_viewed'),
    path('wishlist/toggle/', ToggleWishlistView.as_view(), name='toggle_wishlist'),
    path('wishlist/', MyWishlistView.as_view(), name='my_wishlist'),
    path('recommendations/', UserRecommendationsView.as_view(), name='user_recommendations'),
]
