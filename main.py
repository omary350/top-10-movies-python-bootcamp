from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer , String , desc
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField , FloatField
from wtforms.validators import DataRequired
import os
import requests
API_KEY = os.environ["api_key"]
API_URl = "https://api.themoviedb.org/3/search/movie"
DATA_API = "https://api.themoviedb.org/3/movie/"
PATH = "https://image.tmdb.org/t/p/original"

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
app.config["SQLALCHEMY_DATABASE_URI"]= "sqlite:///movies-collection.db"
db = SQLAlchemy(app)
Bootstrap5(app)


class EditForm(FlaskForm):
    new_rating = FloatField('New Rating Out of 10',validators=[DataRequired()])
    new_review = StringField('New Review',validators=[DataRequired()])
    submit = SubmitField(label="Done")

class AddForm(FlaskForm):
    movie = StringField('Movie Title',validators=[DataRequired()])
    submit = SubmitField(label="Add Movie")
class Movie(db.Model):
    id = Column(Integer,primary_key=True)
    title = Column(String,unique=True,nullable=False)
    year = Column(Integer,nullable=False)
    description = Column(String,nullable=False)
    rating = Column(Integer,nullable=True)
    ranking =  Column(Integer,nullable=True)
    review = Column(String,nullable=True)
    img_url =  Column(String,nullable=True)

with app.app_context():
    db.create_all()



movies = []
@app.route("/")
def home():
    rank = 1
    reslut = db.session.execute(db.select(Movie).order_by(desc(Movie.rating))).scalars().all()
    movies = reslut
    for movie in movies:
        movie.ranking = rank
        db.session.commit()
        rank += 1
    return render_template("index.html",movies=movies)

@app.route("/edit",methods = ["GET","POST"])
def edit():
    edit = EditForm()
    movie_id = request.args.get("id")
    movie = db.session.execute(db.select(Movie).where(Movie.id == movie_id)).scalar()
    if request.method == "POST":
        if edit.validate_on_submit():
            movie.rating = edit.data['new_rating']
            movie.review = edit.data['new_review']
            db.session.commit()
            return redirect(url_for('home'))
    return render_template("edit.html",form= edit,movie = movie)

@app.route("/delete",methods = ["GET","POST"])
def delete():
    movie_id = request.args.get("id")
    movie = db.session.execute(db.select(Movie).where(Movie.id == movie_id)).scalar()
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for('home'))

@app.route("/add",methods = ["GET","POST"])
def add():
    add = AddForm()
    expexted_movies = []
    if request.method == "POST":
        movie = add.data["movie"]
        headers = {
            "accept" : "application/json",
            "Authorization" : API_KEY
        }
        params = {
            "query" : movie
        }
        response = requests.get(url= API_URl,headers=headers,params=params)
        result= response.json()
        for first in result["results"]:
            movie_data = {
                "name" : first["original_title"],
                "year" : first["release_date"],
                "id"    : first["id"]
            }
            expexted_movies.append(movie_data)
        return render_template('select.html',movie=expexted_movies)

    return render_template("add.html",form = add)

@app.route("/select",methods = ["GET","POST"])
def select():
    movie_id = request.args.get("id")
    headers = {
        "accept": "application/json",
        "Authorization": API_KEY
    }
    response = requests.get(url=f"{DATA_API}{movie_id}", headers=headers)
    result = response.json()
    movie = Movie(title=result["original_title"], year=result["release_date"][0:4], description=result["overview"],
                  img_url=f"{PATH}{result['poster_path']}",id=result["id"])
    db.session.add(movie)
    db.session.commit()
    return redirect(url_for('edit',id = movie_id) )

if __name__ == '__main__':
    app.run(debug=True)
