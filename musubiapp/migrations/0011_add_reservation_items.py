# Generated migration for reservation items

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('musubiapp', '0010_add_discount_fields_to_order'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReservationItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='musubiapp.product')),
                ('reservation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='musubiapp.reservation')),
            ],
        ),
    ]
