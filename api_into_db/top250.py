# coding: utf-8
import requests
import re
from lxml import html
from papapt.models import db, Top, Douban, Imdb
from papapt.gadgets import parse_info, get_json


"""
delimiter //
create procedure ins250() 
begin 
declare num int; 
set num=1; 
while num < 251 do 
insert into top(rank) values(num); 
set num=num+1;
end while;
end
//
call ins250()
"""


class Base(object):
    def __init__(self):
        self.new_rows = []

    def _get_page(self, url, proxy_dict=None):
        good, resp = False, None
        r = requests.get(url,  proxies=proxy_dict)
        if r.status_code == 200:
            good = True
            resp = r
        return good, resp

    def _commit_db(self):
        if self.new_rows:
            db.session.add_all(self.new_rows)
        db.session.commit()


class GetImdb(Base):
    def __init__(self):
        super(GetImdb, self).__init__()
        self.site = 'imdb'
        self.base_url = 'http://www.imdb.com/chart/top'
        self.model = self._get_site_model(self.site)

    def run(self):
        good, r = self._get_page(self.base_url)
        if good:
            print 'resp seems good, now save all items in one round'
            page = r.content
            tree = html.fromstring(page)
            all_250s = tree.xpath('.//tbody[@class="lister-list"]/tr')
            for item in all_250s:
                url = item[1][0].attrib['href']  # title tt url
                rank = int(item[0][0].attrib['data-value'])  # rank in top list
                item_id = re.findall(r"/(tt\d+)", url)[0].encode('utf-8')
                self._update_record(self.site, rank, item_id)
            self._commit_db()
            print 'done!'

    def save_detail_info(self, start, end):
        """
        get range site_id from top 250, then fetch each item, like:
        d = GetDouban()

        only run it at the first time for emtpy table
        d.bulk_insert()

        get top 250 records
        d.run()

        douban api hour limit around 150
        d.save_detail_info(0, 150)
        """
        all_ids = Top.query.filter(Top.rank.between(start, end)).all()
        not_good = []
        for row in all_ids:
            site_id = getattr(row, self.site + '_id')
            print 'working on %s id: %s' % (self.site, site_id),
            good, json = get_json(self.site, site_id)
            if good:
                print 'resp good, save it now'
                info = parse_info(self.site, json)
                self._save_single(site_id, info)
            else:
                print 'resp not good'
                not_good.append(site_id)
        self._show_fail(not_good)
        self._commit_db()

    def _show_fail(self, fail_list):
        if fail_list:
            print 'here are fail ids: ',
            for i in fail_list:
                print i,

    def _get_site_model(self, website):
        return globals()[website.title()]

    def _update_record(self, site, rank, site_id):
        column = site + '_id'
        Top.query.filter(Top.rank == rank).update({column: site_id})

    def bulk_insert(self):
        for i in range(1, 251):
            self.new_rows.append(Top(i))
        self._commit_db()

    def _save_single(self, site_id, info):
        q = self.model.query.filter(self.model.web_id == site_id).first()
        if not q:
            self.new_rows.append(self.model(info))
        else:  # maybe just for douban, run() method cant get full info
            info.pop('web_id')
            for k, v in info.iteritems():
                setattr(q, k, v)


class GetDouban(GetImdb):
    def __init__(self):
        super(GetDouban, self).__init__()
        self.site = 'douban'
        self.model = self._get_site_model(self.site)
        self.items_each_page = 50
        self.base_url = 'https://api.douban.com/v2/movie/top250'

    def run(self):
        for i in range(5):  # 250 / 50
            print 'working on page #%s' % i
            start_id = i * self.items_each_page
            good, r = self._get_page(
                                    self.base_url +
                                    '?start=' +
                                    str(start_id) +
                                    '&count=' +
                                    str(self.items_each_page)
                                    )
            if good:
                page_items = r.json().get('subjects', 0)
                if page_items:
                    print 'resp seems have items, now save them'
                    self._iterate_save(page_items, start_id)
        self._commit_db()

    def _iterate_save(self, page_items, start_id):
        for i in range(self.items_each_page):
            rank = start_id + i + 1  # 1-50 51-100 ...
            item = page_items[i]
            info = parse_info(self.site, item)
            item_id = info['web_id']
            self._update_record(self.site, rank, item_id)
            already_have = self.model.query.filter_by(web_id=item_id).first()
            if not already_have:
                self.new_rows.append(self.model(info))  # must save it now
            # some violence movie cant fetch by single id, fight club
