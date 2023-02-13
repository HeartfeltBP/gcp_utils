from gcp_utils.data import raw_valid_sample
from firebase_admin import credentials, firestore, initialize_app

cred = credentials.Certificate('.env')
initialize_app(cred)
database = firestore.client()
col = database.collection('new_samples')

sample = raw_valid_sample()
col.add(sample)
