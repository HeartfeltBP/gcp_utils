import mock
from gcp_utils import constants
from gcp_utils.tools.utils import format_as_json
from firebase_admin import firestore, initialize_app

from main import onNewSample, onValidSample

initialize_app()

def test_onNewSample():
    context = mock.Mock()
    database = firestore.client()
    col = database.collection(u'heartfelt_data')

    # Add raw valid sample to collection (and get document id)
    col.add(constants.RAW_VALID_SAMPLE)
    doc = [x for x in col.where(u'sample_id', u'==', u'123456789').stream()][0]
    context.resource = '/databases/documents/heartfelt_data/' + str(doc.id)

    # Convert to JSON dictionary and test cloud function
    data = format_as_json(constants.RAW_VALID_SAMPLE)
    onNewSample(data, context)

    # Get expected result
    expected_data = format_as_json(constants.processed_valid_sample())

    # Get processed data from firebase and compare
    doc = col.where(u'sample_id', u'==', u'123456789').stream()
    data = format_as_json(doc)
    assert data == expected_data

def test_onValidSample():
    context = mock.Mock()
    database = firestore.client()
    col = database.collection(u'heartfelt_data')

    # Get test sample data
    doc = col.where(u'sample_id', u'==', u'123456789').stream()
    data = format_as_json(doc)

    # Get context
    doc = [x for x in col.where(u'sample_id', u'==', u'123456789').stream()][0]
    context.resource = '/databases/documents/heartfelt_data/' + str(doc.id)

    # Test cloud function
    onValidSample(data, context)

    # Get expected result
    expected_data = format_as_json(constants.predicted_sample())

    # Get prediction from firebase and compare
    doc = col.where(u'sample_id', u'==', u'123456789').stream()
    data = format_as_json(doc)
    assert data == expected_data
