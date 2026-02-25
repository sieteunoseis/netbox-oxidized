"""URL configuration for NetBox Oxidized plugin."""

from django.urls import path

from . import views

urlpatterns = [
    path("settings/", views.SettingsView.as_view(), name="settings"),
    path("test-connection/", views.TestConnectionView.as_view(), name="test_connection"),
    path("device/<int:pk>/content/", views.DeviceOxidizedContentView.as_view(), name="device_content"),
]
