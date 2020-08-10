# -*- coding: utf-8 -*-
from json import dumps, loads
from time import sleep
from xml.etree.ElementTree import fromstring

from bs4 import BeautifulSoup
from requests import get, post

from props import *


def main():
    source_url = 'http://multiki.arjlover.net/multiki/'
    req = get(source_url)
    if req.status_code == 200:
        req.encoding = 'windows-1251'
        content = req.text
        soup = BeautifulSoup(content, 'html.parser')
        find_result = soup.find_all('tr', class_='o')
        find_result += soup.find_all('tr', class_='e')
        items = []
        for tag in find_result:
            # getting name
            name_tag = tag.find('td', class_='l').find('a')
            name = name_tag.text
            # getting size
            size_tag = tag.find('td', class_='r')
            size = int(size_tag.text.replace('.', ''))
            # getting frame size
            frame_size_tag = tag.select('td')
            frame_size = frame_size_tag[3].text
            _result = frame_size.split('x', 2)
            width = _result[0]
            height = _result[1]
            # getting length
            length_str = frame_size_tag[4].text
            _result = length_str.split(':')
            length_h = int(_result[0])
            length_m = int(_result[1])
            length_s = int(_result[2])
            length_in_seconds = length_h * 60 * 60
            length_in_seconds += length_m * 60
            length_in_seconds += length_s
            # getting page url
            page_url = name_tag.get('href', None)
            full_page_url = source_url + page_url
            # getting file url
            url_tag = tag.find_all('a', text='http', limit=1)[0]
            file_url = url_tag.get('href', None)
            full_file_url = source_url + file_url
            # getting torrent file url
            torrent_tag = tag.find_all('a', text='torrent', limit=1)[0]
            torrent_file_url = torrent_tag.get('href', None)
            torrent_file_full_url = source_url + torrent_file_url

            description = ''
            kp_id = None
            kp_rating = None
            oddly = True

            kinopoisk_unof_tech = do_search_first_kinopoisk_unof_tech(name)
            if kinopoisk_unof_tech:
                kp_id = kinopoisk_unof_tech.get('filmId', None)
                kp_rating = get_kinopoisk_rating_by_id(kp_id)

            kino_teatr = do_search_kino_teatr(name)
            if kino_teatr:
                description = kino_teatr.get('description', None)

            # if kinopoisk_unof_tech:
            #     ru_name = kinopoisk_unof_tech.get('nameRu', None)
            #     print('kinopoisk_unof_tech %s//%s ratio %s' % (name, ru_name, fuzz.partial_token_sort_ratio(name, ru_name)))
            #     if fuzz.ratio(name, ru_name) >= 95:
            #         oddly = False
            # if kino_teatr:
            #     names = kino_teatr.get('names', None)
            #     if names:
            #         _oddly = True
            #         for _name in names:
            #             print('kinopoisk_unof_tech %s//%s ratio %s' % (name, _name, fuzz.partial_token_sort_ratio(name, _name)))
            #             if fuzz.ratio(name, _name) >= 95:
            #                 _oddly = False
            #                 break
            #         if _oddly is True and oddly is not True:
            #             oddly = True

            if kinopoisk_unof_tech:
                countries = kinopoisk_unof_tech.get('countries', None)
                genres = kinopoisk_unof_tech.get('genres', None)
                contains_allowed_country = None
                contains_allowed_genre = None
                if countries:
                    for country_obj in countries:
                        country = country_obj.get('country', None)
                        if country in ALLOWED_COUNTRIES:
                            contains_allowed_country = True
                            break
                    if contains_allowed_country is None:
                        contains_allowed_country = False
                if genres:
                    for genre_obj in genres:
                        genre = genre_obj.get('genre', None)
                        if genre in ALLOWED_GENRES:
                            contains_allowed_genre = True
                            break
                    if contains_allowed_genre is None:
                        contains_allowed_genre = False
                if contains_allowed_country is not None and contains_allowed_genre is not None:
                    oddly = not (contains_allowed_country and contains_allowed_genre)
                elif contains_allowed_country is not None:
                    oddly = not contains_allowed_country
                elif contains_allowed_genre is not None:
                    oddly = not contains_allowed_genre

            media_item = {
                'name': name,
                'description': description,
                'frame': {
                    'width': width,
                    'height': height
                },
                'size': size,
                'length': length_in_seconds,
                'metadata': {
                    'oddly': oddly
                },
                'source': {
                    'arjlover.net': {
                        'name': name,
                        'size': size,
                        'page_url': full_page_url,
                        'media_file_url': full_file_url,
                        'torrent_file_url': torrent_file_full_url
                    },
                    'kinopoiskapiunofficial.tech': kinopoisk_unof_tech,
                    'rating.kinopoisk.ru': {
                        'id': kp_id,
                        'rating': kp_rating,
                    },
                    'kino-teatr.ru': kino_teatr
                }
            }
            items.append(media_item)
            sleep(TIMEOUT_S)
            if len(items) == 11:
                break
        with open(SAVE_RESULT_TO, 'w+') as result_file:
            data = {
                'media': items,
                'version': DB_VERSION
            }
            result_file.write(dumps(data, indent=4))

