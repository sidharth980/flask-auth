from flask import Flask, request, flash, url_for, redirect, render_template, session, send_file
from flask import jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import re
import threading
import os
import numpy as np
from cv2 import VideoWriter, VideoWriter_fourcc
import cv2 as cv
import librosa
import ffmpeg

screen_width = 1280
screen_height = 720
FPS = 30
seconds = 10
no_of_bars = 120
left_space = 10
max_freq = 600
division_number = 1.1**65
t = threading.Thread()
rederdercomplete = False


class bar:
    def __init__(self, x, y, color, max_height = 100, min_height = 5, width = 10, height_decibel_ratio = 0.5):
        self.x, self.y = x, y
        self.color = color
        self.max_height, self.min_height = max_height, min_height
        self.width = width
        self.height = 0
        self.height_decibel_ratio = height_decibel_ratio
    # def update(self, decibel, dt):

    #     desired_height = -1*decibel*self.height_decibel_ratio + self.min_height
    #     speed = (desired_height - self.height)/0.05

    #     self.height += speed * dt
    #     self.height = clamp(self.min_height, self.max_height, self.height)


def main(filename):

    #Make sense of audio

    VidName = f'{filename}_TEMP.avi'
    
    no_of_circles = 4


    ts, sr = librosa.load(UPLOAD_FOLDER + filename)
    stft = np.abs(librosa.stft(ts, hop_length = 512, n_fft = 2048*4))
    spectrogram = librosa.amplitude_to_db(stft, ref=np.max)
    # frequencies = librosa.core.fft_frequencies(n_fft=2048*4)
    # freq_index_ratio = len(frequencies)/frequencies[-1]
    # max_freq = int(frequencies[-1])
    freq_step = int(max_freq/no_of_bars)
    music_duration = librosa.get_duration(ts, sr)
    print("duration", music_duration)
    seconds = int(music_duration)

    #Video things
    fourcc = VideoWriter_fourcc(*'MP42')
    video = VideoWriter(VidName, fourcc, float(FPS), (screen_width, screen_height))

    bar_width = int((screen_width-left_space)/no_of_bars)
    bar_max_height = int(screen_height*8/14)
    bars = []
    for number in range(no_of_bars):
        bars.append(bar(left_space*number, 20, (255,0,0), bar_max_height, 30, bar_width))
    

    for video_frame_no in range(FPS*seconds):
        time_frame = librosa.core.time_to_frames(video_frame_no/FPS, sr = sr)

        video_frame = np.empty((screen_height, screen_width, 3), np.uint8)
        # video_frame.fill(255)
        video_frame[:][:] = [52, 42, 37] # [37, 42, 52]
        




        bar_count = 0
        # for each in bars:

        #     barLeft = each.x + (bar_width)*bar_count + left_space
        #     barBottom = screen_height - each.min_height
        #     barRight = each.x + (bar_width)*(bar_count+1) + left_space
        #     barTop = screen_height - int(each.max_height*video_frame_no/(FPS*seconds))-each.min_height

        #     cv.rectangle(video_frame, (barLeft, barBottom), (barRight, barTop), (255, 0, 0), -1)
        #     bar_count += 1
        bar_heights = []
        # for i in range(10, max_freq, freq_step):
        #     x = np.mean(spectrogram[int(i*freq_index_ratio):int((i+freq_step)*freq_index_ratio), time_frame])  
        #     bar_heights.append(
        #         clamp(bar_max_height, bar_max_height*(1.1**(80+x))/1.1**65)
        #         )   
        len_of_freq = len(spectrogram.T[time_frame])
        no_of_els_to_add = (freq_step - len_of_freq % freq_step)
        x = np.pad(spectrogram.T[time_frame], (0, no_of_els_to_add))
        mean = np.mean(x.reshape(-1, freq_step), axis = 1)
        # bar_heights = np.power(1.1, np.mean(x.reshape(-1, freq_step), axis = 1)+ 80)*bar_max_height/1.1**65
        # bar_heights = (np.mean(x.reshape(-1, freq_step), axis = 1)+ 80)*bar_max_height/80*1.2
        bar_heights = bar_max_height*((np.power(1.1, (mean + 80))-1)/division_number)
        bar_heights[bar_heights > bar_max_height] = bar_max_height
        w = 3
        bar_heights_convolved = np.convolve(bar_heights, np.ones(w), 'valid') / w 
        

        circleradi = ((mean+80)/80*300).astype(int)
        # cv.circle(video_frame, (int(screen_width/2), int(screen_height/3)), 7, (30,174,152)[::-1], -1)
        cv.circle(video_frame, (int(screen_width/2), int(screen_height/3)), 50*int(circleradi[3]/300), (30,174,152)[::-1], -1)
        colors = [(8,217,214), (255,46,99), (234,234,234), (31,171,137)]
        for j in range(no_of_circles):
            cv.circle(video_frame, (int(640*(j)), int(screen_height/3)), circleradi[100*j+no_of_bars], colors[j][::-1], 5)
            

        no_of_available_divisions = len(bar_heights)
        for each in bars:

            barLeft = each.x + (bar_width)*bar_count + left_space
            barBottom = screen_height - each.min_height
            barRight = each.x + (bar_width)*(bar_count+1) + left_space
            if(bar_count < no_of_available_divisions):
                barTop = screen_height - int(bar_heights_convolved[bar_count]) -each.min_height
            else:
                barTop = screen_height -each.min_height

            cv.rectangle(video_frame, (barLeft, barBottom), (barRight, barTop), (bar_count/no_of_bars*244, (no_of_bars- bar_count)/no_of_bars*244, 234), -1)
            bar_count += 1

        video.write(video_frame)
    video.release()

    input_video = ffmpeg.input(VidName)
    input_audio = ffmpeg.input(UPLOAD_FOLDER + filename)
    try:
        ffmpeg.concat(input_video, input_audio, v=1, a=1).output( UPLOAD_FOLDER + f'{filename}_finished.mp4').run()
    except ffmpeg.Error as e:
        print(e.stderr)
    if os.path.exists(VidName):
        os.remove(VidName)
    global rederdercomplete
    rederdercomplete =  True
    print("Render Complete")


