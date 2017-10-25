#!/usr/bin/env python2

import pygame
import time
import json


class Library():
    def __init__(self, width, blocksize):
        self.WIN_WIDTH = width
        self.SIZEBLOCK = blocksize
        self.last_pos = (0, 0)
        self.last_vector = (0, 0)
        self.total_angle = 0
        self.pos_to_mark = {}
        self.runtime_row = 0
        self.runtime_col = 0

        self.color_page_very_current = (0, 200, 200)
        self.color_page_current = (180, 180, 180)
        self.color_page_not_current = (40, 40, 40)

        self.color_book_tip = (0, 200, 200)
        self.color_shelf_tip = (0, 200, 200)

        self.color_book_very_current = (110, 110, 110)
        self.color_book_current = (10, 10, 10)
        self.color_book_not_current = (1, 1, 1)

        self.color_shelf = (0, 0, 0)


    def load_library(self):
        try:
            self.library = json.loads(open("library.json").read())
        except:
            self.library = {}
        self.rect_need_draw = []


    def store_library(self):
        library_string = json.dumps(self.library, indent=2)
        open("library.json", "w").write(library_string)


    def update_library_display(self, surface):
        self.rect_need_draw.reverse()
        for color, rect in self.rect_need_draw:
            pygame.draw.rect(surface, color, rect, 0)
        self.rect_need_draw = []


    def draw_rect(self, surface, color, rect, margin=1):
        offset = margin
        self.rect_need_draw += [(color, rect.inflate(-offset, -offset))]


    def draw_page(self, surface, page, is_current_shelf, is_current_book, is_current, rect):
        color = self.color_page_not_current
        if is_current:
            if is_current_shelf:
                if is_current_book:
                    color = self.color_page_very_current
                else:
                    color = self.color_page_current
        self.draw_rect(surface, color, rect, margin=6)


    def draw_book(self, surface, book, is_current_shelf, is_current, shelfidx, bookidx, pos=0):
        pagei = book["mark"]
        left = 0
        top  = pos
        width = self.SIZEBLOCK
        height = self.SIZEBLOCK
        for idx, page in enumerate(book["pages"]):
            rect = pygame.Rect(left, top, width, height)
            self.draw_page(surface, page, is_current_shelf, is_current, idx==pagei, rect)
            self.pos_to_mark[(self.runtime_row, self.runtime_col)] = (shelfidx, bookidx, idx)
            self.runtime_col += 1
            left += width
            if idx < len(book["pages"])-1 and width > self.WIN_WIDTH - left:
                self.runtime_row += 1
                self.runtime_col = 0
                left = 0
                top += height
        self.runtime_row += 1
        self.runtime_col = 0

        if is_current_shelf:
            if top - pos >= height:
                color = self.color_book_tip
                book_rect_tip = pygame.Rect(self.WIN_WIDTH-4, pos, 4, top+height - pos)
                self.draw_rect(surface, color, book_rect_tip, margin=4)
        if is_current_shelf:
            color = self.color_book_current
            if is_current:
                color = self.color_book_very_current
        else:
            color = self.color_book_not_current
        book_rect = pygame.Rect(0, pos, self.WIN_WIDTH, top+height - pos)
        self.draw_rect(surface, color, book_rect, margin=4)
        return top+height - pos


    def draw_shelf(self, surface, shelf, is_current, shelfidx, pos=0):
        booki = shelf["mark"]
        top = pos
        for idx, book in enumerate(shelf["books"]):
            height = self.draw_book(surface, book, is_current, idx==booki, shelfidx, idx, top)
            top += height
        if is_current:
            color = self.color_shelf_tip
            shelf_rect_tip = pygame.Rect(0, pos, 2, top - pos)
            self.draw_rect(surface, color, shelf_rect_tip, margin=2)
        color = self.color_shelf
        shelf_rect = pygame.Rect(0, pos, self.WIN_WIDTH, top - pos)
        self.draw_rect(surface, color, shelf_rect, margin=2)

        return top - pos


    def draw_library(self, surface, pos=0):
        if "mark" not in self.library:
            return
        self.runtime_row = 0
        self.runtime_col = 0
        self.pos_to_mark = {}
        shelfi = self.library["mark"]
        for idx, shelf in enumerate(self.library["shelfs"]):
            height = self.draw_shelf(surface, shelf, idx==shelfi, idx, pos)
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
        current_idx = self.library['mark']
        self.library['shelfs'][current_idx:current_idx] = [shelf]


    def new_book(self):
        if 'shelfs' not in self.library:
            self.new_shelf()
        current_shelf_idx = self.library['mark']
        current_shelf = self.library['shelfs'][current_shelf_idx]
        self.library['max_book_id'] += 1
        book = {
            'mark': 0,
            'id': self.library['max_book_id'],
            'title': "book-%d" % self.library['max_book_id'],
            'pages': []
        }
        current_idx = current_shelf['mark']
        current_shelf['books'][current_idx:current_idx] = [book]


    def new_page(self):
        if 'shelfs' not in self.library:
            self.new_shelf()

        current_shelf_idx = self.library['mark']
        current_shelf = self.library['shelfs'][current_shelf_idx]
        if len(current_shelf['books']) == 0:
            self.new_book()
        current_book_idx = current_shelf['mark']
        current_book = current_shelf['books'][current_book_idx]
        self.library['max_page_id'] += 1
        page = {
            'id': self.library['max_page_id'],
            'title': "page-%d" % self.library['max_page_id'],
            'shelf-id': current_shelf['id'],
            'book-id': current_book['id'],
            'sections': [{
                "title": "section-1",
                "statements": [{
                    "title": "statement-1",
                    "id": 1,
                    "words": [{
                        "type": "Close", # Close/Word/Page/Time/Link/...
                        "start": 0,
                        "update_time": 0,
                        "create_time": 0,
                        "end": 0,
                        "statement-id": 1,
                        "title": "word-1",
                        "timestamp": 0,
                        "section-id": 1,
                        "id": 1,
                        "ancher": {
                            "pageid": 0,
                            "ancher": ""
                        }
                    }],
                    "mark": 0
                }],
                "id": 1,
                "mark": 0
            }],
            'mark': 0,
            'max_section_id': 1,
            'max_statement_id': 1,
            'max_word_id': 1,
        }
        current_idx = current_book['mark']
        current_book['pages'][current_idx:current_idx] = [{
            "id": self.library['max_page_id'],
            "create_time": 0,
            "update_time": 0,
        }]

        page_string = json.dumps(page)
        open("pages/page-%d.json" % page['id'],
             "w").write(page_string)


    def next_shelf(self):
        length = len(self.library['shelfs'])
        if length <= 0:
            return False
        current_idx = self.library['mark']
        current_idx += 1
        if current_idx >= length:
            return False
        self.library['mark'] = current_idx
        return True

    def prev_shelf(self):
        length = len(self.library['shelfs'])
        if length <= 0:
            return False
        current_idx = self.library['mark']
        current_idx -= 1
        if current_idx < 0:
            return False
        self.library['mark'] = current_idx
        return True


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


    def swap_book(self):
        length = len(self.library['shelfs'])
        if length <= 0:
            return False
        current_shelf_idx = self.library['mark']
        current_shelf = self.library['shelfs'][current_shelf_idx]
        length = len(current_shelf['books'])
        if length <= 0:
            return False
        current_idx = current_shelf['mark']
        if current_idx < 1:
            return False
        current_shelf['mark'] = current_idx-1

        a, b = current_shelf['books'][current_idx-1], current_shelf['books'][current_idx]
        current_shelf['books'][current_idx-1], current_shelf['books'][current_idx] = b, a
        return True


    def next_page(self):
        length = len(self.library['shelfs'])
        if length <= 0:
            return False
        current_shelf_idx = self.library['mark']
        current_shelf = self.library['shelfs'][current_shelf_idx]
        length = len(current_shelf['books'])
        if length <= 0:
            return False
        current_book_idx = current_shelf['mark']
        current_book = current_shelf['books'][current_book_idx]

        length = len(current_book['pages'])
        if length <= 0:
            return False
        current_idx = current_book['mark']
        current_idx += 1
        if current_idx >= length:
            return False
        current_book['mark'] = current_idx
        return True


    def prev_page(self):
        length = len(self.library['shelfs'])
        if length <= 0:
            return False
        current_shelf_idx = self.library['mark']
        current_shelf = self.library['shelfs'][current_shelf_idx]
        length = len(current_shelf['books'])
        if length <= 0:
            return False
        current_book_idx = current_shelf['mark']
        current_book = current_shelf['books'][current_book_idx]
        length = len(current_book['pages'])
        if length <= 0:
            return False
        current_idx = current_book['mark']
        current_idx -= 1
        if current_idx < 0:
            return False
        current_book['mark'] = current_idx
        return True


    def swap_page(self):
        length = len(self.library['shelfs'])
        if length <= 0:
            return False
        current_shelf_idx = self.library['mark']
        current_shelf = self.library['shelfs'][current_shelf_idx]
        length = len(current_shelf['books'])
        if length <= 0:
            return False
        current_book_idx = current_shelf['mark']
        current_book = current_shelf['books'][current_book_idx]
        length = len(current_book['pages'])
        if length <= 0:
            return False
        current_idx = current_book['mark']
        if current_idx >= length-1:
            return False
        current_book['mark'] = current_idx+1
        a, b = current_book['pages'][current_idx], current_book['pages'][current_idx+1]
        current_book['pages'][current_idx], current_book['pages'][current_idx+1] = b, a
        return True


    def get_current_page_sound_filename(self):
        results = self.get_current_page_id()
        if not results:
            return "", 0
        shelf_id, book_id, page_id, create_time = results
        filename = "sounds/shelf.%d-book.%d-page.%d.wav" % (shelf_id, book_id, page_id)
        return filename, create_time


    def get_current_page_id(self):
        length = len(self.library['shelfs'])
        if length <= 0:
            return 0
        current_shelf_idx = self.library['mark']
        current_shelf = self.library['shelfs'][current_shelf_idx]
        length = len(current_shelf['books'])
        if length <= 0:
            return 0
        current_book_idx = current_shelf['mark']
        current_book = current_shelf['books'][current_book_idx]
        length = len(current_book['pages'])
        if length <= 0:
            return 0
        current_idx = current_book['mark']
        if current_idx < 0 or current_idx >= length:
            return 0
        return current_shelf['id'], current_book['id'], current_book['pages'][current_idx]['id'], current_book['pages'][current_idx]['create_time']


    def set_current_page(self, create_time, update_time):
        length = len(self.library['shelfs'])
        if length <= 0:
            return 0
        current_shelf_idx = self.library['mark']
        current_shelf = self.library['shelfs'][current_shelf_idx]
        length = len(current_shelf['books'])
        if length <= 0:
            return 0
        current_book_idx = current_shelf['mark']
        current_book = current_shelf['books'][current_book_idx]
        length = len(current_book['pages'])
        if length <= 0:
            return 0
        current_idx = current_book['mark']
        if current_idx < 0 or current_idx >= length:
            return 0
        page = current_book['pages'][current_idx]
        page['create_time'] = create_time
        page['update_time'] = update_time


    def on_event(self, event):
        feedback = ""
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_3:
                self.new_shelf()
                feedback += "new shelf. "
            elif event.key == pygame.K_2:
                self.new_book()
                feedback += "new book. "
            elif event.key == pygame.K_1:
                self.new_page()
                feedback += "new page. "


            if event.key == pygame.K_h:
                if self.prev_page():
                    feedback += "previous page. "
                else:
                    feedback += "none. "
            elif event.key == pygame.K_l:
                if self.next_page():
                    feedback += "next page. "
                else:
                    feedback += "none. "
            if event.key == pygame.K_k:
                if not self.prev_book():
                    if self.prev_shelf():
                        feedback += "previous shelf. "
                    else:
                        feedback += "none. "
                else:
                    feedback += "previous book. "
            elif event.key == pygame.K_j:
                if not self.next_book():
                    if self.next_shelf():
                        feedback += "previous shelf. "
                    else:
                        feedback += "none. "
                else:
                    feedback += "previous book. "

        elif event.type == pygame.MOUSEBUTTONDOWN:
            b1, b2, b3 = pygame.mouse.get_pressed()
            # Nav book
            if b1 and not b3:
                if event.button == 5:
                    if not self.next_book():
                        if self.next_shelf():
                            feedback += "next shelf. "
                        else:
                            feedback += "none. "
                    else:
                        feedback += "next book. "
                elif event.button == 4:
                    if not self.prev_book():
                        if self.prev_shelf():
                            feedback += "previous shelf. "
                        else:
                            feedback += "none. "
                    else:
                        feedback += "previous book. "
            # Nav page
            if not b1 and not b3:
                if event.button == 5:
                    if self.next_page():
                        feedback += "next page. "
                    else:
                        feedback += "none. "
                elif event.button == 4:
                    if self.prev_page():
                        feedback += "previous page. "
                    else:
                        feedback += "none. "

            # Create
            if b3 and not b1:
                if event.button == 5:
                    self.new_page()
                    feedback += "new page. "
                elif event.button == 4:
                    self.new_book()
                    feedback += "new book. "

            # Swap block
            if b3 and b1:
                # Swap block
                if event.button == 5:
                    self.swap_page()
                elif event.button == 4:
                    self.swap_book()

        elif event.type == pygame.MOUSEMOTION:
            #Nav by point to
            x, y = event.pos
            col, row = x/self.SIZEBLOCK, y/self.SIZEBLOCK
            (shelfi, booki, pagei) = self.pos_to_mark.get((row, col), (-1, -1, -1))
            if shelfi >= 0:
                self.library['mark'] = shelfi
            if booki >= 0:
                self.library['shelfs'][shelfi]['mark'] = booki
            if pagei >= 0:
                self.library['shelfs'][shelfi]['books'][booki]['mark'] = pagei

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
            #         if not self.next_book():
            #             self.next_shelf()
            #         y-=diff
            #     while y <= -diff:
            #         if not self.prev_book():
            #             self.prev_shelf()
            #         y+=diff
            # else:
            #     x += dx
            #     while x >= diff:
            #         self.next_page()
            #         x -= diff
            #     while x <= -diff:
            #         self.prev_page()
            #         x += diff
            # self.last_pos = (x, y)


            #Nav by wheel and key
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

        return feedback
