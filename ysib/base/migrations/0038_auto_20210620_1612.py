# Generated by Django 2.2.22 on 2021-06-20 16:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0037_valf_montaj_sibop'),
    ]

    operations = [
        migrations.AlterField(
            model_name='valf_montaj',
            name='sibop',
            field=models.PositiveIntegerField(default=1, null=True),
        ),
    ]
