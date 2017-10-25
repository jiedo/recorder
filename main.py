#!/usr/bin/env python2

import pygame
import time

from library import Library
from page import Page
from sound import play, say, Recorder
from event import EventChecker

#constants
WIN_HEIGHT = 3840
WIN_WIDTH = 2160
WINSIZE = [WIN_WIDTH, WIN_HEIGHT]
SIZEBLOCK = 30

MODE_LIBRARY = 1
MODE_PAGE = 2

SUBMODE_NONE = 0
SUBMODE_PLAYSOUND = -1
SUBMODE_RECORDSOUND = -2


def main():
    clock = pygame.time.Clock()
    pygame.init()
    screen = pygame.display.set_mode(WINSIZE)
    pygame.display.set_caption('EyeSys')
    black = 20, 20, 20
    screen.fill(black)

    library = Library(WIN_WIDTH, SIZEBLOCK)
    page = Page(WIN_WIDTH, SIZEBLOCK)
    recorder = Recorder()
    library.load_library()
    mode = MODE_LIBRARY
    last_mode = SUBMODE_NONE
    display_need_reflash = True
    done = 0
    start_time = 0

    event_checker = EventChecker()
    while not done:
        if display_need_reflash:
            screen.fill(black)
            if mode == MODE_LIBRARY:
                library.draw_library(screen)
            elif mode == MODE_PAGE:
                page.draw_page(screen)
            pygame.display.update()
            display_need_reflash = False

        for e in pygame.event.get():
            action = event_checker.do(e)
            display_need_reflash = True
            if mode == MODE_LIBRARY:
                feedback = library.on_event(e)
                if action == "quit":
                    library.store_library()
                    done = 1
                    break
                elif action == "enter":
                    results = library.get_current_page_id()
                    if not results:
                        say("ignored")
                        continue
                    shelf_id, book_id, page_id, _ = results
                    say("load page %d" % page_id)
                    page.load_page(page_id)
                    mode = MODE_PAGE
                elif action == "left":
                    # enter page mode
                    results = library.get_current_page_id()
                    if not results:
                        continue
                    shelf_id, book_id, page_id, _ = results
                    say("load page %d" % page_id)
                    page.load_page(page_id)
                    mode = MODE_PAGE
            elif mode == MODE_PAGE:
                feedback = page.on_event(e)
                if action == "quit":
                    mode = MODE_LIBRARY
                    page.store_page()
                    say("back to library")
                elif action == "enter":
                    mode = MODE_LIBRARY
                    page.store_page()
                    say("back to library")
                elif action == "left":
                    word = page.get_current_word()
                    if word['type'] == 'Close':
                        mode = MODE_LIBRARY
                        page.store_page()
                        say("back to library")
                    elif word['type'] == 'Word':
                        say(word['title'])
                    elif word['type'] == 'Time':
                        say(time.ctime())
            elif mode == MODE_PLAYSOUND:
                if action == "quit":
                    mode = MODE_LIBRARY
                    page.store_page()
                    say("back to library")
                elif action == "enter":
                    mode = MODE_LIBRARY
                    page.store_page()
                    say("back to library")
                elif action == "left":
                    word = page.get_current_word()
                    if word['type'] == 'Close':
                        mode = MODE_LIBRARY
                        page.store_page()
                        say("back to library")
                    elif word['type'] == 'Word':
                        say(word['title'])
                    elif word['type'] == 'Time':
                        say(time.ctime())
            # if feedback:
            #     say(feedback)

            #################
            if action == "right":
                if mode == MODE_LIBRARY:
                    filename, create_time = library.get_current_page_sound_filename()
                elif mode == MODE_PAGE:
                    filename, create_time = page.get_current_word_sound_filename()
                # enter playsound mode
                if create_time > 0:
                    last_mode, mode = mode, SUBMODE_PLAYSOUND
                    #play(filename)
                else:
                    say("no sound")

            elif action == "both":
                # enter record mode
                last_mode, mode = mode, SUBMODE_RECORDSOUND
                start_time = time.time()
                recorder.start()
            elif action == "wheel":
                # cancel recording
                if mode == SUBMODE_RECORDSOUND:
                    mode = last_mode
            elif action == "!both":
                # save the audio data
                if mode != SUBMODE_RECORDSOUND:
                    continue
                mode = last_mode
                if mode == MODE_LIBRARY:
                    filename, create_time = library.get_current_page_sound_filename()
                elif mode == MODE_PAGE:
                    filename, create_time = page.get_current_word_sound_filename()
                if not filename:
                    continue
                end_time = time.time()
                if int(end_time - start_time) < 1:
                    continue
                if mode == MODE_LIBRARY:
                    library.set_current_page(int(start_time*1000), int(end_time*1000))
                elif mode == MODE_PAGE:
                    page.set_current_word(int(start_time*1000), int(end_time*1000))
                recorder.flush(filename)

        if mode == SUBMODE_RECORDSOUND:
            recorder.breath()
        clock.tick(50)
    recorder.terminate()


# if python says run, then we should run
if __name__ == '__main__':
    main()
