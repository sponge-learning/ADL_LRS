import datetime
import hashlib
import json
import secrets

from django.core.files.base import ContentFile
from django.db import transaction
from datetime import timezone

from ..models import ActivityState
from ..exceptions import IDNotFoundError, ParamError
from ..util import etag

#: Text state up to this many UTF-8 bytes is kept on the row, in json_state, instead of
#: in a file. A state PUT is the LRS's busiest write, and a file meant a storage delete
#: and upload on every save. The cap is in UTF-8 bytes (64 KiB), sized for SCORM 2004's
#: 64,000-character suspend_data, the largest bookmark a course is built to send, when
#: that text is ASCII. Multi-byte text over the byte cap takes the file path, as does
#: text holding a NUL (which a Postgres text column rejects).
DB_TEXT_STATE_MAX_BYTES = 64 * 1024


def text_state_for_db(content):
    """The text to store on the row for these state bytes, or None if they need a file."""
    if len(content) > DB_TEXT_STATE_MAX_BYTES or b"\x00" in content:
        return None
    try:
        return content.decode('utf-8')
    except UnicodeDecodeError:
        return None


def delete_file_on_commit(field_file):
    """
    Delete a state's stored file once the transaction commits, and clear the field.

    Deleting inside the transaction would lose the state if the save then rolled back.
    robust=True keeps a storage error from turning a committed save into an error; the
    object is left behind and nothing reads it.
    """
    storage, name = field_file.storage, field_file.name
    transaction.on_commit(lambda: storage.delete(name), robust=True)
    setattr(field_file.instance, field_file.field.attname, None)


def non_json_state_filename(s):
    # The activity id is an IRI, so it can hold "/" and be any length. Used raw, the
    # storage reads every "/" as a directory and the last path component can be too
    # short to truncate under the FileField's max_length (SuspiciousFileOperation).
    # A sha1 of it is always 40 hex characters. Rows already stored keep the name
    # saved on them.
    #
    # The name also ends in a random token, so every save writes a new name. A
    # concurrent save's post-commit delete of the old name can then never hit the file
    # this save wrote, and a save that rolls back leaves the old file intact. The sha1
    # is cut to 32 hex characters to keep "activity_state/" + name within the
    # FileField's max_length (100) with the token added.
    activity_hash = hashlib.sha1(s.activity_id.encode('utf-8')).hexdigest()[:32]
    return "%s_%s_%s_%s" % (s.agent_id, activity_hash, s.id, secrets.token_hex(4))


