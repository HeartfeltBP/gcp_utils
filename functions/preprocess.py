from google.cloud import firestore
import ast
import itertools
import numpy as np
from scipy import signal, integrate
from heartpy.preprocessing import flip_signal
from heartpy.peakdetection import detect_peaks
from heartpy.datautils import rolling_mean


class Preprocessor():
    def __init__(
        self,
        ppg,
        fs,
    ):
        self._ppg =[float(x['doubleValue']) for x in ppg['values']]
        self._fs = int(fs)

    def run(self):
        low=0.5
        high=8.0
        df=0.2
        snr_t=2.0
        f0_low=0.667
        f0_high=4.0
        windowsize=1
        ma_perc=20
        beat_sim=0.2

        # Get data
        ppg = np.array(self._ppg, dtype=np.float)
        ppg[np.isnan(ppg)] = 0

        # Apply bandpass filter to ppg
        ppg = bandpass(ppg, low=low, high=high, fs=self._fs)

        # Signal level cleaning
        out = self._signal_level_check(
            p=ppg,
            low=low,
            high=high,
            df=df,
            snr_t=snr_t,
            f0_low=f0_low,
            f0_high=f0_high,
            windowsize=windowsize,
            ma_perc=ma_perc,
            beat_sim=beat_sim,
        )
        return out

    def _signal_level_check(
        self,
        p,
        low,
        high,
        df,
        snr_t,
        f0_low,
        f0_high,
        windowsize,
        ma_perc,
        beat_sim,
    ):
        # Get SNR & fundamental frequencies
        snr_p, f0_p = get_snr(p, low=low, high=high, df=df, fs=self._fs)

        # Check for flat lines
        flat_p = flat_lines(p)

        beat_sim_p = beat_similarity(
            p,
            windowsize=windowsize,
            ma_perc=ma_perc,
            fs=self._fs,
        )

        # Check similarity, snr, hr, bp, and peaks
        nan_check = np.nan in [snr_p, f0_p]
        snr_check = (snr_p < snr_t)
        hr_check = (f0_p < f0_low).any() | (f0_p > f0_high).any()
        beat_check = (beat_sim_p < beat_sim)
        if nan_check | snr_check | hr_check | flat_p | beat_check:
            valid = False
        else:
            valid = True

        vpg = np.gradient(p, axis=1)  # 1st derivative of ppg
        apg = np.gradient(vpg, axis=1)  # 2nd derivative of vpg
        return dict(
            ppg=list(p),
            vpg=list(vpg),
            apg=list(apg),
            valid=valid,
            snr=float(snr_p),
            hr=float(f0_p * 60),  # Multiply by 60 to estimate HR
            beat_sim=float(beat_sim_p),
        )


def make_equal_len(x, y):
    len_x = len(x)
    len_y = len(y)
    if len_x > len_y:
        y = np.pad(y, pad_width=[0, len_x - len_y])
    else:
        x = np.pad(x, pad_width=[0, len_y - len_x])
    return x, y

def bandpass(x, low, high, fs):
    """
    Filters signal with a 4th order Cheby II filter.

    Args:
        x (np.ndarray): Signal data.
        low (float, optional): Lower frequency in Hz.
        high (float, optional): Upper frequency in Hz.
        fs (int, optional): Sampling rate.

    Returns:
        x (np.ndarray): Filtered signal.
    """
    cby = signal.cheby2(
        N=4,
        rs=20,
        Wn=[low, high],
        btype='bandpass',
        output='sos',
        fs=fs,
    )
    x = signal.sosfiltfilt(cby, x, padtype=None)
    return x

def get_similarity(x, y):
    """
    Calculates time or spectral similarity.

    Args:
        x (np.ndarray): PPG data.
        y (np.ndarray): ABP data.
        spectral (boolean): If True calculate fft
            of signals.

    Returns:
        coef (float): Pearson correlation coefficient.
    """
    x_bar = np.mean(x)
    y_bar = np.mean(y)
    y_temp = y - y_bar
    x_temp = x - x_bar
    covar = np.sum( (x_temp * y_temp) )
    var = np.sqrt( np.sum( (x_temp ** 2 ) ) * np.sum( (y_temp ** 2) ) )
    with np.errstate(divide='ignore', invalid='ignore'):
        try:
            coef = covar / var
        except (ZeroDivisionError, RuntimeWarning):
            coef = 0
    return coef

