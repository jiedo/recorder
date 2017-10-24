#!/usr/bin/env python2

"""A simple starfield example. Note you can move the 'center' of
the starfield by leftclicking in the window. This example show
the basics of creating a window, simple pixel plotting, and input
event management"""

import os
import wave
import pyaudio
import tempfile
import subprocess
import random, math, pygame
from pygame.locals import *
import time


def activeListenToAllOptions(audio_object):
    """
        Records until a second of silence or times out after 12 seconds
        Returns a list of the matching options or None
    """
    RATE = 16000
    CHUNK = 1024
    LISTEN_TIME = 4
    play('beep_hi.wav')
    # prepare recording stream
    stream = audio_object.open(format=pyaudio.paInt16,
                              channels=1,
                              rate=RATE,
                              input=True,
                              frames_per_buffer=CHUNK)
    frames = []
    # increasing the range # results in longer pause after command
    # generation
    for i in range(0, RATE / CHUNK * LISTEN_TIME):
        data = stream.read(CHUNK)
        frames.append(data)

    play('beep_lo.wav')
    # save the audio data
    stream.stop_stream()
    stream.close()

    filename = "rec/%d.%d" % (int(time.time()), 4)
    with open(filename, "w+b") as f:
        wav_fp = wave.open(f, 'wb')
        wav_fp.setnchannels(1)
        wav_fp.setsampwidth(pyaudio.get_sample_size(pyaudio.paInt16))
        wav_fp.setframerate(RATE)
        wav_fp.writeframes(''.join(frames))
        wav_fp.close()


def play(filename):
    # FIXME: Use platform-independent audio-output here
    # See issue jasperproject/jasper-client#188
    soundObj = pygame.mixer.Sound(filename)
    soundObj.play()
    return
    cmd = ['aplay', '-D', 'default', str(filename)]
    with tempfile.TemporaryFile() as f:
        subprocess.call(cmd, stdout=f, stderr=f)
        f.seek(0)
        output = f.read()


def say(phrase):
    voice = "en"
    pitch_adjustment = 40
    words_per_minute = 200

    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        fname = f.name
    cmd = ['espeak', '-v', voice,
                     '-p', str(pitch_adjustment),
                     '-s', str(words_per_minute),
                     '-w', fname,
                     phrase]

    with tempfile.TemporaryFile() as f:
        subprocess.call(cmd, stdout=f, stderr=f)
        f.seek(0)
        output = f.read()
    play(fname)
    os.remove(fname)


class Recorder():
    RATE = 22000
    CHUNK = 1024

    def __init__(self):
        self.audio_object = pyaudio.PyAudio()
        self.frames = []
        self.stream = None
        self.recording = False

    def cancel(self):
        self.recording = False

    def isrecording(self):
        return self.recording

    def start(self):
        self.recording = True
        play('beep_hi.wav')
        # prepare recording stream
        self.stream = self.audio_object.open(format=pyaudio.paInt16,
                   channels=1,
                   rate=self.RATE,
                   input=True,
                   frames_per_buffer=self.CHUNK)
        self.frames = []

    def breath(self):
        if self.recording:
            # 0.1 second delay
            for i in range(0, self.RATE / self.CHUNK /10):
                data = self.stream.read(self.CHUNK)
                self.frames.append(data)

    def terminate(self):
        self.audio_object.terminate()

    def flush(self, filename):
        if self.recording:
            self.recording = False
            self.stream.stop_stream()
            self.stream.close()
            with open(filename, "w+b") as f:
                wav_fp = wave.open(f, 'wb')
                wav_fp.setnchannels(1)
                wav_fp.setsampwidth(pyaudio.get_sample_size(pyaudio.paInt16))
                wav_fp.setframerate(self.RATE)
                wav_fp.writeframes(''.join(self.frames))
                wav_fp.close()
            play('beep_lo.wav')
