"""Navigation menu items for NetBox Oxidized plugin."""

from netbox.plugins import PluginMenuItem

menu_items = (
    PluginMenuItem(
        link="plugins:netbox_oxidized:settings",
        link_text="Oxidized Settings",
        permissions=["dcim.view_device"],
    ),
)
