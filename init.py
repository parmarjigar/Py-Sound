from flask import Flask, render_template, flash, request, url_for, redirect, session
from wtforms import Form, BooleanField, TextField, PasswordField, validators
from wtforms.fields.html5 import EmailField
from MySQLdb import escape_string as escape
from dbconnect import connection
import os
from werkzeug.utils import secure_filename
import acoustid

UPLOAD_FOLDER = 'E:\pycloud\uploaded songs'
ALLOWED_EXTENSIONS = set(['ogg','mp3','flac','wma','m4a'])

app=Flask('__main__')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def homepage():
	return render_template("index.html")


@app.route('/login/', methods=["GET","POST"])
def login():
	error=''
	try:
		c,conn=connection()
		if request.method == "POST": 
			
			data= c.execute("SELECT * FROM entries WHERE username= (%s)",[escape(request.form['username'])])
			data =c.fetchone()[3]
			
			#if int(data) == 0:
			#	error = "Invalid Username/Password.  Try again!"
			
			if request.form['password']==data:
				session['logged_in'] = True
				session['username'] = request.form['username']
				#flash("You are now logged in!")
				return redirect(url_for('homepage'))
			else:
				error= "Invalid Username/Password.  Try again!"
				
		return render_template("login.html",error=error)
				
	except Exception as e:
		#flash (e)
		error= "Invalid Username/Password.  Try again!"
		return render_template("login.html", error=error)
		
@app.route('/logout/')
def logout():
	session.clear()
	#flash("You are logged out")
	return redirect(url_for('login'))	

@app.route('/signup/', methods=["GET","POST"])
def signup():
	try:
		if request.method == "POST":	
			name=request.form["name"]
			username =request.form["username"]
			email = request.form["email"]
			password =request.form["password"]
			c,conn=connection()
			u= c.execute("SELECT * FROM entries WHERE username = (%s)",[(escape(username))])
			
			if int(u)>0:
				flash("Username already taken, Choose another one")
				return render_template("signup.html", form=form)
			else:
				c.execute("INSERT INTO entries(name,username, password, email) VALUES (%s, %s, %s, %s)",(escape(name),escape(username),escape(password),escape(email)))
				
				conn.commit()
				flash("Thanks for Registering")
				c.close()
				conn.close()
				
				session['logged_in'] = True
				session['username'] = username
				
				return render_template("index.html")
		
		return render_template("signup.html")	
		
	except Exception as e:
		return(str(e)) 	
	
#####################################



def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
			print file.filename
			filename = secure_filename(file.filename)
			file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
			print UPLOAD_FOLDER + "\\" +filename
			songs=[]
			for score, recording_id, title, artist in acoustid.match("WwBfOuvUWZ",UPLOAD_FOLDER+"\\"+filename):
				songs.append((title + "-" +artist).title()+"." +filename.rsplit('.', 1)[1].lower())
			songs=list(set(songs))
			print session['username']
			c,conn=connection()
			try:
				os.rename(UPLOAD_FOLDER+"\\"+filename, UPLOAD_FOLDER+"\\"+songs[0])
				print "song renamed"
				uid=c.execute("select uid from entries where username=(%s)",[session['username']])
				uid=c.fetchone()[0]
				print "uid selected"
				u=c.execute("INSERT INTO UPLOADED_SONGS(sname) VALUES (%s)",[songs[0]])
				print "song inserted in db"
				sid=c.execute("select sid from UPLOADED_SONGS where sname=(%s)",[songs[0]])
				print "sid selected"
				sid=c.fetchone()[0]	
				u=c.execute("INSERT INTO UPLOADED_BY(uid,sid) VALUES (%s,%s)",[uid,sid])
				print "uploaded_by done"
				conn.commit()
			except:
				os.remove(UPLOAD_FOLDER+"\\"+filename)
				uid=c.execute("select uid from entries where username=(%s)",[session['username']])
				uid=c.fetchone()[0]
				print "uid selected"
				sid=c.execute("select sid from UPLOADED_SONGS where sname=(%s)",[songs[0]])
				print "sid selected"
				sid=c.fetchone()[0]	
				u=c.execute("INSERT INTO UPLOADED_BY(uid,sid) VALUES (%s,%s)",[uid,sid])
				print "uploaded_by done"
				conn.commit()
			
			return redirect(url_for('homepage'))
	else:		
		return redirect(url_for('homepage'))
	
if __name__== "__main__":
	app.secret_key= 'super secret_key'
	app.run(debug=True)	
