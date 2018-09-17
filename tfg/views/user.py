# -*- coding: utf-8 -*-
from flask import Blueprint,Flask, render_template, make_response, current_app, redirect, url_for, jsonify, request
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user
from flask import request
from random import randint
from pymongo import MongoClient
from time import time
from humbledb import Mongo, Document, Index
from cPickle import dump, dumps, load, loads
from flask import Response
from functools import wraps
from flask import g
from flask import flash
import humbledb
import io
import datetime
from humbledb.array import Array
from ..models import *


import os
from flask import Flask, request, redirect, url_for
from werkzeug.utils import secure_filename
from flask import send_from_directory, send_file
from bson.objectid import ObjectId
from cStringIO import StringIO
from bson.binary import Binary

user = Blueprint('user', __name__)

ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

def required_roles(*roles):
   def wrapper(f):
      @wraps(f)
      def wrapped(*args, **kwargs):
         if get_current_user_role() not in roles:
            flash('Authentication error, please check your details and try again','error')
            return redirect(url_for('identificacion'))
         return f(*args, **kwargs)
      return wrapped
   return wrapper

def get_current_user_role():
   return g.user.role

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@user.route('/', methods = ["GET"])
def hello_world():
	if request.method == 'GET':
		values = {}
		return render_template("user/welcome.html", vs = values)



@user.route('/ident', methods = ["GET"])
def identificacion():
	if request.method == 'GET':
		values = {}
		return render_template("user/ident.html", vs = values)

@user.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('user.identificacion'))



@user.route("/protected/",methods=["GET"])
@login_required
def protected():
    return Response(response="Hello Protected World!", status=200)


@user.route('/registro', methods = ["GET","POST"])
def registro():
	if request.method == 'GET':
		values = []
		with Mongo:
			facultades = Facultad.find().sort("nombre")
		for facultad in facultades:
			values.append(facultad.nombre)
		return render_template("user/inicio_registro.html", vs = values)

	if request.method == 'POST':
		values = []
		nombre = request.form['facultad']
		with Mongo:
			facultad = Facultad.find_one({Facultad.nombre: nombre })
			id_facultad = facultad._id
			titulaciones = Titulacion.find({Titulacion.id_facultad : id_facultad}).sort("nombre")
		for titulacion in titulaciones:
			values.append(titulacion.nombre)
		return render_template("user/registro.html", vs = values, facultad = nombre , error = False )

@user.route('/registro/fin', methods = ["POST"])
def finalizar_registro():
	values = []
	nombre = request.form['facultad']
	file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
   	if file.filename == '':
   		flash('No selected file')
   		return redirect(request.url)
   	if file and allowed_file(file.filename):
   		filename = secure_filename(file.filename)
	usuario = Usuario()
	usuario.crearUsuario(filename,request.form['nombre'],request.form['password'],request.form['email'],request.form['facultad'],request.form['titulacion'])
	file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
	with Mongo:
		facultad = Facultad.find_one({Facultad.nombre: nombre })
		id_facultad = facultad._id
		titulaciones = Titulacion.find({Titulacion.id_facultad : id_facultad})
		for titulacion in titulaciones:
			values.append(titulacion.nombre)

	with Mongo:
		user = Usuario.find_one({Usuario.nombre : usuario.nombre })
		t = Titulacion.find_one({Titulacion.nombre : request.form['titulacion']})
		cursos = Curso.find({Curso.id_titulacion:t._id})
		resultados = Archivo.find({Archivo.id_titulacion: t._id}).sort("fecha",-1).limit(3)
		if user is None:
			u = Usuario.insert(usuario)
			for i in range(9,21):
				hora = Horario()
				hora.hora = i
				hora.id_usuario= u
				hora.l=""
				hora.m=""
				hora.x=""
				hora.j = ""
				hora.v=""
				Horario.insert(hora)
		else:
			return render_template("user/registro.html", vs = values, facultad = nombre, error = True )
	user = User(str(usuario._id), usuario.nombre,usuario.role)
	login_user(user)
	return render_template("user/inicio.html", usuario = usuario , cursos = cursos , busqueda = False, resultados = resultados)

@user.route('/comp_ident', methods = ["POST"])
def comprobar_identidad():
    if request.method == 'POST':
    	logout_user()
        values = {}
        values["nombre"] = request.form['nombre']
        values["password"] = request.form['password']
        d = datetime.date.today()
        date = d.isoformat()
        with Mongo:
			usuario = Usuario.find_one({Usuario.nombre : values["nombre"]})
			if usuario is None:
				return render_template("user/ident_fallida.html" , motivo = "Nombre de Usuario")
			else:
				if values["password"] == usuario.password and usuario.role == "Admin":
					user = User(str(usuario._id),values["nombre"],usuario.role)
					login_user(user)
					return redirect(url_for('admin.admin_inicio',nombre = usuario.nombre))
				elif values["password"] == usuario.password and usuario.role == "Usuario" and usuario.activo_desde<=date:
					Usuario.update({Usuario._id : usuario._id },{'$set': {Usuario.activo: True}})
					t = Titulacion.find_one({Titulacion.nombre : usuario.titulacion})
					cursos = Curso.find({Curso.id_titulacion:t._id})
					user = User( str(usuario._id),values["nombre"],usuario.role)
					login_user(user)
					resultados = Archivo.find({Archivo.id_titulacion: t._id}).sort("_id",-1).limit(3)
					return render_template("user/inicio.html", usuario = usuario, cursos = cursos , busqueda = False, resultados = resultados)
				else:
					return render_template("user/ident_fallida.html", motivo='Usuario bloqueado hasta el ' + usuario.activo_desde)

###################################################################################################################
#                                                                                                                 #
#                          VIEWS PARTE DEL USUARIO INICIO                                                         #
#                                                                                                                 #
###################################################################################################################

@user.route('/usuario/inicio/volver/<string:nombre>', methods = ["GET","POST"])
@login_required
@required_roles('Usuario')
def usuario_volver_inicio(nombre):
	with Mongo:
		u  = Usuario.find_one({Usuario.nombre : nombre})
		f = Facultad.find_one({Facultad.nombre : u.facultad})
		t = Titulacion.find_one({Titulacion.nombre : u.titulacion},{Titulacion.id_facultad: f._id})
		cursos = Curso.find({Curso.id_titulacion: t._id})
		resultados = Archivo.find({Archivo.id_titulacion: t._id}).sort("_id",-1).limit(3)

	return render_template("user/inicio.html", usuario = u, cursos = cursos ,resultados= resultados)




