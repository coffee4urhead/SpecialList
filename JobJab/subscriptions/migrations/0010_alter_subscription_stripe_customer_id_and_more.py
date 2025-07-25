# Generated by Django 5.2.1 on 2025-07-19 15:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0009_subscriptionrecord_stripe_invoice_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subscription',
            name='stripe_customer_id',
            field=models.CharField(max_length=512, unique=True),
        ),
        migrations.AlterField(
            model_name='subscription',
            name='stripe_invoice_id',
            field=models.CharField(blank=True, help_text='The Stripe subscription ID', max_length=512, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='subscription',
            name='stripe_subscription_id',
            field=models.CharField(blank=True, help_text='The Stripe subscription ID', max_length=512, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='subscriptionrecord',
            name='stripe_customer_id',
            field=models.CharField(max_length=512),
        ),
        migrations.AlterField(
            model_name='subscriptionrecord',
            name='stripe_invoice_id',
            field=models.CharField(blank=True, help_text='The Stripe subscription ID', max_length=512, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='subscriptionrecord',
            name='stripe_price_id',
            field=models.CharField(max_length=512),
        ),
        migrations.AlterField(
            model_name='subscriptionrecord',
            name='stripe_subscription_id',
            field=models.CharField(max_length=512),
        ),
    ]
