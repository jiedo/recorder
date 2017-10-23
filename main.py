#!/usr/bin/env python2

"""A simple starfield example. Note you can move the 'center' of
the starfield by leftclicking in the window. This example show
the basics of creating a window, simple pixel plotting, and input
event management"""

import os
import wave
import pyaudio
import random, math, pygame
from pygame.locals import *
import time
from library import Library
from sound import play, say

#constants
WIN_HEIGHT = 3840
WIN_WIDTH = 2160
WINSIZE = [WIN_WIDTH, WIN_HEIGHT]
SIZEBLOCK = 30


def main():
    "This is the starfield code"
    #create our starfield
    random.seed()
    clock = pygame.time.Clock()
    #initialize and prepare screen
    pygame.init()
    screen = pygame.display.set_mode(WINSIZE)
    pygame.display.set_caption('pygame Stars Example')
    white = 255, 240, 200
    black = 20, 20, 20
    screen.fill(black)

    library = Library(WIN_WIDTH, SIZEBLOCK)
    library.load_library()

    RATE = 16000
    CHUNK = 1024
    LISTEN_TIME = 1
    frames = []
    stream = None
    recording = False
    done = 0
    start_time = 0
    audio_object = pyaudio.PyAudio()
    while not done:
        screen.fill(black)
        library.draw_library(screen)

        pygame.display.update()

        for e in pygame.event.get():
            library.on_event(e)

            if e.type == QUIT or (e.type == KEYUP and e.key == K_ESCAPE):
                say("you exit")
                done = 1
                break
            elif e.type == MOUSEBUTTONDOWN:
                pass
                # mod = pygame.key.get_mods()
                # if e.button == 1:
                #     recording = True
                #     play('beep_hi.wav')
                #     start_time = time.time()
                #     # prepare recording stream
                #     stream = audio_object.open(format=pyaudio.paInt16,
                #                channels=1,
                #                rate=RATE,
                #                input=True,
                #                frames_per_buffer=CHUNK)
                #     frames = []

            elif e.type == MOUSEBUTTONUP:
                pass
                # if e.button == 1:
                #     # save the audio data
                #     recording = False
                #     stream.stop_stream()
                #     stream.close()
                #     end_time = time.time()
                #     if int(end_time - start_time) < 1:
                #         continue
                #     filename = "sounds/%d.%d" % (int(end_time), int(end_time - start_time))
                #     with open(filename, "w+b") as f:
                #         wav_fp = wave.open(f, 'wb')
                #         wav_fp.setnchannels(1)
                #         wav_fp.setsampwidth(pyaudio.get_sample_size(pyaudio.paInt16))
                #         wav_fp.setframerate(RATE)
                #         wav_fp.writeframes(''.join(frames))
                #         wav_fp.close()
                #     play('beep_lo.wav')

        if recording:
            for i in range(0, RATE / CHUNK * LISTEN_TIME/10):
                data = stream.read(CHUNK)
                frames.append(data)

        clock.tick(50)

    audio_object.terminate()


# if python says run, then we should run
if __name__ == '__main__':
    main()
