from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.hybrid import hybrid_property
db = SQLAlchemy()

class Artist(db.Model):
    __tablename__ = 'artist'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String())
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    _genres = db.Column('genres', db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking_venue  = db.Column(db.Boolean, default = False, nullable = False)
    seeking_description = db.Column(db.String())
    website = db.Column(db.String())
    @hybrid_property
    def genres(self):
        return [str(x) for x in self._genres.split(',')]
    @genres.setter
    def genres(self, value):
        self._genres += ',%s' % value
    def __repr__(self) -> str:
        return f'Artist(id:{self.id}, name: {self.name})'

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Venue(db.Model):
    __tablename__ = 'venue'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    _genres = db.Column('genres', db.String(500))
    website = db.Column(db.String())
    facebook_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, default = False, nullable = False)
    seeking_description = db.Column(db.String())
    image_link=db.Column(db.String())
    @hybrid_property
    def genres(self) ->str :
        return [str(x) for x in self._genres.split(',')]
    @genres.setter
    def genres(self, value):
        print('this ia VLUE' + str(value[1]))
        data = ''
        for v in value:
           data += ',%s' % str(v)
        self._genres =  data
    def __repr__(self) -> str:
        return f'Venue(id:{self.id}, name: {self.name})'
    # TODO: implement any missing fields, as a database migration using Flask-Migrate


class Show(db.Model):
    __tablename__ = 'shows'
    artist_id =  db.Column(db.Integer, db.ForeignKey('artist.id'), primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('venue.id'), primary_key=True)
    start_time =  db.Column('start_time', db.DateTime, primary_key=True)
    artists = db.relationship('Artist', backref = 'show_list', lazy = True)
    venues = db.relationship('Venue', backref = 'show_list', lazy = True)