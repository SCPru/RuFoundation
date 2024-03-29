# Generated by Django 4.0.6 on 2022-08-16 01:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0010_update_rimg_syntax'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='category',
            options={'verbose_name': 'Настройки категории', 'verbose_name_plural': 'Настройки категории'},
        ),
        migrations.AddField(
            model_name='article',
            name='media_name',
            field=models.TextField(null=True, verbose_name='Название папки с файлами в ФС-хранилище'),
        ),
        migrations.AlterField(
            model_name='category',
            name='users_can_delete',
            field=models.BooleanField(default=False, verbose_name='Пользователи могут удалять статьи'),
        ),
        migrations.AlterField(
            model_name='settings',
            name='category',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='_settings', to='web.category'),
        ),
        migrations.AlterField(
            model_name='settings',
            name='site',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='_settings', to='web.site'),
        ),
    ]
