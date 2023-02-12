from google.cloud import firestore
# from gcp_utils.tools.preprocess import validate_window
# from gcp_utils.tools.predict import get_inputs, predict_bp
from tools.preprocess import validate_window
from tools.predict import get_inputs, predict_bp

client = firestore.Client()

CONFIG = dict(
    scaler_path='scalers/mimic3-min-max-2022-11-08.pkl',
    checks=['snr', 'hr', 'beat'],
    fs=125,                                 # sampling frequency
    win_len=256,                            # window length
    freq_band=[0.5, 8.0],                   # bandpass frequencies
    sim=0.6,                                # similarity threshold
    snr=2.0,                                # SNR threshold
    hr_freq_band=[0.667, 3.0],              # valid heartrate frequency band in Hz
    hr_delta=1/6,                           # maximum heart rate difference between ppg, abp
    dbp_bounds=[20, 130],                   # upper and lower threshold for DBP
    sbp_bounds=[50, 225],                   # upper and lower threshold for SBP
    windowsize=1,                           # windowsize for rolling mean
    ma_perc=20,                             # multiplier for peak detection
    beat_sim=0.2,                           # lower threshold for beat similarity
)

# Validate window
def onNewSample(data, context):
    path_parts = context.resource.split('/documents/')[1].split('/')
    collection_path = path_parts[0]
    document_path = '/'.join(path_parts[1:])

    affected_doc = client.collection(collection_path).document(document_path)

    username = data["value"]["fields"]["username"]["stringValue"]
    sample_id = data["value"]["fields"]["sample_id"]["integerValue"]
    ppg_raw = data["value"]["fields"]["ppg_raw"]["arrayValue"]

    result = validate_window(
        username=username,
        sample_id=sample_id,
        ppg=ppg_raw,
        config=CONFIG,
    )
    client.collection('processed_samples').add(result)
    affected_doc.update({
        u'processed': True,
    })

# Make prediction on ppg using enceladus (vital-bee-206-serving)
def onValidSample(data, context):
    path_parts = context.resource.split('/documents/')[1].split('/')
    collection_path = path_parts[0]
    document_path = '/'.join(path_parts[1:])

    affected_doc = client.collection(collection_path).document(document_path)

    username = data["value"]["fields"]["username"]["stringValue"]
    sample_id = data["value"]["fields"]["sample_id"]["integerValue"]

    valid = data["value"]["fields"]["valid"]["booleanValue"]
    if valid:
        instance_dict = get_inputs(data)
        abp = predict_bp(
            project="123543907199",
            endpoint_id="4207052545266286592",
            location="us-central1",
            instance_dict=instance_dict,
        )
        
        result = dict(
            username=username,
            sample_id=sample_id,
            abp=abp,
        )
        client.collection('predictions').add(result)

        affected_doc.update({
            u'predicted': True
        })
