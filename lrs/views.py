import json
import logging
import urllib.request, urllib.parse, urllib.error
from base64 import b64decode

from django.conf import settings
from django.contrib.auth import logout, login, authenticate, get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import SuspiciousOperation, ValidationError
from django.urls import reverse
from django.db import transaction
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest, HttpResponseNotFound
from django.shortcuts import render
from django.utils.decorators import decorator_from_middleware
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods

from .exceptions import BadRequest, ParamError, Unauthorized, Forbidden, NotFound, Conflict, PreconditionFail, \
    OauthUnauthorized, OauthBadRequest
from .forms import ValidatorForm, RegisterForm, RegClientForm
from .models import Statement, Verb, Agent, Activity, StatementAttachment, ActivityState
from .util import req_validate, req_parse, req_process, XAPIVersionHeaderMiddleware, accept_middleware, \
    StatementValidator

from oauth_provider.consts import ACCEPTED, CONSUMER_STATES
from oauth_provider.models import Consumer, Token

User = get_user_model()

# This uses the lrs logger for LRS specific information
logger = logging.getLogger(__name__)
LOGIN_URL = "/accounts/login"


@decorator_from_middleware(accept_middleware.AcceptMiddleware)
@csrf_protect
def home(request):

    stats = {}
    stats['usercnt'] = User.objects.all().count()
    stats['stmtcnt'] = Statement.objects.all().count()
    stats['verbcnt'] = Verb.objects.all().count()
    stats['agentcnt'] = Agent.objects.filter().count()
    stats['activitycnt'] = Activity.objects.filter().count()

    if request.method == 'GET':
        form = RegisterForm()
        context = {"stats": stats, "form": form}
        return render(request, "home.html", context)


@decorator_from_middleware(accept_middleware.AcceptMiddleware)
@csrf_protect
def stmt_validator(request):
    if request.method == 'GET':
        form = ValidatorForm()
        return render(request, "validator.html", {"form": form})
    elif request.method == 'POST':
        form = ValidatorForm(request.POST)
        # Form should always be valid - only checks if field is required and that's handled client side
        if form.is_valid():
            # Once know it's valid JSON, validate keys and fields
            try:
                validator = StatementValidator.StatementValidator(form.cleaned_data['jsondata'])
                valid = validator.validate()
            except ParamError as e:
                clean_data = form.cleaned_data['jsondata']
                context = {"form": form, "error_message": e.message, "clean_data": clean_data}
                return render(request, "validator.html", context)
            else:
                clean_data = json.dumps(json.loads(form.cleaned_data['jsondata']), indent=4, sort_keys=True)
                context = {"form": form, "valid_message": valid, "clean_data": clean_data}
                return render(request, "validator.html", context)
    return render(request, "validator.html", {"form": form})


