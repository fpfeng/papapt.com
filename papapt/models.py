# coding: utf-8
from flask_sqlalchemy import SQLAlchemy
# from sqlalchemy import Column, Float, Integer, String, Text, ForeignKey, func
from sqlalchemy.schema import FetchedValue
from sqlalchemy.orm import relationship


db = SQLAlchemy()


class Torrent(db.Model):
    __tablename__ = 'torrent'

    db_id = db.Column(db.Integer, primary_key=True)
    t_from = db.Column(db.String(11), nullable=False)
    t_id = db.Column(db.Integer, nullable=False)
    t_recat = db.Column(db.String(5), nullable=False)
    t_defi = db.Column(db.Integer, nullable=False)
    t_u_title = db.Column(db.String(255), nullable=False)
    t_d_title = db.Column(db.String(255), nullable=False)
    t_size = db.Column(db.Float, nullable=False)
    t_seed = db.Column(db.SmallInteger, nullable=False)
    t_peer = db.Column(db.SmallInteger, nullable=False)
    t_snatch = db.Column(db.Integer, nullable=False)
    t_discount = db.Column(db.String(20), nullable=False)
    t_addtime = db.Column(db.DateTime, nullable=False)
    t_comment = db.Column(db.SmallInteger, nullable=False)
    t_imdb = db.Column(db.String(11), nullable=False)
    t_douban = db.Column(db.Integer, nullable=False)
    last_edit = db.Column(db.DateTime, nullable=False)
    t_cat = db.Column(db.String(20), nullable=False)


class Imdb(db.Model):
    __tablename__ = 'imdb'

    db_id = db.Column(db.Integer, primary_key=True)
    web_id = db.Column(db.String(11), db.ForeignKey('search_keyword.keyword'), nullable=False, unique=True)
    title = db.Column(db.String(255), nullable=False)
    rating = db.Column(db.Float, nullable=False)
    plot = db.Column(db.String(2000), nullable=False)
    director = db.Column(db.String(255), nullable=False)
    actor = db.Column(db.String(255), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    country = db.Column(db.String(255), nullable=False)
    genre = db.Column(db.String(50), nullable=False)
    rank = db.relationship("Top", backref="imdb", lazy='dynamic')

    def __init__(self, info_dict):
        for k, v in info_dict.iteritems():
            setattr(self, k, v)

    def __repr__(self):
        return '<imdb %r>' % self.web_id


class Douban(db.Model):
    __tablename__ = 'douban'

    db_id = db.Column(db.Integer, primary_key=True)
    web_id = db.Column(db.Integer, db.ForeignKey('search_keyword.keyword'), nullable=False, unique=True)
    rating = db.Column(db.Float, nullable=False)
    director = db.Column(db.String(255), nullable=False)
    plot = db.Column(db.String(2000), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    actor = db.Column(db.String(255), nullable=False)
    alt_title = db.Column(db.String(255), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    country = db.Column(db.String(255), nullable=False)
    genre = db.Column(db.String(50), nullable=False)
    rank = relationship("Top", backref="douban", lazy='dynamic')

    def __init__(self, info_dict):
        for k, v in info_dict.iteritems():
            setattr(self, k, v)

    def __repr__(self):
        return '<douban %r>' % self.web_id


class Top(db.Model):
    __tablename__ = 'top'

    rank = db.Column(db.Integer, primary_key=True)
    douban_id = db.Column(db.Integer, db.ForeignKey('douban.web_id'))
    imdb_id = db.Column(db.String(30), db.ForeignKey('imdb.web_id'))

    def __init__(self, rank, douban_id=None, imdb_id=None):
        self.rank = rank
        if douban_id:
            self.douban_id = douban_id
        elif imdb_id:
            self.imdb_id = imdb_id

    def __repr__(self):
        return '<top #%r>' % self.rank


class Ustv(db.Model):
    __tablename__ = 'ustv'

    db_id = db.Column(db.Integer, primary_key=True)
    maze_id = db.Column(db.Integer, nullable=False, unique=True)
    title = db.Column(db.String(255), nullable=False)
    imdb = db.Column(db.String(11), nullable=False)
    chs_title = db.Column(db.String(255), nullable=False)
    douban = db.Column(db.Integer, nullable=False)
    network = db.Column(db.String(50), nullable=False)
    runtime = db.Column(db.Integer, nullable=False)
    episodes = relationship("Schedule", backref="tv", lazy='dynamic')

    def __init__(self, **kwargs):
        super(Ustv, self).__init__(**kwargs)

    def __repr__(self):
        return '<tv #%r>' % self.maze_id


class Schedule(db.Model):
    __tablename__ = 'schedule'

    db_id = db.Column(db.Integer, primary_key=True)
    show_id = db.Column(db.Integer, db.ForeignKey('ustv.maze_id'), nullable=False)
    season = db.Column(db.Integer, nullable=False)
    episode = db.Column(db.Integer, nullable=False)
    air_date = db.Column(db.DateTime, nullable=False)
    episode_id = db.Column(db.Integer, nullable=False, unique=True)

    def __init__(self, **kwargs):
        super(Schedule, self).__init__(**kwargs)

    def __repr__(self):
        return '<schedule %r>' % self.db_id


class SearchKeyword(db.Model):
    __tablename__ = 'search_keyword'

    db_id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column(db.String(255), nullable=False)
    hit = db.Column(db.Integer, nullable=False)
    keyword_type = db.Column(db.String(11), nullable=False)
    dates = relationship("SearchDate", backref='keyword', lazy='dynamic')
    douban = relationship("Douban", uselist=False)
    imdb = relationship("Imdb", uselist=False)

    def __init__(self, keyword, hit, keyword_type):
        self.keyword = keyword
        self.hit = hit
        self.keyword_type = keyword_type

    def __repr__(self):
        return '<keyword %r>' % self.db_id


class SearchDate(db.Model):
    __tablename__ = 'search_date'

    db_id = db.Column(db.Integer, primary_key=True)
    keyword_id = db.Column(db.Integer, db.ForeignKey('search_keyword.db_id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False)

    def __init__(self, date):
        self.date = date

    def __repr__(self):
        return '<date %r of keyword %r>' % (self.db_id, self.keyword_id)
