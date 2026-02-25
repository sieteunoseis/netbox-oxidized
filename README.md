# NetBox Oxidized Plugin

A NetBox plugin that displays [Oxidized](https://github.com/ytti/oxidized) device configuration backups directly in Device detail pages.

![NetBox Version](https://img.shields.io/badge/NetBox-4.0+-blue)
![Python Version](https://img.shields.io/badge/Python-3.10+-green)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![PyPI](https://img.shields.io/pypi/v/netbox-oxidized)](https://pypi.org/project/netbox-oxidized/)

## Features

- **Oxidized Tab** - Adds an "Oxidized" tab to Device detail pages
- **Config Display** - Shows the latest device configuration as code with copy button
- **Node Status** - Displays backup status, model, and last backup time
- **Link to Oxidized** - Direct link to the device's version history in Oxidized
- **Device Filtering** - Configurable by device role and manufacturer slugs
- **HTMX Loading** - Async content loading without blocking the page
- **Caching** - API responses cached to reduce load on Oxidized

## Requirements

- NetBox 4.0 or higher
- Python 3.10+
- Oxidized with REST API enabled

## Installation

### From PyPI (recommended)

```bash
pip install netbox-oxidized
```

### Docker Installation

Add to your NetBox Docker requirements file:

```bash
# requirements-extra.txt
netbox-oxidized
```

## Configuration

Add the plugin to your NetBox configuration:

```python
# configuration.py or plugins.py

PLUGINS = [
    'netbox_oxidized',
]

PLUGINS_CONFIG = {
    'netbox_oxidized': {
        # Required: Oxidized REST API URL
        'oxidized_url': 'http://oxidized:8888',
        # Optional: External URL for browser links (if behind reverse proxy)
        'oxidized_external_url': 'https://oxidized.example.com',
        # API timeout in seconds
        'timeout': 30,
        # Cache duration in seconds
        'cache_timeout': 300,
        # SSL certificate verification
        'verify_ssl': False,
        # Device role slugs to show tab for (empty = all)
        'device_roles': ['voice-gateway'],
        # Manufacturer slugs to show tab for (empty = all)
        'manufacturers': ['cisco'],
    }
}
```

See the [Configuration wiki](https://github.com/sieteunoseis/netbox-oxidized/wiki/Configuration) for full details.

## Usage

Once installed and configured:

1. Navigate to any Device in NetBox that matches your filter criteria
2. Click the **Oxidized** tab
3. View the node status and latest configuration
4. Use the **Copy** button to copy the config
5. Click **Open in Oxidized** to view version history

## Documentation

Full documentation is available on the [Wiki](https://github.com/sieteunoseis/netbox-oxidized/wiki):

- [Installation](https://github.com/sieteunoseis/netbox-oxidized/wiki/Installation)
- [Configuration](https://github.com/sieteunoseis/netbox-oxidized/wiki/Configuration)
- [Troubleshooting](https://github.com/sieteunoseis/netbox-oxidized/wiki/Troubleshooting)

## Development

### Setup

```bash
git clone https://github.com/sieteunoseis/netbox-oxidized.git
cd netbox-oxidized
pip install -e ".[dev]"
```

### Code Style

```bash
black netbox_oxidized/
isort netbox_oxidized/
flake8 netbox_oxidized/
```

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for release history.

## Support

If you find this plugin helpful, consider supporting development:

[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-support-yellow?style=flat&logo=buy-me-a-coffee)](https://buymeacoffee.com/automatebldrs)

## License

Apache License 2.0 - See [LICENSE](LICENSE) for details.

## Author

sieteunoseis
