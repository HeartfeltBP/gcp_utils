from gcp_utils import constants
from firebase_admin import firestore, initialize_app
from gcp_utils.tools.utils import query_collection

initialize_app()

UID = 'v2iHQmPIVfVW0IuhfZ1yCIegsB52'

database = firestore.client()
frames_ref = database.collection(f'bpm_data/{UID}/frames')

# Trigger function
frames_ref.add(constants.NEW_BPM_FRAME)

doc = query_collection(frames_ref, 'fid', '==', '0')[0]
doc_ref = database.collection(f'bpm_data/{UID}/frames').document(doc.id)
doc_ref.update({'spo2': -1})
