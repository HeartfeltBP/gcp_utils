import mock
import unittest
from gcp_utils import constants
from gcp_utils.tools.utils import format_as_json
from firebase_admin import firestore, initialize_app

from main import onNewFrame, onNewSample, onValidSample

initialize_app()

def test_onNewFrame():
    context = mock.Mock()
    database = firestore.client()
    col = database.collection(u'frames_test')

    # Add frame
    col.add(constants.BPM_FRAME)
    doc = [x for x in col.where(u'fid', u'==', u'987654321').stream()][0]
    context.resource = 'databases/documents/frames_test/' + str(doc.id)

    # Convert to JSON and test cloud function
    data = format_as_json(constants.BPM_FRAME)[0]  # dict
    onNewFrame(data, context)

    # Get expected result
    expected_data = format_as_json(constants.processed_frame())

    # Get processed data from firebase and compare
    col = database.collection(u'data_test')
    doc_gen = col.where(u'fid', u'==', u'987654321').stream()
    cloud_data = format_as_json(doc_gen)  # multiple docs
    case = unittest.TestCase()
    case.assertCountEqual(cloud_data, expected_data)

def test_onNewSample():
    context = mock.Mock()
    database = firestore.client()
    col = database.collection(u'data_test')

    # Add raw valid sample to collection (and get document id)
    col.add(constants.RAW_VALID_SAMPLE)
    doc = [x for x in col.where(u'sid', u'==', u'123456789').stream()][0]
    context.resource = '/databases/documents/data_test/' + str(doc.id)

    # Convert to JSON dictionary and test cloud function
    data = format_as_json(constants.RAW_VALID_SAMPLE)[0]  # dict
    onNewSample(data, context)

    # Get expected result
    expected_data = format_as_json(constants.processed_valid_sample())[0]

    # Get processed data from firebase and compare
    doc = col.where(u'sid', u'==', u'123456789').stream()
    cloud_data = format_as_json(doc)[0]  # single doc
    assert cloud_data == expected_data

def test_onValidSample():
    context = mock.Mock()
    database = firestore.client()
    col = database.collection(u'data_test')

    # Get test sample data
    doc = col.where(u'sid', u'==', u'123456789').stream()
    data = format_as_json(doc)[0]  # single doc

    # Get context
    doc = [x for x in col.where(u'sid', u'==', u'123456789').stream()][0]
    context.resource = '/databases/documents/data_test/' + str(doc.id)

    # Test cloud function
    onValidSample(data, context)

    # Get expected result
    expected_data = format_as_json(constants.predicted_sample())[0]  # dict

    # Get prediction from firebase and compare
    doc = col.where(u'sid', u'==', u'123456789').stream()
    cloud_data = format_as_json(doc)[0]  # single doc
    assert cloud_data == expected_data
