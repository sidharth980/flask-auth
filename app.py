from flask import Flask, request, flash, url_for, redirect, render_template, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import re

# Functions

regex = '^(\w|\.|\_|\-)+[@](\w|\_|\-|\.)+[.]\w{2,3}$'


def check(email):

    if(re.search(regex, email)):
        return False

    else:
        return True

# User info


# App and database
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///user.sqlite3'
app.config['SECRET_KEY'] = "random string"


db = SQLAlchemy(app)

# User Class


class usrInfo(db.Model):
    id = db.Column('usrid', db.Integer, primary_key=True)
    usr = db.Column(db.String(100))
    pswd = db.Column(db.String(100))
    email = db.Column(db.String(100))

    def __init__(self, usr, pswd, email):
        self.usr = usr
        self.pswd = pswd
        self.email = email

# Route


@app.route('/')
def mainred():
    return redirect("/main")


@app.route('/main')
def mainpage():
    # global loginUsr
    if "user" in session:
        usrname = session["user"]
    else:
        usrname = None
    if usrInfo.query.filter_by(usr=usrname).first():
        pass
    else:
        usrname = None
    return render_template("main.html", name=usrname)


@app.route('/admin/<psd>')
def admin(psd):
    if psd == 'admin2045':
        return render_template('admin.html', usrInfo=usrInfo.query.all())
    else:
        return redirect(url_for("mainpage"))


@app.route('/new', methods=['GET', 'POST'])
def new():
    if request.method == 'POST':
        if not request.form['usr'] or not request.form['pswd1'] or not request.form['email']:
            flash('Please enter all the fields', 'error')
        elif request.form['pswd1'] != request.form['pswd2']:
            flash('Password not same', 'error')
        elif usrInfo.query.filter_by(usr=request.form['usr']).first():
            flash('Username already exists', 'error')
        elif len(request.form['pswd1']) < 8:
            flash('pswd too small', 'error')
        elif check(request.form['email']):
            flash('Invalid Email', 'Error')
        else:
            temp = usrInfo(
                request.form['usr'], generate_password_hash(
                    request.form['pswd1'], method='sha256'), request.form['email'])
            db.session.add(temp)
            db.session.commit()
            flash('Record was successfully added')
            return redirect(url_for('mainpage'))
    return render_template('new.html')


@app.route("/login", methods=['GET', 'POST'])
def login():
    # global loginUsr
    if request.method == 'POST':
        usr = request.form['usr']
        password = request.form['pswd']
        user = usrInfo.query.filter_by(usr=usr).first()
        if not usr or not user:
            flash('Please check your login details and try again.', 'error')
        elif not check_password_hash(user.pswd, password):
            flash('Incorrect Password', 'error')
        else:
            session["user"] = usr
            return redirect(url_for('mainpage'))
    return render_template("login.html")


@app.route('/delete/<int:id>')
def delete(id):
    task_to_delete = usrInfo.query.get_or_404(id)

    try:
        db.session.delete(task_to_delete)
        db.session.commit()
        return redirect(url_for("mainpage"))
    except:
        return 'There was a problem deleting that task'


@app.route('/change', methods=['GET', 'POST'])
def change():
    if request.method == 'POST':
        usrname = request.form['usr']
        oldpswd = request.form['oldpswd']
        newpswd = request.form['pswd1']
        confirmpswd = request.form['pswd2']
        print(usrname, oldpswd, newpswd, confirmpswd)
        admin = usrInfo.query.filter_by(usr=usrname).first()
        if not admin:
            flash('Please check your login details and try again.', 'error')
        elif not check_password_hash(admin.pswd, oldpswd):
            flash('incorrect old password', 'error')
        elif newpswd != confirmpswd:
            flash('password not same', 'error')
        elif len(request.form['pswd1']) < 8:
            flash('pswd too small', 'error')
        else:
            admin.pswd = generate_password_hash(newpswd, method='sha256')
            db.session.commit()
            return redirect('/main')
    return render_template('changepass.html')


@app.route("/logout")
def logout():
    # global loginUsr
    session.pop("user", None)
    return redirect(url_for("mainpage"))


if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
