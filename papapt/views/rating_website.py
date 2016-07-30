# coding: utf-8
from flask import Blueprint, render_template, redirect, url_for, Markup,\
            flash, request, jsonify
from ..models import db, Douban, Imdb
from ..gadgets import save_keyword, get_json, parse_info
from .. import celery


rating = Blueprint('rating', __name__)


@rating.route('/<website>/<site_id>')
def by_site_id(website, site_id):
    if check_id_valid(website, site_id):
        maybe_int_id = check_turn_int(website, site_id)
        model = get_site_model(website)
        r = model.query.filter_by(web_id=maybe_int_id).first()
        if r:
            save_keyword(site_id, website)
        return render_template(
                                'byid.html',
                                website=website,
                                site_id=site_id,
                                result=r
                                )
    else:
        flash(create_id_invaild_msg(website, site_id))
        return redirect(url_for('home.index'))


def check_turn_int(website, site_id):
    return int(site_id) if website == 'douban' else site_id


def create_id_invaild_msg(website, site_id):
    site_name = {'imdb': 'IMDb', 'douban': '豆瓣'}.get(website, 'error')
    msg = '提取的%s编号<mark>%r</mark>位数不对，检查一下吧。'\
        % (site_name, site_id.encode('utf-8'))
    return Markup(msg.decode('utf-8'))


def check_id_valid(website, site_id):
    if website == 'imdb':
        return len(site_id) == 9
    if website == 'douban':
        return 6 < len(site_id) < 9


def get_site_model(website):
    return globals()[website.title()]


def create_new_row(website, info):
    row = None
    model = get_site_model(website)
    row = model(info)
    return row


@celery.task(bind=True)
def json_task(self, website, site_id):
    print('new task {0.id}, args: {0.args!r}'.format(self.request))
    self.update_state(state='PROGRESS', meta={'current': 30})
    success, json = get_json(website, site_id)
    self.update_state(state='PROGRESS', meta={'current': 50})
    if success:
        info = parse_info(website, json)
        self.update_state(state='PROGRESS', meta={'current': 70})
        row = create_new_row(website, info)
        self.update_state(state='PROGRESS', meta={'current': 80})
        db.session.add(row)
        self.update_state(state='PROGRESS', meta={'current': 90})
        db.session.commit()
        return {'current': 100}
    else:
        return {'current': 1}


@rating.route('/kickoff', methods=['POST'])
def start_task():
    website = request.form['website']
    site_id = request.form['id']
    if website == 'douban':
        site_id = int(site_id)
    task = json_task.delay(website, site_id)
    return jsonify({}), 202, {'progress': url_for('.task_status', task_id=task.id)}


@rating.route('/spider_status/<task_id>')
def task_status(task_id):
    status_msg = {
            30: '捕捉蜘蛛成功',
            50: '蜘蛛织网中',
            70: '收集信息成功',
            80: '蜘蛛回途中',
            90: '写入数据库',
            100: '1秒后刷新'
            }
    task = json_task.AsyncResult(task_id)
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'current': 10,
            'status': '寻找空闲蜘蛛'
        }
    elif task.state != 'FAILURE':
        current = task.info.get('current', 0)
        status = status_msg.get(current, 'error')
        response = {
            'state': task.state,
            'current': current,
            'status': status
        }
        if current == 1:
            response['status'] = '网络好像有点问题，或者试试别个编号吧'
        elif current == 100:
            response['job_done_mark'] = 1
    else:
        response = {
            'state': task.state,
            'current': 0,
            'status': '蜘蛛被你玩坏了'
        }
    return jsonify(response)
