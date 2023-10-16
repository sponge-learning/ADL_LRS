# Generated by Django 3.0.14 on 2023-10-16 12:44

from django.db import migrations
import lrs.util.util


class Migration(migrations.Migration):

    dependencies = [
        ('lrs', '0002_auto_20230907_0731'),
    ]

    operations = [
        migrations.AlterField(
            model_name='activity',
            name='activity_definition_choices',
            field=lrs.util.util.CustomLRSJSONField(blank=True, default=dict),
        ),
        migrations.AlterField(
            model_name='activity',
            name='activity_definition_crpanswers',
            field=lrs.util.util.CustomLRSJSONField(blank=True, default=dict),
        ),
        migrations.AlterField(
            model_name='activity',
            name='activity_definition_description',
            field=lrs.util.util.CustomLRSJSONField(blank=True, default=dict),
        ),
        migrations.AlterField(
            model_name='activity',
            name='activity_definition_extensions',
            field=lrs.util.util.CustomLRSJSONField(blank=True, default=dict),
        ),
        migrations.AlterField(
            model_name='activity',
            name='activity_definition_name',
            field=lrs.util.util.CustomLRSJSONField(blank=True, default=dict),
        ),
        migrations.AlterField(
            model_name='activity',
            name='activity_definition_scales',
            field=lrs.util.util.CustomLRSJSONField(blank=True, default=dict),
        ),
        migrations.AlterField(
            model_name='activity',
            name='activity_definition_sources',
            field=lrs.util.util.CustomLRSJSONField(blank=True, default=dict),
        ),
        migrations.AlterField(
            model_name='activity',
            name='activity_definition_steps',
            field=lrs.util.util.CustomLRSJSONField(blank=True, default=dict),
        ),
        migrations.AlterField(
            model_name='activity',
            name='activity_definition_targets',
            field=lrs.util.util.CustomLRSJSONField(blank=True, default=dict),
        ),
        migrations.AlterField(
            model_name='statement',
            name='context_extensions',
            field=lrs.util.util.CustomLRSJSONField(blank=True, default=dict),
        ),
        migrations.AlterField(
            model_name='statement',
            name='full_statement',
            field=lrs.util.util.CustomLRSJSONField(),
        ),
        migrations.AlterField(
            model_name='statement',
            name='result_extensions',
            field=lrs.util.util.CustomLRSJSONField(blank=True, default=dict),
        ),
        migrations.AlterField(
            model_name='statementattachment',
            name='description',
            field=lrs.util.util.CustomLRSJSONField(blank=True, default=dict),
        ),
        migrations.AlterField(
            model_name='statementattachment',
            name='display',
            field=lrs.util.util.CustomLRSJSONField(blank=True, default=dict),
        ),
        migrations.AlterField(
            model_name='substatement',
            name='context_extensions',
            field=lrs.util.util.CustomLRSJSONField(blank=True, default=dict),
        ),
        migrations.AlterField(
            model_name='substatement',
            name='result_extensions',
            field=lrs.util.util.CustomLRSJSONField(blank=True, default=dict),
        ),
        migrations.AlterField(
            model_name='verb',
            name='display',
            field=lrs.util.util.CustomLRSJSONField(blank=True, default=dict),
        ),
    ]
