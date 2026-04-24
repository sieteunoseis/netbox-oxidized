from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Collect Oxidized statistics and save to database'

    def handle(self, *args, **options):
        from netbox_oxidized.jobs import collect_stats_now
        try:
            obj = collect_stats_now()
            self.stdout.write(self.style.SUCCESS(
                f'OK: {obj.devices_backed_up} devices, '
                f'{obj.config_lines_total} lines, '
                f'{obj.backup_size_human}'
            ))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error: {e}'))