@user.route('/usuario/inicio/curso/_search', methods = ["GET"])
@login_required
@required_roles('Usuario')
def usuario_busqueda_curso():
    if request.method == 'GET':
        resultados = []
        curso = request.args.get('busqueda')
        nombre = request.args.get('name')
        with Mongo:
        	asignaturas = Asignatura.find({Asignatura.id_curso: ObjectId(curso)}).sort("nombre")
        textosalida = ""
        for a in asignaturas:
        	textosalida += '''<a href= /usuario/ver_asignatura/''' +str(a._id)+'''/''' + (nombre).encode('utf-8') + '''  class="button" > '''+ str(a.num_ficheros)+''' &nbsp;&nbsp;<i class="fa fa-file-o" aria-hidden="true"></i>&nbsp;&nbsp;&nbsp;&nbsp;''' +  (a.nombre).encode('utf-8') + ''' </a> '''

        return jsonify(result=textosalida)

@user.route('/usuario/inicio/nombre/_search', methods = ["GET"])
@login_required
@required_roles('Usuario')
def usuario_busqueda_nombre():
    if request.method == 'GET':
        resultados = []
        a = []
        asignatura = str(request.args.get('busqueda')).capitalize();
        nombre = request.args.get('name')
        with Mongo:
        	u = Usuario.find_one({Usuario.nombre : nombre })
        	t = Titulacion.find_one({Titulacion.nombre : u.titulacion })
        	id_titulacion = t._id
        	c = Curso.find({Curso.id_titulacion : id_titulacion })
        	for i in c:
        		print i._id
        		a.append(i._id)
        		asignaturas = Asignatura.find({Asignatura.nombre: {'$regex': asignatura}}).sort("nombre")
        for asig in asignaturas:
        	for iden in a:
        		if asig.id_curso == iden:
        			resultados.append(asig)
        textosalida = ""
        for a in resultados:
        	textosalida += '''<a href= /usuario/ver_asignatura/''' +str(a._id)+'''/''' + (nombre).encode('utf-8') + '''  class="button" > '''+ str(a.num_ficheros)+''' &nbsp;&nbsp;<i class="fa fa-file-o" aria-hidden="true"></i>&nbsp;&nbsp;&nbsp;&nbsp;''' +  (a.nombre).encode('utf-8') + ''' </a> '''

        return jsonify(result=textosalida)


###################################################################################################################
#                                                                                                                 #
#                          VIEWS PARTE DEL USUARIO ASIGNATURAS Y ARCHIVOS                                         #
#                                                                                                                 #
###################################################################################################################


@user.route('/usuario/ver_asignatura/<asignatura>/<string:usuario>',methods=['GET', 'POST'])
@login_required
@required_roles('Usuario')
def ver_asignatura(asignatura, usuario):
	with Mongo:
		a = Asignatura.find_one({Asignatura._id: ObjectId(asignatura)})
		u = Usuario.find_one({Usuario.nombre : usuario })
		archivos = Archivo.find({Archivo.id_asignatura : a._id })

	resultados= []
	tipos = ["Apuntes","Examenes","Ejercicios"]
	for archivo in archivos:
		if archivo.autorizado == True:
			resultados.append(archivo)

	return render_template("user/ver_asignatura.html", asignatura = a, resultados = resultados, usuario = u, tipos = tipos)


@user.route('/usuario/ver_archivo/<string:archivo>/<string:usuario>',methods=['GET', 'POST'])
@login_required
@required_roles('Usuario')
def ver_archivo(archivo, usuario):
	with Mongo:
		archivo = Archivo.find_one({Archivo.nombre : archivo })
		autor = Usuario.find_one({Usuario.nombre: archivo.autor})
		comentarios = Comentario.find({Comentario.id_archivo : archivo._id })
		u = Usuario.find_one({Usuario.nombre : usuario })
		comments = Comments(archivo._id)
		for comentario in comentarios:
			comments.append(comentario)

		first_page = []
		pagina = 0
		n = 0
		if comments.length() > 0:
			n = comments.pages() - 1 # Return the current number of pages
			print(comments.length()) - 1  # Return the current number of entries
			first_page = comments[0]
			pagina = 0

		comments.clear()  # Remove all entries


	return render_template("user/ver_archivo.html",  autor=autor ,archivo = archivo,  usuario = u, comentarios = first_page, pagina = pagina, paginas = n)

@user.route('/usuario/ver_archivo2/<string:archivo>/<string:usuario>/<int:pagina>',methods=['GET', 'POST'])
@login_required
@required_roles('Usuario')
def ver_archivo2(archivo, usuario, pagina):
	with Mongo:

		archivo = Archivo.find_one({Archivo.nombre : archivo })
		autor = Usuario.find_one({Usuario.nombre: archivo.autor})
		comentarios = Comentario.find({Comentario.id_archivo : archivo._id })
		u = Usuario.find_one({Usuario.nombre : usuario })
		comments = Comments(archivo._id)
		for comentario in comentarios:
			comments.append(comentario)


		n = comments.pages() - 1   # Return the current number of pages
		print(n)
		#print(comments.length())  # Return the current number of entries
		pagina = pagina + 1
		print(pagina)
		first_page = comments[pagina]

		comments.clear()  # Remove all entries


	return render_template("user/ver_archivo.html",  autor=autor ,archivo = archivo,  usuario = u, comentarios = first_page , pagina = pagina, paginas = n)


