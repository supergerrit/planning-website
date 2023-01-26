# Generated by Django 3.2.5 on 2021-07-24 14:41

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('PlanningViewer', '0009_auto_20201111_1720'),
    ]

    operations = [
        migrations.AlterField(
            model_name='overurenajust',
            name='year',
            field=models.IntegerField(default=2021, validators=[django.core.validators.MaxValueValidator(2030), django.core.validators.MinValueValidator(2019)]),
        ),
    ]