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


class page():
    def __init__(self, width, blocksize):
        self.WIN_WIDTH = width
        self.SIZEBLOCK = blocksize
        self.last_pos = (0, 0)
        self.last_vector = (0, 0)
        self.total_angle = 0


    def load_page(self):
        self.page = json.loads(open("page.json").read())
        self.rect_need_draw = []


    def store_page(self):
        page_string = json.dumps(self.page)
        open("page.json", "w").write(page_string)


    def update_page_display(self, surface):
        self.rect_need_draw.reverse()
        for color, rect in self.rect_need_draw:
            pygame.draw.rect(surface, color, rect, 0)
        self.rect_need_draw = []


    def draw_rect(self, surface, color, rect, margin=1):
        times = 1
        offset = margin * times
        self.rect_need_draw += [(color, rect.inflate(-offset, -offset))]


    def draw_word(self, surface, word, is_current_section, is_current_statement, is_current, rect):
        color = (40, 40, 40)
        if is_current:
            if is_current_section:
                if is_current_statement:
                    color = (0, 180, 180)
                else:
                    color = (180, 180, 180)
        self.draw_rect(surface, color, rect, margin=6)


    def draw_statement(self, surface, statement, is_current_section, is_current, pos=0):
        wordi = statement["mark"]
        left = 0
        top  = pos
        width = self.SIZEBLOCK
        height = self.SIZEBLOCK
        for idx, word in enumerate(statement["words"]):
            rect = pygame.Rect(left, top, width, height)
            self.draw_word(surface, word, is_current_section, is_current, idx==wordi, rect)
            left += width
            if width > self.WIN_WIDTH - left:
                left = 0
                top += height
        if is_current_section:
            if top - pos >= height:
                color = (200, 200, 200)
                statement_rect_tip = pygame.Rect(self.WIN_WIDTH-4, pos, 4, top+height - pos)
                self.draw_rect(surface, color, statement_rect_tip, margin=4)
        if is_current_section:
            color = (10, 10, 10)
            if is_current:
                color = (110, 110, 110)
        else:
            color = (1, 1, 1)
        statement_rect = pygame.Rect(0, pos, self.WIN_WIDTH, top+height - pos)
        self.draw_rect(surface, color, statement_rect, margin=4)
        return top+height - pos


    def draw_section(self, surface, section, is_current, pos=0):
        statementi = section["mark"]
        top = pos
        for idx, statement in enumerate(section["statements"]):
            height = self.draw_statement(surface, statement, is_current, idx==statementi, top)
            top += height
        if is_current:
            color = (200, 200, 200)
            section_rect_tip = pygame.Rect(0, pos, 2, top - pos)
            self.draw_rect(surface, color, section_rect_tip, margin=2)
        color = (0, 0, 0)
        section_rect = pygame.Rect(0, pos, self.WIN_WIDTH, top - pos)
        self.draw_rect(surface, color, section_rect, margin=2)

        return top - pos


    def draw_page(self, surface, pos=0):
        if "mark" not in self.page:
            return
        sectioni = self.page["mark"]
        for idx, section in enumerate(self.page["sections"]):
            height = self.draw_section(surface, section, idx==sectioni, pos)
            pos += height
        self.update_page_display(surface)


    def new_section(self):
        if 'sections' not in self.page:
            self.page['sections'] = []
            self.page['mark'] = 0
            self.page['max_section_id'] = 1
            self.page['max_statement_id'] = 0
            self.page['max_word_id'] = 0
        else:
            self.page['max_section_id'] += 1
        section = {
            'mark': 0,
            'id': self.page['max_section_id'],
            'title': "section-%d" % self.page['max_section_id'],
            'statements': []
        }
        self.page['sections'] += [section]


    def new_statement(self):
        current_section_idx = self.page['mark']
        current_section = self.page['sections'][current_section_idx]
        self.page['max_statement_id'] += 1
        statement = {
            'mark': 0,
            'id': self.page['max_statement_id'],
            'title': "statement-%d" % self.page['max_statement_id'],
            'words': []
        }
        current_section['statements'] += [statement]


    def new_word(self):
        current_section_idx = self.page['mark']
        current_section = self.page['sections'][current_section_idx]
        length = len(current_section['statements'])
        if length <= 0:
            return
        current_statement_idx = current_section['mark']
        current_statement = current_section['statements'][current_statement_idx]
        self.page['max_word_id'] += 1
        word = {
            'mark-p': 0,
            'mark-s': 0,
            'mark-w': 0,
            'id': self.page['max_word_id'],
            'title': "word-%d" % self.page['max_word_id'],
            'section-id': current_section['id'],
            'statement-id': current_statement['id'],
            'body': []
        }
        current_statement['words'] += [self.page['max_word_id']]

        word_string = json.dumps(word)
        open("words/word-%d.json" % word['id'],
             "w").write(word_string)


    def next_section(self):
        length = len(self.page['sections'])
        if length <= 0:
            return
        current_idx = self.page['mark']
        current_idx += 1
        if current_idx >= length:
            return
        self.page['mark'] = current_idx


    def prev_section(self):
        length = len(self.page['sections'])
        if length <= 0:
            return
        current_idx = self.page['mark']
        current_idx -= 1
        if current_idx < 0:
            return

        self.page['mark'] = current_idx


    def next_statement(self):
        length = len(self.page['sections'])
        if length <= 0:
            return False
        current_section_idx = self.page['mark']
        current_section = self.page['sections'][current_section_idx]
        length = len(current_section['statements'])
        if length <= 0:
            return False
        current_idx = current_section['mark']
        current_idx += 1
        if current_idx >= length:
            return False
        current_section['mark'] = current_idx
        return True


    def prev_statement(self):
        length = len(self.page['sections'])
        if length <= 0:
            return False
        current_section_idx = self.page['mark']
        current_section = self.page['sections'][current_section_idx]
        length = len(current_section['statements'])
        if length <= 0:
            return False
        current_idx = current_section['mark']
        current_idx -= 1
        if current_idx < 0:
            return False
        current_section['mark'] = current_idx
        return True


    def next_word(self):
        length = len(self.page['sections'])
        if length <= 0:
            return
        current_section_idx = self.page['mark']
        current_section = self.page['sections'][current_section_idx]
        length = len(current_section['statements'])
        if length <= 0:
            return
        current_statement_idx = current_section['mark']
        current_statement = current_section['statements'][current_statement_idx]

        length = len(current_statement['words'])
        if length <= 0:
            return
        current_idx = current_statement['mark']
        current_idx += 1
        if current_idx >= length:
            return
        current_statement['mark'] = current_idx


    def prev_word(self):
        length = len(self.page['sections'])
        if length <= 0:
            return
        current_section_idx = self.page['mark']
        current_section = self.page['sections'][current_section_idx]
        length = len(current_section['statements'])
        if length <= 0:
            return
        current_statement_idx = current_section['mark']
        current_statement = current_section['statements'][current_statement_idx]
        length = len(current_statement['words'])
        if length <= 0:
            return
        current_idx = current_statement['mark']
        current_idx -= 1
        if current_idx < 0:
            return
        current_statement['mark'] = current_idx


    def on_event(self, event):
        if event.type == QUIT or (event.type == KEYUP and event.key == K_ESCAPE):
            self.store_page()

        elif event.type == KEYUP:
            if event.key == K_b:
                self.new_statement()
            elif event.key == K_s:
                self.new_section()
            elif event.key == K_p:
                self.new_word()

        elif event.type == MOUSEMOTION:
            # a, b = self.last_vector
            # c, d = event.rel
            # b1, b2, b3 = event.buttons
            # diff = self.SIZEBLOCK*3
            # self.last_vector = (c, d)
            # e = b*(a+c) - a*(b+d)
            # self.total_angle += e
            # if b3:
            #     while self.total_angle >= diff:
            #         if not self.next_statement():
            #             self.next_section()
            #         self.total_angle-=diff
            #     while self.total_angle <= -diff:
            #         if not self.prev_statement():
            #             self.prev_section()
            #         self.total_angle+=diff
            # else:
            #     while self.total_angle >= diff:
            #         self.next_word()
            #         self.total_angle -= diff
            #     while self.total_angle <= -diff:
            #         self.prev_word()
            #         self.total_angle += diff

            b1, b2, b3 = event.buttons
            diff = self.SIZEBLOCK
            dx, dy = event.rel
            x, y = self.last_pos
            dt = 4
            if dx > 0:
                dx = dx*dx/dt
            else:
                dx = -dx*dx/dt
            if dy > 0:
                dy = dy*dy/dt
            else:
                dy = -dy*dy/dt
            if b3:
                y += dy
                while y >= diff:
                    if not self.next_statement():
                        self.next_section()
                    y-=diff
                while y <= -diff:
                    if not self.prev_statement():
                        self.prev_section()
                    y+=diff
            else:
                x += dx
                while x >= diff:
                    self.next_word()
                    x -= diff
                while x <= -diff:
                    self.prev_word()
                    x += diff
            self.last_pos = (x, y)

        elif event.type == MOUSEBUTTONDOWN:
            b1, b2, b3 = pygame.mouse.get_pressed()
            if b3:
                if event.button == 5:
                    self.next_statement()
                elif event.button == 4:
                    self.prev_statement()
            else:
                if event.button == 5:
                    self.next_word()
                elif event.button == 4:
                    self.prev_word()

            # mod = pygame.key.get_mods()
            # if e.button == 5:
            #     if mod & KMOD_CTRL:
            #         next_statement()
            #     elif mod & KMOD_ALT:
            #         next_section()
            #     else:
            #         next_word()

            # elif e.button == 4:
            #     if mod & KMOD_CTRL:
            #         prev_statement()
            #     elif mod & KMOD_ALT:
            #         prev_section()
            #     else:
            #         prev_word()
