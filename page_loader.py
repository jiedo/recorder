import time
import os
import subprocess
import json
from sound import tts
from ldoce5 import LDOCE5
from bs4 import BeautifulSoup
from tempfile import NamedTemporaryFile


ldoce5 = LDOCE5("/home/jie/abin/ldoce5.data", "/home/jie/.local/share/ldoce5viewer/filemap.cdb")

class PageLoader(object):
    def __init__(self, page):
        self.page_profile = page
        self.page = {
            'id': 0,
            'type': page['type'], #"Wiki",
            'title': page.get('title', page['type']),
            'data': page.get('data', page['type']),
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
        return statement

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
        return word

    def set_page_data(self, data):
        return ""

    def get_page_title(self):
        return ""

    def get_page_info(self):
        return ""



class WikiPageLoader(PageLoader):
    def __init__(self, page):
        PageLoader.__init__(self, page)
        self.page['type'] = "Wiki"

    def load_page(self):
        for i in range(8):
            self.page['mark'] = i
            self.new_section()
            for j in range(4):
                self.page['sections'][i]['mark'] = j
                self.new_statement()
                for k in range(32):
                    self.new_word()
        return self.page

    def store_page(self):
        page_string = json.dumps(self.page, indent=2)
        open("pages/page-wiki.json",
             "w").write(page_string)

    def get_word_sound_filename(self, word):
        filename = tts(word['title'])
        return filename, int(time.time() * 1000)



class VoicePageLoader(PageLoader):
    def __init__(self, page):
        PageLoader.__init__(self, page)
        self.pageid = page['id']
        self.page['type'] = "Voice"

    def load_page(self):
        self.page = json.loads(open("pages/page-%d.json" % self.pageid).read())
        self.page['type'] = "Voice"
        return self.page

    def store_page(self):
        page_string = json.dumps(self.page, indent=2)
        open("pages/page-%d.json" % self.pageid,
             "w").write(page_string)

    def get_word_sound_filename(self, word):
        shelf_id, book_id, page_id, word_id, create_time = (self.page['shelf-id'], self.page['book-id'], self.page['id'],
                                                            word['id'], word['create_time'])
        filename = "sounds/shelf.%d-book.%d-page.%d-word.%d.wav" % (shelf_id, book_id, page_id, word_id)
        return filename, create_time


class DirPageLoader(PageLoader):
    def __init__(self, page):
        PageLoader.__init__(self, page)
        self.page['type'] = "Dir"

    def load_page(self):
        self.new_section()
        self.new_statement()

        for root, dirs, files in os.walk(self.page['data'], topdown=False):
            # for name in dirs:
            #     word = self.new_word()
            #     word['title'] = name
            #     print "dir:", name
            names = [name for name in files]
            names.sort()
            names.reverse()
            for name in names:
                if name[-8:] == "-100.wav":
                    word = self.new_word()
                    word['title'] = name

        return self.page

    def store_page(self):
        page_string = json.dumps(self.page, indent=2)
        open("pages/page-dir.json",
             "w").write(page_string)

    def get_word_sound_filename(self, word):
        filename = os.path.join(self.page['data'], word['title'])
        return filename, int(time.time() * 1000)


class LdocePageListLoader(PageLoader):
    def __init__(self, page):
        PageLoader.__init__(self, page)
        self.page['type'] = "Ldoce"
        wordlist_filename = self.page['data']
        self.wordlist = json.loads(open(wordlist_filename).read())

    def load_page(self):
        self.new_section()
        statement = self.new_statement()
        for word_title, word_path in self.wordlist:
            word = self.new_word()
            word['title'] = word_title
            word['data'] = word_path
            word['type'] = "Ldoce"
        statement['mark'] = 0
        return self.page

    def store_page(self):
        page_string = json.dumps(self.page, indent=2)
        open("pages/page-list-ldoce.json",
             "w").write(page_string)

    def get_word_sound_filename(self, word):
        filename = tts(word['title'])
        return filename, int(time.time() * 1000)


class LdocePageLoader(PageLoader):
    def __init__(self, page):
        PageLoader.__init__(self, page)
        self.wordlist = []
        self.page['type'] = "Ldoce"
        path = self.page['data'].replace("dict://", "")
        data, mime = ldoce5.get_content(path)
        if not data:
            return
        root = BeautifulSoup(data, "lxml")
        for c in root.find_all("a"):
            if "class" in c.attrs and "audio" in c.attrs['class']:
                self.wordlist += [(c.text, c.attrs['href'])]

    def load_page(self):
        self.new_section()
        statement = self.new_statement()
        for word_title, word_path in self.wordlist:
            word = self.new_word()
            word['title'] = word_title
            word['data'] = word_path
            word['type'] = "Mp3"
        statement['mark'] = 0
        return self.page

    def store_page(self):
        page_string = json.dumps(self.page, indent=2)
        open("pages/page-ldoce.json",
             "w").write(page_string)

    def get_word_sound_filename(self, word):
        if "data" not in word:
            filename = tts(word['title'])
            return filename, int(time.time() * 1000)

        path = word['data'].replace("audio://", "")
        data, mime = ldoce5.get_content(path)
        if not data:
            return "", 0
        filename = ""
        with NamedTemporaryFile(mode='w+b', prefix='',
                                suffix='.mp3', delete=True) as f:
            f.write(data)
            f.flush()
            filename = f.name + ".wav"
            subprocess.call(['ffmpeg', '-loglevel', 'quiet',  '-i', f.name, '-vn',
                             filename])
        # filename = tts(word['title'])
        return filename, int(time.time() * 1000)
