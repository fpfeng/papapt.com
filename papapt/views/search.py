# coding: utf-8
import re
from flask import Blueprint, current_app, render_template, request
from sqlalchemy import or_
from datetime import datetime
from ..models import Torrent


search = Blueprint('search', __name__)


@search.route('/search/<path:keyword>')
def result(keyword):
    mix_keyword = strip_and_replace(keyword)

    if mix_keyword == '%%':  # invaild
        return render_template('result.html', keyword=keyword)
    else:
        page = request.args.get('page', 1, type=int)
        order_by = request.args.get('order')
        sort_way = request.args.get('sort', 'des')
        cat = request.args.get('cat')  # torrent category

        title_like = or_(
                    Torrent.t_d_title.like(mix_keyword),
                    Torrent.t_u_title.like(mix_keyword))

        q = Torrent.query.filter(title_like)

        cat_count = {}
        if q.count() < current_app.config['CAT_COUNT_LIMIT_MAX_ITEM']:
            cat_count = count_torrents_cat(q)

        if order_by:
            order_attr = getattr(Torrent, order_by)
            if sort_way == 'asc':
                q = q.order_by(order_attr)
            else:
                q = q.order_by(order_attr.desc())

        if cat:
            q = q.filter(Torrent.t_recat == cat)

        q_pagination = q.paginate(page, current_app.config['ITEM_PER_PAGE'])
        rows = q_pagination.items

        return render_template(
                        'result.html',
                        keyword=keyword,
                        results=rows,
                        pagination=q_pagination,
                        counts=cat_count)


def count_torrents_cat(query):
    count_dict = {}
    for t in query.all():
        count_dict[t.t_recat] = count_dict.get(t.t_recat, 0) + 1
    return count_dict


def strip_and_replace(keyword):  # extract chs, eng, num char
    k = re.sub(u'[^\u4e00-\u9fa5a-zA-Z0-9]+', ' ', keyword)  # other to ' '
    k = '%' + "%".join(k.split()) + '%'  # ' ' to %
    return k


@search.app_template_filter(name='chstime')
def chs_time(dt, future_=u"穿越?", default=u"刚刚"):
    now = datetime.now()
    if now > dt:
        diff = now - dt
        dt_is_past = True
    else:
        diff = dt - now
        dt_is_past = False

    periods = (
        (diff.days / 365, u"年"),
        (diff.days / 30, u"月"),
        (diff.days / 7, u"周"),
        (diff.days, u"天"),
        (diff.seconds / 3600, u"时"),
        (diff.seconds / 60, u"分"),
        (diff.seconds, u"秒"),
    )

    if dt_is_past:
        for period, chs_period in periods:
            if period:
                return "%d%s" % (period, chs_period)
    else:
        return future_
    return default


@search.app_template_filter(name='chscat')
def chs_cat(cat_key):
    cat = {
        'bd': u'原盘',
        'mov': u'电影',
        'eustv': u'欧美剧',
        'eustvp': u'欧美剧包',
        'cntv': u'华语剧',
        'cntvp': u'华语剧包',
        'jktv': u'日韩剧',
        'jktvp': u'日韩剧包',
        'mob': u'移动格式',
        'spo': u'体育',
        'ami': u'动漫',
        'var': u'综艺',
        'mus': u'音乐',
        'doc': u'纪录片',
        'other': u'其它',
    }
    return cat.get(cat_key, u'未知')


@search.app_template_filter(name='defi')
def get_defi(defi_key):
    defi = {
        1: u'不明',
        3: '720p',
        5: '1080i',
        7: '1080p',
        8: 'BD',
        9: 'BD'
    }
    return defi.get(defi_key, u'不明')
