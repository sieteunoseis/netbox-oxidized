"""Views for NetBox Oxidized plugin."""

import difflib
import logging
import json


from dcim.models import Device
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.views import View
from netbox.views import generic
from utilities.views import ViewTab, register_model_view
from django.contrib import messages
from django.shortcuts import redirect
from django.views.generic import TemplateView

from .client import get_client
from .widgets import get_backup_status_context
from .models import OxidizedStats


logger = logging.getLogger(__name__)


class SuperuserRequiredMixin(UserPassesTestMixin):
    """Restrict access to superusers only."""

    def test_func(self):
        return self.request.user.is_superuser


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


class SettingsView(SuperuserRequiredMixin, View):
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


class TestConnectionView(SuperuserRequiredMixin, View):
    """Test connection to Oxidized API."""

    def post(self, request):
        client = get_client()
        if not client:
            return JsonResponse({"success": False, "error": "Plugin not configured"}, status=400)

        success, message = client.test_connection()
        if success:
            return JsonResponse({"success": True, "message": message})
        return JsonResponse({"success": False, "error": message}, status=400)


class ConfigSearchView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Search across all Oxidized device configurations."""

    permission_required = "dcim.view_device"
    template_name = "netbox_oxidized/config_search.html"

    def get(self, request):
        query = request.GET.get("q", "").strip()
        results = []
        device_map = {}
        error = None
        config = settings.PLUGINS_CONFIG.get("netbox_oxidized", {})
        external_url = config.get("oxidized_external_url", config.get("oxidized_url", "")).rstrip("/")

        if query:
            client = get_client()
            if client:
                try:
                    results = client.search_configs(query)
                    # Map to NetBox devices and add URLs
                    if results:
                        device_names = [r["name"] for r in results]
                        devices = Device.objects.filter(name__in=device_names)
                        device_map = {d.name: d for d in devices}
                        for r in results:
                            device = device_map.get(r["name"])
                            if device:
                                r["device_url"] = device.get_absolute_url()
                except Exception as e:
                    logger.error(f"Config search error: {e}")
                    error = str(e)
            else:
                error = "Oxidized plugin not configured."

        return render(
            request,
            self.template_name,
            {
                "query": query,
                "results": results,
                "result_count": len(results),
                "error": error,
                "external_url": external_url,
            },
        )


class ConfigDiffView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Compare configurations of two devices side-by-side."""

    permission_required = "dcim.view_device"
    template_name = "netbox_oxidized/config_diff.html"

    def get(self, request):
        client = get_client()
        nodes = []
        error = None

        if client:
            try:
                nodes = client._get_all_nodes()
            except Exception as e:
                logger.error(f"Failed to fetch nodes for diff: {e}")
                error = str(e)
        else:
            error = "Oxidized plugin not configured."

        config = settings.PLUGINS_CONFIG.get("netbox_oxidized", {})
        external_url = config.get("oxidized_external_url", config.get("oxidized_url", "")).rstrip("/")

        device_a = request.GET.get("device_a", "")
        device_b = request.GET.get("device_b", "")
        diff_html = ""
        config_a = ""
        config_b = ""

        if device_a and device_b and client:
            try:
                config_a_data = client.get_node_config(device_a)
                config_b_data = client.get_node_config(device_b)
                config_a = config_a_data.get("config", "")
                config_b = config_b_data.get("config", "")

                if config_a and config_b:
                    diff = difflib.unified_diff(
                        config_a.splitlines(),
                        config_b.splitlines(),
                        fromfile=device_a,
                        tofile=device_b,
                        lineterm="",
                    )
                    diff_html = "\n".join(diff)
                elif not config_a:
                    error = f"Could not fetch config for {device_a}"
                elif not config_b:
                    error = f"Could not fetch config for {device_b}"
            except Exception as e:
                logger.error(f"Config diff error: {e}")
                error = str(e)

        # Map nodes to NetBox devices for linking
        node_names = sorted(set(n.get("name", "") for n in nodes if n.get("name")))

        return render(
            request,
            self.template_name,
            {
                "node_names": node_names,
                "device_a": device_a,
                "device_b": device_b,
                "diff_html": diff_html,
                "config_a": config_a,
                "config_b": config_b,
                "error": error,
                "external_url": external_url,
            },
        )


