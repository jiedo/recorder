#!/usr/bin/env python2

import pygame
import time
import sys
import os
import copy

from library import Library
from page import Page
from page_loader import VoicePageLoader, WikiPageLoader, DirPageLoader, LdocePageListLoader, LdocePageLoader
from sound import play, say, Recorder, Player
import event_checker

#constants
WIN_HEIGHT = 3840
WIN_WIDTH = 2160
SIZEBLOCK = 30

WIN_HEIGHT = 800
WIN_WIDTH = 1280
SIZEBLOCK = 20
if len(sys.argv) > 3:
    WIN_HEIGHT = int(sys.argv[1])
    WIN_WIDTH = int(sys.argv[2])
    SIZEBLOCK = int(sys.argv[3])

WINSIZE = [WIN_WIDTH, WIN_HEIGHT]

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
    player = Player(WIN_WIDTH, WIN_HEIGHT, SIZEBLOCK)
    library.load_library()
    mode = MODE_LIBRARY
    last_mode = SUBMODE_NONE
    display_need_reflash = True
    done = 0
    start_time = 0
    last_page = None
    event_checker_obj = event_checker.EventChecker()
    last_flash_display_time = time.time()
    while not done:
        if mode == SUBMODE_PLAYSOUND:
            if (time.time() - last_flash_display_time) * 100 > 10:
                display_need_reflash = True
                last_flash_display_time = time.time()

        if display_need_reflash:
            screen.fill(black)
            if mode == MODE_LIBRARY or (mode != MODE_PAGE and last_mode == MODE_LIBRARY):
                library.draw_library(screen)
            elif mode == MODE_PAGE or (mode != MODE_LIBRARY and last_mode == MODE_PAGE):
                page.draw_page(screen)

            if mode == SUBMODE_PLAYSOUND:
                player.draw_player(screen)

            pygame.display.update()
            display_need_reflash = False

        for event in pygame.event.get():
            display_need_reflash = True
            action, pos = event_checker_obj.do(event)
            filename = ""
            if mode == MODE_LIBRARY:
                feedback, filename = library.on_event(event)
                if action == event_checker.EVENT_QUIT:
                    library.store_library()
                    done = 1
                    break
                elif action == event_checker.EVENT_LEFT_CLICK or action == event_checker.EVENT_ENTER:
                    current_page = library.get_current_page()
                    if not current_page:
                        say("load page, but no page here.")
                        continue

                    if current_page['type'] == 'Voice':
                        say("load page voice")
                        PageLoader = VoicePageLoader
                    elif current_page['type'] == 'Wiki':
                        say("load page wiki")
                        PageLoader = WikiPageLoader
                    elif current_page['type'] == 'Dir':
                        say("load page dir")
                        PageLoader = DirPageLoader
                    elif current_page['type'] == 'Ldoce':
                        say("load page Ldoce")
                        PageLoader = LdocePageListLoader
                    else:
                        say("ignored page type: %s" % current_page['type'])
                        continue
                    page.load_page(PageLoader(current_page))
                    mode = MODE_PAGE

            elif mode == MODE_PAGE:
                feedback, filename = page.on_event(event)
                if action == event_checker.EVENT_QUIT or (action == event_checker.EVENT_BOTH and current_page['type'] != 'Voice'):
                    if last_page and current_page['type'] == 'Ldoce':
                        say("load page Ldoce")
                        PageLoader = LdocePageListLoader
                        page.load_page(PageLoader(current_page))
                        page.page = last_page
                        last_page = None
                    else:
                        mode = MODE_LIBRARY
                        page.store_page()
                        say("back to library")
                    continue

                elif action == event_checker.EVENT_LEFT_CLICK or action == event_checker.EVENT_ENTER:
                    current_word = page.get_current_word()
                    if current_word['type'] == 'Close':
                        mode = MODE_LIBRARY
                        page.store_page()
                        say("back to library")
                        continue
                    elif current_word['type'] == 'Time':
                        # fixme: move to page-loader
                        say(time.ctime())
                    elif current_word['type'] == 'Ldoce':
                        PageLoader = LdocePageLoader
                        inner_page = copy.deepcopy(current_page)
                        inner_page["data"] = current_word["data"]
                        last_page = page.page
                        page.load_page(PageLoader(inner_page))

            elif mode == SUBMODE_PLAYSOUND:
                feedback = player.on_action(action, pos, event_checker_obj)
                if action == event_checker.EVENT_RIGHT_CLICK or action == event_checker.EVENT_QUIT:
                    mode = last_mode
                    say("quit play")
                    continue

            if filename and os.path.exists(filename):
                player.load(filename)
            elif feedback:
                say(feedback)

            #################
            if action == event_checker.EVENT_RIGHT_CLICK or action == event_checker.EVENT_SPACE:
                if mode == MODE_LIBRARY:
                    filename, create_time = library.get_current_page_sound_filename()
                elif mode == MODE_PAGE:
                    filename, create_time = page.get_current_word_sound_filename()
                else:
                    continue
                # enter playsound mode
                if create_time > 0 and os.path.exists(filename):
                    last_mode, mode = mode, SUBMODE_PLAYSOUND
                    player.load(filename)
                else:
                    say("no sound")

            elif action == event_checker.EVENT_BOTH:
                if mode not in [MODE_LIBRARY, MODE_PAGE]:
                    continue
                # enter record mode
                last_mode, mode = mode, SUBMODE_RECORDSOUND
                start_time = time.time()
                recorder.start()
            elif action == event_checker.EVENT_WHEEL_UP or action == event_checker.EVENT_WHEEL_DOWN:
                # cancel recording
                if mode == SUBMODE_RECORDSOUND:
                    mode = last_mode
                    recorder.flush("sounds/tmp.wav")
            elif action == event_checker.EVENT_BOTH_RELEASE:
                # save the audio data
                if mode != SUBMODE_RECORDSOUND:
                    continue
                mode = last_mode
                if mode == MODE_LIBRARY:
                    filename, create_time = library.get_current_page_sound_filename()
                elif mode == MODE_PAGE:
                    filename, create_time = page.get_current_word_sound_filename()
                if not filename:
                    recorder.flush("sounds/tmp.wav")
                    continue
                end_time = time.time()
                if int(end_time - start_time) < 1:
                    recorder.flush("sounds/tmp.wav")
                    continue
                if mode == MODE_LIBRARY:
                    library.set_current_page(int(start_time*1000), int(end_time*1000))
                elif mode == MODE_PAGE:
                    page.set_current_word(int(start_time*1000), int(end_time*1000))
                if os.path.exists(filename):
                    os.rename(filename, "%s.%d" % (filename,start_time))
                recorder.flush(filename)

        clock.tick(50)
    recorder.terminate()


# if python says run, then we should run
if __name__ == '__main__':
    main()
