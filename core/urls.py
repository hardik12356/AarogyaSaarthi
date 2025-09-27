# core/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # ----------------------------
    # DASHBOARD & STATIC PAGES
    # ----------------------------
    path('', views.dashboard, name='dashboard'),
    path('home/', views.home, name='home'),
    path('help/', views.help, name='help'),
    path('contact/', views.contact, name='contact'),

    # ----------------------------
    # SYMPTOM REPORTING
    # ----------------------------
    path("report_symptoms/", views.report_symptoms, name="report_symptoms"),
    path("add-dummy-report/", views.add_dummy_report, name="add_dummy_report"),

    # ----------------------------
    # API ENDPOINTS
    # ----------------------------
    path("api/water/", views.api_water, name="api_water"),         # GET latest water data
    path("api/water/post/", views.water_api, name="water_api"),    # POST new water data
    path('api/summary/', views.api_summary, name='api_summary'),  # Village summary with predicted diseases
    path("api/alerts/", views.alerts_api, name="alerts_api"),      # Last 20 active alerts

    # ----------------------------
    # EDUCATIONAL MODULES
    # ----------------------------
    path('modules/', views.educational_modules, name='educational_modules'),

    # ----------------------------
    # AUTHENTICATION
    # ----------------------------
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]
