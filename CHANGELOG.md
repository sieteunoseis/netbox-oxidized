# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.4.0] - 2026-11-17

### Added
- `tab_weight` setting (default `9005`) to control where this plugin's tab sits on object pages, so tab order can be set in config instead of code
- `top_level_menu` setting (default `True`); set `False` to list this plugin's menu items under the shared "Plugins" menu instead of its own top-level sidebar menu

### Changed
- Plugin display name shortened to "Oxidized" (was "NetBox Oxidized") so it matches the sidebar menu label

## [0.3.0] - 2026-03-09

### Added
- Dashboard widget: Oxidized Backup Status showing backup freshness summary
  - Configurable staleness thresholds (default: 24h stale, 7d critical)
  - Color-coded badges: recent (green), stale (yellow), critical (red), failed (dark), never (gray)
  - HTMX async loading for non-blocking dashboard page loads
  - Configurable cache timeout
  - Link to Oxidized UI

## [0.1.0] - 2026-02-03

### Added
- Initial release
- Device tab view
- Virtual Machine tab view
- Settings page
- Caching support
