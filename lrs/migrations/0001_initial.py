# -*- coding: utf-8 -*-
# Generated by Django 1.9.13 on 2023-07-21 10:19
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django_extensions.db.fields
import jsonfield.fields
import lrs.models
import lrs.util.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Activity',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('activity_id', models.CharField(db_index=True, max_length=2083)),
                ('objectType', models.CharField(blank=True, default=b'Activity', max_length=8)),
                ('activity_definition_name', jsonfield.fields.JSONField(blank=True, default={})),
                ('activity_definition_description', jsonfield.fields.JSONField(blank=True, default={})),
                ('activity_definition_type', models.CharField(blank=True, max_length=2083)),
                ('activity_definition_moreInfo', models.CharField(blank=True, max_length=2083)),
                ('activity_definition_interactionType', models.CharField(blank=True, max_length=25)),
                ('activity_definition_extensions', jsonfield.fields.JSONField(blank=True, default={})),
                ('activity_definition_crpanswers', jsonfield.fields.JSONField(blank=True, default={})),
                ('activity_definition_choices', jsonfield.fields.JSONField(blank=True, default={})),
                ('activity_definition_scales', jsonfield.fields.JSONField(blank=True, default={})),
                ('activity_definition_sources', jsonfield.fields.JSONField(blank=True, default={})),
                ('activity_definition_targets', jsonfield.fields.JSONField(blank=True, default={})),
                ('activity_definition_steps', jsonfield.fields.JSONField(blank=True, default={})),
                ('canonical_version', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='ActivityProfile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('profileId', models.CharField(db_index=True, max_length=2083)),
                ('updated', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('activityId', models.CharField(db_index=True, max_length=2083)),
                ('profile', models.FileField(null=True, upload_to=b'activity_profile')),
                ('json_profile', models.TextField(blank=True)),
                ('content_type', models.CharField(blank=True, max_length=255)),
                ('etag', models.CharField(blank=True, max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='ActivityState',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('state_id', models.CharField(max_length=2083)),
                ('updated', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('state', models.FileField(null=True, upload_to=b'activity_state')),
                ('json_state', models.TextField(blank=True)),
                ('activity_id', models.CharField(db_index=True, max_length=2083)),
                ('registration_id', models.CharField(max_length=40)),
                ('content_type', models.CharField(blank=True, max_length=255)),
                ('etag', models.CharField(blank=True, max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='Agent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('objectType', models.CharField(blank=True, default=b'Agent', max_length=6)),
                ('name', models.CharField(blank=True, max_length=100)),
                ('mbox', models.CharField(db_index=True, max_length=128, null=True)),
                ('mbox_sha1sum', models.CharField(db_index=True, max_length=40, null=True)),
                ('openid', models.CharField(db_index=True, max_length=2083, null=True)),
                ('oauth_identifier', models.CharField(db_index=True, max_length=192, null=True)),
                ('canonical_version', models.BooleanField(default=True)),
                ('account_homePage', models.CharField(max_length=2083, null=True)),
                ('account_name', models.CharField(max_length=50, null=True)),
                ('member', models.ManyToManyField(null=True, related_name='_agent_member_+', to='lrs.Agent')),
            ],
        ),
        migrations.CreateModel(
            name='AgentProfile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('profileId', models.CharField(db_index=True, max_length=2083)),
                ('updated', models.DateTimeField(auto_now_add=True)),
                ('profile', models.FileField(null=True, upload_to=b'agent_profile')),
                ('json_profile', models.TextField(blank=True)),
                ('content_type', models.CharField(blank=True, max_length=255)),
                ('etag', models.CharField(blank=True, max_length=50)),
                ('agent', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lrs.Agent')),
            ],
        ),
        migrations.CreateModel(
            name='Statement',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('statement_id', lrs.util.fields.CustomUUIDField(blank=True, db_index=True, editable=False, max_length=36, unique=True, version=1)),
                ('result_success', models.NullBooleanField()),
                ('result_completion', models.NullBooleanField()),
                ('result_response', models.TextField(blank=True)),
                ('result_duration', models.CharField(blank=True, max_length=40)),
                ('result_score_scaled', models.FloatField(blank=True, null=True)),
                ('result_score_raw', models.FloatField(blank=True, null=True)),
                ('result_score_min', models.FloatField(blank=True, null=True)),
                ('result_score_max', models.FloatField(blank=True, null=True)),
                ('result_extensions', jsonfield.fields.JSONField(blank=True, default={})),
                ('stored', models.DateTimeField(db_index=True, default=lrs.models.now)),
                ('timestamp', models.DateTimeField(db_index=True, default=lrs.models.now)),
                ('voided', models.NullBooleanField(default=False)),
                ('context_registration', models.CharField(blank=True, db_index=True, max_length=40)),
                ('context_revision', models.TextField(blank=True)),
                ('context_platform', models.CharField(blank=True, max_length=50)),
                ('context_language', models.CharField(blank=True, max_length=50)),
                ('context_extensions', jsonfield.fields.JSONField(blank=True, default={})),
                ('context_statement', models.CharField(blank=True, max_length=40)),
                ('version', models.CharField(max_length=7)),
                ('full_statement', jsonfield.fields.JSONField()),
                ('actor', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='actor_statement', to='lrs.Agent')),
            ],
        ),
        migrations.CreateModel(
            name='StatementAttachment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('usageType', models.CharField(max_length=2083)),
                ('contentType', models.CharField(max_length=128)),
                ('length', models.PositiveIntegerField()),
                ('sha2', models.CharField(blank=True, max_length=128)),
                ('fileUrl', models.CharField(blank=True, max_length=2083)),
                ('payload', models.FileField(null=True, upload_to=b'attachment_payloads')),
                ('display', jsonfield.fields.JSONField(blank=True, default={})),
                ('description', jsonfield.fields.JSONField(blank=True, default={})),
            ],
        ),
        migrations.CreateModel(
            name='StatementContextActivity',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(max_length=8)),
                ('context_activity', models.ManyToManyField(to='lrs.Activity')),
                ('statement', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lrs.Statement')),
            ],
        ),
        migrations.CreateModel(
            name='StatementRef',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('object_type', models.CharField(default=b'StatementRef', max_length=12)),
                ('ref_id', models.CharField(max_length=40)),
            ],
        ),
        migrations.CreateModel(
            name='SubStatement',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('result_success', models.NullBooleanField()),
                ('result_completion', models.NullBooleanField()),
                ('result_response', models.TextField(blank=True)),
                ('result_duration', models.CharField(blank=True, max_length=40)),
                ('result_score_scaled', models.FloatField(blank=True, null=True)),
                ('result_score_raw', models.FloatField(blank=True, null=True)),
                ('result_score_min', models.FloatField(blank=True, null=True)),
                ('result_score_max', models.FloatField(blank=True, null=True)),
                ('result_extensions', jsonfield.fields.JSONField(blank=True, default={})),
                ('timestamp', models.DateTimeField(blank=True, default=lrs.models.now, null=True)),
                ('context_registration', models.CharField(blank=True, db_index=True, max_length=40)),
                ('context_revision', models.TextField(blank=True)),
                ('context_platform', models.CharField(blank=True, max_length=50)),
                ('context_language', models.CharField(blank=True, max_length=50)),
                ('context_extensions', jsonfield.fields.JSONField(blank=True, default={})),
                ('context_statement', models.CharField(blank=True, max_length=40)),
                ('actor', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='actor_of_substatement', to='lrs.Agent')),
                ('context_instructor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='substatement_context_instructor', to='lrs.Agent')),
                ('context_team', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='substatement_context_team', to='lrs.Agent')),
                ('object_activity', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='object_of_substatement', to='lrs.Activity')),
                ('object_agent', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='object_of_substatement', to='lrs.Agent')),
                ('object_statementref', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='object_of_substatement', to='lrs.StatementRef')),
            ],
        ),
        migrations.CreateModel(
            name='SubStatementContextActivity',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(max_length=8)),
                ('context_activity', models.ManyToManyField(to='lrs.Activity')),
                ('substatement', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lrs.SubStatement')),
            ],
        ),
        migrations.CreateModel(
            name='Verb',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('verb_id', models.CharField(db_index=True, max_length=2083, unique=True)),
                ('display', jsonfield.fields.JSONField(blank=True, default={})),
            ],
        ),
        migrations.AddField(
            model_name='substatement',
            name='verb',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='lrs.Verb'),
        ),
        migrations.AddField(
            model_name='statement',
            name='attachments',
            field=models.ManyToManyField(to='lrs.StatementAttachment'),
        ),
        migrations.AddField(
            model_name='statement',
            name='authority',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='authority_statement', to='lrs.Agent'),
        ),
        migrations.AddField(
            model_name='statement',
            name='context_instructor',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='statement_context_instructor', to='lrs.Agent'),
        ),
        migrations.AddField(
            model_name='statement',
            name='context_team',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='statement_context_team', to='lrs.Agent'),
        ),
        migrations.AddField(
            model_name='statement',
            name='object_activity',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='object_of_statement', to='lrs.Activity'),
        ),
        migrations.AddField(
            model_name='statement',
            name='object_agent',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='object_of_statement', to='lrs.Agent'),
        ),
        migrations.AddField(
            model_name='statement',
            name='object_statementref',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='object_of_statement', to='lrs.StatementRef'),
        ),
        migrations.AddField(
            model_name='statement',
            name='object_substatement',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='object_of_statement', to='lrs.SubStatement'),
        ),
        migrations.AddField(
            model_name='statement',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='statement',
            name='verb',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='lrs.Verb'),
        ),
        migrations.AddField(
            model_name='activitystate',
            name='agent',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lrs.Agent'),
        ),
        migrations.AddField(
            model_name='activity',
            name='authority',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='lrs.Agent'),
        ),
        migrations.AlterUniqueTogether(
            name='agent',
            unique_together=set([('mbox_sha1sum', 'canonical_version'), ('mbox', 'canonical_version'), ('openid', 'canonical_version'), ('oauth_identifier', 'canonical_version'), ('account_homePage', 'account_name', 'canonical_version')]),
        ),
    ]
