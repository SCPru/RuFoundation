# Generated by Django 4.1.10 on 2024-05-11 18:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0035_current_users_are_editors'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='externallink',
            index=models.Index(fields=['link_from', 'link_to'], name='web_externa_link_fr_92155a_idx'),
        ),
        migrations.AddIndex(
            model_name='externallink',
            index=models.Index(fields=['link_type'], name='web_externa_link_ty_8f2d31_idx'),
        ),
    ]