@decorator_from_middleware(accept_middleware.AcceptMiddleware)
def about(request):
    lrs_data = {
        "version": [settings.XAPI_VERSION],
        "extensions": {
            "xapi": {
                "statements":
                    {
                        "name": "Statements",
                        "methods": ["GET", "POST", "PUT", "HEAD"],
                        "endpoint": reverse('lrs.views.statements'),
                        "description": "Endpoint to submit and retrieve XAPI statements.",
                    },
                "activities":
                    {
                        "name": "Activities",
                        "methods": ["GET", "HEAD"],
                        "endpoint": reverse('lrs.views.activities'),
                        "description": "Endpoint to retrieve a complete activity object.",
                    },
                "activities_state":
                    {
                        "name": "Activities State",
                        "methods": ["PUT", "POST", "GET", "DELETE", "HEAD"],
                        "endpoint": reverse('lrs.views.activity_state'),
                        "description": "Stores, fetches, or deletes the document specified by the given stateId that exists in the context of the specified activity, agent, and registration (if specified).",
                    },
                "activities_profile":
                    {
                        "name": "Activities Profile",
                        "methods": ["PUT", "POST", "GET", "DELETE", "HEAD"],
                        "endpoint": reverse('lrs.views.activity_profile'),
                        "description": "Saves/retrieves/deletes the specified profile document in the context of the specified activity.",
                    },
                "agents":
                    {
                        "name": "Agents",
                        "methods": ["GET", "HEAD"],
                        "endpoint": reverse('lrs.views.agents'),
                        "description": "Returns a special, Person object for a specified agent.",
                    },
                "agents_profile":
                    {
                        "name": "Agent Profile",
                        "methods": ["PUT", "POST", "GET", "DELETE", "HEAD"],
                        "endpoint": reverse('lrs.views.agent_profile'),
                        "description": "Saves/retrieves/deletes the specified profile document in the context of the specified agent.",
                    }
            },
            "lrs": {
                "user_register":
                    {
                        "name": "User Registration",
                        "methods": ["POST"],
                        "endpoint": reverse('lrs.views.register'),
                        "description": "Registers a user within the LRS.",
                    },
                "client_register":
                    {
                        "name": "OAuth1 Client Registration",
                        "methods": ["POST"],
                        "endpoint": reverse('lrs.views.reg_client'),
                        "description": "Registers an OAuth client applicaton with the LRS.",
                    },
                "client_register2":
                    {
                        "name": "OAuth2 Client Registration",
                        "methods": ["POST"],
                        "endpoint": reverse('lrs.views.reg_client2'),
                        "description": "Registers an OAuth2 client applicaton with the LRS.",
                    }
            },
            "oauth":
                {
                    "initiate":
                        {
                            "name": "Oauth Initiate",
                            "methods": ["POST"],
                            "endpoint": reverse('oauth:oauth_provider.views.request_token'),
                            "description": "Authorize a client and return temporary credentials.",
                        },
                    "authorize":
                        {
                            "name": "Oauth Authorize",
                            "methods": ["GET"],
                            "endpoint": reverse('oauth:oauth_provider.views.user_authorization'),
                            "description": "Authorize a user for Oauth1.",
                        },
                    "token":
                        {
                            "name": "Oauth Token",
                            "methods": ["POST"],
                            "endpoint": reverse('oauth:oauth_provider.views.access_token'),
                            "description": "Provides Oauth token to the client.",
                        }
                },
            "oauth2":
                {
                    "authorize":
                        {
                            "name": "Oauth2 Authorize",
                            "methods": ["GET"],
                            "endpoint": reverse('oauth2:authorize'),
                            "description": "Authorize a user for Oauth2.",
                        },
                    "access_token":
                        {
                            "name": "Oauth2 Token",
                            "methods": ["POST"],
                            "endpoint": reverse('oauth2:access_token'),
                            "description": "Provides Oauth2 token to the client.",
                        }
                }
        }
    }
    return HttpResponse(json.dumps(lrs_data), content_type="application/json", status=200)


@csrf_protect
@require_http_methods(["POST", "GET"])
def register(request):
    if request.method == 'GET':
        form = RegisterForm()
        return render(request, "register.html", {"form": form})
    elif request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['username']
            pword = form.cleaned_data['password']
            email = form.cleaned_data['email']

            if not User.objects.filter(username__exact=name).count():
                if not User.objects.filter(email__exact=email).count():
                    user = User.objects.create_user(name, email, pword)
                else:
                    context = {"form": form, "error_message": "Email %s is already registered." % email}
                    return render(request, "register.html", context)
            else:
                context = {"form": form, "error_message": "User %s already exists." % name}
                return render(request, "register.html", context)

                # If a user is already logged in, log them out
            if request.user.is_authenticated:
                logout(request)

            new_user = authenticate(username=name, password=pword)
            login(request, new_user)
            return HttpResponseRedirect(reverse('lrs.views.home'))
        else:
            return render(request, "register.html", {"form": form})