@user.route('/usuario/puntuar_archivo/<int:voto>/<string:archivo>/<string:usuario>',methods=['GET', 'POST'])
@login_required
@required_roles('Usuario')
def puntuar_archivo(voto,archivo, usuario):
	with Mongo:
		a = Archivo.find_one({Archivo.nombre : archivo })
		autor = Usuario.find_one({Usuario.nombre: a.autor})
		votos = a.num_votos + 1
		valoraciones = a.sum_valor + voto
		valoracion = round(float(float(valoraciones) / float(votos)),1)
		ent = int(valoracion)
		dec = abs(valoracion) - abs(int(valoracion))
		Archivo.update({Archivo._id: ObjectId(a._id)},{'$set': {Archivo.sum_valor:  valoraciones }})
		Archivo.update({Archivo._id: ObjectId(a._id)},{'$set': {Archivo.valoracion:  valoracion }})
		Archivo.update({Archivo._id: ObjectId(a._id)},{'$set': {Archivo.valor_entero:  ent }})
		Archivo.update({Archivo._id: ObjectId(a._id)},{'$set': {Archivo.num_votos:  votos }})
		Archivo.update({Archivo._id: ObjectId(a._id)},{'$set': {Archivo.valor_dec:  dec }})

		#Desde aqui hasta el final de puntuar-archivo se elimina y se redicrecciona a ver_archivo con url
		comentarios = Comentario.find({Comentario.id_archivo : a._id })
		comments = Comments(a._id)
		for comentario in comentarios:
			comments.append(comentario)

		first_page = []
		pagina = 0
		n = 0
		if comments.length() > 0:
			n = comments.pages()  # Return the current number of pages
			print(comments.length()) - 1  # Return the current number of entries
			first_page = comments[0]
			pagina = 0

		comments.clear()  # Remove all entries
		archivo = Archivo.find_one({Archivo.nombre : archivo })
		u = Usuario.find_one({Usuario.nombre : usuario })

	return render_template("user/ver_archivo.html",  autor=autor ,  archivo = archivo,  usuario = u, comentarios = first_page , pagina = pagina, paginas = n)


@user.route('/usuario/comentar_archivo/<string:archivo>/<string:usuario>',methods=['GET', 'POST'])
@login_required
@required_roles('Usuario')
def comment_file(archivo, usuario):
	with Mongo:
		#Aqui habria que comprobar que la asignatura no solo tiene el nombre adecuado si no que la id_curso
		#es la correspondiente a la titulacion asociada.

		archivo = Archivo.find_one({Archivo.nombre : archivo })
		u = Usuario.find_one({Usuario.nombre : usuario })


	return render_template("user/crear_comentario.html", archivo = archivo,  usuario = u)



@user.route('/usuario/finalizar_comentario',methods=['GET', 'POST'])
@login_required
@required_roles('Usuario')
def end_comment():
	if request.method == 'POST':
		comentario = Comentario()
		comentario.autor = request.form['nombre']
		today = datetime.datetime.now()
		comentario.fecha = today.ctime()
		print(today.ctime())
		comentario.body = request.form['body']
		comentario.titulo = request.form['titulo']
		comentario.likes = 0
		comentario.unlike = 0
		comentario.denuncia = False
		with Mongo:
		#Aqui habria que comprobar que la asignatura no solo tiene el nombre adecuado si no que la id_curso
		#es la correspondiente a la titulacion asociada.
			usuario = Usuario.find_one({Usuario.nombre : request.form['nombre'] })
			n = usuario.comentarios + 1
			Usuario.update({Usuario.nombre : request.form['nombre']},{'$set': {Usuario.comentarios:  n }})
			autor = Usuario.find_one({Usuario.nombre:  request.form['nombre']})
			comentario.autor_avatar = autor.foto
			archivo = Archivo.find_one({Archivo.nombre : request.form['archivo']})
			n = archivo.num_comen + 1
			Archivo.update({Archivo._id: archivo._id},{'$set': {Archivo.num_comen:  n }})
			comentario.id_archivo = archivo._id
			Comentario.insert(comentario)
			comentarios = Comentario.find({Comentario.id_archivo : archivo._id })
			comments = Comments(archivo._id)
			for comentario in comentarios:
				comments.append(comentario)

			first_page = []
			pagina = 0
			n = 0
			if comments.length() > 0:
				n = comments.pages()  # Return the current number of pages
				print(comments.length()) - 1  # Return the current number of entries
				first_page = comments[0]
				pagina = 0

			comments.clear()  # Remove all entries
			u = Usuario.find_one({Usuario.nombre : request.form['nombre'] })


	return redirect(url_for('.ver_archivo', _anchor='exactlocation',  archivo=archivo.nombre , usuario = usuario.nombre))


@user.route('/usuario/valorar_comentario/<int:valor>/<comentario>/<string:archivo>/<string:usuario>' ,methods=['GET', 'POST'])
@login_required
@required_roles('Usuario')
def value_comment(valor,comentario,archivo,usuario):

	if valor==1:
		with Mongo:
			c = Comentario.find_one({Comentario._id : ObjectId(comentario)})
			votos = c.votos
			if votos.has_key(usuario):
				if votos[usuario] == 0:
					unlikes = int(c.unlike) - 1
					likes = int(c.likes) + 1
					votos[usuario] = 1
					Comentario.update({Comentario._id: ObjectId(comentario)},{'$set': {Comentario.likes:  likes, Comentario.unlike:  unlikes, Comentario.votos:  votos }})
			else:
				likes = int(c.likes) + 1
				votos[usuario] = 1
				Comentario.update({Comentario._id: ObjectId(comentario)},{'$set': {Comentario.likes:  likes, Comentario.votos:  votos }})

	else:
		with Mongo:
			c = Comentario.find_one({Post._id : ObjectId(comentario)})
			votos = c.votos
			if votos.has_key(usuario):
				if votos[usuario] == 1:
					unlikes = int(c.unlike) + 1
					likes = int(c.likes) - 1
					votos[usuario] = 0
					Comentario.update({Comentario._id: ObjectId(comentario)},{'$set': {Comentario.likes:  likes, Comentario.unlike:  unlikes, Comentario.votos:  votos }})
			else:
				unlikes = int(c.unlike) + 1
				votos[usuario] = 0
				Comentario.update({Comentario._id: ObjectId(comentario)},{'$set': {Comentario.unlike:  unlikes, Comentario.votos:  votos }})

	return redirect(url_for('.ver_archivo', _anchor='exactlocation',  archivo=archivo , usuario = usuario))

@user.route('/usuario/comentarios/denuncias/<comentario>/<string:archivo>/<string:usuario>', methods = ["GET"])
@login_required
@required_roles('Usuario')
def usuario_comentarios_denuncias(comentario,archivo,usuario):
	with Mongo:
		Comentario.update({Comentario._id: ObjectId(comentario)},{'$set': {Comentario.denuncia:  True }})

	return redirect(url_for('.ver_archivo',  archivo=archivo , usuario = usuario))



