from django.urls import path

from . import views

urlpatterns = [
    path('auth/csrf/', views.CsrfView.as_view()),
    path('auth/register/', views.RegisterView.as_view()),
    path('auth/login/', views.LoginView.as_view()),
    path('auth/logout/', views.LogoutView.as_view()),
    path('me/', views.MeView.as_view()),
    path('receipts/', views.ReceiptListCreateView.as_view()),
    path('products/', views.ProductListView.as_view()),
]
