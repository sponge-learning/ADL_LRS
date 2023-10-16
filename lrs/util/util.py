import ast
import json
import urllib.request, urllib.parse, urllib.error
import urllib.parse
import uuid
from isodate.isodatetime import parse_datetime

from django.apps import apps
from django.contrib import admin
from django.contrib.admin.sites import AlreadyRegistered
from django.contrib.postgres.fields import JSONField # Field
from django.contrib.postgres.forms import JSONField as JSONFieldForm # Form
from django.contrib.postgres.forms.jsonb import InvalidJSONInput
from ..exceptions import ParamError

agent_ifps_can_only_be_one = ['mbox', 'mbox_sha1sum', 'openid', 'account']


def get_agent_ifp(data):
    ifp_sent = [a for a in agent_ifps_can_only_be_one if data.get(a, None) != None]

    ifp = ifp_sent[0]
    canonical_version = data.get('canonical_version', True)
    ifp_dict = {'canonical_version': canonical_version}

    if not 'account' == ifp:
        ifp_dict[ifp] = data[ifp]
    else:
        if not isinstance(data['account'], dict):
            account = json.loads(data['account'])
        else:
            account = data['account']

        ifp_dict['account_homePage'] = account['homePage']
        ifp_dict['account_name'] = account['name']
    return ifp_dict


def convert_to_utc(timestr):
    try:
        date_object = parse_datetime(timestr)
    except ValueError as e:
        raise ParamError("There was an error while parsing the date from %s -- Error: %s" % (timestr, e.message))
    return date_object


def convert_to_dict(incoming_data):
    data = {}
    # GET data will be non JSON string-have to try literal_eval
    if type(incoming_data) == dict:
        return incoming_data
    try:
        data = json.loads(incoming_data)
    except Exception:
        try:
            data = ast.literal_eval(incoming_data)
        except Exception:
            data = incoming_data
    return data


def convert_post_body_to_dict(incoming_data):
    qs = urllib.parse.parse_qsl(urllib.parse.unquote_plus(incoming_data))
    return dict((k, v) for k, v in qs)


def get_lang(langdict, lang):
    if lang:
        # Return where key = lang
        try:
            return {lang: langdict[lang]}
        except KeyError:
            pass

    first = next(iter(langdict.items()))
    return {first[0]: first[1]}


def autoregister(*app_list):
    for app_name in app_list:
        application = apps.get_app_config(app_name)
        for model in application.get_models():
            try:
                admin.site.register(model)
            except AlreadyRegistered:
                pass


def get_default_uuid_string():
    return str(uuid.uuid4())


class CustomFormLRSJSONField(JSONFieldForm):
    def bound_data(self, data, initial):
        if self.disabled:
            return initial
        # Added this condition to make json.loads(data) work
        if data == None:
            data = ''
        try:
                return json.loads(data)
        except json.JSONDecodeError:
            return InvalidJSONInput(data)


class CustomLRSJSONField(JSONField):
    def formfield(self, **kwargs):
        return super().formfield(**{
            'form_class': CustomFormLRSJSONField,
            **kwargs,
        })