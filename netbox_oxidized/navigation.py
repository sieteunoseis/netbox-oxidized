"""Navigation menu items for NetBox Oxidized plugin."""

from netbox.plugins import PluginMenu, PluginMenuItem

menu = PluginMenu(
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
