
from django.db import migrations


class Migration(migrations.Migration):
    
    dependencies = [
        ('web', '0042_alter_articlelogentry_type_and_more'),
    ]

    operations = [migrations.RunSQL("""
        DO $$
        DECLARE
            rec RECORD;
            old_table_name TEXT;
            new_table_name TEXT;
        BEGIN
            UPDATE public.django_content_type 
            SET app_label = 'web' 
            WHERE app_label = 'system';
                                            
            FOR rec IN
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                AND table_name LIKE 'system_%'
            LOOP
                old_table_name := rec.table_name;
                new_table_name := 'web_' || SUBSTRING(old_table_name FROM 8);
                                    
                EXECUTE FORMAT('DROP TABLE IF EXISTS %I;', new_table_name);
                EXECUTE FORMAT('ALTER TABLE %I RENAME TO %I;', old_table_name, new_table_name);
            END LOOP;
        END $$;
        """)
    ]
