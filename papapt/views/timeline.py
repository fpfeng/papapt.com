from flask import Blueprint, render_template, request
from ..models import Torrent


timeline = Blueprint('timeline', __name__)


@timeline.route('/timeline')
def pages():
    page = request.args.get('page', 1, type=int)
    query = Torrent.query.order_by(Torrent.t_addtime.desc())
    q_pagination = query.paginate(page, 20)
    page_items = q_pagination.items
    return render_template('timeline.html', rows=page_items, current_page=page)
