from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0025_projectworkerattendances_payment_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='projectworkerattendances',
            name='hours',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True, verbose_name='Hours Worked'),
        ),
    ]
