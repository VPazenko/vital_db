from scipy.signal.windows import hamming
import numpy as np
import neurokit2 as nk


def fir_filter(y, h):
    """z = fir_filter(y, h).
    Returns an iterator that provides a filtered streaming
    signal z based on the iterator y. The signal is obtained
    by applying a Finite Impulse Response (FIR) filter of
    order M with impulse response h.
    y      = iterator {yi}
    h      = {h0,h1,...,hM}
    """
    history = np.zeros_like(h)
    for yi in y:
        history = np.append(history[1:], yi)
        zi = sum(history[i]*h[h.size - i - 1] for i in range(h.size))
        yield zi


#Data store and convert:
class Data_store:
    """
    This class allows you to store information in raw form, 
    and the methods allow you to do some processing of the ECG signal 
    """
    def __init__(self, raw_df):
        self.raw_data = raw_df

    def fourier_transform(self, ecg):
        """
        Input: 1. ecg - raw ECG signal

        Function use a fourier filter to smooth the signal

        Output: ecg_fourier - smoothed signal
        """
        # Create filter (generate impuls respons)
        f = np.fft.fftshift(np.fft.fftfreq(5000, 1/500))
        c_add = np.linspace(-1.0, 1.0, 399, endpoint=False)
        c_add = np.concatenate([np.zeros(2301), np.abs(c_add[::-1])])
        c_add = np.concatenate([c_add, np.zeros(2300)])
        c_filter = ((np.abs(f) >= 20) + c_add )
        impuls_respons = np.fft.ifft(np.fft.ifftshift(c_filter) / 5000.0, norm='forward').real
        elem = 100
        finite_impuls_respons = np.roll(impuls_respons, elem//2)[:elem] * hamming(elem)
        
        # Use filter
        ecg_fourier = np.array([zi for zi in fir_filter(ecg, finite_impuls_respons)])
        
        return ecg_fourier

    def find_peaks_and_hr(self, ecg):
        """
        Input: 1. ecg - df that contain column ('ECG_f') with smoothed ECG signal

        Function use Neurokit library to find all peaks and calculated Hr

        Output: 1. df_peaks - initial df, but only the rows with the peak index 
        (new column - label of peak occurrence) and a new column with the calculated Hr.
                2. info['ECG_R_Peaks_Uncorrected'] - list of peaks indexes
        """
        ecg = ecg.dropna(subset=['ECG_f'])
        ecg = ecg.reset_index()
        signals, info = nk.ecg_peaks(ecg.loc[:,'ECG_f'], sampling_rate=500, correct_artifacts=True, show=False)
        ecg['peaks'] = np.nan
        ecg.loc[info['ECG_R_Peaks_Uncorrected'], 'peaks'] = 1
        df_peaks = ecg.dropna(subset=['peaks'])
        df_peaks.loc[:,'diff'] = df_peaks.loc[:,'Time'].diff() 
        df_peaks.loc[:,'hr'] = 60 / df_peaks.loc[:,'diff']
        df_peaks = df_peaks.drop('diff', axis=1)               
        return df_peaks, info['ECG_R_Peaks_Uncorrected']
    

if __name__ == "__main__":
    print(__doc__)
else:
    print(f"Module '{__name__}' is imported successfully!\n")







