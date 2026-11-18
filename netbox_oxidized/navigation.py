"""Navigation menu items for NetBox Oxidized plugin."""

from django.conf import settings
from netbox.plugins import PluginMenu, PluginMenuItem

_menu = PluginMenu(
    label="Oxidized",
    groups=(
        (
            "Configs",
            (
                PluginMenuItem(
                    link="plugins:netbox_oxidized:config_search",
                    link_text="Config Search",
                    permissions=["dcim.view_device"],
                ),
                PluginMenuItem(
                    link="plugins:netbox_oxidized:config_diff",
                    link_text="Config Diff",
                    permissions=["dcim.view_device"],
                ),
                PluginMenuItem(
                    link="plugins:netbox_oxidized:config_audit",
                    link_text="Config Audit",
                    permissions=["dcim.view_device"],
                ),

            ),
        ),
        (
           "Dashboard",
           (
                PluginMenuItem(
                link="plugins:netbox_oxidized:stats_collect",
                link_text="Statistics",
                permissions=["netbox_oxidized.superuser_required"],
                        ),
                    ),
                ),
        (
            "Settings",
            (
                PluginMenuItem(
                    link="plugins:netbox_oxidized:settings",
                    link_text="Configuration",
                    permissions=["netbox_oxidized.superuser_required"],
                ),
            ),
        ),
    ),
    icon_class="mdi mdi-file-document-outline",
)


# top_level_menu=False puts this plugin's items under the shared "Plugins" menu
# (grouped by plugin name) instead of its own top-level sidebar menu.
if settings.PLUGINS_CONFIG.get("netbox_oxidized", {}).get("top_level_menu", True):
    menu = _menu
else:
    menu_items = tuple(item for group in _menu.groups for item in group.items)
