from gcp_utils.tools.preprocess import validate_window
from gcp_utils.tools.predict import predict_bp
from gcp_utils.tools.utils import format_as_json

CONFIG = dict(
    scaler_path='gcp_utils/data/mimic3-min-max-2022-11-08.pkl',
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

RAW_VALID_SAMPLE = {
    'user_id': 'test',
    'sample_id': '123456789',
    'status': 'new',
    'ppg_raw': [-0.017258197,-0.016361266,-0.014650792,-0.013177723,-0.0120610595,-0.011393756,-0.011266887,-0.011709392,-0.012673438,-0.014070511,-0.015725493,-0.017408043,-0.01886046,-0.019752711,-0.019766122,-0.018629134,-0.016068399,-0.011877805,-0.005972892,0.0016396344,0.010848671,0.021410793,0.032973945,0.045104414,0.05731094,0.06911057,0.07994479,0.08933163,0.09698847,0.10258037,0.10590902,0.106984764,0.10589141,0.10282117,0.09806773,0.0919908,0.08498633,0.07748631,0.06981969,0.062290728,0.0552139,0.04868868,0.042740345,0.037386894,0.03251478,0.027958423,0.02354002,0.019073278,0.0143916905,0.009373039,0.0039643347,-0.0018445551,-0.007992685,-0.014323711,-0.020664275,-0.026797652,-0.03247556,-0.03747964,-0.041594505,-0.044661075,-0.046598434,-0.04737106,-0.04702416,-0.04567285,-0.043483615,-0.040678173,-0.037484854,-0.03413126,-0.030852407,-0.02784723,-0.025263697,-0.023207933,-0.021738857,-0.020865291,-0.020547688,-0.020723969,-0.021291465,-0.022134304,-0.023165435,-0.024283916,-0.025394052,-0.026448876,-0.027415454,-0.028269142,-0.029019684,-0.029680729,-0.03027299,-0.030829519,-0.031345546,-0.0318152,-0.03225845,-0.03262469,-0.032853276,-0.03291917,-0.032767385,-0.03235486,-0.031663805,-0.030700773,-0.029500097,-0.028137594,-0.026718736,-0.025342792,-0.024136633,-0.02325061,-0.022765607,-0.022722214,-0.023154318,-0.024008363,-0.025162995,-0.026444465,-0.0276137,-0.028410941,-0.028560132,-0.027734995,-0.025658637,-0.022141844,-0.016988486,-0.010104924,-0.0015418231,0.00858134,0.020012021,0.032384366,0.045256406,0.05812034,0.07045853,0.08177927,0.09156656,0.099438906,0.10519987,0.10863599,0.10969153,0.10850564,0.10528073,0.100307256,0.09396312,0.086657375,0.07880652,0.070827246,0.06302118,0.055639267,0.048898846,0.04283303,0.03739217,0.03249353,0.027972192,0.023619264,0.019219995,0.014587939,0.009573728,0.004090309,-0.0018881857,-0.008302748,-0.015022159,-0.021862924,-0.02858755,-0.03493455,-0.040638834,-0.045463145,-0.049210325,-0.051743433,-0.05301006,-0.053024128,-0.051893666,-0.049771428,-0.04686241,-0.043440387,-0.039743364,-0.036010772,-0.03247994,-0.029334188,-0.02669689,-0.024656922,-0.023245245,-0.022435546,-0.022188127,-0.022398293,-0.022951841,-0.023765773,-0.024715245,-0.025682688,-0.026602,-0.02741167,-0.02805677,-0.028503984,-0.028734177,-0.028738797,-0.028505176,-0.028028548,-0.027281731,-0.026245266,-0.024942815,-0.023343742,-0.021444708,-0.019302845,-0.016952425,-0.014466971,-0.011950314,-0.009508491,-0.007284969,-0.0054467916,-0.004146248,-0.003430456,-0.0033902228,-0.004133463,-0.005528152,-0.007413596,-0.009645581,-0.01196593,-0.014060855,-0.015602559,-0.01628831,-0.015828967,-0.013992459,-0.010597378,-0.005559653,0.0010818839,0.009224057,0.018637627,0.028984308,0.03985864,0.050789267,0.061282694,0.07086742,0.07911256,0.085693985,0.09032223,0.092839,0.09330377,0.091759145,0.08834827,0.083357066,0.07709432,0.069888294,0.062062502,0.053937525,0.0457893,0.037846714,0.030273527,0.023138106,0.016478062,0.010300189,0.004526943,-0.0009263158,-0.0061154366,-0.011103153,-0.015924633,-0.020573825,-0.025010943,-0.02915752,-0.03293416,-0.036208928,-0.038864702,-0.04084128,-0.042050898,-0.042458564,-0.04246521],
    'ppg': [0],
    'vpg': [0],
    'apg': [0],
    'ppg_scaled': [0],
    'vpg_scaled': [0],
    'apg_scaled': [0],
    'abp_scaled': [0],
    'abp': [0],
}

def config():
    return CONFIG

def raw_valid_sample():
    return RAW_VALID_SAMPLE

def processed_valid_sample():
    result = validate_window(RAW_VALID_SAMPLE['ppg_raw'], CONFIG)
    processed_valid_sample = {
        'user_id': 'test',
        'sample_id': '123456789',
        'status': 'valid',
        'ppg_raw': RAW_VALID_SAMPLE['ppg_raw'],
        'ppg': result['ppg'],
        'vpg': result['vpg'],
        'apg': result['apg'],
        'ppg_scaled': result['ppg_scaled'],
        'vpg_scaled': result['vpg_scaled'],
        'apg_scaled': result['apg_scaled'],
        'abp_scaled': [0],
        'abp': [0],
    }
    return processed_valid_sample

def predicted_sample():
    processed_sample = processed_valid_sample()
    data = format_as_json(processed_sample)
    result = predict_bp(data, CONFIG)
    predicted_sample = {
        'user_id': 'test',
        'sample_id': '123456789',
        'status': 'predicted',
        'ppg_raw': RAW_VALID_SAMPLE['ppg_raw'],
        'ppg': processed_sample['ppg'],
        'vpg': processed_sample['vpg'],
        'apg': processed_sample['apg'],
        'ppg_scaled': processed_sample['ppg_scaled'],
        'vpg_scaled': processed_sample['vpg_scaled'],
        'apg_scaled': processed_sample['apg_scaled'],
        'abp_scaled': result['abp_scaled'],
        'abp': result['abp'],
    }
    return predicted_sample
