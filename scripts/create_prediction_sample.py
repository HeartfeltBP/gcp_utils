from firebase_admin import credentials, firestore, initialize_app

cred = credentials.Certificate('../.env')
initialize_app(cred)

database = firestore.client()

col = database.collection('predictions')