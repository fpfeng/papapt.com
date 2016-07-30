import requests
from datetime import datetime
from models import db, SearchKeyword, SearchDate


def save_keyword(keyword, keyword_type='normal'):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    r = SearchKeyword.query.filter_by(keyword=keyword).first()
    if not r:
        r = SearchKeyword(keyword, 1, keyword_type)
        db.session.add(r)
    else:
        r.hit += 1
    r.dates.append(SearchDate(now))
    db.session.commit()


def match_site(site, expect_site):
    return site == expect_site


def get_json(website, site_id, proxy_dict=None):
    if match_site(website, 'imdb'):
        r = requests.get(
            'http://www.omdbapi.com/?i=%s&plot=short&r=json' % site_id,
            proxies=proxy_dict
            )
    elif match_site(website, 'douban'):
        r = requests.get(
            'https://api.douban.com/v2/movie/subject/%d' % site_id,
            proxies=proxy_dict
            )
    return check_resp_vaild(website, r)


def check_key_counts(json, vaild_num):
    return True if len(json.keys()) > vaild_num else False


def check_resp_vaild(website, resp):
    status = False
    json = resp.json()
    if match_site(website, 'imdb'):
        if 'Error' not in json:
            if check_key_counts(json, 10):
                status = True
    elif match_site(website, 'douban'):
        if resp.status_code == 200:
            if check_key_counts(json, 20):
                status = True
    return status, json


def get_name(_dict):
    names = []
    for item in _dict:
        names.append(item.get('name', 0))
    return list_join_comma(names)


def list_join_comma(a_list):
    return ', '.join(a_list)


def get_vaules(json, website):
    def safe_get(key):
        return json.get(key, 0)
    values = {}

    if match_site(website, 'imdb'):
        values['web_id'] = safe_get('imdbID')
        values['director'] = safe_get('Director')
        values['title'] = safe_get('Title')
        values['plot'] = safe_get('Plot')
        values['actor'] = safe_get('Actors')
        values['year'] = int(safe_get('Year')[:4])
        values['country'] = safe_get('Country')
        values['genre'] = safe_get('Genre')

        rating = safe_get('imdbRating')
        if rating == 'N/A':
            values['rating'] = 0
        else:
            values['rating'] = float(rating)
    elif match_site(website, 'douban'):
        values['web_id'] = int(safe_get('id'))
        values['rating'] = safe_get('rating').get('average', 0)
        values['director'] = get_name(safe_get('directors'))
        values['title'] = safe_get('title')
        values['plot'] = safe_get('summary')
        values['actor'] = get_name(safe_get('casts'))
        values['alt_title'] = safe_get('original_title')
        values['year'] = int(safe_get('year'))
        values['genre'] = list_join_comma(safe_get('genres'))

        country = safe_get('countries')
        if country != 0:
            values['country'] = list_join_comma(country)
    for k in values.keys():
        if type(values[k]) == unicode:
            values[k] = turn_utf8(values[k])

    return values


def parse_info(website, json):
    info = get_vaules(json, website)
    return info


def turn_utf8(unicode_obj):
    try:
        return unicode_obj.encode('utf-8')
    except UnicodeError:
        return unicode_obj
