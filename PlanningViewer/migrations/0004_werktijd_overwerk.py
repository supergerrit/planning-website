# Generated by Django 3.0.2 on 2020-03-19 13:15

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('PlanningViewer', '0003_werktijd_colors'),
    ]

    operations = [
        migrations.AddField(
            model_name='werktijd',
            name='overwerk',
            field=models.IntegerField(default=0),
        ),
    ]
