from flask import Flask
from simple_recom import get_recommendations
from flask import render_template
from flask import request

app=Flask(__name__)

@app.route('/')
def index():
	return render_template('index.html',temp_title="World of Movies")



@app.route('/recommender')
def recommender():
	html_form_data= dict(request.args)
	print(html_form_data)
	recs = get_recommendations(html_form_data)
	return render_template('recommender.html',
                temp_title_rec="World of Movies Recommender", movies = recs)
