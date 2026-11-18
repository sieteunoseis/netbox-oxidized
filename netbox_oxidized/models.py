"""
models.py
"""

from django.db import models
from django.utils import timezone


class OxidizedStats(models.Model):
    """Snapshots stats Oxidized."""

    collected_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        verbose_name="Save at",
    )

    # ── General counters ──────────────────────────────────────────────────
    total_devices = models.IntegerField(default=0, verbose_name="Total devices")
    devices_backed_up = models.IntegerField(default=0, verbose_name="Backuped")
    config_lines_total = models.IntegerField(default=0, verbose_name="Rows configs")
    backup_size_bytes = models.BigIntegerField(default=0, verbose_name="Size backup(bytes)")
    failed_devices = models.IntegerField(default=0, verbose_name="Unsuccessful / no attempts.")

    # ── Stats by group ─────────────────────────────────────────────────
    groups_data = models.JSONField(default=list, blank=True, verbose_name="Data by groups")

    # ── Stats by model ────────────────────────────────────────────────
    models_data = models.JSONField(default=list, blank=True, verbose_name="Data by models")

    # ── Top device (for graph "Number of config lines" / "Config size") ─
    top_devices_data = models.JSONField(default=list, blank=True, verbose_name="Top device")

    # ── Time collect ────────────────────────────────────────────────────────────
    collection_duration_ms = models.FloatField(
        null=True, blank=True, verbose_name="Time to collect (ms)"
    )

    class Meta:
        verbose_name = "Stats Oxidized"
        verbose_name_plural = "Stats Oxidized"
        ordering = ["-collected_at"]

    def __str__(self):
        return f"OxidizedStats @ {self.collected_at.strftime('%Y-%m-%d %H:%M:%S')}"

    # ── General property ───────────────────────────────────────────────────

    @property
    def backup_size_kb(self) -> float:
        return round(self.backup_size_bytes / 1024, 1)

    @property
    def backup_size_mb(self) -> float:
        return round(self.backup_size_bytes / (1024 * 1024), 2)

    @property
    def backup_size_human(self) -> str:
        if self.backup_size_bytes >= 1024 * 1024:
            return f"{self.backup_size_mb} MB"
        return f"{self.backup_size_kb} kB"