def get_snr(x, low, high, df, fs):
    """
    Calculate the Signal-to-noise ratio (SNR) of the cardiac signal.
    Density of spectrum between low and high frequencies is considered
    signal power. Density of spectrum outside low to high frequency
    band is considered signal noise. F0 is estimated to be the frequency
    at which the power spectrum is at its maximum.

    Args:
        x (np.ndarray): Cardiac signal data.
        low (float): Lower frequency in Hz.
        high (float): Upper frequency in Hz.
        df (float): Delta f for calculating power.
        fs (int): Sampling rate of signal.

    Returns:
        snr (float): SNR of signal in dB.
        f0 (float): Fundamental frequency of signal in Hz.
    """
    # Estimate spectral power density
    freqs, psd = signal.periodogram(x, fs, nfft=2048)
    freq_res = freqs[1] - freqs[0]

    dpdf = np.diff(psd) / np.diff(freqs)
    peak_idx = np.where(np.diff(np.sign(dpdf)))[0] + 1
    peak_x = freqs[peak_idx]
    try:
        f_idx = np.sort(np.argpartition(psd[peak_idx], -3)[-3:])
        f0, f1, f2 = peak_x[f_idx]
    except:
        return -10, 0

    # Signal power
    idx_sig_fund = np.logical_and(freqs >= f0 - df, freqs <= f0 + df)
    idx_sig_harm1 = np.logical_and(freqs >= f1 - df, freqs <= f1 + df)
    idx_sig_harm2 = np.logical_and(freqs >= f2 - df, freqs <= f2 + df)

    # Try statements are easiest way of preventing errors during integration
    try:
        p_sig_fund = integrate.simps(psd[idx_sig_fund], dx=freq_res)
    except:
        p_sig_fund = 0
    try:
        p_sig_harm1 = integrate.simps(psd[idx_sig_harm1], dx=freq_res)
    except:
        p_sig_harm1 = 0
    try:
        p_sig_harm2 = integrate.simps(psd[idx_sig_harm2], dx=freq_res)
    except:
        p_sig_harm2 = 0
    p_sig = p_sig_fund + p_sig_harm1 + p_sig_harm2

    # Noise power
    idx_cardiac = np.logical_and(freqs >= low, freqs <= high)

    try:
        p_cardiac = integrate.simps(psd[idx_cardiac], dx=freq_res)
    except:
        p_cardiac = 0
    p_noise = p_cardiac - p_sig

    # Try, except to prevent divide by 0 error
    with np.errstate(divide='ignore', invalid='ignore'):
        try:
            # Find SNR and convert to dB
            snr = 10 * np.log10(p_sig / p_noise)
        except (ZeroDivisionError, RuntimeWarning):
            snr = -10
    return snr, f0

def flat_lines(x):
    """
    Flat line detection.

    Args:
        x (np.ndarray): Signal to process.

    Returns:
        bool: True if flat lines are present and False otherwise.
    """
    for i, val in enumerate(x):
        if (i + 2) >= len(x):
            break
        if (x[i + 1] == val) & (x[i + 2] == val):
            return True
    return False

def beat_similarity(x, windowsize, ma_perc, fs, get_bp=False):
    """Calculates beat similarity by segmenting beats at valleys and
       calculating the Pearson correlation coefficient. The final value
       output is the mean of the correlation coefficients calculated from
       every combination (n=2) of beats in the signal.
       
       This function also doubles for checking the number of beats and returns
       -1 if it fails.

    Args:
        x (np.ndarray): Cardiac signal.
        windowsize (float): Window size for rolling mean in seconds (windowsize * fs).
        ma_perc (float): Rolling mean multiplier for peak detection.
        fs (int): Sampling rate of cardiac signal.

    Returns:
        s: Normalized correlation coeffient. Segmentation failure results in -1.
    """
    pad_width = 19
    x_pad = np.pad(x, pad_width=[pad_width, 0], constant_values=[x[0]])
    x_pad = np.pad(x_pad, pad_width=[0, pad_width], constant_values=[x[-1]])

    rol_mean = rolling_mean(x_pad, windowsize=windowsize, sample_rate=fs)
    peaks = detect_peaks(x_pad, rol_mean, ma_perc=ma_perc, sample_rate=fs)['peaklist']
    peaks = np.array(peaks) - pad_width - 1
    
    flip = flip_signal(x_pad)
    rol_mean = rolling_mean(flip, windowsize=windowsize, sample_rate=fs)
    valleys = detect_peaks(flip, rol_mean, ma_perc=ma_perc, sample_rate=fs)['peaklist']
    valleys = np.array(valleys) - pad_width - 1

    # check no peaks are valleys
    if np.isin(peaks, valleys).any() | (len(peaks) < 2) | (len(valleys) < 2):
        return -1

    # check that peaks and valleys are in order
    hist = np.digitize(valleys, peaks)
    if not np.array([hist[i] == hist[i+1] - 1 for i in range(len(hist) - 1)]).all():
        return -2

    neg_len = lambda x : len(x) * -1
    if len(peaks) <= len(valleys):
        beats = sorted(np.split(x, valleys), key=neg_len)

        aligned_beats = [beats[0]]

        for i, b in enumerate(beats[1::]):
            b_new = np.pad(b, pad_width=[len(beats[0]) - len(b), 0])
            aligned_beats.append(b_new)
    else:
        beats = sorted(np.split(x, valleys[1::]), key=neg_len)

        aligned_beats = [beats[0]]

        for i, b in enumerate(beats[1::]):
            b_new = np.pad(b, pad_width=[np.abs(peaks[0] - (peaks[i + 1] - valleys[i])), 0])
            aligned_beats.append(b_new)

    aligned_beats = [b for b in aligned_beats if len(b[b != 0]) > fs / 2]
    idx = [(i, j) for ((i, _), (j, _)) in itertools.combinations(enumerate([i for i in range(len(aligned_beats))]), 2)]

    s = 0
    for i, j in idx:
        beat1, beat2 = make_equal_len(aligned_beats[i], aligned_beats[j])
        s += get_similarity(beat1, beat2)
    try:
        sim = s / len(aligned_beats)
        if get_bp:
            sbp = np.mean(x[peaks])
            dbp = np.mean(x[valleys])
            return sim, sbp, dbp
        else:
            return sim
    except ZeroDivisionError:
        return -3

client = firestore.Client()

def onNewSample(data, context):
    path_parts = context.resource.split('/documents/')[1].split('/')
    collection_path = path_parts[0]
    document_path = '/'.join(path_parts[1:])

    affected_doc = client.collection(collection_path).document(document_path)

    sample_id = data["value"]["fields"]["sample_id"]["integerValue"]
    username = data["value"]["fields"]["username"]["stringValue"]
    ppg = data["value"]["fields"]["ppg"]["arrayValue"]
    result = Preprocessor(
        ppg=ppg,
        fs=125,
    ).run()
    result['sample_id'] = sample_id
    result['username'] = username
    client.collection('processed_sample').add(result)
    affected_doc.set({u'processed': True})