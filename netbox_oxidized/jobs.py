"""
jobs.py
"""

import time
import logging
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

from netbox.jobs import JobRunner
from .models import OxidizedStats

logger = logging.getLogger("netbox_oxidized.jobs")

MAX_SNAPSHOTS = 1000


class CollectOxidizedStatsJob(JobRunner):

    class Meta:
        name = "Collect Oxidized Statistics"

    def run(self, *args, **kwargs):
        from django.conf import settings
        from .client import get_client
        from django.core.cache import cache

        cfg = settings.PLUGINS_CONFIG.get("netbox_oxidized", {})
        if not cfg.get("oxidized_url"):
            self.log_warning("oxidized_url not settings.")
            return

        t0 = time.monotonic()
        try:
            client = get_client()
            cache.delete("netbox_oxidized_all_nodes")
            nodes = client._get_all_nodes()

            def fetch_one(node):
                name = node.get("name", "")
                try:
                    data = client.get_node_config(name)
                    cfg_text = data.get("config", "") or ""
                    return {
                        "name": name,
                        "lines": len(cfg_text.splitlines()),
                        "size": len(cfg_text.encode("utf-8")),
                    }
                except Exception:
                    return {"name": name, "lines": 0, "size": 0}

            config_map = {}
            with ThreadPoolExecutor(max_workers=10) as executor:
                for result in executor.map(fetch_one, nodes):
                    config_map[result["name"]] = result

            for node in nodes:
                cs = config_map.get(node.get("name", ""), {})
                node["_lines"] = cs.get("lines", 0)
                node["_size"] = cs.get("size", 0)

            stats = self._build_stats(nodes)
            stats["collection_duration_ms"] = round((time.monotonic() - t0) * 1000, 1)
            self._save(stats)
            self._rotate()
            self.log_success(
                f"Collect: {stats['devices_backed_up']} device, "
                f"{stats['config_lines_total']} rowd."
            )
        except Exception as exc:
            logger.exception("Error collect stats Oxidized")
            self.log_failure(f"Error: {exc}")
            raise

    @staticmethod
    def _build_stats(nodes: list) -> dict:
        total = len(nodes)
        backed_up = 0
        failed = 0
        total_lines = 0
        total_size = 0

        groups_count = defaultdict(int)
        models_lines = defaultdict(int)
        models_size = defaultdict(int)
        models_count = defaultdict(int)

        top_devices = []

        for node in nodes:
            last = node.get("last") or {}
            status = (last.get("status") or node.get("status") or "").lower()
            lines = int(node.get("_lines") or 0)
            size = int(node.get("_size") or 0)
            model = (node.get("model") or "unknown").strip()
            group = (node.get("group") or "").strip()
            full_name = node.get("full_name") or node.get("name") or ""

            if status == "success":
                backed_up += 1
            elif status in ("never", "fail", "timeout", "notconnected"):
                failed += 1

            total_lines += lines
            total_size += size

            if group:
                groups_count[group] += 1
            models_count[model] += 1
            models_lines[model] += lines
            models_size[model] += size

            top_devices.append({
                "name": full_name,
                "lines": lines,
                "size_bytes": size,
                "status": status,
                "last_backup": node.get("time") or last.get("end") or "",
                "model": model,
                "group": group,
            })

        top_devices.sort(key=lambda x: x["lines"], reverse=True)

        groups_data = []
        total_grouped = sum(groups_count.values()) or 1
        for gname, cnt in sorted(groups_count.items(), key=lambda x: -x[1]):
            groups_data.append({
                "name": gname,
                "count": cnt,
                "pct": round(cnt / total_grouped * 100),
            })

        models_data = []
        total_m = sum(models_count.values()) or 1
        total_l = total_lines or 1
        total_s = total_size or 1
        for mname, cnt in sorted(models_count.items(), key=lambda x: -x[1]):
            ml = models_lines[mname]
            ms = models_size[mname]
            models_data.append({
                "model": mname,
                "count": cnt,
                "pct": round(cnt / total_m * 100),
                "lines": ml,
                "lines_pct": round(ml / total_l * 100),
                "avg_lines": round(ml / cnt) if cnt else 0,
                "size_bytes": ms,
                "size_pct": round(ms / total_s * 100),
                "avg_size_bytes": round(ms / cnt) if cnt else 0,
            })

        return {
            "total_devices": total,
            "devices_backed_up": backed_up,
            "config_lines_total": total_lines,
            "backup_size_bytes": total_size,
            "failed_devices": failed,
            "groups_data": groups_data,
            "models_data": models_data,
            "top_devices_data": top_devices[:50],
        }

    @staticmethod
    def _save(stats: dict) -> OxidizedStats:
        return OxidizedStats.objects.create(**stats)

    @staticmethod
    def _rotate():
        qs = OxidizedStats.objects.order_by("-collected_at")
        if qs.count() > MAX_SNAPSHOTS:
            cutoff_id = qs[MAX_SNAPSHOTS - 1].pk
            OxidizedStats.objects.filter(pk__lt=cutoff_id).delete()


def collect_stats_now() -> OxidizedStats:
    from .client import get_client
    from django.core.cache import cache

    client = get_client()
    if not client:
        raise ValueError("oxidized_url is not configured in PLUGINS_CONFIG")

    t0 = time.monotonic()
    cache.delete("netbox_oxidized_all_nodes")
    nodes = client._get_all_nodes()

    if not nodes:
        raise ValueError("Oxidized return empty list.")

    def fetch_one(node):
        name = node.get("name", "")
        try:
            data = client.get_node_config(name)
            cfg_text = data.get("config", "") or ""
            return {
                "name": name,
                "lines": len(cfg_text.splitlines()),
                "size": len(cfg_text.encode("utf-8")),
            }
        except Exception:
            return {"name": name, "lines": 0, "size": 0}

    config_map = {}
    with ThreadPoolExecutor(max_workers=10) as executor:
        for result in executor.map(fetch_one, nodes):
            config_map[result["name"]] = result

    for node in nodes:
        cs = config_map.get(node.get("name", ""), {})
        node["_lines"] = cs.get("lines", 0)
        node["_size"] = cs.get("size", 0)

    stats = CollectOxidizedStatsJob._build_stats(nodes)
    stats["collection_duration_ms"] = round((time.monotonic() - t0) * 1000, 1)
    obj = CollectOxidizedStatsJob._save(stats)
    CollectOxidizedStatsJob._rotate()
    return obj