@user.route('/usuario/ver_asignatura/guardar_fichero', methods=['POST'])
@login_required
@required_roles('Usuario')
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        asignatura = request.form['asignatura']
        usuario = request.form['nombre']
        archivos = []
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            content = StringIO(file.read())
            filebody = Binary(content.getvalue())
            with Mongo:
            	u = Usuario.find_one({Usuario.nombre: usuario})
            	num= u.archivos_subidos + 1

            	a = Asignatura.find_one({Asignatura.nombre : asignatura})
            	curso = Curso.find_one({Curso._id : a.id_curso})
            	id_asignatura = a._id
            	archivo = Archivo()
            	archivo.nombre = filename
            	archivo.autor = request.form['nombre']
            	archivo.tipo = request.form['tipo']
            	archivo.fichero = filebody
            	archivo.valoracion = 0
            	archivo.id_asignatura = id_asignatura
            	archivo.autorizado = False
            	archivo.num_descargas = 0
            	archivo.num_votos = 0
            	archivo.suma_valor = 0
            	archivo.valor_entero = 0
            	archivo.valor_dec = 0
            	archivo.num_comen = 0
            	archivo.asignatura = a.nombre
            	archivo.id_titulacion = curso.id_titulacion
            	dia = datetime.date.today()
            	d = dia.strftime("%d/%m/%y")
            	f = dia.strftime("%y/%m/%d")
            	archivo.fecha = d
            	archivo.formato = f
            	numero = a.num_ficheros + 1



            	for i in range(len(a.nombre_ficheros)):
            		archivos.append(a.nombre_ficheros[i])

            	arc = Archivo.find_one({Archivo.nombre : filename})

            	archivos.append(filename)
            	if arc == None:
            		Archivo.insert(archivo)
            		Asignatura.update({Asignatura._id : id_asignatura },{'$set': {Asignatura.num_ficheros: numero}})
            		Asignatura.update({Asignatura._id : id_asignatura },{'$set': {Asignatura.nombre_ficheros: archivos}})
            		Usuario.update({Usuario._id : u._id },{'$set': {Usuario.archivos_subidos: num}})
            # file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('.ver_asignatura',
                                    asignatura= a._id , usuario =usuario ))






#Descargar archivo por el nombre desde la pagina de cada archivo
@user.route('/usuario/upload/<filename>/<string:usuario>',methods=['GET', 'POST'])
@login_required
@required_roles('Usuario')
def uploaded_file(filename, usuario):
	with Mongo:
		usuario = Usuario.find_one({Usuario.nombre : usuario})
		descargas = usuario.descargas + 1
		Usuario.update({Usuario._id : usuario._id },{'$set': {Usuario.descargas: descargas}})
		archivo = Archivo.find_one({Archivo.nombre : filename})
		num = int(archivo.num_descargas)+1
		Archivo.update({Archivo.nombre : filename },{'$set': {Archivo.num_descargas: num}})
		return send_file(io.BytesIO(archivo.fichero),
                     attachment_filename=filename,as_attachment=True)



###################################################################################################################
#                                                                                                                 #
#                          VIEWS PARTE DEL USUARIO PERFIL                                                         #
#                                                                                                                 #
###################################################################################################################

@user.route('/usuario/perfil/<string:nombre>',methods=['GET', 'POST'])
@login_required
@required_roles('Usuario')
def perfil(nombre):
	with Mongo:
		u  = Usuario.find_one({Usuario.nombre : nombre})
		facultad = Facultad.find_one({Facultad.nombre : u.facultad})
		titul = Titulacion.find({Titulacion.id_facultad : facultad._id}).sort("nombre")
		facul = Facultad.find()

	return render_template("user/perfil.html", usuario = u, titul = titul, facul = facul )

@user.route('/usuario/perfil/cargar_imagen', methods=['POST'])
@login_required
@required_roles('Usuario')
def upload_image():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        usuario = request.form['nombre']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            with Mongo:
            	Usuario.update({Usuario.nombre : usuario },{'$set': {Usuario.foto: filename}})

            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('.perfil', nombre=usuario))



@user.route('/usuario/perfil/_search')
@login_required
@required_roles('Usuario')
def search():
	with Mongo:
		facultad = Facultad.find_one({Facultad.nombre : request.args.get('busqueda')})
		titul = Titulacion.find({Titulacion.id_facultad : facultad._id}).sort("nombre")
	textosalida = ""
	for t in titul:
		textosalida += "<option value= "+ t.nombre +" >"+t.nombre+"</option>"
	return jsonify(result=textosalida)

@user.route('/usuario/perfil/cambiar_facultad')
@login_required
@required_roles('Usuario')
def perfil_nueva_facul():
	nombre = request.args.get('nombre')
	with Mongo:
		Usuario.update({Usuario.nombre : request.args.get('nombre') },{'$set': {Usuario.facultad: request.args.get('nueva_facultad')}})
		Usuario.update({Usuario.nombre : request.args.get('nombre') },{'$set': {Usuario.titulacion: request.args.get('nueva_titulacion')}})

	textosalida = ''''''
	return jsonify(result=textosalida)

@user.route('/usuario/perfil/cambiar_titulacion')
@login_required
@required_roles('Usuario')
def perfil_nueva_titul():
	nombre = request.args.get('nombre')
	with Mongo:
		Usuario.update({Usuario.nombre : request.args.get('nombre') },{'$set': {Usuario.titulacion: request.args.get('nueva_titulacion')}})

	textosalida = ''''''
	return jsonify(result=textosalida)


@user.route('/usuario/perfil/cambiar_mail')
@login_required
@required_roles('Usuario')
def perfil_nuevo_mail():
	nombre = request.args.get('nombre')
	with Mongo:
		Usuario.update({Usuario.nombre : nombre },{'$set': {Usuario.email: request.args.get('nuevo_mail')}})
	textosalida = '''<b>Email >> </b>'''+request.args.get('nuevo_mail')+'''<button id="usuario_email"   class="button" > Editar </button>'''
	return jsonify(result=textosalida)

