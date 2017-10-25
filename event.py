#!/usr/bin/env python2

import pygame
import time

class EventChecker():
    def __init__(self):
        self.pure_left_button_up = False
        self.pure_right_button_up = False
        self.pure_left_right_button_up = False
        pass

    def do(self, e):
        if e.type == pygame.KEYUP:
            if e.key == pygame.K_RETURN:
                return "enter"
            elif e.key == pygame.K_ESCAPE:
                return "quit"

        if e.type == pygame.QUIT:
            return "quit"

        if e.type == pygame.MOUSEBUTTONDOWN:
            button1, button2, button3 = pygame.mouse.get_pressed()
            # check one click
            if button1:
                self.pure_left_button_up = True
            if button2 or button3 or e.button != 1:
                self.pure_left_button_up = False
            if button3:
                self.pure_right_button_up = True
            if button1 or button2 or e.button != 3:
                self.pure_right_button_up = False
            # press button1 + button3 at the sametime, beside, without any other button pressed
            if button3 and button1 and (e.button == 1 or e.button == 3):
                self.pure_left_right_button_up = True
                return "both"
            if e.button == 4 or e.button == 5:
                self.pure_left_right_button_up = False


        elif e.type == pygame.MOUSEBUTTONUP:
            button1, button2, button3 = pygame.mouse.get_pressed()
            # use wheel
            if e.button == 4 or e.button == 5:
                return "wheel"

            # only left click
            if e.button == 1 and self.pure_left_button_up:
                self.pure_left_button_up = False
                return "left"

            # only right click
            if e.button == 3 and self.pure_right_button_up:
                self.pure_right_button_up = False
                return "right"

            # release button1 + button3
            if (e.button == 1 or e.button == 3) and (not button1 and not button3) and self.pure_left_right_button_up:
                return "!both"

        return ""
