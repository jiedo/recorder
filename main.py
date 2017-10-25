#!/usr/bin/env python2

import pygame
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

SUBMODE_NONE = 0
SUBMODE_PLAYSOUND = 1
SUBMODE_RECORDSOUND = 2


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
    submode = SUBMODE_NONE
    display_need_reflash = True
    done = 0
    start_time = 0
    pure_left_button_up = False
    pure_right_button_up = False
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
            display_need_reflash = True
            if mode == MODE_LIBRARY:
                feedback = library.on_event(e)
            elif mode == MODE_PAGE:
                feedback = page.on_event(e)
            # if feedback:
            #     say(feedback)

            ### press RETURN
            if e.type == pygame.KEYUP and e.key == pygame.K_RETURN:
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
                elif mode == MODE_PAGE:
                    mode = MODE_LIBRARY
                    page.store_page()
                    say("back to library")

            ### press ESC
            if e.type == pygame.QUIT or (e.type == pygame.KEYUP and e.key == pygame.K_ESCAPE):
                #Exit page mode or Quit
                if mode == MODE_LIBRARY:
                    library.store_library()
                    done = 1
                    break
                elif mode == MODE_PAGE:
                    mode = MODE_LIBRARY
                    page.store_page()
                    say("back to library")

            ### mouse
            if e.type == pygame.MOUSEBUTTONDOWN:
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

                # press button1 + button3 at the sametime, beside, without any other button pressed
                if button3 and button1 and (e.button == 1 or e.button == 3):
                    # enter record mode
                    submode = SUBMODE_RECORDSOUND
                    start_time = time.time()
                    recorder.start()

            elif e.type == pygame.MOUSEBUTTONUP:
                button1, button2, button3 = pygame.mouse.get_pressed()

                # use wheel
                if e.button == 4 or e.button == 5:
                    # cancel recording
                    if submode == SUBMODE_RECORDSOUND:
                        submode = SUBMODE_NONE
                    continue

                if mode == MODE_LIBRARY:
                    filename, create_time = library.get_current_page_sound_filename()
                elif mode == MODE_PAGE:
                    filename, create_time = page.get_current_word_sound_filename()

                # only left click
                if e.button == 1 and pure_left_button_up:
                    pure_left_button_up = False

                    if mode == MODE_LIBRARY:
                        # enter page mode
                        results = library.get_current_page_id()
                        if not results:
                            continue
                        shelf_id, book_id, page_id, _ = results
                        say("load page %d" % page_id)
                        page.load_page(page_id)
                        mode = MODE_PAGE
                        continue
                    elif mode == MODE_PAGE:
                        word = page.get_current_word()
                        if word['type'] == 'Close':
                            mode = MODE_LIBRARY
                            page.store_page()
                            say("back to library")
                        elif word['type'] == 'Word':
                            say(word['title'])
                        elif word['type'] == 'Time':
                            say(time.ctime())

                # only right click
                if e.button == 3 and pure_right_button_up:
                    pure_right_button_up = False

                    # enter playsound mode
                    if create_time > 0:
                        submode = SUBMODE_PLAYSOUND
                        #play(filename)
                    else:
                        say("no sound")

                # release button1 + button3
                if (e.button == 1 or e.button == 3) and (not button1 and not button3):
                    # save the audio data
                    if submode != SUBMODE_RECORDSOUND:
                        continue
                    submode = SUBMODE_NONE
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

        if submode == SUBMODE_RECORDSOUND:
            recorder.breath()
        clock.tick(50)
    recorder.terminate()


# if python says run, then we should run
if __name__ == '__main__':
    main()
