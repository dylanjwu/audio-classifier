import os
import sys
import shutil
import librosa
import numpy as np
import soundfile as sf
from pickle import dump
import sklearn.preprocessing
from pydub import AudioSegment
from classifiers.music_other_knn import MusicKNN



class MusicAgent:
    
    def __init__(self,audio):
        self.audio = audio
        self.segments = []

    # def procces_audio(self):


    def segment_audio(self,seconds):
        #can change to from_file if no difference in wav
        full_audio = AudioSegment.from_wav(self.audio)
        duration = full_audio.duration_seconds
        num_segments = int(duration//seconds)
        if os.path.isdir('segments'):
            shutil.rmtree('segments')
        os.mkdir('segments')
        for segment in range(num_segments):
            t0 = segment * seconds * 1000
            t1 = t0 + (seconds * 1000)
            full_audio[t0:t1].export('segments/file_{}.wav'.format(segment), format='wav')
            audio, samplerate = sf.read('segments/file_{}.wav'.format(segment))
            sf.write('segments/file_{}.wav'.format(segment), audio, samplerate, subtype='PCM_16')

    def extract_features(self, directory):
        signals = np.array([librosa.load('{}/{}'.format(directory,f))[0] for f in os.listdir(directory)])

        zcr = np.array([librosa.feature.zero_crossing_rate(x)[0] for x in signals])
        sc = np.array([librosa.feature.spectral_centroid(y=x)[0] for x in signals])
        mfcc = librosa.feature.mfcc(y=signals)

        zcr_mean = np.mean(zcr, axis=1, keepdims=True)
        sc_mean = np.mean(sc, axis=1, keepdims=True)
        mfcc_mean = np.mean(mfcc, axis=2)

        zcr_var = np.var(zcr, axis=1, keepdims=True)
        sc_var = np.var(sc, axis=1, keepdims=True)
        mfcc_var = np.var(mfcc, axis=2)

        feature_table = np.hstack((zcr_mean,sc_mean,mfcc_mean,zcr_var,sc_var,mfcc_var))
        
        return feature_table


class TrainingBuilder(MusicAgent):

    def __init__(self, music_dir, other_dir):
        self.music_dir = music_dir
        self.other_dir = other_dir

    def create_training(self):
        music_features = np.array([])
        for directory in self.music_dir:
            if music_features.size == 0:
                music_features = super().extract_features(directory)
            else:
                music_features = np.vstack((other_features,super().extract_features(directory)))
        music_labels = np.ones((music_features.shape[0],1))

        other_features = np.array([])
        for directory in self.other_dir:
            if other_features.size == 0:
                other_features = super().extract_features(directory)
            else:
                other_features = np.vstack((other_features,super().extract_features(directory)))
        other_labels = np.zeros((other_features.shape[0],1))

        labels = np.vstack((music_labels,other_labels))

        feature_table = np.vstack((music_features,other_features))
        feature_table_normalized = self.normalize(feature_table)

        training_data = np.hstack((feature_table_normalized,labels))
        print(training_data.shape)
        np.savetxt('data.csv', training_data, delimiter=',')

    def normalize(self, features):
        scaler = sklearn.preprocessing.StandardScaler().fit(features)
        features_normalized = scaler.transform(features)
        return features_normalized 
        
        
                



def main(argv):
    # ma = MusicAgent(argv[1])
    # print(ma.audio)
    # ma.segment_audio(3)
    # ma.extract_features()
    training = TrainingBuilder(['music_wav_3sec'],['other_wav1_3sec','other_wav2_3sec','other_wav3_3sec'])
    training.create_training()


if __name__ == '__main__':
    main(sys.argv)


