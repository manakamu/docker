# Generated by Django 2.2.2 on 2020-06-12 12:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pole', '0003_auto_20200606_2311'),
    ]

    operations = [
        migrations.CreateModel(
            name='Log',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(verbose_name='日時')),
                ('log', models.IntegerField(verbose_name='ログ')),
            ],
        ),
    ]
