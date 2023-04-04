import mock
import unittest
from gcp_utils import constants
from gcp_utils.tools.utils import format_as_json
from firebase_admin import firestore, initialize_app

from main import onUpdateFrame, onCreateWindow, onUpdateWindow

initialize_app()

# camhpjohnson@gmail.com
UID = 'wx1jF08b3DTPijtQcwGiEwpEFai2'

def test_onNewFrame():
    context = mock.Mock()
    database = firestore.client()
    col = database.collection(u'bpm_data_test').document(UID).collection(u'frames')

    # Add frame
    col.add(constants.BPM_FRAME)
    doc = [x for x in col.where(u'fid', u'==', u'987654321').stream()][0]
    context.resource = f'databases/documents/bpm_data_test/{UID}/frames/' + str(doc.id)

    # Convert to JSON and test cloud function
    data = format_as_json(constants.BPM_FRAME)[0]  # dict
    onUpdateFrame(data, context)

    # Get expected result
    expected_processed_frame, expected_windows = constants.processed_frame_and_windows()
    expected_processed_frame = format_as_json(expected_processed_frame)[0]
    expected_windows = format_as_json(expected_windows)

    col = database.collection(u'bpm_data_test').document(UID).collection(u'frames')
    doc = col.where(u'fid', u'==', u'987654321').stream()
    cloud_processed_frame = format_as_json(doc)[0]

    # Get processed data from firebase and compare
    col = database.collection(u'bpm_data_test').document(UID).collection(u'windows')
    doc_gen = col.where(u'fid', u'==', u'987654321').stream()
    cloud_windows = format_as_json(doc_gen)  # multiple docs
    case = unittest.TestCase()
    case.assertCountEqual(dict(x=cloud_processed_frame, y=cloud_windows), dict(x=expected_processed_frame, y=expected_windows))

def test_onNewWindow():
    context = mock.Mock()
    database = firestore.client()
    col = database.collection(u'bpm_data_test').document(UID).collection(u'windows')

    # Add raw valid sample to collection (and get document id)
    col.add(constants.RAW_VALID_WINDOW)
    doc = [x for x in col.where(u'sid', u'==', u'123456789').stream()][0]
    context.resource = f'/databases/documents/bpm_data_test/{UID}/windows/' + str(doc.id)

    # Convert to JSON dictionary and test cloud function
    data = format_as_json(constants.RAW_VALID_WINDOW)[0]  # dict
    onCreateWindow(data, context)

    # Get expected result
    expected_processed_window = format_as_json(constants.processed_valid_window())[0]

    # Get processed data from firebase and compare
    doc = col.where(u'sid', u'==', u'123456789').stream()
    cloud_processed_window = format_as_json(doc)[0]  # single doc
    assert cloud_processed_window == expected_processed_window

def test_onValidWindow():
    context = mock.Mock()
    database = firestore.client()
    col = database.collection(u'bpm_data_test').document(UID).collection(u'windows')

    # Get test sample data
    doc = col.where(u'sid', u'==', u'123456789').stream()
    data = format_as_json(doc)[0]  # single doc

    # Get context
    doc = [x for x in col.where(u'sid', u'==', u'123456789').stream()][0]
    context.resource = f'/databases/documents/bpm_data_test/{UID}/windows/' + str(doc.id)

    # Test cloud function
    onUpdateWindow(data, context)

    # Get expected result
    expected_predicted_window = format_as_json(constants.predicted_window())[0]  # dict

    # Get prediction from firebase and compare
    doc = col.where(u'sid', u'==', u'123456789').stream()
    cloud_predicted_window = format_as_json(doc)[0]  # single doc
    assert cloud_predicted_window == expected_predicted_window