@login_required(login_url=LOGIN_URL)
@require_http_methods(["GET"])
def admin_attachments(request, path):
    if request.user.is_superuser:
        try:
            att_object = StatementAttachment.objects.get(sha2=path)
        except StatementAttachment.DoesNotExist:
            raise HttpResponseNotFound("File not found")
        chunks = []
        try:
            # Default chunk size is 64kb
            for chunk in att_object.payload.chunks():
                decoded_data = b64decode(chunk)
                chunks.append(decoded_data)
        except OSError:
            return HttpResponseNotFound("File not found")

        response = HttpResponse(chunks, content_type=str(att_object.contentType))
        response['Content-Disposition'] = 'attachment; filename="%s"' % path
        return response


@login_required(login_url=LOGIN_URL)
@require_http_methods(["POST", "GET"])
def reg_client(request):
    if request.method == 'GET':
        form = RegClientForm()
        return render(request, "regclient.html", {"form": form})
    elif request.method == 'POST':
        form = RegClientForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            description = form.cleaned_data['description']
            rsa_signature = form.cleaned_data['rsa']
            secret = form.cleaned_data['secret']

            try:
                client = Consumer.objects.get(name__exact=name)
            except Consumer.DoesNotExist:
                client = Consumer.objects.create(name=name, description=description, user=request.user,
                                                 status=ACCEPTED, secret=secret, rsa_signature=rsa_signature)
            else:
                context = {"form": form, "error_message": "Client %s already exists." % name}
                return render(request, "regclient.html", context)

            client.generate_random_codes()
            context = {
                "name": client.name,
                "app_id": client.key,
                "secret": client.secret,
                "rsa": client.rsa_signature,
                "info_message": "Your Client Credentials"
            }
            return render(request, "reg_success.html", context)
        else:
            return render(request, "regclient.html", {"form": form})


@login_required(login_url="/accounts/login")
@require_http_methods(["GET", "HEAD"])
def my_download_statements(request):
    stmts = Statement.objects.filter(user=request.user).order_by('-stored')
    result = "[%s]" % ",".join([stmt.object_return() for stmt in stmts])

    response = HttpResponse(result, content_type='application/json', status=200)
    response['Content-Length'] = len(result)
    return response


@transaction.atomic
@login_required(login_url=LOGIN_URL)
@require_http_methods(["DELETE"])
def my_delete_statements(request):
    Statement.objects.filter(user=request.user).delete()
    stmts = Statement.objects.filter(user=request.user)
    if not stmts:
        return HttpResponse(status=204)
    else:
        raise Exception("Unable to delete statements")


@login_required(login_url=LOGIN_URL)
def my_activity_state(request):
    act_id = request.GET.get("act_id", None)
    state_id = request.GET.get("state_id", None)
    if act_id and state_id:
        try:
            ag = Agent.objects.get(mbox="mailto:" + request.user.email)
        except Agent.DoesNotExist:
            return HttpResponseNotFound("Agent does not exist")
        except Agent.MultipleObjectsReturned:
            return HttpResponseBadRequest("More than one agent returned with email")

        try:
            state = ActivityState.objects.get(activity_id=urllib.parse.unquote(act_id), agent=ag,
                                              state_id=urllib.parse.unquote(state_id))
        except ActivityState.DoesNotExist:
            return HttpResponseNotFound("Activity state does not exist")
        except ActivityState.MultipleObjectsReturned:
            return HttpResponseBadRequest("More than one activity state was found")
        # Really only used for the SCORM states so should only have json_state
        return HttpResponse(state.json_state, content_type=state.content_type, status=200)
    return HttpResponseBadRequest("Activity ID, State ID and are both required")


