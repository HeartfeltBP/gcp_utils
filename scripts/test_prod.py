from gcp_utils import constants
from firebase_admin import firestore, initialize_app

initialize_app()

UID = 'v2iHQmPIVfVW0IuhfZ1yCIegsB52'

database = firestore.client()
frames_ref = database.collection(u'bpm_data').document(UID).collection(u'frames')

# Trigger function
frames_ref.add(constants.NEW_BPM_FRAME)
