from django.conf import settings
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Plan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
                ('tier', models.CharField(choices=[('free', 'Free'), ('starter', 'Starter'), ('pro', 'Pro'), ('enterprise', 'Enterprise')], max_length=20, unique=True)),
                ('price', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('is_active', models.BooleanField(default=True)),
                ('max_businesses', models.IntegerField(default=1)),
                ('max_services', models.IntegerField(default=10)),
                ('max_staff', models.IntegerField(default=5)),
                ('max_bookings_per_month', models.IntegerField(default=100)),
                ('max_calendar_views', models.IntegerField(default=500)),
                ('custom_themes', models.BooleanField(default=False)),
                ('analytics_enabled', models.BooleanField(default=True)),
                ('api_access', models.BooleanField(default=False)),
                ('priority_support', models.BooleanField(default=False)),
                ('custom_domain', models.BooleanField(default=False)),
                ('remove_branding', models.BooleanField(default=False)),
                ('stripe_price_id', models.CharField(blank=True, max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'db_table': 'platform_plans', 'ordering': ['price']},
        ),
        migrations.CreateModel(
            name='Announcement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('message', models.TextField()),
                ('announcement_type', models.CharField(choices=[('info', 'Information'), ('warning', 'Warning'), ('maintenance', 'Maintenance'), ('feature', 'New Feature'), ('update', 'Update')], default='info', max_length=20)),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('published', 'Published'), ('archived', 'Archived')], default='draft', max_length=20)),
                ('target_all', models.BooleanField(default=True)),
                ('target_plans', models.JSONField(blank=True, default=list)),
                ('published_at', models.DateTimeField(blank=True, null=True)),
                ('expires_at', models.DateTimeField(blank=True, null=True)),
                ('is_dismissible', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={'db_table': 'platform_announcements', 'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='UserUsage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bookings_this_month', models.IntegerField(default=0)),
                ('api_calls_this_month', models.IntegerField(default=0)),
                ('storage_used_mb', models.FloatField(default=0)),
                ('total_bookings', models.IntegerField(default=0)),
                ('total_revenue', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('last_reset', models.DateField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='usage', to=settings.AUTH_USER_MODEL)),
            ],
            options={'db_table': 'platform_user_usage'},
        ),
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(choices=[('user_create', 'User Created'), ('user_update', 'User Updated'), ('user_suspend', 'User Suspended'), ('user_delete', 'User Deleted'), ('user_activate', 'User Activated'), ('business_deactivate', 'Business Deactivated'), ('business_activate', 'Business Activated'), ('plan_change', 'Plan Changed'), ('payment_refund', 'Payment Refunded'), ('ticket_resolve', 'Ticket Resolved'), ('announcement_create', 'Announcement Created'), ('settings_update', 'Settings Updated')], max_length=30)),
                ('target_business_id', models.CharField(blank=True, max_length=50)),
                ('details', models.JSONField(default=dict)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('admin_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='audit_logs', to=settings.AUTH_USER_MODEL)),
                ('target_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='audit_entries', to=settings.AUTH_USER_MODEL)),
            ],
            options={'db_table': 'platform_audit_logs', 'ordering': ['-created_at']},
        ),
    ]
