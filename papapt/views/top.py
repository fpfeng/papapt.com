from flask import Blueprint, render_template, request, abort
from ..models import Top


top = Blueprint('top', __name__)


@top.route('/top250')
def top_rank():
    site = request.args.get('site')
    page = request.args.get('page', 1, type=int)
    items_each_page = 25
    if site in ['imdb', 'douban'] and 0 < page < 11:
        end = page * items_each_page
        start = end - items_each_page + 1
        result = Top.query.filter(Top.rank.between(start, end))
        return render_template('top.html', site=site, result=result.all())
    else:
        abort(404)
