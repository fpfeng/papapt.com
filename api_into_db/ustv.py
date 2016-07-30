# coding: utf-8
import re
import calendar
from datetime import date
from sqlalchemy import and_
from dateutil import tz
from dateutil.parser import parse
from papapt.models import db, Ustv, Schedule, Douban
from papapt.gadgets import parse_info, get_json
from top250 import Base


UNWANTED_SHOW = (
            'The Young and the Restless',
            'Days of Our Lives',
            'General Hospital',
            'The Bold and the Beautiful',
            'Sesame Street'
            )

UNWANTED_NETWORK = (
                'IFC',
                'BOUNCE TV',
                'Oprah Winfrey Network',
                'Nickelodeon',
                'Disney Channel',
                'Hallmark Channel',
                'Telemundo',
                'Audience Network',
                'WGN america',
                'TVland',
                'History',
                'Adult Swim',
                'Chiller',
                'Hallmark Movies & Mysteries',
                'Univision',
                'Comedy Central',
                'VH1',
                'Disney XD',
                'TV One',
                'BET',
                'Bravo',
                'Nick Jr.',
                'BBC America',
                'truTV',
                'nicktoons',
                'E!',
                'We tv',
                'Investigation Discovery',
                'REELZ',
                'CMT',
                'UP TV',
                'Centric',
                'NBCSN',
                'Discovery Channel',
                'TLC',
                'Syndication',
                'CNBC',
                'Food Network',
                'TeenNick',
                'MTV2',
                'Outdoor Channel',
                'Bloomberg TV',
                'CBS Sports Network',
                'TV Guide Channel',
                u'UniMás',
                )


class GetSchedule(Base):
    def __init__(self):
        super(GetSchedule, self).__init__()
        self.base_url = 'http://api.tvmaze.com/schedule?country=US&date='
        self.douban_url = 'https://api.douban.com/v2/movie/imdb/'
        self.proxy = None
        # self.proxy = dict(  # useful when your test at china
        #         http='socks5://192.168.1.1:6667',  # go to line 145
        #         https='socks5://192.168.1.1:6667'
        #         )  # pip install requests[socks]

    def save_schedule(self, year, month):
        """
        main method
        g = GetSchedule()
        g.save_schedule(2016, 6)
        g.update_chs_title()
        thats all
        """
        last_day = calendar.monthrange(year, month)[1]
        days = [date(year, month, d).isoformat() for d in range(1, last_day + 1)]
        show_records = [tv.maze_id for tv in Ustv.query.all()]
        episode_records = [s.episode_id for s in Schedule.query.all()]
        for d in days:
            print 'working on date: ',
            print d
            self._save_schedule_of_day(d, show_records, episode_records)

    def update_chs_title(self):
        """
        douban api hour limit around 150
        """
        rows = Ustv.query.filter(and_(Ustv.douban == 1, Ustv.imdb != 'tt1')).all()
        for r in rows:
            self._imdb_reverse_douban(r)
        self._commit_db()

    def _imdb_reverse_douban(self, row):
        website = 'douban'
        status, json = self._get_json_of_url(self.douban_url, row.imdb)
        print 'working on imdb: %s, ' % row.imdb,
        if status:
            print 'and it have link to douban'
            print 'now try to get chs title, ',
            db_id = re.findall(r"douban.+/(\d+)", json['id'])[0]
            success, json = get_json(website, int(db_id))
            if success:
                print 'got it!'
                info = parse_info(website, json)
                title = info['title']
                if ' ' in title:
                    row.chs_title = info['title'].split()[0]  # xx 第x季
                else:
                    row.chs_title = title
                row.douban = info['web_id']
                new_row = Douban(info)  # dont waste this api access count
                self.new_rows.append(row)
            else:
                print 'fail! maybe it is censored item, need manual edit'
                row.douban = 3  # for example the walking dead
        else:
            print 'douban id not found or your reach api limit'
            row.chs_title = row.title

    def _get_json_of_url(self, head, tail, proxy_dict=None):
        resp_json = None
        good, r = self._get_page(head + tail, proxy_dict)
        if good:
            resp_json = r.json()
        return good, resp_json

    def _save_schedule_of_day(self, date_string, show_records, episode_records):
        resp, tv_json = self._get_json_of_url(
                                            self.base_url,
                                            date_string,
                                            self.proxy
                                            )
        if resp:
            from_tz = tz.gettz('America/New_York')
            to_tz = tz.gettz('Asia/Shanghai')
            for tv in tv_json:
                if self._check_is_vaild(tv):
                    show_info, schedule_info = {}, {}
                    maze_id = int(tv['show']['id'])
                    if maze_id not in show_records:# only save new show
                        show_info['maze_id'] = maze_id
                        show_info['title'] = tv['show']['name']
                        show_info['network'] = tv['show']['network']['name']

                        runtime = tv.get('runtime')
                        show_info['runtime'] = int(runtime) if runtime else 1

                        imdb = tv['show']['externals']['imdb']  # go maze forum
                        show_info['imdb'] = imdb if imdb else 'tt1'  # post fix it

                        show_records.append(maze_id)
                        row = Ustv(**show_info)
                        self.new_rows.append(row)

                    ep_id = int(tv['id'])
                    schedule_info['show_id'] = maze_id
                    schedule_info['season'] = int(tv['season'])
                    schedule_info['episode'] = int(tv['number'])
                    us = parse(tv['airstamp']).replace(tzinfo=from_tz)
                    cn = us.astimezone(to_tz).strftime("%Y-%m-%d %H:%M:%S")
                    schedule_info['air_date'] = cn

                    if ep_id in episode_records:  # maybe delay airtime fix it
                        q = Schedule.query.filter_by(episode_id=ep_id).first()
                        for k, v in schedule_info.iteritems():
                            setattr(q, k, v)
                    else:
                        schedule_info['episode_id'] = ep_id
                        row = Schedule(**schedule_info)
                        self.new_rows.append(row)
                        episode_records.append(ep_id)
            self._commit_db()

    def _check_is_vaild(self, tv_dict):
        is_vaild = False
        if tv_dict['show']['type'] == 'Scripted' and \
                tv_dict['show']['network']['name'] not in UNWANTED_NETWORK and \
                tv_dict['show']['name'] not in UNWANTED_SHOW and \
                tv_dict['number']:  # null means that just tv show preview
            is_vaild = True
        return is_vaild
