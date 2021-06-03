from flask import Flask, render_template, request ,session
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.utils import redirect
import certifi

app = Flask(__name__)
app.secret_key = 'python'

client = MongoClient("mongodb+srv://admin:<password>@cluster0.xvmi0.mongodb.net/test?retryWrites=true&w=majority",tls=True,tlsCAFile=certifi.where()) 
db = client.hospital_beds
col = db.hospital
users_col = db.users

@app.route("/")
def home():
    res = list(col.find())
    pincodes = set()
    zones = set()
    for x in res:
        pincodes.add(x['pincode'])
        zones.add(x['zone'])
    return render_template("index.html",hospitals = res,pincodes = pincodes,zones = zones)

@app.route("/appointments")
def appointments():
    username = session['user']
    user = users_col.find_one({"username":username})
    appointments = user['appointment']

    return render_template("appointments.html",appointments = appointments)

@app.route("/cencel/<email>/<hospital>/<bed>")
def cencel(email,hospital,bed):
    username = session['user']
    users_col.update_one(
        {"username":username},
        {"$pull":{"appointment":{"email":email}}}
    )
    col.update_one({"name":hospital},{"$inc":{bed : 1 , "beds_available ":1}})
    return redirect("/appointments")

@app.route("/filter",methods=['GET','POST'])
def filter():
    res = list(col.find())
    pincodes = set()
    zones = set()
    for x in res:
        pincodes.add(x['pincode'])
        zones.add(x['zone'])
    if request.method == 'POST':
        pincode = request.form['pincode']
        zone = request.form['zone']
        condition = request.form['condition']
        filter_res = []
        if pincode != "all" and zone != "all" and condition != "all":
            for x in res:
                if x['pincode'] == int(pincode) and x['zone'] == zone and x[condition]>0:
                    filter_res.append(x)
        elif pincode == "all" and zone == "all" and condition == "all":
            filter_res = res
        elif pincode != "all" and zone == "all" and condition == "all":
            for x in res:
                if x['pincode'] == int(pincode):
                    filter_res.append(x)
        elif pincode == "all" and zone != "all" and condition == "all":
            for x in res:
                if x['zone'] == zone:
                    filter_res.append(x)
        elif pincode == "all" and zone == "all" and condition != "all":
            for x in res:
                if x[condition] > 0:
                    filter_res.append(x)
        elif pincode != "all" and zone != "all" and condition == "all":
            for x in res:
                if x['zone'] == zone and x['pincode'] == int(pincode):
                    filter_res.append(x)
        elif pincode == "all" and zone != "all" and condition != "all":
            for x in res:
                if x['zone'] == zone and x[condition] > 0:
                    filter_res.append(x)
        elif pincode != "all" and zone == "all" and condition != "all":
            for x in res:
                if x['pincode'] == int(pincode) and x[condition] > 0:
                    filter_res.append(x)
        return render_template("index.html",hospitals = filter_res,pincodes = pincodes,zones = zones)

@app.route("/book/<id>")
def book(id):
    if ('user' in session):
        _id = ObjectId(id)
        hospital = col.find_one({"_id":_id})
        return render_template("book.html",hospital = hospital)
    return render_template("login.html")

@app.route("/booked",methods=['GET','POST'])
def booked():
    id = request.form['id']
    hospital = request.form['hospital_name']
    name = request.form['name']
    email = request.form['email']
    phone = request.form['phone']
    bed = request.form['bed_type']
    _id = ObjectId(id)
    filter = {"_id" : _id}
    new_value = {"$inc" : { bed : -1 , "beds_available ":-1} }
    print(bed)
    col.update_one(filter,new_value)
    username = session['user']
    filter = {"username":username}
    new_value = {"$push":{"appointment":{"hospital":hospital,"name":name,"email":email,"phone":phone,"bed":bed}}}
    users_col.update(filter,new_value)
    return redirect("/")

@app.route("/login",methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = users_col.find_one({"username":username,"password":password})
        if user:
            session['user'] = username
            return redirect("/")
        return render_template("login.html")

@app.route("/signup",methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        new_user = {
            "username":username,
            "password":password
        }
        users_col.insert_one(new_user)
        session['user'] = username
        return redirect("/")
    return render_template("signup.html")

if __name__ == "__main__":
    app.run(debug=True)