@user.route('/usuario/perfil/cambiar_password')
@login_required
@required_roles('Usuario')
def perfil_nuevo_pass():
	nombre = request.args.get('nombre')
	with Mongo:
		Usuario.update({Usuario.nombre : request.args.get('nombre') },{'$set': {Usuario.password: request.args.get('nuevo_pass')}})

	textosalida = '''<b>Password >> </b>'''+request.args.get('nuevo_pass')+'''<button id="usuario_password"   class="button" > Editar </button>'''
	return jsonify(result=textosalida)

@user.route('/usuario/perfil/finalizar_mensaje')
@login_required
@required_roles('Usuario')
def escribir_mensaje_perfil():

	autor = request.args.get('autor')
	destinatario = request.args.get('destino')
	asunto = request.args.get('asunto')
	body = request.args.get('body')
	with Mongo:
		mensaje = Mensaje()
		mensaje2 = Mensaje()
		compa  = Usuario.find_one({Usuario.nombre : destinatario})
		Usuario.update({Usuario._id: compa._id},{'$set': {Usuario.no_leidos: compa.no_leidos + 1 }})
		autor = Usuario.find_one({Usuario.nombre : autor})
		mensaje.asunto = asunto
		mensaje2.asunto = asunto
		mensaje.id_usuario = compa._id
		mensaje2.id_usuario = compa._id
		mensaje.autor = autor.nombre
		mensaje2.autor = autor.nombre
		mensaje.autor_avatar = autor.foto
		mensaje2.autor_avatar = autor.foto
		mensaje.body = body
		mensaje2.body = body
		mensaje.denuncia = False
		mensaje2.denuncia = False
		d = datetime.date.today()
		d = d.strftime("%d/%m/%y")
		mensaje.fecha = d
		mensaje2.fecha = d
		mensaje.estado = "No Leídos"
		Mensaje.insert(mensaje)
		mensaje2.estado = "Enviados"
		Mensaje.insert(mensaje2)

	return jsonify(result="textosalida")

@user.route('/usuario/perfil/mensajes/denuncias', methods = ["GET"])
@login_required
@required_roles('Usuario')
def usuario_perfil_denuncias():
	print("Aqui estoy")
	mensaje = request.args.get('busqueda')
	with Mongo:
		Mensaje.update({Mensaje._id: ObjectId(mensaje)},{'$set': {Mensaje.denuncia: True }})

	return jsonify(result="textosalida")

@user.route('/usuario/perfil/mensajes/obtener')
@login_required
@required_roles('Usuario')
def perfil_mensajes():
	estado = request.args.get('busqueda')
	nombre = request.args.get('nombre')
	with Mongo:
		u = Usuario.find_one({Usuario.nombre: nombre})
		if estado == "Enviados":
			mensajes = Mensaje.find({Mensaje.autor : nombre, Mensaje.estado :estado})
		else:
			mensajes = Mensaje.find({Mensaje.id_usuario : u._id, Mensaje.estado :estado})
	textosalida = ""
	for b in mensajes:
		if b.estado == "Enviados":
			with Mongo:
				u = Usuario.find_one({Usuario._id : b.id_usuario})
			textosalida = '''<div class="correo"><a class="link_correo" href=/usuario/perfil/mensajes/leer/'''+nombre+'''/'''+str(b._id)+'''>'''+b.asunto+'''&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'''+u.nombre+'''&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'''+b.fecha+'''</a></div>'''
		else:
			textosalida = '''<div class="correo"><a class="link_correo" href=/usuario/perfil/mensajes/leer/'''+nombre+'''/'''+str(b._id)+'''>'''+b.asunto+'''&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'''+b.autor+'''&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'''+b.fecha+'''</a></div>'''
	return jsonify(result=textosalida)

@user.route('/usuario/perfil/buzon/<string:nombre>',methods=['GET', 'POST'])
@login_required
@required_roles('Usuario')
def usuario_mensajes(nombre):
	with Mongo:
		u  = Usuario.find_one({Usuario.nombre : nombre})
		mensajes = Mensaje.find({Mensaje.id_usuario : u._id, Mensaje.estado :"No Leídos"})

	return render_template("user/mensajes.html", usuario = u, buzon=mensajes)

@user.route('/usuario/perfil/mensajes/leer/<string:nombre>/<string:mensaje>',methods=['GET', 'POST'])
@login_required
@required_roles('Usuario')
def usuario_leer_mensajes(nombre, mensaje):
	destino = {}
	with Mongo:
		u  = Usuario.find_one({Usuario.nombre : nombre})
		m = Mensaje.find_one({Mensaje._id: ObjectId(mensaje)})
		if m.estado.encode('utf-8') == "No Leídos":
			enlace = "#no_leidos"
			Mensaje.update({Mensaje._id:ObjectId(mensaje)},{'$set': { Mensaje.estado: "Leídos"}})
			Usuario.update({Usuario._id:u._id},{'$set': { Usuario.no_leidos: u.no_leidos - 1 }})
		elif m.estado.encode('utf-8') == "Leídos":
			enlace = "#leidos"
		else:
			enlace = "#enviados"
			destino = Usuario.find_one({Usuario._id : ObjectId(m.id_usuario)})
	return render_template("user/ver_mensaje.html", usuario = u, mensaje=m, enlace=enlace, destino = destino)

###################################################################################################################
#                                                                                                                 #
#                          VIEWS PARTE DE ANOTACIONES                                                             #
#                                                                                                                 #
###################################################################################################################




@user.route('/usuario/anotaciones/<string:nombre>', methods = ["GET","POST"])
@login_required
@required_roles('Usuario')
def usuario_anotaciones(nombre):
	with Mongo:
		u  = Usuario.find_one({Usuario.nombre : nombre})
		notas = Notas.find({Notas.autor : nombre}).sort("formato")


	busqueda = False
	filtro = ""


	return render_template("user/anotaciones.html", usuario = u,  notas = notas, busqueda = busqueda, filtro = filtro)

@user.route('/usuario/anotaciones/filtro/<string:nombre>/<string:filtro>', methods = ["GET","POST"])
@login_required
@required_roles('Usuario')
def usuario_anotaciones_filtro(nombre, filtro):
	with Mongo:
		u  = Usuario.find_one({Usuario.nombre : nombre})
		notas = Notas.find({Notas.autor : nombre}).sort("formato")


	busqueda = True


	return render_template("user/anotaciones.html", usuario = u,  notas = notas, busqueda = busqueda, filtro = filtro)

