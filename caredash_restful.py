import os

from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
from flask import jsonify

from flask import json
from sqlalchemy.ext.declarative import DeclarativeMeta

from flask_sqlalchemy import SQLAlchemy

from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.ext.hybrid import hybrid_method
from sqlalchemy.ext.hybrid import hybrid_property

Base = declarative_base()

project_dir = os.path.dirname(os.path.abspath(__file__))
database_file = "sqlite:///{}".format(os.path.join(project_dir, "doctordatabase.db"))

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = database_file
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

@app.route('/doctors', methods=["GET"])
def get_doctors():
    '''
    Get Method for all doctors
    '''
    doctors = None
    try:
        doctors = Doctor.query.all()
    except Exception as exc:
        print("Failed to get doctor")
        print(exc)
    d_list = []
    for d in doctors:
        n = d.name
        i = d.id
        try:
            r = Review.query.filter_by(doctor_id=i).all()
        except Exception as exc:
            print("No reviews.")
            r = None
        l = {'name':n,'id':i,'reviews':[{'description':a.description,'id':a.id,'doctor_id':a.doctor_id} for a in r]}
        d_list.append(l)

    return json.dumps(d_list)

@app.route('/doctors/<doc_id>', methods=["GET"])
def get_doctor(doc_id):
    '''
    Get Method for specific doctor (based on doc_id)
    '''
    docid = doc_id
    l = None
    try:
        d = db.session.query(Doctor).get(docid)
        n = d.name
        i = d.id
        try:
            r = Review.query.filter_by(doctor_id=i).all()
        except Exception as exc:
            print("No reviews.")
            r = None
        l = {'name':n,'id':i,'reviews':[{'description':a.description,'id':a.id,'doctor_id':a.doctor_id} for a in r]}
    except Exception as exc:
        print("Failed to get doctor")
        print(exc)
        return jsonify({"Success?": False})

    return json.dumps(l)

@app.route('/doctors', methods=["POST"])
def post_doctor():
    '''
    Attempts to add a doctor to the database
    '''
    try:
        if request.is_json:
            data = request.get_json()
            id = db.engine.execute('select count(id) from doctor').scalar()
            id = id + 1
            doctor = Doctor(
                name=data["doctor"]["name"],
                id=id,
                reviews=[])
            print(doctor.id)
            db.session.add(doctor)
            db.session.commit()
        else:
            print("Request must be JSON!")
    except Exception as exc:
        print("Failed to add doctor")
        print(exc)
        return jsonify({"Success?": False})
    return jsonify({"Success?": True})

@app.route("/doctors/<doc_id>/reviews", methods=["POST"])
def addReview(doc_id):
    '''
    Attempts to add a reviews to a specific doctor (doc_id)
    '''
    try:
        if request.is_json:
            data = request.get_json()
            docid = doc_id
            addReview(docid,data["review"]["description"])
        else:
            print("Request must be JSON!")
    except Exception as exc:
        print("Failed to add review")
        print(exc)
        return jsonify({"Success?": False})
    return jsonify({"Success?": True})

def addReview(pid, desc):
    '''
    Helper for addReview
    '''
    p = db.session.query(Doctor).get(pid) # will give you either Parent or None
    if not(p):
        p = Doctor(pname, pid)
        db.session.add(p)
        db.session.commit()
    try:
        id = p.child_count
        id = id + 1
    except Exception as exc:
        print(exc)
        id = 1
    p.reviews.append(Review(description=desc, id=id, doctor_id=pid))
    db.session.commit()


@app.route('/doctors/<doc_id>/reviews/<r_id>', methods=["GET"])
def get_review(doc_id,r_id):
    '''
    Gets a specific review from a specific doctor
    '''
    docid = doc_id
    rid = r_id
    l = None
    try:
        try:
            r = db.session.query(Review).get(rid)
            n = r.id
            des = r.description
            d = r.doctor_id
            doc = db.session.query(Doctor).get(docid)
            l = {'id':n,'description':des,'doctor_id':d,'doctor':{'id':doc.id,'name':doc.name}}
        except Exception as exc:
            print("No review.")
    except Exception as exc:
        print("Failed to get review")
    return jsonify(l)

@app.route('/doctors/<doc_id>/reviews/<r_id>', methods=["DELETE"])
def delete_review(doc_id,r_id):
    '''
    Deletes a specific review from a specific doctor
    '''
    docid = doc_id
    rid = r_id
    try:
        r = Doctor.query.filter_by(id=docid).all()
        for i in r:
            if i.id == rid:
                Review.query.filter_by(id=i.id).delete()
                db.session.commit()
    except Exception as exc:
        print("Failed to get doctor")
        print(exc)
        return jsonify({"Success?": False})
    return jsonify({"Success?": True})

@app.route('/doctors/<doc_id>', methods=["DELETE"])
def delete_doctor(doc_id):
    '''
    Deletes a doctor (and subsequently their reviews)
    '''
    docid = doc_id
    try:
        d = Doctor.query.filter_by(id=docid).all()
        for i in d:
            Review.query.filter_by(doctor_id=i.id).delete()
            db.session.commit()
        Doctor.query.filter_by(id=docid).delete()
        db.session.commit()
    except Exception as exc:
        print("Failed to get doctor")
        print(exc)
        return jsonify({"Success?": False})
    return jsonify({"Success?": True})



class Doctor(db.Model):
    '''
    Doctor model: makes sure to include child count property
    '''
    __tablename__ = 'doctor'
    name = db.Column(db.String(80), unique=False, nullable=False, primary_key=False)
    id = db.Column(db.Integer, unique=True, nullable=False, primary_key=True)

    def __repr__(self):
        return "<Title: {}>".format(self.name)

    @hybrid_property
    def child_count(self):
        return len(self.reviews)

class Review(db.Model):
    '''
    Review model: makes sure specify that doctor is the "parent"
    '''
    __tablename__ = 'review'
    description = db.Column(db.String(80), unique=False, nullable=False, primary_key=False)
    id = db.Column(db.Integer, unique=True, nullable=False, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id')) #parentid
    doctors = db.relationship("Doctor", backref='reviews')

    def __repr__(self):
        return "<Added to: {}>".format(self.doctor_id)
  
if __name__ == "__main__":
    app.run(debug=True)