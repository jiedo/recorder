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
from page import Page
from sound import play, say

#constants
WIN_HEIGHT = 3840
WIN_WIDTH = 2160
WINSIZE = [WIN_WIDTH, WIN_HEIGHT]
SIZEBLOCK = 30

MODE_LIBRARY = 1
MODE_PAGE = 2

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

    mode = MODE_LIBRARY

    library = Library(WIN_WIDTH, SIZEBLOCK)
    page = Page(WIN_WIDTH, SIZEBLOCK)
    library.load_library()


    RATE = 22000
    CHUNK = 1024
    LISTEN_TIME = 1
    frames = []
    stream = None
    recording = False
    done = 0
    start_time = 0

    pure_right_button_up = True
    audio_object = pyaudio.PyAudio()
    while not done:
        screen.fill(black)

        if mode == MODE_LIBRARY:
            library.draw_library(screen)
        else:
            page.draw_page(screen)

        pygame.display.update()

        for e in pygame.event.get():
            if mode == MODE_LIBRARY:
                feedback = library.on_event(e)
            else:
                feedback = page.on_event(e)
            if feedback:
                say(feedback)

            ### keys
            if (e.type == KEYUP and e.key == K_RETURN) or (e.type == MOUSEBUTTONDOWN and e.button == 2):
                if mode == MODE_LIBRARY:
                    results = library.get_current_page_id()
                    if not results:
                        say("ignored")
                        continue
                    shelf_id, book_id, page_id, _ = results
                    say("load page %d" % page_id)
                    page.load_page(page_id)
                    mode = MODE_PAGE
                    continue
                else:
                    mode = MODE_LIBRARY
                    page.store_page()

            if e.type == QUIT or (e.type == KEYUP and e.key == K_ESCAPE):
                if mode == MODE_LIBRARY:
                    library.store_library()
                    say("you exit")
                    done = 1
                    break
                else:
                    mode = MODE_LIBRARY
                    page.store_page()

            ### mouse
            if e.type == MOUSEBUTTONDOWN:
                button1, button2, button3 = pygame.mouse.get_pressed()
                if button3:
                    pure_right_button_up = True
                if button1 or button2 or e.button != 3:
                    pure_right_button_up = False

                # start record
                if button3 and button1:
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

            elif e.type == MOUSEBUTTONUP:
                button1, button2, button3 = pygame.mouse.get_pressed()
                # play
                if e.button == 3 and pure_right_button_up:
                    pure_right_button_up = False
                    if mode == MODE_LIBRARY:
                        filename, create_time = library.get_current_page_sound_filename()
                    else:
                        filename, create_time = page.get_current_word_sound_filename()
                    if create_time > 0:
                        play(filename)
                    else:
                        say("no sound")

                # save the audio data
                if not button3 and not button1:
                    if recording:
                        recording = False
                        stream.stop_stream()
                        stream.close()
                        end_time = time.time()
                        if int(end_time - start_time) < 1:
                            continue

                        if mode == MODE_LIBRARY:
                            filename, _ = library.get_current_page_sound_filename()
                            if not filename:
                                continue
                            library.set_current_page(int(start_time*1000), int(end_time*1000))
                        else:
                            filename, _ = page.get_current_word_sound_filename()
                            if not filename:
                                continue
                            page.set_current_word(int(start_time*1000), int(end_time*1000))

                        with open(filename, "w+b") as f:
                            wav_fp = wave.open(f, 'wb')
                            wav_fp.setnchannels(1)
                            wav_fp.setsampwidth(pyaudio.get_sample_size(pyaudio.paInt16))
                            wav_fp.setframerate(RATE)
                            wav_fp.writeframes(''.join(frames))
                            wav_fp.close()
                        play('beep_lo.wav')

        if recording:
            # 0.1 second delay
            for i in range(0, RATE / CHUNK * LISTEN_TIME/10):
                data = stream.read(CHUNK)
                frames.append(data)

        clock.tick(50)

    audio_object.terminate()


# if python says run, then we should run
if __name__ == '__main__':
    main()
