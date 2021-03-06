# Generated by Django 2.0 on 2018-01-18 22:49

from django.db import migrations, models
import localflavor.us.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0009_alter_user_last_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='PSPUser',
            fields=[
                ('id', models.AutoField(auto_created=True,
                                        primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(
                    max_length=128, verbose_name='password')),
                ('is_superuser', models.BooleanField(default=False,
                                                     help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('email', models.EmailField(max_length=255,
                                            unique=True, verbose_name='email address')),
                ('first_name', models.CharField(max_length=128)),
                ('last_name', models.CharField(max_length=128)),
                ('is_active', models.BooleanField(default=True)),
                ('is_admin', models.BooleanField(default=False)),
                ('date_joined', models.DateTimeField(auto_now_add=True)),
                ('last_login', models.DateTimeField(auto_now=True)),
                ('dwolla_url', models.URLField(blank=True, null=True)),
                ('customer_type', models.CharField(
                    default='personal', max_length=32)),
                ('address1', models.CharField(max_length=50)),
                ('address2', models.CharField(blank=True, max_length=50, null=True)),
                ('city', models.CharField(max_length=128)),
                ('postal_code', localflavor.us.models.USZipCodeField(max_length=10)),
                ('state', localflavor.us.models.USStateField(max_length=2)),
                ('ssn_lastfour', models.CharField(max_length=4)),
                ('date_of_birth', models.DateField()),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
                                                  related_name='user_set', related_query_name='user', to='auth.Group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.',
                                                            related_name='user_set', related_query_name='user', to='auth.Permission', verbose_name='user permissions')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
