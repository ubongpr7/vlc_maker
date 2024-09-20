# Generated by Django 4.2.13 on 2024-09-20 05:51

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('djstripe', '0012_2_8'),
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='StripeSubscription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateTimeField(help_text='The start date of the subscription.')),
                ('status', models.CharField(help_text='The status of this subscription.', max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='VlcPlan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('stripe_plan_id', models.CharField(max_length=100)),
                ('monthly_credits', models.IntegerField(default=10)),
            ],
        ),
        migrations.AddField(
            model_name='user',
            name='customer',
            field=models.ForeignKey(blank=True, help_text="The user's Stripe Customer object, if it exists", null=True, on_delete=django.db.models.deletion.SET_NULL, to='djstripe.customer'),
        ),
        migrations.AddField(
            model_name='user',
            name='subscription',
            field=models.ForeignKey(blank=True, help_text="The user's Stripe Subscription object, if it exists", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='subscriber', to='djstripe.subscription'),
        ),
        migrations.CreateModel(
            name='MyStripeModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('stripe_subscription', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='accounts.stripesubscription')),
            ],
        ),
        migrations.CreateModel(
            name='Credit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('credits', models.IntegerField(default=0)),
                ('last_reset', models.DateTimeField(auto_now_add=True)),
                ('product', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='djstripe.product')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]