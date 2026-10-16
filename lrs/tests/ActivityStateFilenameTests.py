# lrs/tests/__init__.py imports the older suites, which no longer import under
# Django 5.2 (they reverse views by dotted path), so this module uses absolute
# imports and runs on its own, against a real database:
#   python -m django test lrs/tests -t lrs/tests -p ActivityStateFilenameTests.py
import shutil
import tempfile

from django.core.files.base import ContentFile
from django.test import TestCase, override_settings

from lrs.managers.ActivityStateManager import ActivityStateManager, non_json_state_filename
from lrs.models import ActivityState, Agent, ACTIVITY_STATE_UPLOAD_TO

# A cmi5 activity id: an IRI whose 150-character course title has "/" separators.
TITLE = ("Brandschutz-Grundlagen/Modul-1/Lektion-2/" * 4)[:150]
ACTIVITY_ID = "https://lms.example.com/cmi5/%s/au/0" % TITLE
STATE_ID = "bookmark"


class ActivityStateFilenameTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super(ActivityStateFilenameTests, cls).setUpClass()
        cls.media_root = tempfile.mkdtemp()
        cls.media_override = override_settings(MEDIA_ROOT=cls.media_root)
        cls.media_override.enable()

    @classmethod
    def tearDownClass(cls):
        cls.media_override.disable()
        shutil.rmtree(cls.media_root, ignore_errors=True)
        super(ActivityStateFilenameTests, cls).tearDownClass()

    def setUp(self):
        self.agent = Agent.objects.retrieve_or_create(mbox="mailto:test@example.com")[0]
        self.manager = ActivityStateManager(self.agent)

    def put_text_state(self, activity_id, content):
        self.manager.put_state({
            'params': {'stateId': STATE_ID, 'activityId': activity_id},
            'headers': {'CONTENT_TYPE': 'text/plain'},
            'state': content,
        })
        return self.manager.get_state(activity_id, None, STATE_ID)

    def test_filename_has_no_slash_and_fits_the_field(self):
        s = ActivityState(id=2 ** 63 - 1, agent_id=2 ** 63 - 1, activity_id=ACTIVITY_ID)
        fn = non_json_state_filename(s, s.id)

        self.assertNotIn("/", fn)
        max_length = ActivityState._meta.get_field('state').max_length
        self.assertLessEqual(len("%s/%s" % (ACTIVITY_STATE_UPLOAD_TO, fn)), max_length)

    def test_put_text_state_for_a_long_slash_bearing_activity_id(self):
        s = self.put_text_state(ACTIVITY_ID, "lesson-3")

        self.assertEqual(s.state.name, "%s/%s" % (ACTIVITY_STATE_UPLOAD_TO, non_json_state_filename(s, s.id)))
        s.state.open()
        self.assertEqual(s.state.read(), b"lesson-3")

        # A second PUT replaces the stored text.
        s = self.put_text_state(ACTIVITY_ID, "lesson-4")
        s.state.open()
        self.assertEqual(s.state.read(), b"lesson-4")

    def test_a_row_stored_under_the_old_filename_keeps_resolving(self):
        activity_id = "http://example.com/course/au"
        s = ActivityState.objects.create(state_id=STATE_ID, agent=self.agent, activity_id=activity_id,
            content_type='text/plain')
        old_name = "%s_%s_%s" % (s.agent_id, activity_id, s.id)
        s.state.save(old_name, ContentFile(b"old-bookmark"))
        stored_name = s.state.name
        self.assertIn("example.com/course/au", stored_name)

        s = self.manager.get_state(activity_id, None, STATE_ID)
        self.assertEqual(s.state.name, stored_name)
        s.state.open()
        self.assertEqual(s.state.read(), b"old-bookmark")

        # The next PUT deletes the old file and saves under the bounded name.
        s = self.put_text_state(activity_id, "new-bookmark")
        self.assertFalse(s.state.storage.exists(stored_name))
        self.assertEqual(s.state.name, "%s/%s" % (ACTIVITY_STATE_UPLOAD_TO, non_json_state_filename(s, s.id)))
        s.state.open()
        self.assertEqual(s.state.read(), b"new-bookmark")