class ActivityStateManager():
    def __init__(self, agent):
        self.Agent = agent

    @transaction.atomic
    def save_non_json_state(self, s, state, request_dict):
        content = state.read()
        s.content_type = request_dict['headers']['CONTENT_TYPE']
        s.etag = etag.create_tag(content)

        if 'updated' in request_dict['headers'] and request_dict['headers']['updated']:
            s.updated = request_dict['headers']['updated']
        else:
            s.updated = datetime.datetime.utcnow().replace(tzinfo=timezone.utc)

        text = text_state_for_db(content)
        if text is not None:
            # Readers take the file when there is one, so a row holding its text must
            # not keep a file (one left by an earlier save, or by an older release).
            s.json_state = text
            if s.state:
                delete_file_on_commit(s.state)
        else:
            # The old file is deleted only after the commit (and only if the new file
            # has another name), so a rolled-back save leaves it in place.
            old_storage, old_name = s.state.storage, (s.state.name if s.state else None)
            s.state.save(non_json_state_filename(s), ContentFile(content), save=False)
            s.json_state = ''
            if old_name and old_name != s.state.name:
                transaction.on_commit(lambda: old_storage.delete(old_name), robust=True)

        # One UPDATE: FieldFile.delete and FieldFile.save would each save the row too.
        s.save()

    def get_state_set(self, activity_id, registration, since):
        if registration:
            # Registration and since
            if since:
                state_set = self.Agent.activitystate_set.filter(activity_id=activity_id, registration_id=registration, updated__gt=since)
            # Registration
            else:
                state_set = self.Agent.activitystate_set.filter(activity_id=activity_id, registration_id=registration)
        else:
            # Since
            if since:
                state_set = self.Agent.activitystate_set.filter(activity_id=activity_id, updated__gt=since)
            # Neither
            else:
                state_set = self.Agent.activitystate_set.filter(activity_id=activity_id)
        return state_set

    @transaction.atomic
    def post_state(self, request_dict):
        registration = request_dict['params'].get('registration', None)
        created = False
        if registration:
            s = ActivityState.objects.filter(state_id=request_dict['params']['stateId'], agent=self.Agent,
                activity_id=request_dict['params']['activityId'], registration_id=request_dict['params']['registration']
                ).order_by('-updated').first()
            if not s:
                s = ActivityState.objects.create(state_id=request_dict['params']['stateId'], agent=self.Agent,
                activity_id=request_dict['params']['activityId'], registration_id=request_dict['params']['registration'])
                created = True
        else:
            s = ActivityState.objects.filter(state_id=request_dict['params']['stateId'], agent=self.Agent,
                activity_id=request_dict['params']['activityId']).order_by('-updated').first()
            if not s:
                s = ActivityState.objects.create(state_id=request_dict['params']['stateId'], agent=self.Agent,
                activity_id=request_dict['params']['activityId'])
                created = True
        
        if "application/json" not in request_dict['headers']['CONTENT_TYPE']:
            try:
                post_state = ContentFile(request_dict['state'].read())
            except:
                try:
                    post_state = ContentFile(request_dict['state'].encode())
                except:
                    try:
                        post_state = ContentFile(request_dict['state'])
                    except:
                        post_state = ContentFile(str(request_dict['state']))
            self.save_non_json_state(s, post_state, request_dict)
        else:
            post_state = request_dict['state']
            # If incoming state is application/json and if a state didn't already exist with the same agent, stateId, actId, and/or registration
            if created:
                s.json_state = post_state
                s.content_type = request_dict['headers']['CONTENT_TYPE']
                s.etag = etag.create_tag(post_state)
            # If incoming state is application/json and if a state already existed with the same agent, stateId, actId, and/or registration
            else:
                orig_state = json.loads(s.json_state)
                post_state = json.loads(post_state)
                if not isinstance(post_state, dict):
                    raise ParamError("The document was not able to be parsed into a JSON object.")
                else:
                    merged = json.dumps(dict(list(orig_state.items()) + list(post_state.items())))
                s.json_state = merged
                s.etag = etag.create_tag(merged)
    
                #Set updated
            if 'updated' in request_dict['headers'] and request_dict['headers']['updated']:
                s.updated = request_dict['headers']['updated']
            else:
                s.updated = datetime.datetime.utcnow().replace(tzinfo=timezone.utc)
            s.save()
        
    @transaction.atomic
    def put_state(self, request_dict):
        registration = request_dict['params'].get('registration', None)
        created = False
        if registration:
            s = ActivityState.objects.filter(state_id=request_dict['params']['stateId'], agent=self.Agent,
                activity_id=request_dict['params']['activityId'], registration_id=request_dict['params']['registration']
                ).order_by('-updated').first()
            if not s:
                s = ActivityState.objects.create(state_id=request_dict['params']['stateId'], agent=self.Agent,
                activity_id=request_dict['params']['activityId'], registration_id=request_dict['params']['registration'])
                created = True
        else:
            s = ActivityState.objects.filter(state_id=request_dict['params']['stateId'], agent=self.Agent,
                activity_id=request_dict['params']['activityId']).order_by('-updated').first()
            if not s:
                s = ActivityState.objects.create(state_id=request_dict['params']['stateId'], agent=self.Agent,
                activity_id=request_dict['params']['activityId'])
                created = True
        
        if "application/json" not in request_dict['headers']['CONTENT_TYPE']:
            try:
                post_state = ContentFile(request_dict['state'].read())
            except:
                try:
                    post_state = ContentFile(request_dict['state'].encode())
                except:
                    try:
                        post_state = ContentFile(request_dict['state'])
                    except:
                        post_state = ContentFile(str(request_dict['state']))
            
            # If a state already existed with the profileId and activityId
            if not created:
                etag.check_preconditions(request_dict, s)
            self.save_non_json_state(s, post_state, request_dict)
        # State being PUT is json
        else:
            if not created:
                etag.check_preconditions(request_dict, s)
                # Readers take the file when there is one, so drop a file left by an
                # earlier non-JSON save or the GET would keep answering with it.
                if s.state:
                    delete_file_on_commit(s.state)
            the_state = request_dict['state']
            s.json_state = the_state
            s.content_type = request_dict['headers']['CONTENT_TYPE']
            s.etag = etag.create_tag(the_state)

            #Set updated
            if 'updated' in request_dict['headers'] and request_dict['headers']['updated']:
                s.updated = request_dict['headers']['updated']
            else:
                s.updated = datetime.datetime.utcnow().replace(tzinfo=timezone.utc)
            s.save()

    def get_state(self, activity_id, registration, state_id):
        if registration:
            state = self.Agent.activitystate_set.filter(state_id=state_id, activity_id=activity_id, registration_id=registration).order_by('-updated').first()
        else:
            state = self.Agent.activitystate_set.filter(state_id=state_id, activity_id=activity_id).order_by('-updated').first()
        if not state:
            err_msg = 'There is no activity state associated with the id: %s' % state_id
            raise IDNotFoundError(err_msg)
        return state

    def get_state_ids(self, activity_id, registration, since):
        state_set = self.get_state_set(activity_id, registration, since)
        # If state_set isn't empty
        if state_set:
            return state_set.values_list('state_id', flat=True)
        return state_set

    @transaction.atomic
    def delete_state(self, request_dict):
        state_id = request_dict['params'].get('stateId', None)
        activity_id = request_dict['params']['activityId']
        registration = request_dict['params'].get('registration', None)
        try:
            # Bulk delete if stateId is not in params
            if not state_id:
                states = self.get_state_set(activity_id, registration, None)
                for s in states:
                    s.delete() # bulk delete skips the custom delete function
            # Single delete
            else:
                self.get_state(activity_id, registration, state_id).delete()
        except ActivityState.DoesNotExist:
            pass
        except IDNotFoundError:
            pass