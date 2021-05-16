from flask import Flask, request, flash, url_for, redirect, render_template
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

loginUsr = None

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///user.sqlite3'
app.config['SECRET_KEY'] = "random string"

db = SQLAlchemy(app)

class usrInfo(db.Model):
   id = db.Column('usrid', db.Integer, primary_key = True)
   usr = db.Column(db.String(100))
   pswd = db.Column(db.String(100))

   def __init__(self, usr, pswd):
      self.usr = usr
      self.pswd = pswd
   
@app.route('/main')
def mainpage():
   global loginUsr
   return render_template("main.html",name = loginUsr)

@app.route('/admin')
def admin():
   return render_template('admin.html', usrInfo = usrInfo.query.all() )

@app.route('/new', methods = ['GET', 'POST'])
def new():
   if request.method == 'POST':
      if not request.form['usr'] or not request.form['pswd1']:
         flash('Please enter all the fields', 'error')
      elif request.form['pswd1']!=request.form['pswd2']:
         flash('Password not same', 'error')
      elif usrInfo.query.filter_by(usr=request.form['usr']).first():
         flash('Username already exists', 'error')
      else:
         temp = usrInfo(request.form['usr'],request.form['pswd1'])
         db.session.add(temp)
         db.session.commit()
         flash('Record was successfully added')
         return redirect(url_for('mainpage'))
   return render_template('new.html')

@app.route("/login",methods=['GET', 'POST'])
def login():
   global loginUsr
   if request.method == 'POST':
      usr = request.form['usr']
      password = request.form['pswd']
      user = usrInfo.query.filter_by(usr = usr).first() 
      if not usr or not password:
         flash('Please check your login details and try again.','error') 
      else:
         loginUsr = usr
         return redirect(url_for('mainpage'))
   return render_template("login.html")


@app.route('/delete/<int:id>')
def delete(id):
    task_to_delete = usrInfo.query.get_or_404(id)

    try:
        db.session.delete(task_to_delete)
        db.session.commit()
        return redirect('/admin')
    except:
        return 'There was a problem deleting that task'
 

if __name__ == '__main__':
   db.create_all()
   app.run(debug = True)