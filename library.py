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
import json

#constants
WIN_HEIGHT = 1024
WIN_WIDTH = 1280
WINSIZE = [WIN_WIDTH, WIN_HEIGHT]
SIZEBLOCK = 20

g_library = {}
g_rect_need_draw = []


def load_library():
    global g_library
    g_library = json.loads(open("library.json").read())


def store_library():
    global g_library
    g_library_string = json.dumps(g_library)
    open("library.json", "w").write(g_library_string)


def update_library_display(surface):
    global g_rect_need_draw
    g_rect_need_draw.reverse()
    for color, rect in g_rect_need_draw:
        pygame.draw.rect(surface, color, rect, 0)
    g_rect_need_draw = []


def draw_rect(surface, color, rect, width=1):
    global g_rect_need_draw
    times = 1
    offset = width * times
    g_rect_need_draw += [(color, rect.inflate(-offset, -offset))]

    # pygame.draw.rect(surface, color, rect.inflate(-offset, -offset), times)


def draw_page(surface, page, is_current_shelf, is_current_book, is_current, rect):
    "used to draw (and clear) the stars"

    color = (40, 40, 40)
    if is_current:
        if is_current_shelf:
            if is_current_book:
                color = (0, 180, 180)
            else:
                color = (180, 180, 180)

    draw_rect(surface, color, rect, width=3)
    #return width, height


def draw_book(surface, book, is_current_shelf, is_current, pos=0):
    "used to draw (and clear) the stars"
    pagei = book["mark"]

    left = 0
    top  = pos

    width = SIZEBLOCK
    height = SIZEBLOCK

    if is_current_shelf:
        color = (10, 10, 10)
        if is_current:
            color = (110, 110, 110)
    else:
        color = (1, 1, 1)

    # book_rect = pygame.Rect(0, pos, WIN_WIDTH, height)
    # draw_rect(surface, color, book_rect, width=6)

    for idx, page in enumerate(book["pages"]):
        rect = pygame.Rect(left, top, width, height)
        draw_page(surface, page, is_current_shelf, is_current, idx==pagei, rect)

        left += width
        if width > WIN_WIDTH - left:
            left = 0
            top += height

    book_rect = pygame.Rect(0, pos, WIN_WIDTH, top+height - pos)
    draw_rect(surface, color, book_rect, width=2)
    return top+height - pos


def draw_shelf(surface, shelf, is_current, pos=0):
    "used to draw (and clear) the stars"
    booki = shelf["mark"]
    top = pos
    for idx, book in enumerate(shelf["books"]):
        height = draw_book(surface, book, is_current, idx==booki, top)
        top += height

    # if is_current:
    #     color = (100, 100, 100)
    # else:
    color = (0, 0, 0)

    shelf_rect = pygame.Rect(0, pos, WIN_WIDTH, top - pos)
    draw_rect(surface, color, shelf_rect, width=1)
    return top - pos


def draw_library(surface, pos=0):
    "used to draw (and clear) the stars"
    global g_library

    if "mark" not in g_library:
        return

    shelfi = g_library["mark"]

    for idx, shelf in enumerate(g_library["shelfs"]):
        height = draw_shelf(surface, shelf, idx==shelfi, pos)
        pos += height
    update_library_display(surface)


def new_shelf():
    global g_library
    shelf = {
        'mark': 0,
        'id': 0,
        'title': "abc",
        'books': []
    }

    if 'shelfs' not in g_library:
        g_library['shelfs'] = [shelf]
        g_library['mark'] = 0
    else:
        g_library['shelfs'] += [shelf]


def new_book():
    global g_library

    current_shelf_idx = g_library['mark']
    current_shelf = g_library['shelfs'][current_shelf_idx]

    book = {
        'mark': 0,
        'id': 0,
        'title': "abc",
        'pages': [0]
    }
    current_shelf['books'] += [book]


def new_page():
    global g_library

    current_shelf_idx = g_library['mark']
    current_shelf = g_library['shelfs'][current_shelf_idx]

    length = len(current_shelf['books'])
    if length <= 0:
        return

    current_book_idx = current_shelf['mark']
    current_book = current_shelf['books'][current_book_idx]
    current_book['pages'] += [0]


def next_shelf():
    global g_library

    length = len(g_library['shelfs'])
    if length <= 0:
        return
    current_idx = g_library['mark']

    current_idx += 1
    if current_idx >= length:
        return
    g_library['mark'] = current_idx


