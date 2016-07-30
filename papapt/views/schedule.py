# coding: utf-8
import calendar
from flask import Blueprint, render_template, current_app, request, abort
from collections import defaultdict
from datetime import date
from ..models import Schedule


ustv = Blueprint('ustv', __name__)


@ustv.route('/ustv')
def schedule():
    app_year = current_app.config['SCHEDULE_CURRENT_YEAR']
    app_month = current_app.config['SCHEDULE_CURRENT_MONTH']
    year = request.args.get('y', app_year, type=int)
    month = request.args.get('m', app_month, type=int)
    title_lang = request.args.get('l', 'e')

    if (year == app_year - 1 and 0 < month < 13 or
        year == app_year and month < app_month + 2) \
            and title_lang in ['c', 'e']:

        start = get_isoformat(year, month, 1)
        if month == 12:
            end = get_isoformat(year + 1, 1, 1)
        else:
            end = get_isoformat(year, month + 1, 1)

        month_rows = Schedule.query.\
            filter(Schedule.air_date.between(start, end)).\
            order_by(Schedule.air_date).\
            all()

        month_cal = calendar.monthcalendar(year, month)

        after_group = group_by_day(month_rows)
        return render_template(
                        'tv.html',
                        cal=month_cal,
                        rows=after_group,
                        lang=title_lang,
                        month=month,
                        year=year)
    else:
        abort(404)


def get_isoformat(year, month, day):
    return date(year, month, day).isoformat()


def group_by_day(month_rows):
    month = defaultdict(list)
    for r in month_rows:
        month[r.air_date.day].append(r)
    return dict(month)


@ustv.app_template_filter(name='dayofweek')
def day_of_week(day_index, lang='chs'):
    weekdays = {
        'eng': ["mon", "tue", "wed", "thu", "fri", "sat", "sun"],
        'chs': [u"周一", u"周二", u"周三", u"周四", u"周五", u"周六", u"周日"]
        }
    return weekdays[lang][day_index]
