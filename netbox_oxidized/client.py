"""API client for Oxidized REST API integration."""

import logging
from typing import Optional

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class OxidizedClient:
    """Client for Oxidized REST API with caching and error handling."""

    def __init__(self):
        """Initialize the client from plugin settings."""
        self.config = settings.PLUGINS_CONFIG.get("netbox_oxidized", {})
        self.base_url = self.config.get("oxidized_url", "").rstrip("/")
        self.timeout = self.config.get("timeout", 30)
        self.cache_timeout = self.config.get("cache_timeout", 300)
        self.verify_ssl = self.config.get("verify_ssl", False)

    def _make_request(self, endpoint: str, expect_json: bool = True):
        """Make request to Oxidized REST API.

        Args:
            endpoint: API endpoint path (e.g., 'nodes.json', 'node/fetch/hostname')
            expect_json: If True, parse response as JSON. If False, return text.

        Returns:
            Parsed JSON (dict or list), text string, or None on error.
        """
        url = f"{self.base_url}/{endpoint}"

        try:
            response = requests.get(
                url,
                timeout=self.timeout,
                verify=self.verify_ssl,
            )
            response.raise_for_status()
            if expect_json:
                return response.json()
            return response.text
        except requests.Timeout:
            logger.error(f"Oxidized API request timed out: {endpoint}")
            return None
        except requests.RequestException as e:
            logger.error(f"Oxidized API request failed: {e}")
            return None

    def _get_all_nodes(self) -> list:
        """Get all nodes from /nodes.json with caching."""
        cache_key = "netbox_oxidized_all_nodes"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        result = self._make_request("nodes.json")
        if result and isinstance(result, list):
            cache.set(cache_key, result, self.cache_timeout)
            return result

        return []

    def get_node(self, name: str) -> dict:
        """Get node status information by looking up in /nodes.json.

        Args:
            name: Device hostname.

        Returns:
            Dict with node info (name, model, status, last backup time) or error.
        """
        nodes = self._get_all_nodes()
        for node in nodes:
            if node.get("name") == name or node.get("full_name") == name:
                node["cached"] = False
                return node

        return {"error": f"Node '{name}' not found in Oxidized", "cached": False}

    def get_node_config(self, name: str) -> dict:
        """Get latest configuration for a node via /node/fetch/<name>.

        Args:
            name: Device hostname.

        Returns:
            Dict with 'config' key containing the config text, or 'error' key.
        """
        cache_key = f"netbox_oxidized_config_{name}"
        cached = cache.get(cache_key)
        if cached:
            cached["cached"] = True
            return cached

        config_text = self._make_request(f"node/fetch/{name}", expect_json=False)
        if config_text is not None:
            result = {"config": config_text, "cached": False}
            cache.set(cache_key, result, self.cache_timeout)
            return result

        return {"error": f"Config not found for '{name}'", "cached": False}

    def test_connection(self) -> tuple[bool, str]:
        """Test connection to Oxidized API.

        Returns:
            Tuple of (success, message).
        """
        result = self._make_request("nodes.json")
        if result is not None:
            if isinstance(result, list):
                return True, f"Connected. Managing {len(result)} nodes."
            return True, "Connected successfully."
        return False, f"Failed to connect to {self.base_url}"


def get_client() -> Optional[OxidizedClient]:
    """Get a configured client instance, or None if not configured."""
    config = settings.PLUGINS_CONFIG.get("netbox_oxidized", {})
    if not config.get("oxidized_url"):
        logger.warning("Oxidized URL not configured")
        return None
    return OxidizedClient()
