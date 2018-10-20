#!/usr/bin/python
import tkinter as tk
from tkinter import *
from iggGamesDB import *
import logging
import requests
from bs4 import BeautifulSoup
import IPython

class IGGApp:
    logging.basicConfig(filename='igggames.log', level=logging.DEBUG,
    #logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    log = logging.getLogger('main')
    srchStr = ''
    txtVar = 'Hi'
    games = []

    customHeaders = {
        'User-Agent': 'igg-bot 1.0',
        #'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection' : 'keep-alive',
        # Cookie: SID=7fjnqeNasdawqcVi-y1; groupCharacter=1; Connection: keep-alive
    }

    def __init__(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        cleanup()

    def cleanup(self, eventData=None):
        self.session.close()
        self.log.info('Requests session terminated.')

    def extractLinks(self, resp):
        soup = BeautifulSoup(resp.text, 'html.parser')
        content = soup.find('div', class_= 'post-content')
        links = content.find_all('a')
        extractedLinks = []
        for link in links:
            lnk = link['href']

            if lnk.find('bluemediafiles.com') >= 0:
                lnk = lnk[lnk.find('?xurl=')+6:]
                lnk = lnk[lnk.find('//')+2:].strip()
                provider = lnk[:lnk.find('/')]
                linkX = {'url': lnk, 'provider': provider}
                extractedLinks.append(linkX)

            if lnk.find('torrent') >= 0:
                # TODO: add with provider torrent
                pass
        return extractedLinks
        # links are grouped in <p>, <a>'s separated by ;
        # something like: ank.nextsibling(p).getall(a) ...


    def extractGames(self, resp):
        soup = BeautifulSoup(resp.text, 'html.parser')
        divcontent = soup.find('div', class_='post-content')
        lis = divcontent.find_all('li', {'id':''})
        games = []
        #self.log.debug('found {} games'.format(len(lis)))
        for li in lis:
            if li.a == None:
                continue
            try:
                game = {'name': li.a.text, 'desc':'', 'url': li.a['href']}
                games.append(game)
                #self.lst.insert(game)
            except Exception as e:
                self.log.error('Error: {} ===> during processing li: {}'.format(e, li))
        return games


    def loadGames(self):
        gms = self.db.list()
        for game in gms:
            gm = {'id': game['id'], 'name': game['name'], 'desc':game['description'], 'url': game['gameUrl']}
            self.games.append(gm)


    def updateAll(self):
        self.log.debug('btn: updating all')
        resp = self.session.get('http://igg-games.com/list-game.html')
        self.games = self.extractGames(resp)
        self.lst.delete(0, END)

        for game in self.games:
            '''
            resp = self.session.get(game['url'])
            links = self.extractLinks(resp)
            if links != None:
                self.db.add(game, links)
            else:
                self.log.error('links for game \'{}\' are empty'.format(game['name']))
            '''
            # only add game
            gameId = self.db.addGame(game)
            self.lst.insert(END, game['name'])
        # TODO: download all the game links ???
        self.db.conn.commit()


    def updateSelected(self):
        #selectedValue = self.lst.get(ACTIVE)
        selectedValue = self.lst.get(int(self.lst.curselection()[0]))
        game = self.db.getGame(selectedValue)
        resp = self.session.get(game['gameUrl'])
        extractedLinks = self.extractLinks(resp)
        self.db.addLinks(selectedValue, extractedLinks)
        self.db.conn.commit()
        return extractedLinks


    def search(self, something):
        # TODO: tokenize search - split to words by ' '
        if self.srchStr == self.searchStr.get().upper():
            return

        self.srchStr = self.searchStr.get().upper()
        self.log.debug('searching for \'{}\''.format(self.srchStr))
        self.lst.delete(0, END)
        #IPython.embed()
        for game in self.games:
            if game['name'].upper().find(self.srchStr) >= 0 or self.srchStr == '':
                self.lst.insert(END, game['name'])


    def display(self, something):
        #selectedValue = self.lst.get(ACTIVE)

        #self.txt.delete(1.0, END)
        #self.txt.insert(END, 'Loading ...')        # changes do not show up, window is frozen while this is running

        if len(self.lst.curselection()) == 0:
            return
        selectedValue = self.lst.get(int(self.lst.curselection()[0]))
        self.log.debug('displaying \'{}\''.format(selectedValue))
        links = self.db.getLinks(selectedValue)
        if len(links) == 0:
            links = self.updateSelected()
        text = ''
        for link in links:
            text += link['url'] + '\n'
        self.txt.delete(1.0, END)
        self.txt.insert(END, text)


    def createGUI(self):
        top = tk.Tk()

        # set txt column to fill the
        Grid.rowconfigure(top, 1, weight=1)
        Grid.columnconfigure(top, 2, weight=1)
        Grid.columnconfigure(top, 0, weight=1)
        
        #top = Frame(root)
        # Code to add widgets will go here...
        btnUpAll = tk.Button(top, text="Update all", command=self.updateAll)
        btnUpSel = tk.Button(top, text="Update selected", command=self.updateSelected)
        self.txt = tk.Text(top)
        #self.log.debug(dir(self.txt))
        
        self.searchStr = StringVar()
        self.inp = tk.Entry(top, textvariable=self.searchStr)
        self.inp.bind('<KeyRelease>', self.search)

        self.lst = tk.Listbox(top)
        scrollBar = Scrollbar(self.lst)
        self.lst.configure(yscrollcommand=scrollBar.set)
        scrollBar.configure(command=self.lst.yview)
        scrollBar.pack(side=tk.RIGHT, fill='y')
        #self.lst.bind('<Button-1>', self.display)
        self.lst.bind('<<ListboxSelect>>', self.display)
        self.lst.yview()
        #self.lst.width = 120
        games = self.db.list()
        for game in games:
            self.lst.insert(END, game['name'])

        self.inp.grid(row=0, column=0, columnspan=2, sticky='we')
        btnUpAll.grid(row=0, column=3)
        btnUpSel.grid(row=0, column=4)
        self.lst.grid(row=1, column=0, columnspan=2, sticky='wens')
        self.txt.grid(row=1, column=2, columnspan=4, sticky='wens')
        #txt.grid_rowconfigure(2, weight=1000)
        #txt.grid_columnconfigure(2, weight=1000)
        #top.protocol("WM_DELETE_WINDOW", self.cleanup)
        top.bind('<Destroy>', self.cleanup)
        top.mainloop()


    def run(self):
        self.session = requests.Session()
        self.session.headers.update(self.customHeaders)
        self.db = IGGDB()
        self.loadGames()
        self.createGUI()


    '''
    - refresh all button (only finds/updates new games)
    - refresh single game button (old values replaced)
    + automatic download from google drive (for others show only links)
    '''

app = IGGApp()
app.run()