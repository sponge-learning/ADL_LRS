import io
import email
import urllib.request, urllib.parse, urllib.error
import json
import itertools
from base64 import b64decode, b64encode
from isodate.isoerror import ISO8601Error
from isodate.isodatetime import parse_datetime

from django.http.multipartparser import MultiPartParser
from django.core.cache import caches

from .util import convert_to_dict, convert_post_body_to_dict
from .etag import get_etag_info
from .jws import JWS, JWSException
from ..exceptions import OauthUnauthorized, OauthBadRequest, ParamError, BadRequest
from ..models import Agent

from oauth_provider.utils import get_oauth_request, require_params
from oauth_provider.decorators import CheckOauth
from oauth_provider.store import store

att_cache = caches['attachment_cache']


def parse(request, more_id=None):
    r_dict = {}
    # Build headers from request in request dict
    r_dict['headers'] = get_headers(request.META)

    # Traditional authorization should be passed in headers
    r_dict['auth'] = {}

    # If we already have an authenticated Django user, use this instead of checking the Authorization header.
    if request.user.is_authenticated:
        user = request.user
        r_dict['auth'] = {
            'type': 'django',
            'user': user,
            'define': True,
            'authority': Agent.objects.retrieve_or_create(
                name=user.get_full_name(),
                account={
                    'homePage': request.build_absolute_uri('/'),
                    'name': '%s.%s:%s' % (user._meta.app_label, user._meta.object_name, user.pk),
                    },
                objectType='Agent',
                )[0],
            }
    elif 'Authorization' in r_dict['headers']:
        # OAuth will always be dict, not http auth. Set required fields for oauth module and type for authentication
        # module
        raise BadRequest("Oauth not supported")
    elif 'Authorization' in request.body.decode('utf-8') or 'HTTP_AUTHORIZATION' in request.body.decode('utf-8'):
        # Authorization could be passed into body if cross origin request
        r_dict['auth']['type'] = 'http'
    else:
        raise BadRequest("Request has no authorization")

    r_dict['params'] = {}
    # lookin for weird IE CORS stuff.. it'll be a post with a 'method' url param
    if request.method == 'POST' and 'method' in request.GET:
        bdy = convert_post_body_to_dict(request.body.decode('utf-8'))
        # 'content' is in body for the IE cors POST
        if 'content' in bdy:
            r_dict['body'] = urllib.parse.unquote(bdy.pop('content'))
        # headers are in the body too for IE CORS, we removes them
        r_dict['headers'].update(get_headers(bdy))
        for h in r_dict['headers']:
            bdy.pop(h, None)

        # remove extras from body
        bdy.pop('X-Experience-API-Version', None)
        bdy.pop('Content-Type', None)
        bdy.pop('If-Match', None)
        bdy.pop('If-None-Match', None)
        
        # all that should be left are params for the request, 
        # we adds them to the params object
        r_dict['params'].update(bdy)
        for k in request.GET:
            if k == 'method': # make sure the method param goes in the special method spot
                r_dict[k] = request.GET[k]
            else:
                r_dict['params'][k] = request.GET[k]
    # Just parse body for all non IE CORS stuff
    else:
        r_dict = parse_body(r_dict, request)
        # Update dict with any GET data
        r_dict['params'].update(request.GET.dict())

    # Method gets set for cors already
    if 'method' not in r_dict:
        # Differentiate GET and POST
        if request.method == "POST" and (request.path[6:] == 'statements' or request.path[6:] == 'statements/'):
            # Can have empty body for POST (acts like GET)
            if 'body' in r_dict:
                # If body is a list, it's a post
                if not isinstance(r_dict['body'], list):
                    if not isinstance(r_dict['body'], dict):
                        raise BadRequest("Cannot evaluate data into dictionary to parse -- Error: %s" % r_dict['body'])
                    # If actor verb and object not in body - means it's a GET or invalid POST
                    if not ('actor' in r_dict['body'] and 'verb' in r_dict['body'] and 'object' in r_dict['body']):
                        # If body keys are in get params - GET - else invalid request
                        if set(r_dict['body'].keys()).issubset(['statementId', 'voidedStatementId', 'agent', 'verb', 'activity', 'registration',
                            'related_activities', 'related_agents', 'since', 'until', 'limit', 'format', 'attachments', 'ascending']):
                            r_dict['method'] = 'GET'
                        else:
                            raise BadRequest("Statement is missing actor, verb, or object")
                    else:
                        r_dict['method'] = 'POST'
                else:
                    r_dict['method'] = 'POST'
            else:
                r_dict['method'] = 'GET'
        else:
            r_dict['method'] = request.method

    # Set if someone is hitting the statements/more endpoint
    if more_id:
        r_dict['more_id'] = more_id
    return r_dict


def get_endpoint(request):
    # Used for OAuth scope
    endpoint = request.path[5:]
    # Since we accept with or without / on end
    if endpoint.endswith("/"):
        return endpoint[:-1]
    return endpoint   

