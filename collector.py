# -*- coding: utf-8 -*-
import time
from typing import Optional, Any

from props import *

db_connection = None
db_cursor = None


def collect_arjlover(domain, link):
    import requests
    r = requests.get(link)
    if r.ok:
        page = r.text

        try:
            from lxml import etree
            dom = etree.HTML(page)

            # tree = html.etree.ElementTree(dom)
            # for e in dom.iter():
            #     print('%s/%s' % (tree.getpath(e), e.text))

            title = dom.xpath('/html/head/title/text()')[0]

            http = dom.xpath('/html/body/table[1]/tr[5]/td/table/tr[1]/td[2]/a/text()')[0]

            torrent = dom.xpath('/html/body/table[1]/tr[5]/td/table/tr[2]/td[2]/a/text()')[0]

            md5 = dom.xpath('/html/body/table[1]/tr[5]/td/table/tr[10]/td[2]/text()')[0]

            size = dom.xpath('/html/body/table[1]/tr[5]/td/table/tr[6]/td[2]/text()')[0]

            linked = dom.xpath('/html/body/table[1]/tr[5]/td/table/tr[4]/td[2]/noindex/a/@href')

            return {
                'url': link,
                'title': title,
                'size': size,
                'md5': md5,
                'linked': linked,
                'download': {
                    'http': '%s/%s' % (domain, http),
                    'torrent': '%s/%s' % (domain, torrent)
                }
            }
        except:
            return None
    return None


def arjlover(cache=True):
    import requests
    for category in multiki_arjlover_net['categories']:
        print('-- Category %s --' % category)
        category_link = multiki_arjlover_net['category_link'] % (category, category)
        r = requests.get(category_link)
        if r.ok:
            import bs4
            page = r.text
            soup = bs4.BeautifulSoup(page, 'html.parser')
            links = [a.get('href', None) for a in soup.select('td.l a')]
            if 0 < len(links):
                for link in links:
                    print()
                    print('Link=%s' % link)
                    info_link = '%s/%s' % (category_link, link)
                    if cache and db_has_arjlover(info_link, category):
                        print('Skip. Exits in database')
                        continue
                    info = collect_arjlover(category_link, info_link)
                    if info:
                        print('Name=%s' % info['title'])
                        db_id = db_add_arjlover(category, info)
                        if db_id:
                            print('Inserted to database id=%s' % db_id)
                            another_arjlover(db_id, info['title'])
                            db_commit()
                            continue
                    db_add_arjlover(category, {'url': info_link})
            print('// Category %s \\\\' % category)


def another_arjlover(db_id, title, year=None):
    # import re
    # if '.' in title:
    #     normalized_name = title[:title.index('.')]
    # normalized_name = re.sub(r'\W|\b\w*\d\b', ' ', normalized_name).strip()
    search = search_kp_unof_tech(title)
    if search and 0 < len(search):
        data = None
        if year:
            for s in search:
                y = s.get('year', None)
                if y:
                    if int(y) is year:
                        data = s
                        break
        if not data:
            data = search[0]
        if data:
            film_id = data['filmId']
            print('Founded in kinopoisk %s' % title)
            db_set_kp(db_id, data)
            rating = get_kp_rating(film_id)
            db_set_rating(db_id, rating)
            time.sleep(0.06)  # kinopoisk unoff api limit 20req per second


def get_kp_rating(film_id):
    import requests
    req = requests.get(kinopoisk_ru['rating_pattern'] % film_id)
    if req.ok:
        from lxml import etree
        xml = etree.fromstring(bytes(req.text, encoding='utf-8'))
        kp = xml.find('kp_rating')
        imdb = xml.find('imdb_rating')
        result = {}
        if kp is not None and kp.get('num_vote', None):
            result['kp'] = {
                'rating': float(kp.text),
                'votes': int(kp.get('num_vote', 0))
            }
        if imdb is not None  and imdb.get('num_vote', None):
            result['imdb'] = {
                'rating': float(imdb.text),
                'votes': int(imdb.get('num_vote', 0))
            }
        return result
    else:
        return None