@user.route('/usuario/anotaciones/crear_nota/<string:nombre>', methods = ["GET","POST"])
@login_required
@required_roles('Usuario')
def crear_nota(nombre):


	if request.method == 'GET':
		with Mongo:

			u  = Usuario.find_one({Usuario.nombre : nombre})
			f = Facultad.find_one({Facultad.nombre : u.facultad})
			for titulacion in f.titulaciones:
				if titulacion == u.titulacion:
					t = Titulacion.find_one({Titulacion.nombre : titulacion})

	cursos = t.num_cursos

	return render_template("user/crear_nota.html", usuario = u)


@user.route('/usuario/anotaciones/finalizar_nota', methods = ["GET","POST"])
@login_required
@required_roles('Usuario')
def finalizar_nota():

	if request.method == 'POST':
		with Mongo:
			u  = Usuario.find_one({Usuario.nombre : request.form['nombre']})
			notas = Notas.find({Notas.autor : request.form['nombre']}).sort("formato")
			f = Facultad.find_one({Facultad.nombre : u.facultad})
			for titulacion in f.titulaciones:
				if titulacion == u.titulacion:
					t = Titulacion.find_one({Titulacion.nombre : titulacion})
			nota = Notas()
			nota.asunto = request.form['asunto']
			nota.titulo = request.form['titulo']
			nota.descripcion = request.form['descripcion']
			nota.fecha = request.form['datepicker']
			fecha = request.form['datepicker']
			day = fecha[0:2]
			moth = fecha[3:5]
			year = fecha[6:10]
			formato = year + "/" + moth + "/" + day
			nota.formato = formato
			nota.autor = request.form['nombre']
			Notas.insert(nota)

		cursos = t.num_cursos

		return render_template("user/anotaciones.html", usuario = u, cursos = cursos , notas = notas)



@user.route('/usuario/anotaciones/ver_nota/<nombre>/<nota>',methods=['GET', 'POST'])
@login_required
@required_roles('Usuario')
def ver_nota(nombre, nota):
	with Mongo:
		nota = Notas.find_one({Notas._id: ObjectId(nota)})
		u = Usuario.find_one({Usuario.nombre : nombre })

	return render_template("user/ver_nota.html", usuario = u, nota = nota)


@user.route('/usuario/anotaciones/borrar_nota/<nombre>/<nota>',methods=['GET', 'POST'])
@login_required
@required_roles('Usuario')
def borrar_nota(nombre, nota):
	with Mongo:
		Notas.delete_one({Notas._id: ObjectId(nota)})
		u  = Usuario.find_one({Usuario.nombre : nombre})
		notas = Notas.find({Notas.autor : nombre}).sort("formato")
		f = Facultad.find_one({Facultad.nombre : u.facultad})
		for titulacion in f.titulaciones:
			if titulacion == u.titulacion:
				t = Titulacion.find_one({Titulacion.nombre : titulacion})


		cursos = t.num_cursos


	return render_template("user/anotaciones.html", usuario = u, cursos = cursos , notas = notas)

###################################################################################################################
#                                                                                                                 #
#                          VIEWS PARTE DE COMUNIDAD                                                               #
#                                                                                                                 #
###################################################################################################################

@user.route('/usuario/comunidad/<string:nombre>', methods = ["GET","POST"])
@login_required
@required_roles('Usuario')
def usuario_comunidad(nombre):
	with Mongo:
		u  = Usuario.find_one({Usuario.nombre : nombre})
		f = Facultad.find_one({Facultad.nombre : u.facultad})
		top_subidas = Usuario.find({Usuario.titulacion: u.titulacion}).sort("archivos_subidos",-1).limit(5)
		top_descargas = Usuario.find({Usuario.titulacion: u.titulacion}).sort("descargas",-1).limit(5)
		compa = Usuario.find({Usuario.titulacion: u.titulacion})
		for titulacion in f.titulaciones:
			if titulacion == u.titulacion:
				t = Titulacion.find_one({Titulacion.nombre : titulacion})
		posts = Post.find({Post.id_titulacion: t._id}).sort("_id",-1)

	return render_template("user/comunidad.html", usuario = u,  posts = posts, titulacion = t._id, top_subidas= top_subidas , compa=compa, top_descargas= top_descargas)

@user.route('/usuario/posts/filtrar', methods = ["GET"])
@login_required
@required_roles('Usuario')
def usuario_comunidad_filtrar():
    if request.method == 'GET':
        resultados = []
        filtro = request.args.get('filtro')
        nombre = request.args.get('name')
        print(filtro)
        with Mongo:
        	posts = Post.find({Post.tema: filtro}).sort("_id",-1)
        textosalida = ""
        for post in posts:

        	textosalida += '''<div class="post">
  						<div class="titulo_post">
  							<a  href=/usuario/ver_comp/'''+nombre.encode('utf-8') +'''/'''+post.autor.encode('utf-8') +'''     title='''+post.autor.encode('utf-8')+''' ><img style="margin: 4px 4px 2px 4px;" class="avatar_post" tittle=post.autor src="/static/'''+post.autor_avatar.encode('utf-8')+'''" /></a>
  							<div>Asunto:'''+filtro.encode('utf-8')+'''</div>
  							<div>Título:'''+post.titulo.encode('utf-8')+'''</div>
  							<div>Fecha:'''+ post.fecha.encode('utf-8')+'''</div>
  							<div>Autor:'''+post.autor.encode('utf-8')+'''</div>
  						</div>
  						<div class="cuerpo_post">
  							<div style="min-height: 80%;">'''+post.body.encode('utf-8')+'''</div>
  							<div class="feedback">
	  							<a href= /usuario/comunidad/valorar_post/0/'''+str(post._id) +'''/'''+nombre.encode('utf-8') +'''   class="like" title="Votar Negativo"><i class="fa fa-thumbs-o-down fa-lg"" aria-hidden="true"></i>&nbsp;&nbsp;'''+str(post.unlikes)+'''</a>
	  							<a href=/usuario/comunidad/valorar_post/1/'''+str(post._id) +'''/'''+nombre.encode('utf-8') +'''   class="like" title="Votar Positivo"><i class="fa fa-thumbs-o-up fa-lg"" aria-hidden="true"></i>&nbsp;&nbsp;'''+str(post.likes)+'''</a>&nbsp;&nbsp;
	  							<a href=/usuario/comunidad/valorar_post/1/'''+str(post._id) +'''/'''+nombre.encode('utf-8') +'''   class="like" title="Denunciar"><i class="fa fa-ban fa-lg" aria-hidden="true"></i></a>
	  						</div>
  						</div>


  					</div>'''

        return jsonify(result=textosalida)

