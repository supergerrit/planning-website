# Generated by Django 4.0.3 on 2022-03-27 13:30

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('PlanningViewer', '0010_alter_overurenajust_year'),
    ]

    operations = [
        migrations.CreateModel(
            name='Mutatie',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('field', models.CharField(choices=[('voornaam', 'Voornaam'), ('achternaam', 'Achternaam'), ('colors', 'Colors')], max_length=64)),
                ('before', models.CharField(max_length=64)),
                ('after', models.CharField(max_length=64)),
            ],
        ),
        migrations.AlterField(
            model_name='overurenajust',
            name='year',
            field=models.IntegerField(default=2022, validators=[django.core.validators.MaxValueValidator(2030), django.core.validators.MinValueValidator(2019)]),
        ),
    ]
