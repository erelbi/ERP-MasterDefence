# Generated by Django 2.2.22 on 2021-05-26 19:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0020_auto_20210526_2237'),
    ]

    operations = [
        migrations.AddField(
            model_name='valf_fm200',
            name='uygunluk',
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
    ]
