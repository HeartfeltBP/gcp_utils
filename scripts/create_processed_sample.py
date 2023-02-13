from database_tools.preprocessing.datastores import Window, ConfigMapper
from gcp_utils.tools.preprocess import validate_window
from gcp_utils.tools.utils import format_as_json
from firebase_admin import credentials, firestore, initialize_app

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

cred = credentials.Certificate('../.env')
initialize_app(cred)
database = firestore.client()

col = database.collection('new_samples')

doc = col.where(u'sample_id', u'==', u'123456789').stream()
data = format_as_json(doc)

result = validate_window(
    user_id=user_id,
    sample_id=sample_id,
    ppg=ppg_raw,
    config=CONFIG,
)
