from bs4 import BeautifulSoup
from ldoce5 import LDOCE5
from ldoce5 import advtree
import json

def page():
    ldoce5 = LDOCE5("/home/jie/abin/ldoce5.data", "/home/jie/.local/share/ldoce5viewer/filemap.cdb")
    path = "/fs/11503730847.6fc"
    data, mime = ldoce5.get_content(path)
    root = BeautifulSoup(data, "lxml")
    for c in root.find_all("a"):
        print (c.attrs, c.text.replace("\n\n", "\n").replace("\n\n", "\n").replace("\n", "\n\t").encode("utf8"))
    print ()

    # for c in root.find_all("div"):
    #     print c.attrs, c.text.replace("\n\n", "\n").replace("\n\n", "\n").replace("\n", "\n\t").encode("utf8")
    # print

    # print data

    # print(root.prettify().encode("utf8"))
    # for child in root:
    #     print(child.attrib, child.text)

def search():
    from utils.text import enc_utf8
    import utils.fulltext import Searcher
    from utils.advanced import search_and_render

    url = "search:///?filters=(asfilter:233)&mode=headwords"
    fulltext_defexa_path = "/home/jie/.local/share/ldoce5viewer/fulltext_de"
    fulltext_hwdphr_path = "/home/jie/.local/share/ldoce5viewer/fulltext_hp"
    variations_path = "/home/jie/.local/share/ldoce5viewer/variations.cdb"
    searcher_hp = Searcher(fulltext_hwdphr_path, variations_path)
    searcher_de = Searcher(fulltext_defexa_path, variations_path)
    data = enc_utf8(search_and_render("headwords", "", "(asfilter:233)", searcher_hp, searcher_de))
    word1000 = {}
    root = BeautifulSoup(data, "lxml")
    for c in root.find_all("a"):
        word1000[c.text] = c.attrs['href']
        # print (c.attrs, c.text)
    print (json.dumps(word1000, indent=2))

page()
