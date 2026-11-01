from django.db import migrations, models
from django.db.models.functions import Lower


class Migration(migrations.Migration):

    dependencies = [
        ('lore', '0001_initial'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='loreentry',
            name='unique_entry_name',
        ),
        migrations.AddConstraint(
            model_name='loreentry',
            constraint=models.UniqueConstraint(
                Lower('entry_name'),
                name='unique_entry_name',
                violation_error_message='A lore entry with this name already exists.',
            ),
        ),
    ]
