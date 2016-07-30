# coding: utf-8
import re
from flask import Blueprint, render_template, current_app, redirect, url_for, \
            g, flash
from datetime import datetime, timedelta
from ..forms import SearchForm
from ..models import SearchKeyword, SearchDate
from ..gadgets import save_keyword


home = Blueprint('home', __name__, static_folder='../static')


@home.before_app_request
def before_app_request():
    g.search_form = SearchForm()


def transfer_format(dt):
    return dt.strftime('%Y-%m-%d %H:%M:%S')


def get_hot_keywords():
    end = datetime.now()
    diff = timedelta(days=current_app.config['INDEX_KEYWORD_PERIOD'])
    start = transfer_format(end - diff)
    end = transfer_format(end)
    r = SearchKeyword.query.\
        join(SearchKeyword.dates).\
        filter(SearchDate.date.between(start, end)).\
        order_by(SearchKeyword.hit.desc())
    return r


@home.route('/')
def index():
    r = get_hot_keywords().\
                        limit(current_app.config['INDEX_MAX_KEYWORD']).\
                        distinct().\
                        all()
    return render_template('index.html', rows=r)


def find_id(keyword):
    found, website, site_id = False, None, None
    imdb = re.findall(r"imdb.+(tt\d+)", keyword)
    douban = re.findall(r"douban.+/(\d+)", keyword)
    if imdb or douban:
        found = True
        website = 'imdb' if imdb else 'douban'
        site_id = imdb[0] if imdb else douban[0]
    return found, website, site_id


def flash_errors(form):
    for field, errors in form.errors.items():
        for error in errors:
            flash(u"%s" % error)


@home.route('/search_query', methods=['POST'])
def search():
    if g.search_form.validate_on_submit():
        keyword = g.search_form.search.data
        found, website, site_id = find_id(keyword)
        if found:
            return redirect(url_for(
                                    'rating.by_site_id',
                                    website=website,
                                    site_id=site_id
                                    ))
        else:
            save_keyword(keyword)
            return redirect(url_for('search.result', keyword=keyword))
    else:
        flash_errors(g.search_form)
        return redirect(url_for('.index'))