def search_kp_unof_tech(keyword):
    import requests
    url = '%s/v2.1/films/search-by-keyword?keyword=%s&page=1' % (kinopoiskapiunofficial_tech['url'], keyword)
    headers = {
        'Content-Type': 'application/json',
        'X-API-KEY': kinopoiskapiunofficial_tech['key']
    }
    req = requests.get(url, headers=headers)
    if req.ok:
        import json
        body = req.text.replace('"null"', 'null')
        json = json.loads(body)
        films = json['films']
        if 0 < len(films):
            return films
        return None
    else:
        return None


def db_init():
    import psycopg2
    global db_connection, db_cursor
    db_connection = psycopg2.connect(postgresql['connect'])
    db_cursor = db_connection.cursor()


def db_commit():
    db_connection.commit()


def db_clear_all_tables():
    db_cursor.execute('TRUNCATE TABLE arjlover_source CASCADE')
    db_connection.commit()


def db_add_arjlover(category, data) -> Optional[int]:
    url = data.get('url', None)
    title = data.get('title', None)
    if url:
        if title:
            d = data['download']
            values = [url, title, data['size'], data['md5'], data['linked'], d['http'], d['torrent'], category]
        else:
            values = [url, None, None, None, None, None, None, category]
    else:
        return None
    db_cursor.execute(
        'INSERT INTO arjlover_source (url, title, size, md5, linked, http, torrent, category) '
        'VALUES (%s, %s, %s, %s, %s, %s, %s, %s) '
        'RETURNING id', values)
    id = db_cursor.fetchone()[0]
    return id


def db_has_arjlover(link, category) -> bool:
    db_cursor.execute('SELECT id FROM arjlover_source WHERE url=%s AND category=%s LIMIT 1', [link, category])
    return db_cursor.fetchone() is not None


def db_set_rating(source_id, data):
    kp = data.get('kp', {})
    imdb = data.get('imdb', {})
    values = [kp.get('rating', None), kp.get('votes', None), imdb.get('rating', None), imdb.get('votes', None), source_id]
    db_cursor.execute(
        'INSERT INTO rating_source (kp, kp_votes, imdb, imdb_votes, ref_id) '
        'VALUES (%s, %s, %s, %s, %s) ', values)


def db_set_kp(source_id, data):
    countries = data.get('countries', None)
    if countries:
        if 0 < len(countries):
            countries = [c.get('country', None) for c in countries]
        else:
            countries = None

    genres = data.get('genres', None)
    if genres:
        if 0 < len(genres):
            genres = [g.get('genre', None) for g in genres]
        else:
            genres = None

    values = [data.get('filmId', None), data.get('nameRu', None),
              data.get('nameEn', None), data.get('year', None),
              data.get('description', None), countries,
              genres, data.get('rating', None),
              data.get('ratingVoteCount', None), data.get('posterUrl', None), source_id]
    db_cursor.execute(
        'INSERT INTO kinopoisk_source (film_id, name_ru, name_en, year, description, countries, genres, rating, rating_vote_count, poster_url, ref_id) '
        'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', values)


def _a():
    db_cursor.execute('SELECT id, title FROM arjlover_source')
    a = db_cursor.fetchall()
    if a:
        for r in a:
            db_cursor.execute('SELECT ref_id FROM kinopoisk_source WHERE ref_id=%s', [r[0]])
            b = db_cursor.fetchone()
            if not b:
                another_arjlover(r[0], r[1])


if __name__ == '__main__':
    db_init()
    if db_connection:
        cache = postgresql['cache']
        if not cache:
            db_clear_all_tables()
        arjlover(cache)
        if db_connection:
            db_connection.commit()
            db_cursor.close()
            db_connection.close()
        else:
            print('Final data not committed. Database not connected')
    else:
        print('Collector not started. Database not connected')

# todolist
# Ебаные индексы в питоновских диктах хуйня полная. Использовать модели
# Глобы как в php ещё та залупень. Использовать классы
