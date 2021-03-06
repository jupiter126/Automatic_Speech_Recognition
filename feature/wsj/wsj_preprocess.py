#-*- coding:utf-8 -*-
#!/usr/bin/python
''' Automatic Speech Recognition

author:
zzw922cn

date:2017-5-5
'''

from __future__ import print_function
#from __future__ import unicode_literals

import sys
sys.path.append('../')
sys.dont_write_bytecode = True

from core.sigprocess import *
from core.calcmfcc import calcfeat_delta_delta
import scipy.io.wavfile as wav
import numpy as np
import os
import cPickle
import glob
import sklearn
import argparse
from sklearn import preprocessing
from subprocess import check_call, CalledProcessError


def wav2feature(rootdir, save_dir, name, feature_len, win_len=0.02, win_step=0.01, mode='mfcc', seq2seq=False, save=False):
  """
  To run for WSJ corpus, you should download sph2pipe_v2.5 first!
  """
  feat_dir = os.path.join(save_dir, name, mode)
  label_dir = os.path.join(save_dir, name, 'label')
  if not os.path.exists(label_dir):
    os.makedirs(label_dir)
  if not os.path.exists(feat_dir):
    os.makedirs(feat_dir)

  count = 0
  for subdir, dirs, files in os.walk(rootdir):
    for f in files:
      fullFilename = os.path.join(subdir, f)
      filenameNoSuffix =  os.path.splitext(fullFilename)[0]
      if f.endswith('.wv1') or f.endswith('.wav'):
        rate = None
        sig = None
        try:
          (rate,sig)= wav.read(fullFilename)
        except ValueError as e:
          sph2pipe = os.path.join(sph2pipe_dir, 'sph2pipe')
          wav_name = fullFilename.replace('wv1', 'wav')
          check_call(['./sph2pipe', '-f', 'rif', fullFilename, wav_name])
          os.remove(fullFilename)
          print(wav_name)
          (rate,sig)= wav.read(wav_name)
          os.remove(fullFilename)

        feat = calcfeat_delta_delta(sig,rate,win_length=win_len,win_step=win_step,feature_len=feature_len,mode=mode)
        feat = preprocessing.scale(feat)
        feat = np.transpose(feat)
        print(feat.shape)
        labelFilename = filenameNoSuffix + '.label'
        with open(labelFilename,'r') as f:
          characters = f.readline().strip().lower()
        targets = []
        if seq2seq is True:
          targets.append(28)
        for c in characters:
          if c == ' ':
            targets.append(0)
          elif c == "'":
            targets.append(27)
          else:
            targets.append(ord(c)-96)
        if seq2seq is True:
          targets.append(29)
        targets = np.array(targets)
        print(targets)
        count+=1
        print('file index:', count)
        if save:
          featureFilename = os.path.join(feat_dir, filenameNoSuffix.split('/')[-1] +'.npy')
          np.save(featureFilename,feat)
          t_f = os.path.join(label_dir, filenameNoSuffix.split('/')[-1] +'.npy')
          print(t_f)
          np.save(t_f,targets)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='wsj_preprocess',
                                     description='Script to preprocess WSJ data')
    parser.add_argument("path", help="Directory of WSJ dataset", type=str)

    parser.add_argument("save", help="Directory where preprocessed arrays are to be saved",
                        type=str)
    parser.add_argument("-n", "--name", help="Name of the dataset",
                        choices=['train_si284', 'test_eval92', 'test_dev'], 
                        type=str, default='train_si284')

    parser.add_argument("-m", "--mode", help="Mode",
                        choices=['mfcc', 'fbank'],
                        type=str, default='mfcc')
    parser.add_argument("--featlen", help='Features length', type=int, default=13)
    parser.add_argument("-s", "--seq2seq", default=False,
                        help="set this flag to use seq2seq", action="store_true")

    parser.add_argument("-wl", "--winlen", type=float,
                        default=0.02, help="specify the window length of feature")

    parser.add_argument("-ws", "--winstep", type=float,
                        default=0.01, help="specify the window step length of feature")

    args = parser.parse_args()
    root_directory = args.path
    save_directory = args.save
    mode = args.mode
    feature_len = args.featlen
    seq2seq = args.seq2seq
    name = args.name
    win_len = args.winlen
    win_step = args.winstep

    if root_directory == '.':
        root_directory = os.getcwd()

    if save_directory == '.':
        save_directory = os.getcwd()

    if not os.path.isdir(root_directory):
        raise ValueError("LibriSpeech Directory does not exist!")

    if not os.path.isdir(save_directory):
        os.makedirs(save_directory)

    wav2feature(root_directory, save_directory, name=name, win_len=win_len, win_step=win_step,
                mode=mode, feature_len=feature_len, seq2seq=seq2seq, save=True)
