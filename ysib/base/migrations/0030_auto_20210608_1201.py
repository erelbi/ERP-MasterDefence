# Generated by Django 2.2.22 on 2021-06-08 12:01

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0029_auto_20210608_1201'),
    ]

    operations = [
        migrations.RenameField(
            model_name='valf_final_montaj',
            old_name='uretim_seri_no',
            new_name='urun_seri_no',
        ),
    ]
