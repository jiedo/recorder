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

#constants
WINSIZE = [1280, 1024]
WINCENTER = [320, 240]
NUMSTARS = 15


def init_star():
    "creates new star values"
    dir = random.randrange(100000)
    velmult = random.random()*.6+.4
    vel = [math.sin(dir) * velmult, math.cos(dir) * velmult]
    return vel, WINCENTER[:]


def initialize_stars():
    "creates a new starfield"
    stars = []
    for x in range(NUMSTARS):
        star = init_star()
        vel, pos = star
        steps = random.randint(0, WINCENTER[0])
        pos[0] = pos[0] + (vel[0] * steps)
        pos[1] = pos[1] + (vel[1] * steps)
        vel[0] = vel[0] * (steps * .09)
        vel[1] = vel[1] * (steps * .09)
        stars.append(star)
    return stars


def draw_stars(surface, stars, color):
    "used to draw (and clear) the stars"
    for vel, pos in stars:
        pos = (int(pos[0]), int(pos[1]))
        surface.set_at(pos, color)



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


def main():
    "This is the starfield code"
    #create our starfield
    random.seed()
    stars = initialize_stars()
    clock = pygame.time.Clock()
    #initialize and prepare screen
    pygame.init()
    screen = pygame.display.set_mode(WINSIZE)
    pygame.display.set_caption('pygame Stars Example')
    white = 255, 240, 200
    black = 20, 20, 40
    screen.fill(black)

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
        draw_stars(screen, stars, white)
        pygame.display.update()
        for e in pygame.event.get():
            if e.type == QUIT or (e.type == KEYUP and e.key == K_ESCAPE):
                say("you exit")
                done = 1
                break
            elif e.type == MOUSEBUTTONDOWN:
                if e.button == 1:
                    recording = True
                    play('beep_hi.wav')
                    start_time = time.time()
                    # prepare recording stream
                    stream = audio_object.open(format=pyaudio.paInt16,
                               channels=1,
                               rate=RATE,
                               input=True,
                               frames_per_buffer=CHUNK)
                    frames = []
                else:
                    say("you press button")

            elif e.type == MOUSEBUTTONUP:
                if e.button == 1:
                    # save the audio data
                    recording = False
                    stream.stop_stream()
                    stream.close()

                    end_time = time.time()
                    if int(end_time - start_time) < 1:
                        continue
                    filename = "rec/%d.%d" % (int(end_time), int(end_time - start_time))
                    with open(filename, "w+b") as f:
                        wav_fp = wave.open(f, 'wb')
                        wav_fp.setnchannels(1)
                        wav_fp.setsampwidth(pyaudio.get_sample_size(pyaudio.paInt16))
                        wav_fp.setframerate(RATE)
                        wav_fp.writeframes(''.join(frames))
                        wav_fp.close()

                    play('beep_lo.wav')
                else:
                    say("you release button")

        if recording:
            for i in range(0, RATE / CHUNK * LISTEN_TIME/10):
                data = stream.read(CHUNK)
                frames.append(data)

        clock.tick(50)

    audio_object.terminate()


# if python says run, then we should run
if __name__ == '__main__':
    main()
