from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('system', '0017_alter_user_visual_group'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                CREATE COLLATION IF NOT EXISTS unicode_ci (
                    provider = 'icu',
                    locale = 'en-u-ks-level2',
                    deterministic = false
                );
            """,
            reverse_sql="DROP COLLATION IF EXISTS unicode_ci;"
        ),
    ]