@user.route('/usuario/comunidad/valorar_post/<int:valor>/<post>/<string:usuario>' ,methods=['GET', 'POST'])
@login_required
@required_roles('Usuario')
def value_post(valor,post,usuario):

	if valor==1:
		with Mongo:
			c = Post.find_one({Post._id : ObjectId(post)})
			votos = c.votos
			if votos.has_key(usuario):
				if votos[usuario] == 0:
					unlikes = int(c.unlikes) - 1
					likes = int(c.likes) + 1
					votos[usuario] = 1
					Post.update({Post._id: ObjectId(post)},{'$set': {Post.likes:  likes, Post.unlikes:  unlikes, Post.votos:  votos }})
			else:
				likes = int(c.likes) + 1
				votos[usuario] = 1
				Post.update({Post._id: ObjectId(post)},{'$set': {Post.likes:  likes, Post.votos:  votos }})

	else:
		with Mongo:
			c = Post.find_one({Post._id : ObjectId(post)})
			votos = c.votos
			if votos.has_key(usuario):
				if votos[usuario] == 1:
					unlikes = int(c.unlikes) + 1
					likes = int(c.likes) - 1
					votos[usuario] = 0
					Post.update({Post._id: ObjectId(post)},{'$set': {Post.likes:  likes, Post.unlikes:  unlikes, Post.votos:  votos }})
			else:
				unlikes = int(c.unlikes) + 1
				votos[usuario] = 0
				Post.update({Post._id: ObjectId(post)},{'$set': {Post.unlikes:  unlikes, Post.votos:  votos }})

	return redirect(url_for('.usuario_comunidad', nombre = usuario))

@user.route('/usuario/comunidad/denuncias/<string:nombre>/<string:post>', methods = ["GET"])
@login_required
@required_roles('Usuario')
def usuario_comunidad_denuncias(nombre,post):
	with Mongo:
		Post.update({Post._id: ObjectId(post)},{'$set': {Post.denuncia: True }})

	return redirect(url_for('.usuario_comunidad', nombre = nombre))


@user.route('/usuario/ver_comp/<string:usuario>/<string:nombre>' , methods = ["GET","POST"])
@login_required
@required_roles('Usuario')
def ver_comp(usuario,nombre):


	if request.method == 'GET':
		with Mongo:

			compa  = Usuario.find_one({Usuario.nombre : nombre})
			u = Usuario.find_one({Usuario.nombre : usuario})
		if nombre == usuario:
			return redirect(url_for('.perfil', nombre=usuario))
		else:
			return render_template("user/ver_usuario.html", usuario = u, compa= compa)

@user.route('/usuario/comunidad/crear_post/<string:nombre>/<string:titulacion>' , methods = ["GET","POST"])
@login_required
@required_roles('Usuario')
def crear_post(nombre,titulacion):


	if request.method == 'GET':
		with Mongo:

			u  = Usuario.find_one({Usuario.nombre : nombre})


	return render_template("user/crear_post.html", usuario = u, titulacion = titulacion )


@user.route('/usuario/comunidad/finalizar_post', methods = ["GET","POST"])
@login_required
@required_roles('Usuario')
def finalizar_post():

	if request.method == 'POST':
		with Mongo:
			post = Post()
			u  = Usuario.find_one({Usuario.nombre : request.form['nombre']})
			post.likes = 0
			post.unlikes = 0
			d = datetime.date.today()
			d = d.strftime("%d/%m/%y")
			post.fecha = d
			post.autor = request.form['nombre']
			post.denuncia = False
			post.autor_avatar = u.foto
			titul = Titulacion.find_one({Titulacion._id : ObjectId(request.form['titulacion'])})
			posts = Post.find({Post.id_titulacion: titul._id}).sort("_id",-1)
			post.tema = request.form['asunto']
			post.titulo = request.form['titulo']
			post.id_titulacion = titul._id
			post.body = request.form['body']
			n = u.posts + 1
			Usuario.update({Usuario._id: u._id},{'$set': {Usuario.posts: n }})
			Post.insert(post)
			top_subidas = Usuario.find({Usuario.titulacion: u.titulacion}).sort("archivos_subidos",-1).limit(5)
			top_descargas = Usuario.find({Usuario.titulacion: u.titulacion}).sort("descargas",-1).limit(5)
			compa = Usuario.find({Usuario.titulacion: u.titulacion})


		return render_template("user/comunidad.html", usuario = u,  posts = posts, titulacion = titul._id, top_subidas= top_subidas , compa=compa, top_descargas= top_descargas)

@user.route('/usuario/comunidad/escribir_mensaje', methods = ["GET","POST"])
@login_required
@required_roles('Usuario')
def escribir_mensaje():

	if request.method == 'POST':
		with Mongo:
			mensaje = Mensaje()
			mensaje2 = Mensaje()
			compa  = Usuario.find_one({Usuario.nombre : request.form['usuario']})
			Usuario.update({Usuario._id: compa._id},{'$set': {Usuario.no_leidos: compa.no_leidos + 1 }})
			autor = Usuario.find_one({Usuario.nombre : request.form['autor']})
			mensaje.asunto = request.form['asunto']
			mensaje2.asunto = request.form['asunto']
			mensaje.id_usuario = compa._id
			mensaje2.id_usuario = compa._id
			mensaje.autor = autor.nombre
			mensaje2.autor = autor.nombre
			mensaje.autor_avatar = autor.foto
			mensaje2.autor_avatar = autor.foto
			mensaje.body = request.form['body']
			mensaje2.body = request.form['body']
			d = datetime.date.today()
			d = d.strftime("%d/%m/%y")
			mensaje.fecha = d
			mensaje2.fecha = d
			mensaje.denuncia = False
			mensaje2.denuncia = False
			mensaje.estado = "No Leídos"
			mensaje2.estado = "Enviados"
			Mensaje.insert(mensaje)
			Mensaje.insert(mensaje2)

		return render_template("user/ver_usuario.html", usuario = autor, compa= compa)


