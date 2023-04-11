import unittest
from gcp_utils import constants
from gcp_utils.tools.utils import format_as_json, query_collection, mock_context
from firebase_admin import firestore, initialize_app

from main import onUpdateFrame, onCreateWindow, onUpdateWindow

initialize_app()

UID = 'v2iHQmPIVfVW0IuhfZ1yCIegsB52'

def test_onUpdateFrame():
    database = firestore.client()
    frames_ref = database.collection(u'bpm_data_test').document(UID).collection(u'frames')

    # Trigger function
    frames_ref.add(constants.NEW_BPM_FRAME)
    doc = query_collection(frames_ref, 'fid', '==', '0')[0]
    data = format_as_json(constants.NEW_BPM_FRAME)[0]
    context = mock_context(doc.reference.path)
    onUpdateFrame(data, context)

    # Get expected result
    expected_frame, expected_windows = constants.processed_frame_and_windows()
    expected_frame, expected_windows = format_as_json(expected_frame)[0], format_as_json(expected_windows)

    # Get actual result
    doc = query_collection(frames_ref, 'fid', '==', '0')[0]
    actual_frame = format_as_json(doc.to_dict())[0]
    windows_ref = database.collection(u'bpm_data_test').document(UID).collection(u'windows')
    docs = query_collection(windows_ref, 'fid', '==', '0')
    actual_windows = format_as_json([d.to_dict() for d in docs])

    case = unittest.TestCase()
    case.maxDiff = None
    case.assertCountEqual(dict(x=expected_frame, y=expected_windows), dict(x=actual_frame, y=actual_windows))

def test_onCreateWindow():
    database = firestore.client()
    windows_ref = database.collection(u'bpm_data_test').document(UID).collection(u'windows')

    # Trigger function
    docs = query_collection(windows_ref, 'fid', '==', '0')
    for d in docs:
        data = format_as_json(d.to_dict())[0]
        context = mock_context(d.reference.path)
        onCreateWindow(data, context)

    # Get expected result
    expected_windows = format_as_json(constants.processed_windows())

    # Get actual result
    docs = query_collection(windows_ref, 'fid', '==', '0')
    actual_windows = format_as_json([d.to_dict() for d in docs])

    case = unittest.TestCase()
    case.maxDiff = None
    case.assertCountEqual(dict(x=expected_windows), dict(x=actual_windows))

def test_onUpdateWindow():
    database = firestore.client()
    windows_ref = database.collection(u'bpm_data_test').document(UID).collection(u'windows')

    # Trigger function
    doc = query_collection(windows_ref, 'fid', '==', '0')[0]
    data = format_as_json(doc.to_dict())[0]
    context = mock_context(doc.reference.path)
    onUpdateWindow(data, context)

    # Get expected result
    expected_windows = format_as_json(constants.predicted_windows())

    # Get actual result
    docs = query_collection(windows_ref, 'fid', '==', '0')
    actual_windows = format_as_json([d.to_dict() for d in docs])

    case = unittest.TestCase()
    case.maxDiff = None
    case.assertCountEqual(dict(x=expected_windows), dict(x=actual_windows))
