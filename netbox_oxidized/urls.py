"""URL configuration for NetBox Oxidized plugin."""

from django.urls import path

from . import views

urlpatterns = [
    path("settings/", views.SettingsView.as_view(), name="settings"),
    path("test-connection/", views.TestConnectionView.as_view(), name="test_connection"),
    path("search/", views.ConfigSearchView.as_view(), name="config_search"),
    path("diff/", views.ConfigDiffView.as_view(), name="config_diff"),
    path("audit/", views.ConfigAuditView.as_view(), name="config_audit"),
    path("device/<int:pk>/content/", views.DeviceOxidizedContentView.as_view(), name="device_content"),
]