def parse_attachment(r, request):
    # Email library insists on having the multipart header in the body - workaround
    message = request.body
    if 'boundary' not in message[:message.index("--")]:
        if 'boundary' in request.META['CONTENT_TYPE']:
            message = "Content-Type:" + request.META['CONTENT_TYPE'] + "\r\n" + message
        else:
            raise BadRequest("Could not find the boundary for the multipart content")

    msg = email.message_from_string(message)
    if msg.is_multipart():
        parts = msg.get_payload()
        stmt_part = parts.pop(0)
        if stmt_part['Content-Type'] != "application/json":
            raise ParamError("Content-Type of statement was not application/json")

        try:
            r['body'] = json.loads(stmt_part.get_payload())
        except Exception:
            raise ParamError("Statement was not valid JSON")

        # Find the signature sha2 from the list attachment values in the statements (there should only be one)
        if isinstance(r['body'], list):
            signature_att = list(itertools.chain(*[[a.get('sha2', None) for a in s['attachments'] if a.get('usageType', None) == "http://adlnet.gov/expapi/attachments/signature"] for s in r['body'] if 'attachments' in s]))
        else:        
            signature_att = [a.get('sha2', None) for a in r['body']['attachments'] if a.get('usageType', None) == "http://adlnet.gov/expapi/attachments/signature" and 'attachments' in r['body']]

        # Get all sha2s from the request
        payload_sha2s = [p.get('X-Experience-API-Hash', None) for p in msg.get_payload()]
        # Check each sha2 in payload, if even one of them is None then there is a missing hash
        for sha2 in payload_sha2s:
            if not sha2:
                raise BadRequest("X-Experience-API-Hash header was missing from attachment")

        # Check the sig sha2 in statements if it not in the payload sha2s then the sig sha2 is missing
        for sig in signature_att:
            if sig:
                if sig not in payload_sha2s:
                    raise BadRequest("Signature attachment is missing from request")
            else:
                raise BadRequest("Signature attachment is missing from request")   

        # We know all sha2s are there so set it and loop through each payload
        r['payload_sha2s'] = payload_sha2s
        for part in msg.get_payload():
            xhash = part.get('X-Experience-API-Hash')
            c_type = part['Content-Type']
            # Payloads are base64 encoded implictly from email lib (except for plaintext)
            if "text/plain" in c_type:
                payload = b64encode(part.get_payload())
            else:
                payload = part.get_payload()
            att_cache.set(xhash, payload)
    else:
        raise ParamError("This content was not multipart for the multipart request.")
    # See if the posted statements have attachments
    att_stmts = []
    if isinstance(r['body'], list):
        for s in r['body']:
            if 'attachments' in s:
                att_stmts.append(s)
    elif 'attachments' in r['body']:
        att_stmts.append(r['body'])
    if att_stmts:
        # find if any of those statements with attachments have a signed statement
        signed_stmts = [(s,a) for s in att_stmts for a in s.get('attachments', None) if a['usageType'] == "http://adlnet.gov/expapi/attachments/signature"]
        for ss in signed_stmts:
            attmnt = b64decode(att_cache.get(ss[1]['sha2']))
            jws = JWS(jws=attmnt)
            try:
                if not jws.verify() or not jws.validate(ss[0]):
                    raise BadRequest("The JSON Web Signature is not valid")
            except JWSException as jwsx:
                raise BadRequest(jwsx)

def parse_body(r, request):
    if request.method == 'POST' or request.method == 'PUT':
        # Parse out profiles/states if the POST dict is not empty
        if 'multipart/form-data' in request.META['CONTENT_TYPE']:
            if list(request.POST.dict().keys()):
                r['params'].update(request.POST.dict())
                parser = MultiPartParser(request.META, io.StringIO(request.raw_post_data),request.upload_handlers)
                post, files = parser.parse()
                r['files'] = files
        # If it is multipart/mixed, parse out all data
        elif 'multipart/mixed' in request.META['CONTENT_TYPE']: 
            parse_attachment(r, request)
        # Normal POST/PUT data
        else:
            if request.body:
                # profile uses the request body
                r['raw_body'] = request.body.decode('utf-8')
                # Body will be some type of string, not necessarily JSON
                r['body'] = convert_to_dict(request.body.decode('utf-8'))
            else:
                raise BadRequest("No body in request")
    return r

def get_headers(headers):
    r = {}
    if 'HTTP_UPDATED' in headers:
        try:
            r['updated'] = parse_datetime(headers['HTTP_UPDATED'])
        except (Exception, ISO8601Error):
            raise ParamError("Updated header was not a valid ISO8601 timestamp")        
    elif 'updated' in headers:
        try:
            r['updated'] = parse_datetime(headers['updated'])
        except (Exception, ISO8601Error):
            raise ParamError("Updated header was not a valid ISO8601 timestamp")

    r['CONTENT_TYPE'] = headers.get('CONTENT_TYPE', '')
    if r['CONTENT_TYPE'] == '' and 'Content-Type' in headers:
        r['CONTENT_TYPE'] = headers['Content-Type']
    # FireFox automatically adds ;charset=foo to the end of headers. This will strip it out
    if ';' in r['CONTENT_TYPE']:
        r['CONTENT_TYPE'] = r['CONTENT_TYPE'].split(';')[0]

    r['ETAG'] = get_etag_info(headers, required=False)
    if 'HTTP_AUTHORIZATION' in headers:
        r['Authorization'] = headers.get('HTTP_AUTHORIZATION', None)
    elif 'Authorization' in headers:
        r['Authorization'] = headers.get('Authorization', None)

    if 'Accept_Language' in headers:
        r['language'] = headers.get('Accept_Language', None)
    elif 'Accept-Language' in headers:
        r['language'] = headers['Accept-Language']

    if 'X-Experience-API-Version' in headers:
            r['X-Experience-API-Version'] = headers['X-Experience-API-Version']
    return r
