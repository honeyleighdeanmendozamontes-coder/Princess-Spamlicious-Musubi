# Generated migration to add discount fields to Order model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('musubiapp', '0009_feedback_review'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='discount_amount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name='order',
            name='discount_details',
            field=models.TextField(blank=True, null=True),
        ),
    ]
