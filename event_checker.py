#!/usr/bin/env python2

import pygame
import time


EVENT_NONE = ""
EVENT_ENTER = "enter"
EVENT_QUIT = "quit"
EVENT_BOTH = "both"
EVENT_WHEEL_UP = "wheel-up"
EVENT_WHEEL_DOWN = "wheel-down"
EVENT_LEFT = "left"
EVENT_RIGHT = "right"
EVENT_BOTH_RELEASE = "!both"
EVENT_LEFT_DRAG = "left-drag"
EVENT_RIGHT_DRAG = "right-drag"
EVENT_BOTH_DRAG = "both-drag"
EVENT_MOVE = "move"

class EventChecker():
    def __init__(self):
        self.pure_left_button_up = False
        self.pure_right_button_up = False
        self.pure_left_right_button_up = False
        self.last_pos = None
        self.button1 = False
        self.button2 = False
        self.button3 = False

    def do(self, event):
        action = EVENT_NONE
        pos = (0, 0)
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_RETURN:
                action = EVENT_ENTER
            elif event.key == pygame.K_ESCAPE:
                action = EVENT_QUIT

        if event.type == pygame.QUIT:
            action = EVENT_QUIT

        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos
            self.last_pos = pos
            # check one click
            if event.button == 1:
                self.button1 = True
            if event.button == 2:
                self.button2 = True
            if event.button == 3:
                self.button3 = True
            button1, button2, button3 = self.button1, self.button2, self.button3

            if event.button == 1:
                self.pure_left_button_up = True
            if button2 or button3 or event.button != 1:
                self.pure_left_button_up = False
            if event.button == 3:
                self.pure_right_button_up = True
            if button1 or button2 or event.button != 3:
                self.pure_right_button_up = False
            # press button1 + button3 at the sametime, beside, without any other button pressed
            if button3 and button1 and (event.button == 1 or event.button == 3):
                self.pure_left_right_button_up = True
                action = EVENT_BOTH
            if event.button == 4 or event.button == 5:
                self.pure_left_right_button_up = False


        elif event.type == pygame.MOUSEBUTTONUP:
            pos = event.pos
            # check one click
            if event.button == 1:
                self.button1 = False
            if event.button == 2:
                self.button2 = False
            if event.button == 3:
                self.button3 = False
            button1, button2, button3 = self.button1, self.button2, self.button3
            if not button1 and not button3:
                self.last_pos = None

            # use wheel
            if event.button == 4:
                action = EVENT_WHEEL_UP
            if event.button == 5:
                action = EVENT_WHEEL_DOWN

            # only left click
            if event.button == 1 and self.pure_left_button_up:
                self.pure_left_button_up = False
                action = EVENT_LEFT

            # only right click
            if event.button == 3 and self.pure_right_button_up:
                self.pure_right_button_up = False
                action = EVENT_RIGHT

            # release button1 + button3
            if (event.button == 1 or event.button == 3) and (not button1 and not button3) and self.pure_left_right_button_up:
                self.pure_left_right_button_up = False
                action = EVENT_BOTH_RELEASE

        elif event.type == pygame.MOUSEMOTION:
            if self.last_pos:
                # drag
                pos = event.pos
                button1, button2, button3 = event.buttons
                if button1 and not button3:
                    action = EVENT_LEFT_DRAG
                elif button3 and not button1:
                    action = EVENT_RIGHT_DRAG
                elif button1 and button3:
                    action = EVENT_BOTH_DRAG

                pos = (pos[0] - self.last_pos[0],
                       pos[1] - self.last_pos[1])

                if abs(pos[0]) + abs(pos[1]) > 4:
                    self.pure_left_button_up = False
                    self.pure_right_button_up = False
                    self.pure_left_right_button_up = False
            else:
                action = EVENT_MOVE
                pos = event.rel

        return action, pos