def prev_shelf():
    global g_library

    length = len(g_library['shelfs'])
    if length <= 0:
        return
    current_idx = g_library['mark']
    current_idx -= 1
    if current_idx < 0:
        return

    g_library['mark'] = current_idx


def next_book():
    global g_library

    length = len(g_library['shelfs'])
    if length <= 0:
        return False

    current_shelf_idx = g_library['mark']
    current_shelf = g_library['shelfs'][current_shelf_idx]

    length = len(current_shelf['books'])
    if length <= 0:
        return False

    current_idx = current_shelf['mark']
    current_idx += 1
    if current_idx >= length:
        return False

    current_shelf['mark'] = current_idx
    return True


def prev_book():
    global g_library

    length = len(g_library['shelfs'])
    if length <= 0:
        return False

    current_shelf_idx = g_library['mark']
    current_shelf = g_library['shelfs'][current_shelf_idx]

    length = len(current_shelf['books'])
    if length <= 0:
        return False

    current_idx = current_shelf['mark']
    current_idx -= 1
    if current_idx < 0:
        return False

    current_shelf['mark'] = current_idx
    return True


def next_page():
    global g_library

    length = len(g_library['shelfs'])
    if length <= 0:
        return

    current_shelf_idx = g_library['mark']
    current_shelf = g_library['shelfs'][current_shelf_idx]

    length = len(current_shelf['books'])
    if length <= 0:
        return

    current_book_idx = current_shelf['mark']
    current_book = current_shelf['books'][current_book_idx]

    length = len(current_book['pages'])
    if length <= 0:
        return

    current_idx = current_book['mark']
    current_idx += 1
    if current_idx >= length:
        return
    current_book['mark'] = current_idx


def prev_page():
    global g_library

    length = len(g_library['shelfs'])
    if length <= 0:
        return

    current_shelf_idx = g_library['mark']
    current_shelf = g_library['shelfs'][current_shelf_idx]

    length = len(current_shelf['books'])
    if length <= 0:
        return

    current_book_idx = current_shelf['mark']
    current_book = current_shelf['books'][current_book_idx]

    length = len(current_book['pages'])
    if length <= 0:
        return

    current_idx = current_book['mark']
    current_idx -= 1
    if current_idx < 0:
        return
    current_book['mark'] = current_idx



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
    clock = pygame.time.Clock()
    #initialize and prepare screen
    pygame.init()
    screen = pygame.display.set_mode(WINSIZE)
    pygame.display.set_caption('pygame Stars Example')
    white = 255, 240, 200
    black = 20, 20, 20
    screen.fill(black)

    load_library()

    RATE = 16000
    CHUNK = 1024
    LISTEN_TIME = 1
    frames = []
    stream = None
    recording = False
    done = 0
    start_time = 0
    audio_object = pyaudio.PyAudio()
    last_pos = (0, 0)
    while not done:
        screen.fill(black)
        draw_library(screen)
        pygame.display.update()
        for e in pygame.event.get():
            if e.type == QUIT or (e.type == KEYUP and e.key == K_ESCAPE):
                store_library()
                say("you exit")
                done = 1
                break

            elif e.type == KEYUP:
                if e.key == K_b:
                    new_book()
                elif e.key == K_s:
                    new_shelf()
                elif e.key == K_p:
                    new_page()


            elif e.type == MOUSEMOTION:
                dx, dy = e.rel

                diff = SIZEBLOCK/2

                x, y = last_pos

                if e.buttons[0]:
                    x += dx
                    if x >= diff:
                        next_page()
                        x=0
                    elif x <= -diff:
                        prev_page()
                        x= 0
                else:
                    y += dy
                    if y >= diff:
                        if not next_book():
                            next_shelf()
                        y=0
                    elif y <= -diff:
                        if not prev_book():
                            prev_shelf()
                        y=0

                last_pos = (x, y)

            elif e.type == MOUSEBUTTONDOWN:
                mod = pygame.key.get_mods()

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

                if e.button == 5:
                    if mod & KMOD_CTRL:
                        next_book()
                    elif mod & KMOD_ALT:
                        next_shelf()
                    else:
                        next_page()

                elif e.button == 4:
                    if mod & KMOD_CTRL:
                        prev_book()
                    elif mod & KMOD_ALT:
                        prev_shelf()
                    else:
                        prev_page()


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
                #     filename = "rec/%d.%d" % (int(end_time), int(end_time - start_time))
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