def get_kinopoisk_rating_by_id(id):
    req = get('https://rating.kinopoisk.ru/%s.xml' % id)
    if req.status_code == 200:
        try:
            root = fromstring(req.text)
            kp = root.find('kp_rating')
            imdb = root.find('imdb_rating')
            return {
                'kp_rating': {
                    'votes': int(kp.get('num_vote', 0)),
                    'rating': float(kp.text)
                },
                'imdb_rating': {
                    'votes': int(imdb.get('num_vote', 0)),
                    'rating': float(imdb.text)
                }
            }
        except:
            return None
    else:
        return None
def do_search_kinopoisk_unof_tech(name):
    req = get(
        'https://kinopoiskapiunofficial.tech/api/v2.1/films/search-by-keyword?keyword=%s&page=1' % name,
        headers={
            'Content-Type': 'application/json',
            'X-API-KEY': API_KEY_kinopoiskapiunofficial_tech
        })
    if req.status_code == 200:
        try:
            return loads(req.text)
        except:
            return None
    else:
        return None
def do_search_first_kinopoisk_unof_tech(name):
    try:
        result = do_search_kinopoisk_unof_tech(name)
        result = result['films'][0]
        result['page_url'] = 'https://www.kinopoisk.ru/film/%s/' % result['filmId']
        return result
    except:
        return None
def do_search_kino_teatr(name):
    print('do_search_kino_teatr  %s' % name)
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = ('text=%s' % name).encode('windows-1251')
    req = post('https://www.kino-teatr.ru/search/', headers=headers, data=data, allow_redirects=True)
    if req.status_code == 200:
        soup = BeautifulSoup(req.text, 'html.parser')
        try:
            item = soup.select_one('div.list_item')
            link = item.select_one('div.list_item_name a').get('href', None)
            names_tag = item.select_one('div.list_item_name')
            names = names_tag.text.split('|')
            more_names_container_tag = item.select_one('div.list_item_content')
            if more_names_container_tag.select_one('span').text == 'Другие названия:':
                more_names_tag = more_names_container_tag.find_all('a')
                for tag in more_names_tag:
                    name = tag.get('title', None)
                    if name:
                        names.append(name)
            for e in link.split('/'):
                try:
                    id = int(e)
                    result = get_kino_teatr_by_id(id)
                    result['names'] = list(map(lambda n: n.strip(), names))
                    return result
                except:
                    pass
        except:
            pass
            # print(soup.text)
    else:
        return None
def get_kino_teatr_by_id(id):
    page_url = 'https://www.kino-teatr.ru/mult/movie/sov/%s/annot/' % id
    req = get(page_url)
    if req.status_code == 200:
        soup = BeautifulSoup(req.text, 'template.parser')
        description = soup.select_one('div.big_content_block div[itemprop="description"]')
        return {
            'id': id,
            'description': description.text,
            'page_url': page_url
        }
    else:
        return None
if __name__ == '__main__':
    main()