class ConfigAuditView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Run security audit on a device's Oxidized configuration."""

    permission_required = "dcim.view_device"
    template_name = "netbox_oxidized/config_audit.html"

    def get(self, request):
        client = get_client()
        nodes = []
        error = None

        if client:
            try:
                nodes = client._get_all_nodes()
            except Exception as e:
                logger.error(f"Failed to fetch nodes for audit: {e}")
                error = str(e)
        else:
            error = "Oxidized plugin not configured."

        config = settings.PLUGINS_CONFIG.get("netbox_oxidized", {})
        external_url = config.get("oxidized_external_url", config.get("oxidized_url", "")).rstrip("/")

        device_name = request.GET.get("device", "")
        audit_html = ""

        if device_name and client:
            try:
                config_data = client.get_node_config(device_name)
                config_text = config_data.get("config", "")

                if config_text:
                    from ciscoconfaudit import CiscoConfAudit
                    from rich.console import Console

                    # Use a wide console to avoid truncation of Status column
                    console = Console(record=True, width=160)
                    audit = CiscoConfAudit()
                    audit.console = console
                    audit.global_config(config_text)
                    audit.interface_config(config_text)
                    # Widen Status column on both tables
                    for table in [audit.global_table, audit.interface_table]:
                        if table and len(table.columns) > 1:
                            table.columns[1].min_width = 30
                    audit.get_report()
                    audit_html = console.export_html(inline_styles=True)
                    import re

                    # Strip Rich's full HTML document wrapper, keep only <body> content
                    body_match = re.search(r"<body[^>]*>(.*?)</body>", audit_html, re.DOTALL)
                    if body_match:
                        audit_html = body_match.group(1).strip()
                    # Fix unescaped angle brackets in check names
                    # (e.g. <domain>, <timezone>) that browser treats as HTML tags.
                    # Escape all < that are NOT part of real HTML tags (span, pre, code, /, br).
                    audit_html = re.sub(r"<(?!/?(span|pre|code|br)\b)", "&lt;", audit_html)
                    # Fix dark mode: replace hardcoded light-theme colors
                    audit_html = audit_html.replace(
                        "background-color: #ffffff", "background-color: transparent"
                    ).replace("color: #000000", "color: inherit")
                else:
                    error = config_data.get("error", f"No config available for {device_name}")
            except ImportError:
                error = "ciscoconfaudit package not installed. Add it to requirements-extra.txt."
            except Exception as e:
                logger.error(f"Config audit error for {device_name}: {e}")
                error = str(e)

        node_names = sorted(set(n.get("name", "") for n in nodes if n.get("name")))

        return render(
            request,
            self.template_name,
            {
                "node_names": node_names,
                "device_name": device_name,
                "audit_html": audit_html,
                "error": error,
                "external_url": external_url,
            },
        )


class WidgetBackupStatusContentView(LoginRequiredMixin, View):
    """HTMX endpoint that returns backup status widget content."""

    def get(self, request):
        stale_hours = int(request.GET.get("stale_hours", 24))
        critical_hours = int(request.GET.get("critical_hours", 168))

        context = get_backup_status_context(
            stale_hours=stale_hours,
            critical_hours=critical_hours,
        )

        return HttpResponse(
            render_to_string(
                "netbox_oxidized/widgets/backup_status_content.html",
                context,
                request=request,
            )
        )
class OxidizedStatsDashboardView(PermissionRequiredMixin, TemplateView):
    """
    Main dashboard stats Oxidized.

    URL: /plugins/oxidized/stats/
    Template: netbox_oxidized/stats_dashboard.html
    """

    permission_required = "netbox_oxidized.view_oxidizedstats"
    template_name = "netbox_oxidized/stats_dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # Last snapshot
        latest: OxidizedStats | None = OxidizedStats.objects.first()
        ctx["latest"] = latest

        if latest:
            ctx["groups_data_json"] = json.dumps(latest.groups_data)
            ctx["models_data_json"] = json.dumps(latest.models_data)
            ctx["top_devices_json"] = json.dumps(latest.top_devices_data)

            # Last N snapshots for graph
            history_qs = OxidizedStats.objects.order_by("collected_at").values(
                "collected_at",
                "devices_backed_up",
                "config_lines_total",
                "backup_size_bytes",
                "failed_devices",
            )[:200]
            ctx["history_json"] = json.dumps(
                [
                    {
                        "ts": s["collected_at"].strftime("%Y-%m-%dT%H:%M:%S"),
                        "backed": s["devices_backed_up"],
                        "lines": s["config_lines_total"],
                        "size": s["backup_size_bytes"],
                        "failed": s["failed_devices"],
                    }
                    for s in history_qs
                ]
            )
        else:
            ctx["groups_data_json"] = "[]"
            ctx["models_data_json"] = "[]"
            ctx["top_devices_json"] = "[]"
            ctx["history_json"] = "[]"

        # Count saved snapshot
        ctx["snapshot_count"] = OxidizedStats.objects.count()

        return ctx


class StatsCollectView(PermissionRequiredMixin, View):
    """
    POST → collect stats and return JSON. For "Update now" button.
    """

    permission_required = "netbox_oxidized.add_oxidizedstats"

    def get(self, request, *args, **kwargs):
        """GET — just collect info."""
        return self.post(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        from .jobs import collect_stats_now

        wants_json = "application/json" in request.META.get("HTTP_ACCEPT", "")

        try:
            obj = collect_stats_now()
            if wants_json:
                return JsonResponse(
                    {
                        "status": "ok",
                        "collected_at": obj.collected_at.isoformat(),
                        "devices_backed_up": obj.devices_backed_up,
                        "config_lines_total": obj.config_lines_total,
                        "backup_size_bytes": obj.backup_size_bytes,
                        "collection_duration_ms": obj.collection_duration_ms,
                    }
                )
            messages.success(
                request,
                f"Stats update: {obj.devices_backed_up} device, "
                f"{obj.config_lines_total} rows, {obj.backup_size_bytes // 1024} кБ.",
            )
        except Exception as exc:
            logger.exception("Error manual update stats")
            if wants_json:
                return JsonResponse({"status": "error", "detail": str(exc)}, status=500)
            messages.error(request, f"Error colect stats: {exc}")

        return redirect("plugins:netbox_oxidized:stats_dashboard")
