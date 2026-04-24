"""
Migration: add model OxidizedStats for save stats in db.
"""

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [

    ]

    operations = [
        migrations.CreateModel(
            name='OxidizedStats',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('collected_at', models.DateTimeField(
                    default=django.utils.timezone.now,
                    db_index=True,
                    verbose_name='Collect at'
                )),


                ('total_devices', models.IntegerField(default=0, verbose_name='Total Device')),
                ('devices_backed_up', models.IntegerField(default=0, verbose_name='Backups device')),
                ('config_lines_total', models.IntegerField(default=0, verbose_name='Rows config')),
                ('backup_size_bytes', models.BigIntegerField(default=0, verbose_name='Size backup (bytes)')),
                ('failed_devices', models.IntegerField(default=0, verbose_name='Unsuccessful / not yet attempted.')),


                ('groups_data', models.JSONField(default=list, blank=True, verbose_name='Data by group')),

                ('models_data', models.JSONField(default=list, blank=True, verbose_name='Data by models')),


                ('top_devices_data', models.JSONField(default=list, blank=True, verbose_name='Top device')),


                ('collection_duration_ms', models.FloatField(
                    null=True, blank=True,
                    verbose_name='Time to collect (ms)'
                )),
            ],
            options={
                'verbose_name': 'Stats Oxidized',
                'verbose_name_plural': 'Stats Oxidized',
                'ordering': ['-collected_at'],
            },
        ),
    ]
