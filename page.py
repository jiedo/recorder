#!/usr/bin/env python2

import pygame


class Page():
    def __init__(self, width, blocksize):
        self.WIN_WIDTH = width
        self.SIZEBLOCK = blocksize
        self.page_loader = None

    def load_page(self, page_loader):
        self.page_loader = page_loader
        self.page = self.page_loader.load_page(self.WIN_WIDTH / self.SIZEBLOCK)
        self.rect_need_draw = []
        self.last_block_pos = (0, 0)
        self.last_block_mark = (0, 0, 0)
        self.last_vector = (0, 0)
        self.total_angle = 0

        self.pos_to_mark = {}
        self.runtime_row = 0
        self.runtime_col = 0

        self.color_word_with_sound_very_current = (0, 0, 0)
        self.color_word_with_sound_current = (0, 0, 0)
        self.color_word_with_sound_not_current = (140, 140, 140)

        self.color_word_very_current_close = (200, 0, 0)
        self.color_word_current_close = (160, 40, 40)
        self.color_word_not_current_close = (100, 20, 20)

        self.color_word_very_current = (0, 200, 0)
        self.color_word_current = (180, 180, 180)
        self.color_word_not_current = (40, 40, 40)

        self.color_statement_tip = (200, 200, 200)
        self.color_section_tip = (200, 200, 200)

        self.color_statement_very_current = (180, 180, 180)
        self.color_statement_current = (110, 110, 110)
        self.color_statement_not_current = (1, 1, 1)

        self.color_section = (0, 0, 0)

    def store_page(self):
        self.page_loader.store_page()

    def update_page_display(self, surface):
        self.rect_need_draw.reverse()
        for color, rect in self.rect_need_draw:
            pygame.draw.rect(surface, color, rect, 0)
        self.rect_need_draw = []


    def draw_rect(self, surface, color, rect, margin=1):
        offset = margin
        self.rect_need_draw += [(color, rect.inflate(-offset, -offset))]


    def draw_word(self, surface, word, is_current_section, is_current_statement, is_current, rect):
        if word['type'] == 'Close':
            color = self.color_word_not_current_close
        else:
            color = self.color_word_not_current
        rec_color = self.color_word_with_sound_not_current
        if is_current:
            if is_current_section:
                if is_current_statement:
                    rec_color = self.color_word_with_sound_very_current
                    if word['type'] == 'Close':
                        color = self.color_word_very_current_close
                    else:
                        color = self.color_word_very_current
                else:
                    rec_color = self.color_word_with_sound_current
                    if word['type'] == 'Close':
                        color = self.color_word_current_close
                    else:
                        color = self.color_word_current

        if word['create_time'] > 0:
            self.draw_rect(surface, rec_color, rect, margin=6+(2+2*(self.SIZEBLOCK-6)/3))

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
                color = self.color_statement_tip
                statement_rect_tip = pygame.Rect(self.WIN_WIDTH-4, pos, 4, top+height - pos)
                self.draw_rect(surface, color, statement_rect_tip, margin=4)
        if is_current_section:
            color = self.color_statement_current
            if is_current:
                color = self.color_statement_very_current
        else:
            color = self.color_statement_not_current
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
            color = self.color_section_tip
            section_rect_tip = pygame.Rect(0, pos, 2, top - pos)
            self.draw_rect(surface, color, section_rect_tip, margin=2)
        color = self.color_section
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
            'mark': -1,
            'id': self.page['max_section_id'],
            'title': "section-%d" % self.page['max_section_id'],
            'statements': []
        }
        current_idx = self.page['mark']+1
        self.page['mark'] = current_idx
        self.page['sections'][current_idx:current_idx] = [section]


    def new_statement(self):
        if len(self.page['sections']) == 0:
            self.new_section()
        current_section_idx = self.page['mark']
        current_section = self.page['sections'][current_section_idx]
        self.page['max_statement_id'] += 1
        statement = {
            'mark': -1,
            'id': self.page['max_statement_id'],
            'title': "statement-%d" % self.page['max_statement_id'],
            'words': []
        }
        current_idx = current_section['mark']+1
        current_section['mark'] = current_idx
        current_section['statements'][current_idx:current_idx] = [statement]


    def new_word(self):
        if len(self.page['sections']) == 0:
            self.new_section()
        current_section_idx = self.page['mark']
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
        current_idx = current_statement['mark']+1
        current_statement['mark'] = current_idx
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
        return "%d of %d" % (current_idx, length)

    def prev_section(self):
        length = len(self.page['sections'])
        if length <= 0:
            return False
        current_idx = self.page['mark']
        current_idx -= 1
        if current_idx < 0:
            return False
        self.page['mark'] = current_idx
        return "%d of %d" % (current_idx, length)

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
        return "%d of %d" % (current_idx, length)


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
        return "%d of %d" % (current_idx, length)


    def swap_word_up(self):
        length = len(self.page['sections'])
        if length <= 0:
            return False
        current_section_idx = self.page['mark']
        current_section = self.page['sections'][current_section_idx]
        length = len(current_section['statements'])
        if length <= 0:
            return False
        current_statement_idx = current_section['mark']
        if current_statement_idx < 1:
            return False
        current_section['mark'] = current_statement_idx - 1
        current_statement = current_section['statements'][current_statement_idx]
        length = len(current_statement['words'])
        if length <= 0:
            return False
        current_idx = current_statement['mark']

        previous_statement = current_section['statements'][current_statement_idx-1]
        length = len(previous_statement['words'])
        if length <= 0:
            return False
        previous_idx = previous_statement['mark']

        a, b = current_statement['words'][current_idx], previous_statement['words'][previous_idx]
        current_statement['words'][current_idx], previous_statement['words'][previous_idx] = b, a
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
        return "%d of %d" % (current_idx, length)


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
        return "%d of %d" % (current_idx, length)


    def swap_word_right(self):
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

        return self.page_loader.get_word_sound_filename(word)


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
        need_check_current_sound_file = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_3:
                self.new_section()
                feedback += "new section. "
            elif event.key == pygame.K_2:
                self.new_statement()
                feedback += "new statements. "
            elif event.key == pygame.K_1:
                self.new_word()
                feedback += "new word. "

            if event.key == pygame.K_h:
                tip = self.prev_word()
                if tip:
                    feedback += "word " + tip
                    need_check_current_sound_file = True
                else:
                    feedback += "none. "
            elif event.key == pygame.K_l:
                tip = self.next_word()
                if tip:
                    feedback += "word " + tip
                    need_check_current_sound_file = True
                else:
                    feedback += "none. "
            if event.key == pygame.K_k:
                tip = self.prev_statement()
                if not tip:
                    tip = self.prev_section()
                    if tip:
                        feedback += "section " + tip
                        need_check_current_sound_file = True
                    else:
                        feedback += "none. "
                else:
                    feedback += "statement " + tip
                    need_check_current_sound_file = True
            elif event.key == pygame.K_j:
                tip = self.next_statement()
                if not tip:
                    tip = self.next_section()
                    if tip:
                        feedback += "section " + tip
                        need_check_current_sound_file = True
                    else:
                        feedback += "none. "
                else:
                    feedback += "statement " + tip
                    need_check_current_sound_file = True
            # swap
            elif event.key == pygame.K_t:
                if event.mod & pygame.KMOD_CTRL:
                    self.swap_word_up()
                else:
                    self.swap_word_right()

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
                # Nav word
                if event.button == 5:
                    tip = self.next_word()
                    if tip:
                        feedback += "word " + tip
                        need_check_current_sound_file = True
                    else:
                        feedback += "none. "
                elif event.button == 4:
                    tip = self.prev_word()
                    if tip:
                        feedback += "word " + tip
                        need_check_current_sound_file = True
                    else:
                        feedback += "none. "
            elif choice == 1:
                # Nav statement
                if event.button == 5:
                    tip = self.next_statement()
                    if not tip:
                        tip = self.next_section()
                        if tip:
                            feedback += "section " + tip
                            need_check_current_sound_file = True
                        else:
                            feedback += "none. "
                    else:
                        feedback += "statement " + tip
                        need_check_current_sound_file = True
                elif event.button == 4:
                    tip = self.prev_statement()
                    if not tip:
                        tip = self.prev_section()
                        if tip:
                            feedback += "section " + tip
                            need_check_current_sound_file = True
                        else:
                            feedback += "none. "
                    else:
                        feedback += "statement " + tip
                        need_check_current_sound_file = True
            elif choice == 2:
                # Create
                if event.button == 5:
                    self.new_word()
                    feedback += "new word. "
                elif event.button == 4:
                    self.new_statement()
                    feedback += "new statements. "
                else:
                    # only left click
                    need_check_current_sound_file = True
            elif choice == 3:
                # Swap block
                if event.button == 5:
                    self.swap_word_right()
                elif event.button == 4:
                    self.swap_word_up()

        elif False and event.type == pygame.MOUSEMOTION:
            #Nav by point to
            x, y = event.pos
            col, row = x/self.SIZEBLOCK, y/self.SIZEBLOCK
            if self.last_block_pos != (col, row):
                self.last_block_pos = (col, row)
                (sectioni, statementi, wordi) = self.pos_to_mark.get((row, col), self.last_block_mark)
                if self.last_block_mark != (sectioni, statementi, wordi):
                    self.last_block_mark = (sectioni, statementi, wordi)
                    need_check_current_sound_file = True
                    if sectioni >= 0:
                        self.page['mark'] = sectioni
                    if statementi >= 0:
                        self.page['sections'][sectioni]['mark'] = statementi
                    if wordi >= 0:
                        self.page['sections'][sectioni]['statements'][statementi]['mark'] = wordi

        filename = ""
        if need_check_current_sound_file:
            filename, create_time = self.get_current_word_sound_filename()
            if create_time <= 0:
                filename = ""

        return feedback, filename
