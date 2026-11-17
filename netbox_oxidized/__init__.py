"""
NetBox Oxidized Plugin

Displays device configuration backups from Oxidized on NetBox device detail pages.
"""

from netbox.plugins import PluginConfig

__version__ = "0.4.0"


class OxidizedConfig(PluginConfig):
    """Plugin configuration for NetBox Oxidized integration."""

    name = "netbox_oxidized"
    verbose_name = "Oxidized"
    description = "Display Oxidized configuration backups in NetBox device views"
    version = __version__
    author = "Jeremy Worden"
    author_email = "jeremy.worden@gmail.com"
    base_url = "oxidized"
    min_version = "4.0.0"
    max_version = "5.99"

    required_settings = []

    default_settings = {
        "top_level_menu": True,
        "tab_weight": 9005,
        "oxidized_url": "",
        "oxidized_external_url": "",
        "timeout": 30,
        "cache_timeout": 300,
        "verify_ssl": False,
        # Device filter - empty lists mean show for all
        "device_roles": [],
        "manufacturers": [],
    }

    def ready(self):
        super().ready()
        from . import widgets  # noqa: F401


config = OxidizedConfig
