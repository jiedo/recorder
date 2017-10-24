#!/usr/bin/env python2

"""A simple starfield example. Note you can move the 'center' of
the starfield by leftclicking in the window. This example show
the basics of creating a window, simple pixel plotting, and input
event management"""

import os
import wave
import pyaudio
import math, pygame
from pygame.locals import *
import time
from library import Library
from page import Page
from sound import play, say, Recorder

#constants
WIN_HEIGHT = 3840
WIN_WIDTH = 2160
WINSIZE = [WIN_WIDTH, WIN_HEIGHT]
SIZEBLOCK = 30

MODE_LIBRARY = 1
MODE_PAGE = 2

def main():
    clock = pygame.time.Clock()
    pygame.init()
    screen = pygame.display.set_mode(WINSIZE)
    pygame.display.set_caption('pygame Stars Example')
    black = 20, 20, 20
    screen.fill(black)

    library = Library(WIN_WIDTH, SIZEBLOCK)
    page = Page(WIN_WIDTH, SIZEBLOCK)
    recorder = Recorder()
    library.load_library()
    mode = MODE_LIBRARY

    done = 0
    start_time = 0
    pure_left_button_up = False
    pure_right_button_up = False
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
            # if feedback:
            #     say(feedback)

            ### keys
            if (e.type == KEYUP and e.key == K_RETURN) or (e.type == MOUSEBUTTONDOWN and e.button == 2):
            #Exit or Enter page mode
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
                    say("back to library")

            #Exit page mode or Quit
            if e.type == QUIT or (e.type == KEYUP and e.key == K_ESCAPE):
                if mode == MODE_LIBRARY:
                    library.store_library()
                    done = 1
                    break
                else:
                    mode = MODE_LIBRARY
                    page.store_page()
                    say("back to library")

            ### mouse
            if e.type == MOUSEBUTTONDOWN:
                button1, button2, button3 = pygame.mouse.get_pressed()
                # check one click
                if button1:
                    pure_left_button_up = True
                if button2 or button3 or e.button != 1:
                    pure_left_button_up = False
                if button3:
                    pure_right_button_up = True
                if button1 or button2 or e.button != 3:
                    pure_right_button_up = False

                # Start record
                if button3 and button1 and (e.button == 1 or e.button == 3):
                    start_time = time.time()
                    recorder.start()

            elif e.type == MOUSEBUTTONUP:
                button1, button2, button3 = pygame.mouse.get_pressed()
                # cancel recording
                if e.button == 4 or e.button == 5:
                    recorder.cancel()
                    continue
                if mode == MODE_LIBRARY:
                    filename, create_time = library.get_current_page_sound_filename()
                else:
                    filename, create_time = page.get_current_word_sound_filename()

                # only left click, then enter
                if e.button == 1 and pure_left_button_up:
                    pure_left_button_up = False

                    if mode == MODE_LIBRARY:
                        results = library.get_current_page_id()
                        if not results:
                            continue
                        shelf_id, book_id, page_id, _ = results
                        say("load page %d" % page_id)
                        page.load_page(page_id)
                        mode = MODE_PAGE
                        continue
                    else:
                        word = page.get_current_word()
                        if word['type'] == 'Close':
                            mode = MODE_LIBRARY
                            page.store_page()
                            say("back to library")
                        elif word['type'] == 'Word':
                            say(word['title'])
                        elif word['type'] == 'Time':
                            say(time.ctime())

                # only right click, then play
                if e.button == 3 and pure_right_button_up:
                    pure_right_button_up = False
                    if create_time > 0:
                        play(filename)
                    else:
                        say("no sound")
                # save the audio data
                if not button3 and not button1:
                    if not recorder.isrecording():
                        continue
                    if not filename:
                        recorder.cancel()
                        continue
                    end_time = time.time()
                    if int(end_time - start_time) < 1:
                        recorder.cancel()
                        continue
                    if mode == MODE_LIBRARY:
                        library.set_current_page(int(start_time*1000), int(end_time*1000))
                    else:
                        page.set_current_word(int(start_time*1000), int(end_time*1000))
                    recorder.flush(filename)

        recorder.breath()
        clock.tick(50)
    recorder.terminate()





# if python says run, then we should run
if __name__ == '__main__':
    main()