@transaction.atomic
@login_required(login_url=LOGIN_URL)
def my_app_status(request):
    try:
        name = request.GET['app_name']
        status = request.GET['status']
        new_status = [s[0] for s in CONSUMER_STATES if s[1] == status][0]  # should only be 1
        client = Consumer.objects.get(name__exact=name, user=request.user)
        client.status = new_status
        client.save()
        ret = {"app_name": client.name, "status": client.get_status_display()}
        return HttpResponse(json.dumps(ret), content_type="application/json", status=200)
    except:
        return HttpResponse(json.dumps({"error_message": "unable to fulfill request"}), content_type="application/json",
                            status=400)


@transaction.atomic
@login_required(login_url=LOGIN_URL)
@require_http_methods(["DELETE"])
def delete_token(request):
    try:
        ids = request.GET['id'].split("-")
        token_key = ids[0]
        consumer_id = ids[1]
        ts = ids[2]
        token = Token.objects.get(user=request.user,
                                  key__startswith=token_key,
                                  consumer__id=consumer_id,
                                  timestamp=ts,
                                  token_type=Token.ACCESS,
                                  is_approved=True)
        token.is_approved = False
        token.save()
        return HttpResponse("", status=204)
    except:
        return HttpResponse("Unknown token", status=400)


def logout_view(request):
    logout(request)
    # Redirect to a success page.
    return HttpResponseRedirect(reverse('lrs.views.home'))


# Called when user queries GET statement endpoint and returned list is larger than server limit (10)
@decorator_from_middleware(XAPIVersionHeaderMiddleware.XAPIVersionHeader)
@require_http_methods(["GET", "HEAD"])
def statements_more(request, more_id):
    return handle_request(request, more_id)


@require_http_methods(["PUT", "GET", "POST", "HEAD"])
@decorator_from_middleware(XAPIVersionHeaderMiddleware.XAPIVersionHeader)
def statements(request):
    if request.method in ['GET', 'HEAD']:
        return doget(request)
    else:
        return doputpost(request)


def doget(request):
    return handle_request(request)


@decorator_from_middleware(XAPIVersionHeaderMiddleware.XAPIVersionHeader)
def doputpost(request):
    return handle_request(request)


@require_http_methods(["PUT", "POST", "GET", "DELETE", "HEAD"])
@decorator_from_middleware(XAPIVersionHeaderMiddleware.XAPIVersionHeader)
def activity_state(request):
    return handle_request(request)


@require_http_methods(["PUT", "POST", "GET", "DELETE", "HEAD"])
@decorator_from_middleware(XAPIVersionHeaderMiddleware.XAPIVersionHeader)
def activity_profile(request):
    return handle_request(request)


@require_http_methods(["GET", "HEAD"])
@decorator_from_middleware(XAPIVersionHeaderMiddleware.XAPIVersionHeader)
def activities(request):
    return handle_request(request)


@require_http_methods(["PUT", "POST", "GET", "DELETE", "HEAD"])
@decorator_from_middleware(XAPIVersionHeaderMiddleware.XAPIVersionHeader)
def agent_profile(request):
    return handle_request(request)


# returns a 405 (Method Not Allowed) if not a GET
@require_http_methods(["GET", "HEAD"])
@decorator_from_middleware(XAPIVersionHeaderMiddleware.XAPIVersionHeader)
def agents(request):
    return handle_request(request)


@login_required
def user_profile(request):
    return render(request, "registration/profile.html")


