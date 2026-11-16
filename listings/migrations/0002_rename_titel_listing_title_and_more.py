import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('listings', '0001_initial'),
        ('realtors', '0001_initial'),
    ]

    operations = [
        # Rename (not remove + add) so existing listing titles are kept
        migrations.RenameField(
            model_name='listing',
            old_name='titel',
            new_name='title',
        ),
        migrations.AlterField(
            model_name='listing',
            name='realtor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='realtors.realtor'),
        ),
        migrations.AlterField(
            model_name='listing',
            name='list_date',
            field=models.DateTimeField(blank=True, default=django.utils.timezone.now),
        ),
    ]