def clamp(max_value, value):

    if value > max_value:
        return max_value
    else:
        return value

# Functions


regex = '^(\w|\.|\_|\-)+[@](\w|\_|\-|\.)+[.]\w{2,3}$'


def check(email):

    if(re.search(regex, email)):
        return False

    else:
        return True


# Upload folder
UPLOAD_FOLDER = 'savedfile/'


# App and database
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///user.sqlite3'
app.config['SECRET_KEY'] = "random string"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_VIDEO_EXTENSIONS'] = ["MP3", "WAV", "AAC", "FLAC"]
app.config['MAX_IMAGE_FILESIZE'] = 5 * 1024 * 1024  # 5mb
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

# Routes


def allowed_image_filesize(filesize):
    if int(filesize) <= app.config['MAX_IMAGE_FILESIZE']:
        return True
    else:
        return False


def allowed_video(filename):

    if not "." in filename:
        return False

    ext = filename.rsplit(".", 1)[1]

    if ext.upper() in app.config['ALLOWED_VIDEO_EXTENSIONS']:
        return True
    else:
        return False


@app.route('/')
def mainred():
    return redirect("/main")

@app.route('/status')
def thread_status():
    global rederdercomplete
    """ Return the status of the worker thread """
    print()
    return jsonify(dict(status=('finished' if rederdercomplete else 'running')))


@app.route('/main', methods=['GET', 'POST'])
def mainpage():
    if request.method == 'POST':
        if request.files:
            file = request.files["image"]
            if file.filename == '':
                print('no filename')
                return redirect(request.url)
            else:
                file.seek(0, 2)
                file_length = file.tell()
                if not allowed_image_filesize(file_length):
                    flash("Please put file less than 5MB")
                    return redirect(request.url)
                file.seek(0)

                if not allowed_video(file.filename):
                    flash("This Video extension is not Allowed")
                    return redirect(request.url)

                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                print("saved file successfully")
                session["filename"] = filename
                return redirect(url_for("convirting"))
    if "user" in session:
        usrname = session["user"]
    else:
        usrname = None
    print(usrname)
    return render_template("main.html", name=usrname)


@app.route('/convert', methods=['GET', 'POST'])
def convirting():
    if request.method == "POST":
        filename = session["filename"]
        t = threading.Thread(target=main,args=(filename,))
        t.daemon = True
        t.start()
        return redirect(url_for("converting"))
    return render_template("convirting.html")

@app.route("/converting")
def converting():
    global rederdercomplete
    print(rederdercomplete)
    if rederdercomplete  and session["filename"] != None:
        rederdercomplete == False
        filename = session["filename"]
        session["filename"] = f'{filename}_finished.mp4'
        print(session["filename"])
        os.remove(UPLOAD_FOLDER+filename)
        return redirect("/download")
    return render_template("convert.html")


@app.route('/download')
def download():
    if "filename" in session:
        print(session["filename"])
        return render_template("download.html", filename=session["filename"])
    else:
        return redirect(url_for("mainpage"))
    return render_template("download.html", filename=None)


@app.route('/return-files/<filename>')
def return_files_tut(filename):
    file_path = UPLOAD_FOLDER + filename
    print(file_path)
    return send_file(file_path, as_attachment=True, attachment_filename='')


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


@app.route("/adminclear")
def adminclear():
    global rederdercomplete
    for f in os.listdir(UPLOAD_FOLDER):
        if f != "keep.txt":
            os.remove(os.path.join(UPLOAD_FOLDER, f))
    if "filename" in session:
        session.pop("filename", None)
    rederdercomplete = False
    return redirect(url_for("mainpage"))


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
