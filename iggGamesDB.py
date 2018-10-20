#!/usr/bin/python
import sqlite3
import logging
import IPython


class IGGDB:

    def __init__(self, dbName='igg.db'):
        self.conn = sqlite3.connect(dbName)
        self.conn.row_factory = sqlite3.Row
        self.c = self.conn.cursor()

        self.log = logging.getLogger('DBIGG')
        self.log.info('DB openned: \'{}\'.'.format(dbName))
        self.initialize()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.conn.commit()
        self.conn.close()
        self.log.info('DB con terminated.')

    def initialize(self):
        if self.c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='config';").fetchone() == None:
            self.log.info('Initializing new database.')
            self.c.execute('''
                CREATE table config (
                    key text,
                    value text
                )
            ''')

            self.c.execute('''
                CREATE table games (
                    id integer primary key,
                    name text not null,
                    description text,
                    gameUrl text not null,
                    constraint name_unique unique (name)
                )
            ''')

            self.c.execute('''
                CREATE table links (
                    id integer primary key,
                    gameId integer,
                    provider text,
                    url text
                )
            ''')

            self.c.execute("INSERT into config(key, value) values('dbversion', '0');")
            self.conn.commit()

        else:
            self.log.info('DB already initialized.')
        self.update()
        self.conn.commit()


    def update(self):
        serviceLvl = int(self.c.execute('select value from config where key=\'dbversion\'').fetchone()['value'])
        if serviceLvl < 1:
            self.update0()
        # if serviceLvl < 2:
        #    self.update1()
        self.log.info('Database update finished.')
    
    def update0(self):
        # function for future database update to version 1
        pass


    def add(self, game, links):
        gameId = self.addGame(game)
        self.addLinks(id=gameId)
        #self.conn.commit()

    def addGame(self, game):
        try:
            self.c.execute('insert into games (id, name, description, gameUrl) values(NULL, ?, ?, ?)', (game['name'], game['desc'], game['url']))
        except Exception as e:
            self.log.error('Unable to insert game into db - duplicate exists: \'{}\''.format(game['name']))
        gameId = self.c.lastrowid
        #self.conn.commit()
        return gameId
        
    def addLinks(self, gameName, links, gameId=-1):
        #IPython.embed()
        if gameId == -1:
            # if id is not provided get it from db
            game = self.getGame(gameName)
            if game == None:
                self.log.error('game \'{}\' not found'.format(gameName))
                return
            gameId = game['id']
        for link in links:
            self.c.execute('insert into links(id, gameId, provider, url) values(NULL, ?, ?, ?)', (gameId, link['provider'], link['url']))
        #self.conn.commit()

      
    def getGame(self, name):
        game = self.c.execute('select * from games where name = ?',(name,)).fetchone()
        return game
    
    def getLinks(self, name):
        links = self.c.execute('select l.gameId, l.provider, l.url from games g join links l on g.id = l.gameId  where g.name = ?',(name,)).fetchall()
        lks = []
        for lnk in links:
            lks.append({'provider': lnk['provider'], 'url': lnk['url']})
            #lks.append((lnk['gameId'], lnk['provider'], lnk['url']))
        return lks


    def list(self):
        return self.c.execute('select * from games order by name asc')
