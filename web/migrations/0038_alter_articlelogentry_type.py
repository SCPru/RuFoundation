# Generated by Django 5.0.6 on 2024-12-24 11:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0037_vote_visual_group'),
    ]

    operations = [
        migrations.AlterField(
            model_name='articlelogentry',
            name='type',
            field=models.TextField(choices=[('source', 'Source'), ('title', 'Title'), ('name', 'Name'), ('tags', 'Tags'), ('new', 'New'), ('parent', 'Parent'), ('file_added', 'Fileadded'), ('file_deleted', 'Filedeleted'), ('file_renamed', 'Filerenamed'), ('votes_deleted', 'Votesdeleted'), ('wikidot', 'Wikidot'), ('revert', 'Revert')], verbose_name='Тип'),
        ),
    ]