from flask import Flask, render_template
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user
from flask import g
from tfg.models import *
from humbledb import Mongo, Document, Index
from bson.objectid import ObjectId


UPLOAD_FOLDER = '/Users/dani/Documents/trabajo/tfg/static'


app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config["SECRET_KEY"] = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "/ident"

@login_manager.user_loader
def load_user(userid):
	print(userid)
	with Mongo:
		usuario = Usuario.find_one({Usuario._id : ObjectId(userid)})
	if usuario is None:
		return None
	return User(userid,usuario.nombre,usuario.role)

@app.before_request
def before_request():
    g.user = current_user


@app.errorhandler(404)
def page_not_found(error):
	return render_template("404.html")

from .views.admin import admin
from .views.user import user

app.register_blueprint(admin)
app.register_blueprint(user)