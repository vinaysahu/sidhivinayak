# Generated for the Add-Payment feature on Project Worker attendances.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0024_alter_projectworkers_project_id_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='projectworkerattendances',
            name='payment_date',
            field=models.DateField(blank=True, null=True, verbose_name='Last Payment Date'),
        ),
    ]
