"""Views for NetBox Oxidized plugin."""

import logging

from dcim.models import Device
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.views import View
from netbox.views import generic
from utilities.views import ViewTab, register_model_view

from .client import get_client

logger = logging.getLogger(__name__)


def should_show_tab(obj):
    """Determine if Oxidized tab should be shown for this device.

    Checks device role and manufacturer against configured filters.
    Empty filter lists mean show for all devices.
    """
    config = settings.PLUGINS_CONFIG.get("netbox_oxidized", {})
    device_roles = config.get("device_roles", [])
    manufacturers = config.get("manufacturers", [])

    if device_roles and hasattr(obj, "role") and obj.role:
        if obj.role.slug not in device_roles:
            return False

    if manufacturers and hasattr(obj, "device_type") and obj.device_type:
        manufacturer_slug = obj.device_type.manufacturer.slug
        if manufacturer_slug not in manufacturers:
            return False

    return True


@register_model_view(Device, "oxidized", path="oxidized")
class DeviceOxidizedView(generic.ObjectView):
    """Oxidized tab view for Device detail pages. Renders HTMX loading spinner."""

    queryset = Device.objects.all()
    template_name = "netbox_oxidized/device_tab.html"
    tab = ViewTab(
        label="Oxidized",
        weight=9005,
        permission="dcim.view_device",
        hide_if_empty=False,
        visible=should_show_tab,
    )

    def get(self, request, pk):
        device = Device.objects.get(pk=pk)
        return render(
            request,
            self.template_name,
            {
                "object": device,
                "tab": self.tab,
            },
        )


class DeviceOxidizedContentView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """HTMX endpoint that returns Oxidized config content for async loading."""

    permission_required = "dcim.view_device"

    def get(self, request, pk):
        device = Device.objects.get(pk=pk)
        config = settings.PLUGINS_CONFIG.get("netbox_oxidized", {})
        external_url = config.get("oxidized_external_url", config.get("oxidized_url", "")).rstrip("/")

        client = get_client()
        node_info = {}
        config_data = {}
        error = None

        if client:
            try:
                node_info = client.get_node(device.name)
                if not node_info.get("error"):
                    config_data = client.get_node_config(device.name)
                else:
                    error = node_info.get("error")
            except Exception as e:
                logger.error(f"Error fetching Oxidized data for {device.name}: {e}")
                error = str(e)
        else:
            error = "Oxidized plugin not configured. Add oxidized_url to PLUGINS_CONFIG."

        return HttpResponse(
            render_to_string(
                "netbox_oxidized/device_tab_content.html",
                {
                    "object": device,
                    "node_info": node_info,
                    "config_text": config_data.get("config", ""),
                    "config_error": config_data.get("error"),
                    "error": error,
                    "external_url": external_url,
                    "cached": node_info.get("cached", False) or config_data.get("cached", False),
                },
                request=request,
            )
        )


class SettingsView(View):
    """Plugin settings page."""

    template_name = "netbox_oxidized/settings.html"

    def get(self, request):
        config = settings.PLUGINS_CONFIG.get("netbox_oxidized", {})
        client = get_client()

        return render(
            request,
            self.template_name,
            {
                "config": config,
                "configured": client is not None,
            },
        )


class TestConnectionView(View):
    """Test connection to Oxidized API."""

    def post(self, request):
        client = get_client()
        if not client:
            return JsonResponse({"success": False, "error": "Plugin not configured"}, status=400)

        success, message = client.test_connection()
        if success:
            return JsonResponse({"success": True, "message": message})
        return JsonResponse({"success": False, "error": message}, status=400)
