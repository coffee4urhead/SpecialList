# Generated by Django 5.2.1 on 2025-07-08 14:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0015_delete_availability'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='preferred_end',
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='customuser',
            name='preferred_start',
            field=models.TimeField(blank=True, null=True),
        ),
    ]