###################################################################################################################
#                                                                                                                 #
#                          VIEWS PARTE DE ENLACES                                                                 #
#                                                                                                                 #
###################################################################################################################


@user.route('/usuario/enlaces/<string:nombre>', methods = ["GET","POST"])
@login_required
@required_roles('Usuario')
def usuario_enlaces(nombre):
	with Mongo:
		u  = Usuario.find_one({Usuario.nombre : nombre})
		f = Facultad.find_one({Facultad.nombre : u.facultad})
		for titulacion in f.titulaciones:
			if titulacion == u.titulacion:
				t = Titulacion.find_one({Titulacion.nombre : titulacion})
		enlaces = Enlaces.find({Enlaces.id_titulacion: t._id})

	return render_template("user/enlaces.html", usuario = u, titulacion = t._id, enlaces=enlaces)

###################################################################################################################
#                                                                                                                 #
#                          VIEWS PARTE DE HORARIO                                                                 #
#                                                                                                                 #
###################################################################################################################


@user.route('/usuario/horario/<string:nombre>', methods = ["GET","POST"])
@login_required
@required_roles('Usuario')
def usuario_horario(nombre):
	with Mongo:
		u  = Usuario.find_one({Usuario.nombre : nombre})
		asignaturas = u.horario.keys()
		asig = []
		for a in asignaturas:
			asig.append(a)
		'''for i in range(9,21):
			hora = Horario()
			hora.hora = i
			hora.id_usuario= u._id
			hora.l=""
			hora.m=""
			hora.x=""
			hora.j = ""
			hora.v=""
			Horario.insert(hora)'''
		horas_ma = Horario.find({Horario.id_usuario: u._id}).sort("hora").limit(6)
		horas_tarde = Horario.find({Horario.id_usuario: u._id}).sort("hora").skip(6)


	return render_template("user/horario.html", usuario = u,  horas_ma=horas_ma, horas_tarde=horas_tarde, asig=asig)


@user.route('/usuario/horario/agregar', methods = ["GET","POST"])
@login_required
@required_roles('Usuario')
def usuario_horario_agregar():
	if request.method == 'POST':
		client = MongoClient('localhost', 27017)
		db = client.trabajofingrado
		with Mongo:
			u  = Usuario.find_one({Usuario.nombre : request.form['usuario']})
			collection = db.usuarios
			nombre = request.form['name']
			numero_horas = int(request.form['horas'])
			h = u.horario
			#horario= { "MD": { "9": "l", "10": "m"}}
			h[nombre]={}
			for i in range(1,numero_horas + 1):
				indice = str(i)
				hora = str(request.form['hora'+indice])
				dia = request.form['dia'+indice].encode('utf-8')
				if hora in h[nombre]:
					a = h[nombre]
					h[nombre][hora].append(dia)
				else:
					h[nombre][hora]=[dia]
			collection.update({"_id" : u._id},{'$set': {"horario": h }})
			for i in range(1,numero_horas + 1):
				indice = str(i)
				hora = int(request.form['hora'+indice])
				dia = request.form['dia'+indice].encode('utf-8')

				if dia=="Lunes":
					Horario.update({Horario.id_usuario: u._id,Horario.hora: hora},{'$set': {Horario.l: nombre }})
				elif dia=="Martes":
					Horario.update({Horario.id_usuario: u._id,Horario.hora: hora},{'$set': {Horario.m: nombre }})
				elif dia=="Miércoles":
					Horario.update({Horario.id_usuario: u._id,Horario.hora: hora},{'$set': {Horario.x: nombre }})
				elif dia=="Jueves":
					Horario.update({Horario.id_usuario: u._id,Horario.hora: hora},{'$set': {Horario.j: nombre }})
				else:
					Horario.update({Horario.id_usuario: u._id,Horario.hora: hora},{'$set': {Horario.v: nombre }})
			asignaturas = u.horario.keys()
			asig = []
			for a in asignaturas:
				asig.append(a)
			horas_ma = Horario.find({Horario.id_usuario: u._id}).sort("hora").limit(6)
			horas_tarde = Horario.find({Horario.id_usuario: u._id}).sort("hora").skip(6)


		return render_template("user/horario.html", usuario = u, horas_ma=horas_ma, horas_tarde=horas_tarde,asig=asig)

@user.route('/usuario/horario/eliminar', methods = ["GET","POST"])
@login_required
@required_roles('Usuario')
def usuario_horario_eliminar():
	if request.method == 'POST':
		client = MongoClient('localhost', 27017)
		db = client.trabajofingrado
		collection = db.usuarios
		with Mongo:
			u  = Usuario.find_one({Usuario.nombre : request.form['usuario']})
			nombre = request.form['asignatura']
			horario = u.horario
			horas = horario[nombre]
			s3='Miércoles'.decode('utf-8')
			for hora in horas:
				for d in horario[nombre][hora]:
					hora = int(hora)
					if d=="Lunes":
						Horario.update({Horario.id_usuario: u._id,Horario.hora: hora},{'$set': {Horario.l: "" }})
					elif d=="Martes":
						Horario.update({Horario.id_usuario: u._id,Horario.hora: hora},{'$set': {Horario.m: "" }})
					elif d==s3:
						Horario.update({Horario.id_usuario: u._id,Horario.hora: hora},{'$set': {Horario.x: "" }})
					elif d=="Jueves":
						Horario.update({Horario.id_usuario: u._id,Horario.hora: hora},{'$set': {Horario.j: "" }})
					else:
						Horario.update({Horario.id_usuario: u._id,Horario.hora: hora},{'$set': {Horario.v: "" }})
			del horario[nombre]
			collection.update({"_id" : u._id},{'$set': {"horario": horario }})
			asignaturas = horario.keys()
			asig = []
			for a in asignaturas:
				asig.append(a)
			horas_ma = Horario.find({Horario.id_usuario: u._id}).sort("hora").limit(6)
			horas_tarde = Horario.find({Horario.id_usuario: u._id}).sort("hora").skip(6)


		return render_template("user/horario.html", usuario = u, horas_ma=horas_ma, horas_tarde=horas_tarde,asig=asig)