def handle_request(request, more_id=None):
    validators = {
        reverse(statements).lower(): {
            "POST": req_validate.statements_post,
            "GET": req_validate.statements_get,
            "PUT": req_validate.statements_put,
            "HEAD": req_validate.statements_get
        },
        reverse(activity_state).lower(): {
            "POST": req_validate.activity_state_post,
            "PUT": req_validate.activity_state_put,
            "GET": req_validate.activity_state_get,
            "HEAD": req_validate.activity_state_get,
            "DELETE": req_validate.activity_state_delete
        },
        reverse(activity_profile).lower(): {
            "POST": req_validate.activity_profile_post,
            "PUT": req_validate.activity_profile_put,
            "GET": req_validate.activity_profile_get,
            "HEAD": req_validate.activity_profile_get,
            "DELETE": req_validate.activity_profile_delete
        },
        reverse(activities).lower(): {
            "GET": req_validate.activities_get,
            "HEAD": req_validate.activities_get
        },
        reverse(agent_profile).lower(): {
            "POST": req_validate.agent_profile_post,
            "PUT": req_validate.agent_profile_put,
            "GET": req_validate.agent_profile_get,
            "HEAD": req_validate.agent_profile_get,
            "DELETE": req_validate.agent_profile_delete
        },
        reverse(agents).lower(): {
            "GET": req_validate.agents_get,
            "HEAD": req_validate.agents_get
        },
        "/xapi/statements/more": {
            "GET": req_validate.statements_more_get,
            "HEAD": req_validate.statements_more_get
        }
    }
    processors = {
        reverse(statements).lower(): {
            "POST": req_process.statements_post,
            "GET": req_process.statements_get,
            "HEAD": req_process.statements_get,
            "PUT": req_process.statements_put
        },
        reverse(activity_state).lower(): {
            "POST": req_process.activity_state_post,
            "PUT": req_process.activity_state_put,
            "GET": req_process.activity_state_get,
            "HEAD": req_process.activity_state_get,
            "DELETE": req_process.activity_state_delete
        },
        reverse(activity_profile).lower(): {
            "POST": req_process.activity_profile_post,
            "PUT": req_process.activity_profile_put,
            "GET": req_process.activity_profile_get,
            "HEAD": req_process.activity_profile_get,
            "DELETE": req_process.activity_profile_delete
        },
        reverse(activities).lower(): {
            "GET": req_process.activities_get,
            "HEAD": req_process.activities_get
        },
        reverse(agent_profile).lower(): {
            "POST": req_process.agent_profile_post,
            "PUT": req_process.agent_profile_put,
            "GET": req_process.agent_profile_get,
            "HEAD": req_process.agent_profile_get,
            "DELETE": req_process.agent_profile_delete
        },
        reverse(agents).lower(): {
            "GET": req_process.agents_get,
            "HEAD": req_process.agents_get
        },
        "/xapi/statements/more": {
            "GET": req_process.statements_more_get,
            "HEAD": req_process.statements_more_get
        }
    }

    try:
        r_dict = req_parse.parse(request, more_id)
        path = request.path.lower()
        if path.endswith('/'):
            path = path.rstrip('/')
        # Cutoff more_id
        if '/xapi/statements/more' in path:
            path = '/xapi/statements/more'

        req_dict = validators[path][r_dict['method']](r_dict)
        return processors[path][req_dict['method']](req_dict)
    except (BadRequest, OauthBadRequest, ValidationError, SuspiciousOperation) as err:
        status = 400
        log_exception(status, request.path)
        response = HttpResponse(str(err), status=status)
    except (Unauthorized, OauthUnauthorized) as autherr:
        status = 401
        log_exception(status, request.path)
        response = HttpResponse(autherr, status=status)
        response['WWW-Authenticate'] = 'Basic realm="ADLLRS"'
    except Forbidden as forb:
        status = 403
        log_exception(status, request.path)
        response = HttpResponse(str(forb), status=status)
    except NotFound as nf:
        status = 404
        log_exception(status, request.path)
        response = HttpResponse(str(nf), status=status)
    except Conflict as c:
        status = 409
        log_exception(status, request.path)
        response = HttpResponse(str(c), status=status)
    except PreconditionFail as pf:
        status = 412
        log_exception(status, request.path)
        response = HttpResponse(str(pf), status=status)
    except Exception as err:
        status = 500
        log_exception(status, request.path)
        response = HttpResponse(str(err), status=status)
    return response


def log_exception(path, ex):
    logger.info("\nException while processing: %s" % path)
    logger.warning(ex, exc_info=True)
