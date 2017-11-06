#!/usr/bin/env python2

import pygame
import time
import json


class Library():
    def __init__(self, width, blocksize):
        self.WIN_WIDTH = width
        self.SIZEBLOCK = blocksize
        self.last_pos = (0, 0)
        self.last_block_mark = (0, 0, 0)
        self.last_vector = (0, 0)
        self.total_angle = 0
        self.pos_to_mark = {}
        self.runtime_row = 0
        self.runtime_col = 0

        self.color_page_with_sound_very_current = (0, 0, 0)
        self.color_page_with_sound_current = (0, 0, 0)
        self.color_page_with_sound_not_current = (140, 140, 140)

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
        except Exception, e:
            print "load library error:", e
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
        rec_color = self.color_page_with_sound_not_current
        if is_current:
            if is_current_shelf:
                if is_current_book:
                    color = self.color_page_very_current
                    rec_color = self.color_page_with_sound_very_current
                else:
                    color = self.color_page_current
                    rec_color = self.color_page_with_sound_current

        if page['create_time'] > 0:
            self.draw_rect(surface, rec_color, rect, margin=6+(2+2*(self.SIZEBLOCK-6)/3))

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
            self.library['mark'] = -1
            self.library['max_shelf_id'] = 1
            self.library['max_book_id'] = 0
            self.library['max_page_id'] = 0
        else:
            self.library['max_shelf_id'] += 1
        shelf = {
            'mark': -1,
            'id': self.library['max_shelf_id'],
            'title': "shelf-%d" % self.library['max_shelf_id'],
            'books': []
        }
        current_idx = self.library['mark']+1
        self.library['mark'] = current_idx
        self.library['shelfs'][current_idx:current_idx] = [shelf]


    def new_book(self):
        if 'shelfs' not in self.library:
            self.new_shelf()
        current_shelf_idx = self.library['mark']
        current_shelf = self.library['shelfs'][current_shelf_idx]
        self.library['max_book_id'] += 1
        book = {
            'mark': -1,
            'id': self.library['max_book_id'],
            'title': "book-%d" % self.library['max_book_id'],
            'pages': []
        }
        current_idx = current_shelf['mark']+1
        current_shelf['mark'] = current_idx
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
            'type': "Voice",
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
        current_idx = current_book['mark']+1
        current_book['mark'] = current_idx
        current_book['pages'][current_idx:current_idx] = [{
            "id": self.library['max_page_id'],
            "type": "Voice",
            'shelf-id': current_shelf['id'],
            'book-id': current_book['id'],
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
        return "%d of %d" % (current_idx, length)

    def prev_shelf(self):
        length = len(self.library['shelfs'])
        if length <= 0:
            return False
        current_idx = self.library['mark']
        current_idx -= 1
        if current_idx < 0:
            return False
        self.library['mark'] = current_idx
        return "%d of %d" % (current_idx, length)


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
        return "%d of %d" % (current_idx, length)


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
        return "%d of %d" % (current_idx, length)


    def swap_page_up(self):
        length = len(self.library['shelfs'])
        if length <= 0:
            return False
        current_shelf_idx = self.library['mark']
        current_shelf = self.library['shelfs'][current_shelf_idx]
        length = len(current_shelf['books'])
        if length <= 0:
            return False
        current_book_idx = current_shelf['mark']
        if current_book_idx < 1:
            return False
        current_shelf['mark'] = current_book_idx - 1
        current_book = current_shelf['books'][current_book_idx]
        length = len(current_book['pages'])
        if length <= 0:
            return False
        current_idx = current_book['mark']

        previous_book = current_shelf['books'][current_book_idx-1]
        length = len(previous_book['pages'])
        if length <= 0:
            return False
        previous_idx = previous_book['mark']

        a, b = current_book['pages'][current_idx], previous_book['pages'][previous_idx]
        current_book['pages'][current_idx], previous_book['pages'][previous_idx] = b, a
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
        return "%d of %d" % (current_idx, length)


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
        return "%d of %d" % (current_idx, length)


    def swap_page_right(self):
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
        page = self.get_current_page()
        if not page:
            return "", 0
        shelf_id, book_id, page_id, create_time = page['shelf-id'], page['book-id'], page['id'], page['create_time']
        filename = "sounds/shelf.%d-book.%d-page.%d.wav" % (shelf_id, book_id, page_id)
        return filename, create_time


    def get_current_page(self):
        if 'shelfs' not in self.library:
            return 0
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
        return current_book['pages'][current_idx]


    def set_current_page(self, create_time, update_time):
        if 'shelfs' not in self.library:
            return 0
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
        need_check_current_sound_file = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_3:
                self.new_shelf()
                feedback += "new shelf. "
            elif event.key == pygame.K_2:
                self.new_book()
                feedback += "new book. "
            elif event.key == pygame.K_1:
                self.new_page()
                feedback += "new page. "
            # Navigation
            if event.key == pygame.K_h:
                tip = self.prev_page()
                if tip:
                    feedback += "page " + tip
                    need_check_current_sound_file = True
                else:
                    feedback += "none. "
            elif event.key == pygame.K_l:
                tip = self.next_page()
                if tip:
                    feedback += "page " + tip
                    need_check_current_sound_file = True
                else:
                    feedback += "none. "
            if event.key == pygame.K_k:
                tip = self.prev_book()
                if not tip:
                    tip = self.prev_shelf()
                    if tip:
                        feedback += "shelf " + tip
                        need_check_current_sound_file = True
                    else:
                        feedback += "none. "
                else:
                    feedback += "book " + tip
                    need_check_current_sound_file = True
            elif event.key == pygame.K_j:
                tip = self.next_book()
                if not tip:
                    tip = self.next_shelf()
                    if tip:
                        feedback += "shelf " + tip
                        need_check_current_sound_file = True
                    else:
                        feedback += "none. "
                else:
                    feedback += "book " + tip
                    need_check_current_sound_file = True
            # swap
            elif event.key == pygame.K_t:
                if event.mod & pygame.KMOD_CTRL:
                    self.swap_page_up()
                else:
                    self.swap_page_right()

        elif event.type == pygame.MOUSEBUTTONDOWN:
            b1, b2, b3 = pygame.mouse.get_pressed()
            choice = 0
            if b1:
                if b3: choice = 3
                else: choice = 2
            else:
                if b3: choice = 1
                else: choice = 0

            if choice == 0:
                # Nav page (!b1+!b3)
                if event.button == 5:
                    tip = self.next_page()
                    if tip:
                        feedback += "page " + tip
                        need_check_current_sound_file = True
                    else:
                        feedback += "none. "
                elif event.button == 4:
                    tip = self.prev_page()
                    if tip:
                        feedback += "page " + tip
                        need_check_current_sound_file = True
                    else:
                        feedback += "none. "
            elif choice == 1:
                # Nav book (!b1+b3)
                if event.button == 5:
                    tip = self.next_book()
                    if not tip:
                        tip = self.next_shelf()
                        if tip:
                            feedback += "shelf " + tip
                            need_check_current_sound_file = True
                        else:
                            feedback += "none. "
                    else:
                        feedback += "book " + tip
                        need_check_current_sound_file = True
                elif event.button == 4:
                    tip = self.prev_book()
                    if not tip:
                        tip = self.prev_shelf()
                        if tip:
                            feedback += "shelf " + tip
                            need_check_current_sound_file = True
                        else:
                            feedback += "none. "
                    else:
                        feedback += "book " + tip
                        need_check_current_sound_file = True
            elif choice == 2:
                # Create (b1+!b3)
                if event.button == 5:
                    self.new_page()
                    feedback += "new page. "
                elif event.button == 4:
                    self.new_book()
                    feedback += "new book. "
            elif choice == 3:
                # Swap block (b1+b3)
                if event.button == 5:
                    self.swap_page_right()
                elif event.button == 4:
                    self.swap_page_up()

        elif False and event.type == pygame.MOUSEMOTION:
            #Nav by point to
            x, y = event.pos
            col, row = x/self.SIZEBLOCK, y/self.SIZEBLOCK
            if self.last_pos != (col, row):
                self.last_pos = (col, row)
                (shelfi, booki, pagei) = self.pos_to_mark.get((row, col), self.last_block_mark)
                if self.last_block_mark != (shelfi, booki, pagei):
                    self.last_block_mark = (shelfi, booki, pagei)
                    need_check_current_sound_file = True
                    if shelfi >= 0:
                        self.library['mark'] = shelfi
                    if booki >= 0:
                        self.library['shelfs'][shelfi]['mark'] = booki
                    if pagei >= 0:
                        self.library['shelfs'][shelfi]['books'][booki]['mark'] = pagei

        filename = ""
        if need_check_current_sound_file:
            filename, create_time = self.get_current_page_sound_filename()
            if create_time <= 0:
                filename = ""

        return feedback, filename
