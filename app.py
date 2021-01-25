#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

from datetime import date
import json
from typing import final
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify, abort
from flask.globals import session
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from werkzeug.datastructures import ImmutableMultiDict
from wtforms.validators import ValidationError
from forms import *
from domain.models import db, Venue, Artist, Show
from flask_migrate import Migrate
import sys
from sqlalchemy import inspect, and_
import datetime
from sqlalchemy.sql.functions import func
from itertools import groupby 
from operator import itemgetter 
import traceback 
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#
app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app)
migrate = Migrate(app, db)
db_time_format = '%Y-%m-%d %H:%M:%S'
form_dt_format = '%Y-%m-%dT%H:%M:%S.%sZ'

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#
def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

def row_as_dict(obj):
  result = {}
  for c in inspect(obj).mapper.column_attrs:
    if c.key[0] == '_':
      result[c.key[1:]] = getattr(obj, c.key[1:])
    else:
      result[c.key] = getattr(obj, c.key)
  return result

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------
@app.route('/venues')
def venues():
  current_date = datetime.datetime.now().strftime(db_time_format)
  venue_list_result = Venue.query.outerjoin(Show, and_(Venue.id == Show.venue_id, Show.start_time >= current_date)) \
    .with_entities(Venue.id.label('venue_id'), Venue.name, Venue.city, Venue.state, db.func.count(Show.venues).label('num_upcoming_shows')) \
      .group_by(Venue.id).all()
  records = [dict(zip(row.keys(), row)) for row in venue_list_result]
  data = []
  for key, value in groupby(records, key = lambda d: (d['city'], d['state'])):
     current_city = {}
     current_city['city'] = key[0]
     current_city['state'] = key[1]
     current_city['venues'] = []
     for k in value:
       current_venue = {}
       current_venue['id'] = k['venue_id']
       current_venue['name'] = k['name']
       current_venue['num_upcoming_shows'] = k['num_upcoming_shows']
       current_city['venues'].append(current_venue)
     data.append(current_city)
  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_str =  search_term=request.form.get('search_term', '')
  current_date = datetime.datetime.now().strftime(db_time_format)
  result = Venue.query.outerjoin(Show, and_(Venue.id == Show.venue_id, Show.start_time > current_date)) \
    .with_entities(Venue.id, Venue.name, db.func.count(Show.artists).label('num_upcoming_shows')) \
      .group_by(Venue.id).having(Venue.name.ilike('%'+search_str+'%')).all()
  response={
    "count": len(result),
    "data":result
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  venue = Venue.query.get(venue_id);
  data = row_as_dict(venue)
  current_date = datetime.datetime.now().strftime(db_time_format)
  upcoming_show_result =Show.query.join(Artist).with_entities(Show.artist_id, Artist.name.label('artist_name'), 
  Artist.image_link.label('artist_image_link'), Show.start_time) \
    .filter(Show.venue_id == venue_id).filter(Show.start_time > current_date).all()
  records = [dict(zip(row.keys(), row)) for row in upcoming_show_result]
  for record in records:
    record['start_time'] = record['start_time'].strftime(form_dt_format)
  data["upcoming_shows"] = records
  data["upcoming_shows_count"] = len(records)
  past_show_result = Show.query.join(Artist).with_entities(Show.artist_id, Artist.name.label('artist_name'), 
  Artist.image_link.label('artist_image_link'), Show.start_time) \
    .filter(Show.venue_id == venue_id).filter(Show.start_time <= current_date).all()
  records = [dict(zip(row.keys(), row)) for row in past_show_result]
  for record in records:
    record['start_time'] = record['start_time'].strftime(form_dt_format)
  data["past_shows"] = records
  data["past_shows_count"] = len(records)
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------
@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  data: ImmutableMultiDict = request.form;
  venue = Venue()
  try:   
    venue.name = data['name']
    venue.city = data['city']
    venue.state = data['state']
    venue.address = data['address']
    venue.phone = data['phone']
    venue.genres = data.getlist('genres')
    venue.facebook_link = data['facebook_link']
    venue.website = data['website']
    venue.image_link = data['image_link']
    venue.seeking_description = data['seeking_description']
    if(data.get('seeking_talent', False) == 'y'):
      venue.seeking_talent = True
    else:
      venue.seeking_talent = False
    db.session.add(venue)
    db.session.commit()
    flash('Venue ' + venue.name + ' was successfully listed!')
  except:
    traceback.print_exc() 
    print(sys.exc_info())
    flash('An error occurred. Venue ' + data['name'] + ' could not be listed.', 'error')
    db.session.rollback()
  finally:
    db.session.close()    
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  venue: Venue = Venue.query.get(venue_id)
  try:    
    db.session.delete(venue)
    db.session.commit()
    flash('Venue ' + venue.name + ' was successfully Deleted')
  except:
    print(sys.exc_info())
    flash('Failed to delete Venue ' + venue.name)
    db.session.rollback()
  finally:
    db.session.close()
  return redirect(url_for('index'))

@app.route('/artists/<artist_id>', methods=['DELETE'])
def delete_artist(artist_id):
  artist: Artist = Artist.query.get(artist_id)
  try:    
    db.session.delete(artist)
    db.session.commit()
    flash('Artist ' + artist.name + ' was successfully Deleted')
  except:
    print(sys.exc_info())
    flash('Failed to delete Artist ' + artist.name)
    db.session.rollback()
  finally:
    db.session.close()
  return redirect(url_for('index'))

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  records = Artist.query.with_entities(Artist.id, Artist.name).all()
  return render_template('pages/artists.html', artists=records)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_str =  search_term=request.form.get('search_term', '')
  current_date = datetime.datetime.now().strftime(db_time_format)
  result = Artist.query.outerjoin(Show, and_(Artist.id == Show.artist_id, Show.start_time >= current_date)) \
    .with_entities(Artist.id, Artist.name, db.func.count(Show.artists).label('num_upcoming_shows')) \
      .group_by(Artist.id).having(Artist.name.ilike('%'+search_str+'%')).all()

  response={
    "count": len(result),
    "data": result
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  artist = Artist.query.get(artist_id);
  data = row_as_dict(artist)
  current_date = datetime.datetime.now().strftime(db_time_format)
  upcoming_show_result = Show.query.join(Venue).with_entities(Show.artist_id, 
  Venue.name.label('venue_name'), Venue.image_link.label('venue_image_link'), Show.start_time) \
    .filter(Show.artist_id == artist_id).filter(Show.start_time > current_date).all()
  records = [dict(zip(row.keys(), row)) for row in upcoming_show_result]
  for record in records:
    record['start_time'] = record['start_time'].strftime(form_dt_format)
  data["upcoming_shows"] = records
  data["upcoming_shows_count"] = len(records)

  past_show_result = Show.query.join(Venue).with_entities(Show.artist_id, 
  Venue.name.label('venue_name'), Venue.image_link.label('venue_image_link'), Show.start_time) \
    .filter(Show.artist_id == artist_id).filter(Show.start_time <= current_date).all()
  records = [dict(zip(row.keys(), row)) for row in past_show_result]
  for record in records:
    record['start_time'] = record['start_time'].strftime(form_dt_format)
  data["past_shows"] = records
  data["past_shows_count"] = len(records)
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.get(artist_id);
  data = row_as_dict(artist)
  return render_template('forms/edit_artist.html', form=form, artist=data)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  data: ImmutableMultiDict = request.form;
  artist = Artist.query.get(artist_id)
  try:
    if data['name']:
      artist.name = data['name']
    if data['city']:
      artist.city = data['city']
    if data['state']:
      artist.state = data['state']
    if data['phone']:
        artist.phone = data['phone']
    if data['genres']:
      artist.genres = data.getlist('genres')
    if data['facebook_link']:
      artist.facebook_link = data['facebook_link']
    if data['website']:
      artist.website = data['website']
    if data['image_link']:
      artist.image_link = data['image_link']
    if data['seeking_description']:
      artist.seeking_description = data['seeking_description']
    if(data.get('seeking_venue', False) == 'y'):
       artist.seeking_venue = True
    else:
       artist.seeking_venue = False
    db.session.add(artist)
    db.session.commit()
    flash('Artist ' + artist.name + ' was successfully listed!')
  except:
    traceback.print_exc() 
    print(sys.exc_info())
    flash('An error occurred. Artist ' + data['name'] + ' could not be listed.', 'error')
    db.session.rollback()
  finally:
    db.session.close()    

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id);
  data = row_as_dict(venue)
  print(data)
  return render_template('forms/edit_venue.html', form=form, venue=data)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  data: ImmutableMultiDict = request.form;
  venue = Venue.query.get(venue_id)
  try:
    if data['name']:
      venue.name = data['name']
    if data['city']:
      venue.city = data['city']
    if data['state']:
      venue.state = data['state']
    if data['address']:
      venue.address = data['address']
    if data['phone']:
        venue.phone = data['phone']
    if data['genres']:
      venue.genres = data.getlist('genres')
    if data['facebook_link']:
      venue.facebook_link = data['facebook_link']
    if data['website']:
      venue.website = data['website']
    if data['image_link']:
      venue.image_link = data['image_link']
    if data['seeking_description']:
      venue.seeking_description = data['seeking_description']
    if(data.get('seeking_talent', False) == 'y'):
       venue.seeking_talent = True
    else:
       venue.seeking_talent = False
    db.session.add(venue)
    db.session.commit()
    flash('Venue ' + venue.name + ' was successfully listed!')
  except:
    traceback.print_exc() 
    print(sys.exc_info())
    flash('An error occurred. Venue ' + data['name'] + ' could not be listed.', 'error')
    db.session.rollback()
  finally:
    db.session.close()    
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------
@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  data: ImmutableMultiDict = request.form;
  print(data)
  artist = Artist()
  error = False
  try:   
    artist.name = data['name']
    artist.city = data['city']
    artist.state = data['state']
    artist.phone = data['phone']
    artist.genres = data.getlist('genres')
    artist.facebook_link = data['facebook_link']
    artist.website = data['website']
    artist.image_link = data['image_link']
    artist.seeking_description = data['seeking_description']
    if(data.get('seeking_venue', False) == 'y'):
      artist.seeking_venue = True
    else:
      artist.seeking_venue = False   
    db.session.add(artist)
    db.session.commit()
    flash('Artist ' + artist.name + ' was successfully listed!')
  except:
    error = True
    traceback.print_exc() 
    print(sys.exc_info())
    flash('An error occurred. Venue ' + data['name'] + ' could not be listed.', 'error')
    db.session.rollback()
  finally:
    db.session.close()
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------
@app.route('/shows')
def shows():
  results = Show.query.join(Artist).join(Venue).with_entities(Venue.id.label('venue_id'), \
    Venue.name.label('venue_name'), Artist.id.label('artist_id'), Artist.name.label('artist_name'), \
      Artist.image_link.label('artist_image_link'), Show.start_time).all()
  records = [dict(zip(row.keys(), row)) for row in results]
  for record in records:
     record['start_time'] = record['start_time'].strftime("%Y-%m-%dT%H:%M:%S.%sZ")  
  return render_template('pages/shows.html', shows=records)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  data: ImmutableMultiDict = request.form;
  show : Show = Show()
  error = False
  try:   
    show.artist_id = data['artist_id']
    show.venue_id = data['venue_id']
    show.start_time = data['start_time']   
    db.session.add(show)
    db.session.commit()
    flash('Show was successfully listed!')
  except:
    error = True
    traceback.print_exc() 
    print(sys.exc_info())
    flash('An error occurred. Show could not be listed.', 'error')
    db.session.rollback()
  finally:
    db.session.close()
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')


#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
