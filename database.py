import os
import sqlite3

import music_tag

INIT_SCRIPT = """
    CREATE TABLE Genre (
    id    INTEGER PRIMARY KEY ASC AUTOINCREMENT,
    title TEXT    UNIQUE
    );
    
    CREATE TABLE Artist (
    id   INTEGER PRIMARY KEY ASC AUTOINCREMENT,
    name TEXT    UNIQUE
    );
    
    CREATE TABLE Album (
    id         INTEGER PRIMARY KEY ASC AUTOINCREMENT,
    title      TEXT,
    artistId   INTEGER REFERENCES Artist (id),
    coverImage BLOB
    );
    
    CREATE TABLE Track (
    id          INTEGER PRIMARY KEY ASC AUTOINCREMENT,
    albumId     INTEGER REFERENCES Album (id),
    title       TEXT,
    releaseYear INTEGER,
    path        TEXT    UNIQUE,
    genreId     INTEGER REFERENCES Genre (id),
    albumIndex  INTEGER
    );

    CREATE TABLE Track_Artist (
    artistId INTEGER REFERENCES Artist (id),
    trackId  INTEGER REFERENCES Track (id) 
    );
    
    INSERT INTO Artist (
                       name, id)
                   VALUES (
                       'unknown',0);
"""
DEFAULT_COVER_IMAGE = open('media/default_cover.jpg', 'br').read()


class Database:
    def __init__(self):
        self.con = sqlite3.connect('music.sqlite')

        cur = self.con.cursor()
        if not cur.execute('SELECT name FROM sqlite_master').fetchall():
            cur.executescript(INIT_SCRIPT)

    def _add_track(self, title: str, album: int, path: str, year: int, genre: int, album_index: int):
        cur = self.con.cursor()
        cur.execute("""
            INSERT INTO Track (
                      genreId,
                      path,
                      releaseYear,
                      title,
                      albumId,
                      albumIndex
                  )
                  VALUES (?,?,?,?,?,?); 
        """, (genre, path, year, title, album, album_index))
        self.con.commit()

    def _update_track(self, ids: tuple[int], **kwargs):
        cur = self.con.cursor()
        for key, val in kwargs.items():
            cur.execute(f"""UPDATE Track
                            SET {key} = {val}
                            WHERE id IN {ids}""")

    def _get_track(self, **kwargs) -> tuple:
        cur = self.con.cursor()
        column = list(kwargs.keys())[0]
        return cur.execute(f"""SELECT * FROM Track WHERE {column} = {kwargs[column]}""").fetchone()

    def _add_album(self, title: str, artist: int, cover_image):
        cur = self.con.cursor()
        cur.execute("""
                    INSERT INTO Album (
                              title,
                              artistId,
                              coverImage
                          )
                          VALUES (?, ?, ?); 
                """, (title, artist, cover_image))
        self.con.commit()

    def _add_genre(self, title: str):
        cur = self.con.cursor()
        cur.execute("""
                    INSERT INTO Genre (
                              title
                          )
                          VALUES (?); 
                """, (title,))
        self.con.commit()

    def _add_artist(self, name: str):
        cur = self.con.cursor()
        cur.execute("""
                    INSERT INTO Artist (
                              name
                          )
                          VALUES (?); 
                """, (name,))
        self.con.commit()

    def _add_track_artist(self, track_id: int, artist_id: int):
        cur = self.con.cursor()
        cur.execute("""
                            INSERT INTO Track_Artist (
                                      artistId,
                                      trackId
                                  )
                                  VALUES (?, ?); 
                        """, (artist_id, track_id))
        self.con.commit()

    def _get_track_tags_from_file(self, path):
        file = music_tag.load_file(path)

        if not file['tracktitle']:
            file['tracktitle'] = os.path.basename(path)
        title = str(file['tracktitle'])

        album = str(file['album']) if file['album'] else ''
        year = int(file['year'])
        genre = str(file['genre']) if file['genre'] else ''
        index = int(file['tracknumber'])
        image = file['artwork'].first.data if file['artwork'].first else None
        artist = str(file['artist']) if file['artist'] else ''

        return {'title': title, 'album': album, 'year': year, 'genre': genre, 'path': path, 'index': index,
                'coverimage': image, 'artist': artist}

    def fill_database_from_files(self, paths: list[str]):
        cur = self.con.cursor()
        existing = list(map(lambda x: x[0], cur.execute("""SELECT path FROM Track""").fetchall()))
        to_add = filter(lambda x: x not in existing, paths)

        for path in to_add:
            data = self._get_track_tags_from_file(path)

            artist = cur.execute("SELECT id FROM Artist WHERE name = ?", (data['artist'],)).fetchone()
            if data['artist'] and not artist:
                self._add_artist(data['artist'])
                artist = cur.execute("SELECT id FROM Artist WHERE name = ?", (data['artist'],)).fetchone()

            album = cur.execute("""SELECT id FROM Album WHERE title = ? AND artistId = ?""",
                                (data['album'], *artist)).fetchone()
            cover_image = data['coverimage'] if data['coverimage'] else DEFAULT_COVER_IMAGE
            if not album:
                if not data['album']:
                    album_title = data['title']
                else:
                    album_title = data['album']

                self._add_album(album_title, *artist, cover_image)
                album = cur.execute("""SELECT id FROM Album WHERE title = ? AND artistId = ?""",
                                    (album_title, *artist)).fetchone()

            genre = cur.execute("""SELECT id FROM Genre WHERE title = ?""", (data['genre'],)).fetchone()
            if not genre and data['genre']:
                self._add_genre(data['genre'])
                genre = cur.execute("""SELECT id FROM Genre WHERE title = ?""", (data['genre'],)).fetchone()

            self._add_track(data['title'], *album, path, data['year'], *genre, data['index'])

            track = cur.execute("""SELECT id FROM Track WHERE path = ?""", (path,)).fetchone()
            self._add_track_artist(*track, *artist)
