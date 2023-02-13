from gcp_utils.data import raw_valid_sample
from firebase_admin import credentials, firestore, initialize_app

initialize_app()
database = firestore.client()
col = database.collection('heartfelt_data')

sample = raw_valid_sample()
col.add(sample)
