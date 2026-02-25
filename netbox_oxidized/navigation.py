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
            "Settings",
            (
                PluginMenuItem(
                    link="plugins:netbox_oxidized:settings",
                    link_text="Configuration",
                    permissions=["dcim.view_device"],
                ),
            ),
        ),
    ),
    icon_class="mdi mdi-file-document-outline",
)
