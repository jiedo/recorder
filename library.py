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


class Library():
    def __init__(self, width, blocksize):
        self.WIN_WIDTH = width
        self.SIZEBLOCK = blocksize
        self.last_pos = (0, 0)
        self.last_vector = (0, 0)
        self.total_angle = 0


    def load_library(self):
        self.library = json.loads(open("library.json").read())
        self.rect_need_draw = []


    def store_library(self):
        library_string = json.dumps(self.library)
        open("library.json", "w").write(library_string)


    def update_library_display(self, surface):
        self.rect_need_draw.reverse()
        for color, rect in self.rect_need_draw:
            pygame.draw.rect(surface, color, rect, 0)
        self.rect_need_draw = []


    def draw_rect(self, surface, color, rect, margin=1):
        times = 1
        offset = margin * times
        self.rect_need_draw += [(color, rect.inflate(-offset, -offset))]


    def draw_page(self, surface, page, is_current_shelf, is_current_book, is_current, rect):
        color = (40, 40, 40)
        if is_current:
            if is_current_shelf:
                if is_current_book:
                    color = (0, 180, 180)
                else:
                    color = (180, 180, 180)
        self.draw_rect(surface, color, rect, margin=6)


    def draw_book(self, surface, book, is_current_shelf, is_current, pos=0):
        pagei = book["mark"]
        left = 0
        top  = pos
        width = self.SIZEBLOCK
        height = self.SIZEBLOCK
        for idx, page in enumerate(book["pages"]):
            rect = pygame.Rect(left, top, width, height)
            self.draw_page(surface, page, is_current_shelf, is_current, idx==pagei, rect)
            left += width
            if width > self.WIN_WIDTH - left:
                left = 0
                top += height
        if is_current_shelf:
            if top - pos >= height:
                color = (200, 200, 200)
                book_rect_tip = pygame.Rect(self.WIN_WIDTH-4, pos, 4, top+height - pos)
                self.draw_rect(surface, color, book_rect_tip, margin=4)
        if is_current_shelf:
            color = (10, 10, 10)
            if is_current:
                color = (110, 110, 110)
        else:
            color = (1, 1, 1)
        book_rect = pygame.Rect(0, pos, self.WIN_WIDTH, top+height - pos)
        self.draw_rect(surface, color, book_rect, margin=4)
        return top+height - pos


    def draw_shelf(self, surface, shelf, is_current, pos=0):
        booki = shelf["mark"]
        top = pos
        for idx, book in enumerate(shelf["books"]):
            height = self.draw_book(surface, book, is_current, idx==booki, top)
            top += height
        if is_current:
            color = (200, 200, 200)
            shelf_rect_tip = pygame.Rect(0, pos, 2, top - pos)
            self.draw_rect(surface, color, shelf_rect_tip, margin=2)
        color = (0, 0, 0)
        shelf_rect = pygame.Rect(0, pos, self.WIN_WIDTH, top - pos)
        self.draw_rect(surface, color, shelf_rect, margin=2)

        return top - pos


    def draw_library(self, surface, pos=0):
        if "mark" not in self.library:
            return
        shelfi = self.library["mark"]
        for idx, shelf in enumerate(self.library["shelfs"]):
            height = self.draw_shelf(surface, shelf, idx==shelfi, pos)
            pos += height
        self.update_library_display(surface)


    def new_shelf(self):
        if 'shelfs' not in self.library:
            self.library['shelfs'] = []
            self.library['mark'] = 0
            self.library['max_shelf_id'] = 1
            self.library['max_book_id'] = 0
            self.library['max_page_id'] = 0
        else:
            self.library['max_shelf_id'] += 1
        shelf = {
            'mark': 0,
            'id': self.library['max_shelf_id'],
            'title': "shelf-%d" % self.library['max_shelf_id'],
            'books': []
        }
        self.library['shelfs'] += [shelf]


    def new_book(self):
        current_shelf_idx = self.library['mark']
        current_shelf = self.library['shelfs'][current_shelf_idx]
        self.library['max_book_id'] += 1
        book = {
            'mark': 0,
            'id': self.library['max_book_id'],
            'title': "book-%d" % self.library['max_book_id'],
            'pages': []
        }
        current_shelf['books'] += [book]


    def new_page(self):
        current_shelf_idx = self.library['mark']
        current_shelf = self.library['shelfs'][current_shelf_idx]
        length = len(current_shelf['books'])
        if length <= 0:
            return
        current_book_idx = current_shelf['mark']
        current_book = current_shelf['books'][current_book_idx]
        self.library['max_page_id'] += 1
        page = {
            'mark-p': 0,
            'mark-s': 0,
            'mark-w': 0,
            'id': self.library['max_page_id'],
            'title': "page-%d" % self.library['max_page_id'],
            'shelf-id': current_shelf['id'],
            'book-id': current_book['id'],
            'body': []
        }
        current_book['pages'] += [self.library['max_page_id']]

        page_string = json.dumps(page)
        open("pages/page-%d.json" % page['id'],
             "w").write(page_string)


    def next_shelf(self):
        length = len(self.library['shelfs'])
        if length <= 0:
            return
        current_idx = self.library['mark']
        current_idx += 1
        if current_idx >= length:
            return
        self.library['mark'] = current_idx


    def prev_shelf(self):
        length = len(self.library['shelfs'])
        if length <= 0:
            return
        current_idx = self.library['mark']
        current_idx -= 1
        if current_idx < 0:
            return

        self.library['mark'] = current_idx


    def next_book(self):
        length = len(self.library['shelfs'])
        if length <= 0:
            return False
        current_shelf_idx = self.library['mark']
        current_shelf = self.library['shelfs'][current_shelf_idx]
        length = len(current_shelf['books'])
        if length <= 0:
            return False
        current_idx = current_shelf['mark']
        current_idx += 1
        if current_idx >= length:
            return False
        current_shelf['mark'] = current_idx
        return True


    def prev_book(self):
        length = len(self.library['shelfs'])
        if length <= 0:
            return False
        current_shelf_idx = self.library['mark']
        current_shelf = self.library['shelfs'][current_shelf_idx]
        length = len(current_shelf['books'])
        if length <= 0:
            return False
        current_idx = current_shelf['mark']
        current_idx -= 1
        if current_idx < 0:
            return False
        current_shelf['mark'] = current_idx
        return True


    def next_page(self):
        length = len(self.library['shelfs'])
        if length <= 0:
            return
        current_shelf_idx = self.library['mark']
        current_shelf = self.library['shelfs'][current_shelf_idx]
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


    def prev_page(self):
        length = len(self.library['shelfs'])
        if length <= 0:
            return
        current_shelf_idx = self.library['mark']
        current_shelf = self.library['shelfs'][current_shelf_idx]
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


    def on_event(self, event):
        if event.type == QUIT or (event.type == KEYUP and event.key == K_ESCAPE):
            self.store_library()

        elif event.type == KEYUP:
            if event.key == K_b:
                self.new_book()
            elif event.key == K_s:
                self.new_shelf()
            elif event.key == K_p:
                self.new_page()

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
            #         if not self.next_book():
            #             self.next_shelf()
            #         self.total_angle-=diff
            #     while self.total_angle <= -diff:
            #         if not self.prev_book():
            #             self.prev_shelf()
            #         self.total_angle+=diff
            # else:
            #     while self.total_angle >= diff:
            #         self.next_page()
            #         self.total_angle -= diff
            #     while self.total_angle <= -diff:
            #         self.prev_page()
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
                    if not self.next_book():
                        self.next_shelf()
                    y-=diff
                while y <= -diff:
                    if not self.prev_book():
                        self.prev_shelf()
                    y+=diff
            else:
                x += dx
                while x >= diff:
                    self.next_page()
                    x -= diff
                while x <= -diff:
                    self.prev_page()
                    x += diff
            self.last_pos = (x, y)

        elif event.type == MOUSEBUTTONDOWN:
            b1, b2, b3 = pygame.mouse.get_pressed()
            if b3:
                if event.button == 5:
                    self.next_book()
                elif event.button == 4:
                    self.prev_book()
            else:
                if event.button == 5:
                    self.next_page()
                elif event.button == 4:
                    self.prev_page()

            # mod = pygame.key.get_mods()
            # if e.button == 5:
            #     if mod & KMOD_CTRL:
            #         next_book()
            #     elif mod & KMOD_ALT:
            #         next_shelf()
            #     else:
            #         next_page()

            # elif e.button == 4:
            #     if mod & KMOD_CTRL:
            #         prev_book()
            #     elif mod & KMOD_ALT:
            #         prev_shelf()
            #     else:
            #         prev_page()
