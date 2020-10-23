from flask import Flask, render_template, flash, redirect, request, url_for, send_file, session
from werkzeug.utils import secure_filename
from functools import wraps
from authenticate import authenticate
import datetime
import couchdb
import json
from flask_mail import Mail, Message
import xlsxwriter
from cloudant.client import Cloudant
from cloudant.error import CloudantException
from cloudant.result import Result, ResultByKey

app = Flask(__name__)
#couch = couchdb.Server("http://%s:%s@localhost:5984"%("admin","admin123"))
client = Cloudant("a1c47c16-1328-46c9-9a6e-ea7970217b2a-bluemix", "4ce4ba06d89179652f10b5f22586a83a5f18541edecee9bec7d66d380e9216a7", url="https://a1c47c16-1328-46c9-9a6e-ea7970217b2a-bluemix:4ce4ba06d89179652f10b5f22586a83a5f18541edecee9bec7d66d380e9216a7@a1c47c16-1328-46c9-9a6e-ea7970217b2a-bluemix.cloudantnosqldb.appdomain.cloud")
client.connect()

#-----CREATE DB IF IT DOESN'T ALREADY EXIST AND RETURN A DATABASE OBJECT-----------------------------------------------#

def dbCreate(dbname,client):
    if dbname in client:
        db = client[dbname]
    else:
        db = client.create_database(dbname)
    return db

#-----CREATING REQUIRED DATABASES AND ASSIGNING OBJECTS----------------------------------------------------------------#

dbQuestMaster = dbCreate('quest_master',client)
dbFeedbackForm = dbCreate('feedback_form',client)
dbSubmitFeedback = dbCreate('submit_feedback',client)
dbinstitution = dbCreate('feedback_institution',client)


@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = datetime.timedelta(minutes=20)


def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))

    return wrap


@app.route('/submitFeedBack/<id>', methods=['POST','GET'])
def submitFeedBack(id):
	eventId = ""
	eventname = ""
	collegeName = ""
	eventdate = ""
	questIdList = []
	question = []
	for feedback in dbFeedbackForm:
	    if feedback['eventId'] == id:
	        eventname = feedback['eventName']
	        eventdate = feedback['eventdate']
	        collegeName = feedback['institution']
	        eventId = feedback['eventId']
	        questIdList = feedback['questtionList']

	        for questId in questIdList:
	            for quest in dbQuestMaster:
	                if quest['_id'] == questId:
	                    question.append(quest)
	        session['question'] = question
	        session['collegeName'] = collegeName
	        return render_template('submitFeedback.html',eventname = eventname, eventdate = eventdate,eventId = eventId,question = question,collegeName=collegeName)

@app.route('/saveFeedback/<id>', methods=['POST','GET'])
@is_logged_in
def saveFeedback(id):
	rating = request.form.getlist('feedackRating')
	prtName = request.form['partName']
	eventId = ""
	eventname = ""
	eventdate = ""
	questIdList = []
	question = []
	i = 0
	ratingList = []
	collegeName=session['collegeName']
	for feedback in dbFeedbackForm:
	    if feedback['eventId'] == id:
	        eventId = feedback['eventId']
	        eventname = feedback['eventName']
	        eventdate = feedback['eventdate']
	        questIdList = feedback['questtionList']
	        for quest in dbQuestMaster:
	            if quest['_id'] in questIdList:
	                feedbackList = {
						"question" : quest['question'],
						"rating":rating[i]
						}
	                i = i + 1
	                ratingList.append(feedbackList)
	        rating = {"eventid":eventId,
					  "eventName":eventname,
					  "partName":prtName,
					  "eventDate":eventdate,
					  "rating" : ratingList
					  }
	        dbSubmitFeedback.create_document(rating)

	flash('Feedback sumitted sucessfuly, Please close the browser. Thank you.', 'success')
	return render_template('submitFeedback.html',eventname = eventname, eventdate = eventdate,eventId = eventId,submitted = True,prtName=prtName,collegeName=collegeName)


if __name__ == '__main__':
    app.secret_key = 'secret123'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.run(host='0.0.0.0',port=5022,debug=True)
