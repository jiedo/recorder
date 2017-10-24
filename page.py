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


class Page():
    def __init__(self, width, blocksize):
        self.WIN_WIDTH = width
        self.SIZEBLOCK = blocksize

    def load_page(self, pageid):
        self.pageid = pageid
        self.page = json.loads(open("pages/page-%d.json" % self.pageid).read())
        self.rect_need_draw = []
        self.last_pos = (0, 0)
        self.last_vector = (0, 0)
        self.total_angle = 0

        self.pos_to_mark = {}
        self.runtime_row = 0
        self.runtime_col = 0


    def store_page(self):
        page_string = json.dumps(self.page, indent=2)
        open("pages/page-%d.json" % self.pageid,
             "w").write(page_string)


    def update_page_display(self, surface):
        self.rect_need_draw.reverse()
        for color, rect in self.rect_need_draw:
            pygame.draw.rect(surface, color, rect, 0)
        self.rect_need_draw = []


    def draw_rect(self, surface, color, rect, margin=1):
        offset = margin
        self.rect_need_draw += [(color, rect.inflate(-offset, -offset))]


    def draw_word(self, surface, word, is_current_section, is_current_statement, is_current, rect):
        color = (40, 40, 40)
        if is_current:
            if is_current_section:
                if is_current_statement:
                    color = (0, 200, 0)
                else:
                    color = (180, 180, 180)
        self.draw_rect(surface, color, rect, margin=6)


    def draw_statement(self, surface, statement, is_current_section, is_current, sectionidx, statementidx, pos=0):
        wordi = statement["mark"]
        left = 0
        top  = pos
        width = self.SIZEBLOCK
        height = self.SIZEBLOCK
        for idx, word in enumerate(statement["words"]):
            rect = pygame.Rect(left, top, width, height)
            self.draw_word(surface, word, is_current_section, is_current, idx==wordi, rect)
            self.pos_to_mark[(self.runtime_row, self.runtime_col)] = (sectionidx, statementidx, idx)
            self.runtime_col += 1
            left += width
            if idx < len(statement["words"])-1 and width > self.WIN_WIDTH - left:
                self.runtime_row += 1
                self.runtime_col = 0
                left = 0
                top += height
        self.runtime_row += 1
        self.runtime_col = 0

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


    def draw_section(self, surface, section, is_current, sectionidx, pos=0):
        statementi = section["mark"]
        top = pos
        for idx, statement in enumerate(section["statements"]):
            height = self.draw_statement(surface, statement, is_current, idx==statementi, sectionidx, idx, top)
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
        self.runtime_row = 0
        self.runtime_col = 0
        self.pos_to_mark = {}
        sectioni = self.page["mark"]
        for idx, section in enumerate(self.page["sections"]):
            height = self.draw_section(surface, section, idx==sectioni, idx, pos)
            pos += height
        self.update_page_display(surface)


    def new_section(self):
        self.page['max_section_id'] += 1
        section = {
            'mark': 0,
            'id': self.page['max_section_id'],
            'title': "section-%d" % self.page['max_section_id'],
            'statements': []
        }
        current_idx = self.page['mark']
        self.page['sections'][current_idx:current_idx] = [section]


    def new_statement(self):
        current_section_idx = self.page['mark']
        if len(self.page['sections']) == 0:
            self.new_section()
        current_section = self.page['sections'][current_section_idx]
        self.page['max_statement_id'] += 1
        statement = {
            'mark': 0,
            'id': self.page['max_statement_id'],
            'title': "statement-%d" % self.page['max_statement_id'],
            'words': []
        }
        current_idx = current_section['mark']
        current_section['statements'][current_idx:current_idx] = [statement]


    def new_word(self):
        current_section_idx = self.page['mark']
        if len(self.page['sections']) == 0:
            self.new_section()
        current_section = self.page['sections'][current_section_idx]
        if len(current_section['statements']) == 0:
            self.new_statement()
        current_statement_idx = current_section['mark']
        current_statement = current_section['statements'][current_statement_idx]
        self.page['max_word_id'] += 1
        word = {
            'id': self.page['max_word_id'],
            'type': 'Word',
            'title': "word-%d" % self.page['max_word_id'],
            'timestamp': 0,
            'create_time': 0,
            'update_time': 0,
            'start': 0,
            'end': 0,
            'ancher': {'pageid': 0, 'ancher': ""},
            'section-id': current_section['id'],
            'statement-id': current_statement['id'],
        }
        current_idx = current_statement['mark']
        current_statement['words'][current_idx:current_idx] = [word]


    def next_section(self):
        length = len(self.page['sections'])
        if length <= 0:
            return False
        current_idx = self.page['mark']
        current_idx += 1
        if current_idx >= length:
            return False
        self.page['mark'] = current_idx
        return True

    def prev_section(self):
        length = len(self.page['sections'])
        if length <= 0:
            return False
        current_idx = self.page['mark']
        current_idx -= 1
        if current_idx < 0:
            return False
        self.page['mark'] = current_idx
        return True

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


    def swap_statement(self):
        length = len(self.page['sections'])
        if length <= 0:
            return False
        current_section_idx = self.page['mark']
        current_section = self.page['sections'][current_section_idx]
        length = len(current_section['statements'])
        if length <= 0:
            return False
        current_idx = current_section['mark']
        if current_idx < 1:
            return False
        current_section['mark'] = current_idx - 1

        a, b = current_section['statements'][current_idx-1], current_section['statements'][current_idx]
        current_section['statements'][current_idx-1], current_section['statements'][current_idx] = b, a
        return True


    def next_word(self):
        length = len(self.page['sections'])
        if length <= 0:
            return False
        current_section_idx = self.page['mark']
        current_section = self.page['sections'][current_section_idx]
        length = len(current_section['statements'])
        if length <= 0:
            return False
        current_statement_idx = current_section['mark']
        current_statement = current_section['statements'][current_statement_idx]

        length = len(current_statement['words'])
        if length <= 0:
            return False
        current_idx = current_statement['mark']
        current_idx += 1
        if current_idx >= length:
            return False
        current_statement['mark'] = current_idx
        return True


    def prev_word(self):
        length = len(self.page['sections'])
        if length <= 0:
            return False
        current_section_idx = self.page['mark']
        current_section = self.page['sections'][current_section_idx]
        length = len(current_section['statements'])
        if length <= 0:
            return False
        current_statement_idx = current_section['mark']
        current_statement = current_section['statements'][current_statement_idx]
        length = len(current_statement['words'])
        if length <= 0:
            return False
        current_idx = current_statement['mark']
        current_idx -= 1
        if current_idx < 0:
            return False
        current_statement['mark'] = current_idx
        return True


    def swap_word(self):
        length = len(self.page['sections'])
        if length <= 0:
            return False
        current_section_idx = self.page['mark']
        current_section = self.page['sections'][current_section_idx]
        length = len(current_section['statements'])
        if length <= 0:
            return False
        current_statement_idx = current_section['mark']
        current_statement = current_section['statements'][current_statement_idx]
        length = len(current_statement['words'])
        if length <= 0:
            return False
        current_idx = current_statement['mark']
        if current_idx >= length-1:
            return False
        current_statement['mark'] = current_idx+1
        a, b = current_statement['words'][current_idx], current_statement['words'][current_idx+1]
        current_statement['words'][current_idx], current_statement['words'][current_idx+1] = b, a
        return True


    def get_current_word_sound_filename(self):
        word = self.get_current_word()
        if not word:
            return "", 0
        shelf_id, book_id, page_id, word_id, create_time = (self.page['shelf-id'], self.page['book-id'], self.page['id'],
                                                            word['id'], word['create_time'])
        filename = "sounds/shelf.%d-book.%d-page.%d-word.%d.wav" % (shelf_id, book_id, page_id, word_id)
        return filename, create_time


    def get_current_word(self):
        length = len(self.page['sections'])
        if length <= 0:
            return 0
        current_section_idx = self.page['mark']
        current_section = self.page['sections'][current_section_idx]
        length = len(current_section['statements'])
        if length <= 0:
            return 0
        current_statement_idx = current_section['mark']
        current_statement = current_section['statements'][current_statement_idx]
        length = len(current_statement['words'])
        if length <= 0:
            return 0
        current_idx = current_statement['mark']
        if current_idx < 0 or current_idx >= length:
            return 0
        return current_statement['words'][current_idx]


    def set_current_word(self, create_time, update_time):
        length = len(self.page['sections'])
        if length <= 0:
            return 0
        current_section_idx = self.page['mark']
        current_section = self.page['sections'][current_section_idx]
        length = len(current_section['statements'])
        if length <= 0:
            return 0
        current_statement_idx = current_section['mark']
        current_statement = current_section['statements'][current_statement_idx]
        length = len(current_statement['words'])
        if length <= 0:
            return 0
        current_idx = current_statement['mark']
        if current_idx < 0 or current_idx >= length:
            return 0
        word = current_statement['words'][current_idx]
        word['create_time'] = create_time
        word['update_time'] = update_time


    def on_event(self, event):
        feedback = ""
        if event.type == KEYUP:
            if event.key == K_3:
                self.new_section()
                feedback += "new section. "
            elif event.key == K_2:
                self.new_statement()
                feedback += "new statements. "
            elif event.key == K_1:
                self.new_word()
                feedback += "new word. "

            if event.key == K_h:
                if self.prev_word():
                    feedback += "previous word. "
                else:
                    feedback += "none. "
            elif event.key == K_l:
                if self.next_word():
                    feedback += "next word. "
                else:
                    feedback += "none. "
            if event.key == K_k:
                if not self.prev_statement():
                    if self.prev_section():
                        feedback += "previous section. "
                    else:
                        feedback += "none. "
                else:
                    feedback += "previous statements. "
            elif event.key == K_j:
                if not self.next_statement():
                    if self.next_section():
                        feedback += "next section. "
                    else:
                        feedback += "none. "
                else:
                    feedback += "next statements. "

        elif event.type == MOUSEBUTTONDOWN:
            b1, b2, b3 = pygame.mouse.get_pressed()
            # Nav statement
            if b1 and not b3:
                if event.button == 5:
                    if not self.next_statement():
                        if self.next_section():
                            feedback += "next section. "
                        else:
                            feedback += "none. "
                    else:
                        feedback += "next statements. "
                elif event.button == 4:
                    if not self.prev_statement():
                        if self.prev_section():
                            feedback += "previous section. "
                        else:
                            feedback += "none. "
                    else:
                        feedback += "previous statements. "

            # Nav word
            if not b1 and not b3:
                if event.button == 5:
                    if self.next_word():
                        feedback += "next word. "
                    else:
                        feedback += "none. "
                elif event.button == 4:
                    if self.prev_word():
                        feedback += "previous word. "
                    else:
                        feedback += "none. "

            # Create
            if b3 and not b1:
                if event.button == 5:
                    self.new_word()
                    feedback += "new word. "
                elif event.button == 4:
                    self.new_statement()
                    feedback += "new statements. "

            # Swap block
            if b3 and b1:
                # Swap block
                if event.button == 5:
                    self.swap_word()
                elif event.button == 4:
                    self.swap_statement()

        elif event.type == MOUSEMOTION:
            #Nav by point to
            x, y = event.pos
            col, row = x/self.SIZEBLOCK, y/self.SIZEBLOCK
            (sectioni, statementi, wordi) = self.pos_to_mark.get((row, col), (-1, -1, -1))
            if sectioni >= 0:
                self.page['mark'] = sectioni
            if statementi >= 0:
                self.page['sections'][sectioni]['mark'] = statementi
            if wordi >= 0:
                self.page['sections'][sectioni]['statements'][statementi]['mark'] = wordi

            #Nav by draw circle and button
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


            #Nav by wheel and button
            # b1, b2, b3 = event.buttons
            # diff = self.SIZEBLOCK
            # dx, dy = event.rel
            # x, y = self.last_pos
            # dt = 4
            # if dx > 0:
            #     dx = dx*dx/dt
            # else:
            #     dx = -dx*dx/dt
            # if dy > 0:
            #     dy = dy*dy/dt
            # else:
            #     dy = -dy*dy/dt
            # if b1:
            #     y += dy
            #     while y >= diff:
            #         if not self.next_statement():
            #             self.next_section()
            #         y-=diff
            #     while y <= -diff:
            #         if not self.prev_statement():
            #             self.prev_section()
            #         y+=diff
            # else:
            #     x += dx
            #     while x >= diff:
            #         self.next_word()
            #         x -= diff
            #     while x <= -diff:
            #         self.prev_word()
            #         x += diff
            # self.last_pos = (x, y)


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
        return feedback
