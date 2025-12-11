from django.urls import path
from . import views

urlpatterns = [
    path('', views.calculator_view, name='calculator'),
    path('history/', views.history_view, name='history'),
    path('admin-panel/', views.admin_panel_view, name='admin-panel'),
    path('simple/', views.simple_calc_view, name='simple'),
    path('debug/', views.debug_view, name='debug'),
    path('test-csrf/', views.test_csrf_view, name='test-csrf'),
    
    path('api/register/', views.RegisterView.as_view(), name='register'),
    path('api/login/', views.LoginView.as_view(), name='login'),
    path('api/logout/', views.LogoutView.as_view(), name='logout'),
    path('api/profile/', views.ProfileView.as_view(), name='profile'),
    path('api/token/refresh/', views.TokenRefreshView.as_view(), name='token_refresh'),
    
    path('api/calculate/', views.CalculateView.as_view(), name='calculate'),
    path('api/calculations/', views.CalculationListView.as_view(), name='calculations-list'),
    path('api/calculations/<int:pk>/', views.CalculationDetailView.as_view(), name='calculation-detail'),
    path('api/admin/calculations/', views.AdminCalculationListView.as_view(), name='admin-calculations'),
    path('api/statistics/', views.statistics_view, name='statistics'),
    path('api/clear-history/', views.clear_history, name='clear-history'),
    path('api/get-csrf-token/', views.get_csrf_token, name='get-csrf-token'),
]