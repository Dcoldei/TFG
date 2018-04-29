# -*- coding: utf-8 -*-
from flask import Blueprint,Flask, render_template, make_response, current_app, redirect, url_for, jsonify, request
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user
from flask import request 
from random import randint
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



admin = Blueprint('admin', __name__)

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










###################################################################################################################
#                                                                                                                 #
#                          VIEWS PARTE DE ADMINISTRADOR                                                           #
#                                                                                                                 # 
###################################################################################################################

@admin.route('/admin', methods = ["GET"])
def admin_access():		
	return render_template("admin/welcome_admin.html")	




		
@admin.route('/admin/comp_ident', methods = ["POST"])
def comprobar_admin():		
	if request.method == 'POST':
		values = {}
		values["nombre"] = request.form['nombre']
		values["password"] = request.form['password']
		with Mongo:
			#usuario = Usuario.find_one({"nombre" : "Daniel"})
			admin = Usuario.find_one({Usuario.nombre : values["nombre"]})
			if admin is None:
				return render_template("ident_fallida.html" , value = values)
			else:
				if values["password"] == admin.password and admin.role == "Admin":
					user = User(values["nombre"],admin.role)
					login_user(user)
					return render_template("admin/inicio_admin.html", value = values)	
				else:
					return render_template("admin/ident_fallida.html", value = values)
					
@admin.route('/admin/inicio/<string:nombre>', methods = ["GET"])
def admin_inicio(nombre):	
	with Mongo: 
		u  = Usuario.find_one({Usuario.nombre : nombre})
		posts = Post.find({Post.denuncia: True}).count()
		comentarios = Comentario.find({Comentario.denuncia: True}).count()
		mensajes = Mensaje.find({Mensaje.denuncia: True}).count()
		denuncias = posts + comentarios + mensajes
		pendientes = Archivo.find({Archivo.autorizado: False}).count()

	return render_template("admin/inicio_admin.html", usuario = u, denuncias = denuncias, pendientes= pendientes)	



@admin.route('/admin/config/<string:nombre>',methods=['GET', 'POST'])
@login_required
@required_roles('Admin')
def config(nombre):
	with Mongo: 
		u  = Usuario.find_one({Usuario._id : ObjectId(nombre)})
		

	return render_template("admin/config.html", usuario = u )		

@admin.route('/admin/perfil/cambiar_nombre')
def admin_nuevo_nombre():
	nombre = request.args.get('nombre')
	with Mongo:
		u = Usuario.find_one({Usuario.nombre: request.args.get('nuevo_nombre')})
		if u == None:			
			Usuario.update({Usuario.nombre : nombre },{'$set': {Usuario.nombre: request.args.get('nuevo_nombre')}})	
			textosalida = ''''''
			repeat = "No"
		else:
			textosalida = '''Nombre de Usuario ya existente, elija otro.'''
			repeat = "Si"
	
	return jsonify(result=textosalida,repeat=repeat)

@admin.route('/admin/perfil/cambiar_password')
def admin_nuevo_pass():
	nombre = request.args.get('nombre')
	print(request.args.get('nombre'))
	print()
	with Mongo:
		Usuario.update({Usuario.nombre : request.args.get('nombre') },{'$set': {Usuario.password: request.args.get('nuevo_pass')}})		

	textosalida = '''<b>Password >> </b>'''+request.args.get('nuevo_pass')+'''<button id="usuario_password"   class="button" > Editar </button>'''
	return jsonify(result=textosalida)


###################################################################################################################
#                                                                                                                 #
#                          VIEWS BORRAR FACULTAD , TITULACION ,TRATAR CON USUARIOS Y ARCHIVOS                     #
#                                                                                                                 # 
###################################################################################################################

@admin.route('/admin/usuarios/<string:nombre>', methods = ["GET","POST"])
def admin_usuarios(nombre):
	activos = []
	bloqueados = []	
	with Mongo:
		u  = Usuario.find_one({Usuario._id : ObjectId(nombre)})
		facul = Facultad.find_one()
		titul = Titulacion.find_one({Titulacion.id_facultad: facul._id})
		usuarios = Usuario.find({Usuario.titulacion: titul.nombre})
		titul = Titulacion.find({Titulacion.id_facultad: facul._id})
		facul = Facultad.find()
		for usuario in usuarios:
			if usuario.activo == True:
				activos.append(usuario.nombre)
			else:
				bloqueados.append(usuario.nombre)

	return render_template("admin/bloquear_usuario.html", activos=activos , bloqueados=bloqueados, usuario=u, facul = facul, titul = titul)	


@admin.route('/admin/bloquear_usuario', methods = ["GET","POST"])
def admin_bloquear():
	if request.method == 'POST':
		nombre = request.form['nombre']
		usuario = request.form['bloquear']
		date = request.form['datepicker']
		with Mongo:
			u = Usuario.find_one({Usuario._id : ObjectId(nombre)})
			Usuario.update({Usuario.nombre : usuario },{'$set': {Usuario.activo: False}})
			Usuario.update({Usuario.nombre : usuario },{'$set': {Usuario.activo_desde: date }})



		return redirect(url_for('admin/admin_usuarios' ,nombre = u._id))	

@admin.route('/admin/bloquear_usuario/facultad/_search')
def search_usuarios():
	activos = []
	bloqueados = []	
	with Mongo:
		facultad = Facultad.find_one({Facultad.nombre : request.args.get('busqueda')})
		titul = Titulacion.find({Titulacion.id_facultad : facultad._id})
		t = Titulacion.find_one({Titulacion.id_facultad : facultad._id})
		usuarios = Usuario.find({Usuario.titulacion: t.nombre})
		for usuario in usuarios:
			if usuario.activo == True:
				activos.append(usuario.nombre)
			else:
				bloqueados.append(usuario.nombre)
	textosalida = ""
	ac=""
	bl=""
	for t in titul:
		textosalida += "<option value= "+ t.nombre +" >"+t.nombre+"</option>"
	for a in activos:
		ac += "<option value= "+ a +" >"+a+"</option>"
	for b in bloqueados:
		bl += "<option value= "+ b +" >"+b+"</option>"
	return jsonify(result=textosalida,activar=bl,bloquear=ac)

@admin.route('/admin/bloquear_usuario/titulacion/_search')
def search_usuarios_t():
	activos = []
	bloqueados = []	
	with Mongo:
		titul = Titulacion.find({Titulacion.nombre: request.args.get('busqueda')})
		t = Titulacion.find_one({Titulacion.nombre : request.args.get('busqueda')})
		usuarios = Usuario.find({Usuario.titulacion: t.nombre})
		for usuario in usuarios:
			if usuario.activo == True:
				activos.append(usuario.nombre)
			else:
				bloqueados.append(usuario.nombre)
	a=""
	b=""
	for t in activos:
		a += "<option value= "+ t +" >"+t +"</option>"
	for t in bloqueados:
		b += "<option value= "+ t +" >"+t+"</option>"
	return jsonify(activar=b,bloquear=a)


@admin.route('/admin/desbloquear_usuario', methods = ["GET","POST"])
def admin_desbloquear():
	if request.method == 'POST':
		nombre = request.form['nombre']
		usuario = request.form['activar']
		d = datetime.date.today()
		date = d.isoformat()
		with Mongo:
			u = Usuario.find_one({Usuario._id : ObjectId(nombre)})
			Usuario.update({Usuario.nombre : usuario },{'$set': {Usuario.activo: True}})
			Usuario.update({Usuario.nombre : usuario },{'$set': {Usuario.activo_desde: date }})
		return redirect(url_for('admin/admin_usuarios', nombre = u._id))


@admin.route('/admin/pendientes/<string:nombre>', methods = ["GET"])
def admin_pendientes(nombre):
	pendientes = []
	with Mongo:
		u = Usuario.find_one({Usuario._id : ObjectId(nombre)})
		archivos = Archivo.find({Archivo.autorizado: False})
		pendientes = Archivo.find({Archivo.autorizado: False})

	return render_template("admin/pendientes.html", pendientes=pendientes,archivos=archivos, usuario=u)

@admin.route('/admin/denuncias/<string:nombre>', methods = ["GET"])
def admin_denuncias(nombre):
	
	with Mongo:
		u = Usuario.find_one({Usuario._id : ObjectId(nombre)})
		posts = Post.find({Post.denuncia: True})
		comentarios = Comentario.find({Comentario.denuncia: True})
		mensajes = Mensaje.find({Mensaje.denuncia: True})


	return render_template("admin/denuncias.html", comentarios = comentarios, posts=posts, mensajes=mensajes, usuario=u, denuncias =False, denuncia=[])


@admin.route('/admin/denuncias/eliminar/<string:nombre>/<string:identidad>', methods = ["GET"])
def admin_denuncias_eliminar(nombre,identidad):
	
	with Mongo:
		Mensaje.remove({Mensaje._id : ObjectId(identidad) })
		Post.remove({Post._id : ObjectId(identidad) })
		Comentario.remove({Comentario._id : ObjectId(identidad) })


	return redirect(url_for('admin.admin_denuncias', nombre = nombre))

@admin.route('/admin/denuncias/obviar/<string:nombre>/<string:identidad>', methods = ["GET"])
def admin_denuncias_obviar(nombre,identidad):
	
	with Mongo:
		Mensaje.update({Mensaje._id : ObjectId(identidad) },{'$set': {Mensaje.denuncia: False}})
		Post.update({Post._id : ObjectId(identidad) },{'$set': {Post.denuncia: False}})
		Comentario.update({Comentario._id : ObjectId(identidad) },{'$set': {Comentario.denuncia: False}})


	return redirect(url_for('admin.admin_denuncias', nombre = nombre))

@admin.route('/admin/denuncias/cargar/<string:usuario>/<string:den>/<int:tipo>', methods = ["GET"])
def admin_denuncias_cargar(usuario,den,tipo):
	
	denuncia = {}
	with Mongo:
		u = Usuario.find_one({Usuario._id : ObjectId(usuario)})
		posts = Post.find({Post.denuncia: True})
		comentarios = Comentario.find({Comentario.denuncia: True})
		mensajes = Mensaje.find({Mensaje.denuncia: True})
		if tipo==1:
			denuncia = Post.find_one({Post._id : ObjectId(den)})
		elif tipo==2:
			denuncia = Comentario.find_one({Comentario._id : ObjectId(den)})	
		else:			
			m = Mensaje.find_one({Mensaje._id : ObjectId(den)})
			denuncia['body'] = m.body
			denuncia['fecha'] = m.fecha
			denuncia['autor'] = m.autor
			denuncia['titulo'] = m.asunto



	return render_template("admin/denuncias.html", comentarios = comentarios, posts=posts, mensajes=mensajes, usuario=u, denuncias =True, denuncia=denuncia)


@admin.route('/admin/autorizar', methods = ["GET","POST"])
def admin_autorizar():
	if request.method == 'POST':
		nombre = request.form['nombre']
		archivo = request.form['revisar']
		with Mongo:
			u = Usuario.find_one({Usuario._id : ObjectId(nombre)})
			Archivo.update({Archivo.nombre : archivo },{'$set': {Archivo.autorizado: True}})

		return redirect(url_for('admin/admin_pendientes' , nombre = u))

@admin.route('/admin/archivos/<string:nombre>', methods = ["GET"])
def admin_archivos(nombre):
	lista = []
	asig = []
	with Mongo:
		u = Usuario.find_one({Usuario._id : ObjectId(nombre)})
		facul = Facultad.find_one()
		titul_one = Titulacion.find_one({Titulacion.id_facultad: facul._id})
		titul = Titulacion.find({Titulacion.id_facultad: facul._id})
		facul = Facultad.find()
		cursos = Curso.find({Curso.id_titulacion: titul_one._id })
		for curso in cursos:
			asignaturas = Asignatura.find({Asignatura.id_curso : curso._id})
			for a in asignaturas:
				asig.append(a)
		a= asig[0]
		archivos = Archivo.find({Archivo.id_asignatura: a._id})


	return render_template("admin/archivos.html", archivos=archivos,asig=asig, usuario=u, facul = facul, titul = titul)


@admin.route('/admin/archivos/facultad/_search')
def search_archivos():
	asig = []	
	print("Hola")
	print(request.args.get('busqueda'))
	with Mongo:
		facul = Facultad.find_one({Facultad._id: ObjectId(request.args.get('busqueda')) })
		titul_one = Titulacion.find_one({Titulacion.id_facultad: facul._id})
		titul = Titulacion.find({Titulacion.id_facultad: facul._id})
		facul = Facultad.find()
		cursos = Curso.find({Curso.id_titulacion: titul_one._id })
		for curso in cursos:
			asignaturas = Asignatura.find({Asignatura.id_curso : curso._id})
			for a in asignaturas:
				asig.append(a)
		a= asig[0]
		archivos = Archivo.find({Archivo.id_asignatura: a._id})
	titulacion = ""
	asign=""
	arch=""
	for t in titul:
		titulacion += "<option value= "+ str(t._id) +" >"+t.nombre+"</option>"
	for a in asig:
		asign += "<option value= "+ str(a._id) +" >"+a.nombre+"</option>"
	for b in archivos:
		arch += "<option value= "+ str(b._id) +" >"+b.nombre+"</option>"
	return jsonify(result=titulacion,asignaturas=asign,archivos=arch)

@admin.route('/admin/archivo/titulacion/_search')
def search_archivos_t():
	asig = []	
	with Mongo:
		titul_one = Titulacion.find_one({Titulacion._id: ObjectId(request.args.get('busqueda'))})
		print(titul_one.nombre)
		cursos = Curso.find({Curso.id_titulacion: titul_one._id })
		for curso in cursos:
			asignaturas = Asignatura.find({Asignatura.id_curso : curso._id})
			for a in asignaturas:
				asig.append(a)
		a= asig[0]
		archivos = Archivo.find({Archivo.id_asignatura: a._id})
	asign=""
	arch=""
	for a in asig:
		asign += "<option value= "+ str(a._id) +" >"+a.nombre+"</option>"
	for b in archivos:
		arch += "<option value= "+ str(b._id) +" >"+b.nombre+"</option>"
	return jsonify(asignaturas=asign,archivos=arch)

@admin.route('/admin/archivo/asignatura/_search')
def search_archivos_a():
	asig = []	
	with Mongo:
		archivos = Archivo.find({Archivo.id_asignatura: ObjectId(request.args.get('busqueda'))})
	arch=""
	for b in archivos:
		arch += "<option value= "+ str(b._id) +" >"+b.nombre+"</option>"
	return jsonify(archivos=arch)

@admin.route('/admin/upload/<filename>',methods=['GET', 'POST'])
@login_required
@required_roles('Admin')
def uploaded_file_admin(filename):
	with Mongo:
		archivo = Archivo.find_one({Archivo.nombre : filename})
		num = int(archivo.num_descargas)+1
		print(num)
		Archivo.update({Archivo.nombre : filename },{'$set': {Archivo.num_descargas: num}})
		return send_file(io.BytesIO(archivo.fichero),
                     attachment_filename=filename,as_attachment=True)

@admin.route('/admin/archivo/borrar', methods = ["GET","POST"])
def admin_archivo_borrar():
	if request.method == 'POST':
		nombre = request.form['nombre']
		archivos = []
		borrar = request.form['borrar']
		print(borrar)
		with Mongo:
			u = Usuario.find_one({Usuario._id : ObjectId(nombre)})
			archivo = Archivo.find_one({Archivo._id : ObjectId(borrar) })
			asig = Asignatura.find_one({Asignatura._id: archivo.id_asignatura})
			numero = asig.num_ficheros - 1;
			for i in range(len(asig.nombre_ficheros)):
				if asig.nombre_ficheros[i] != nombre:
					archivos.append(asig.nombre_ficheros[i])
			Asignatura.update({Asignatura._id: archivo.id_asignatura},{'$set': {Asignatura.num_ficheros:  numero }})
			Asignatura.update({Asignatura._id: archivo.id_asignatura},{'$set': {Asignatura.nombre_ficheros:  archivos }})
			Archivo.delete_one({Archivo._id: archivo._id})

		return redirect(url_for('admin.admin_archivos' , nombre = u._id))


@admin.route('/admin/borrar_facultad/<string:facultad>/<string:usuario>', methods = ["GET","POST"])
def admin_borrar(facultad,usuario):	
	with Mongo:
		usuario = Usuario.find_one({Usuario._id: ObjectId(usuario)})
		facultad = Facultad.find_one({Facultad.nombre : facultad})
		Facultad.delete_one({Facultad.nombre : facultad.nombre})
		cursor_facultad = Titulacion.find({Titulacion.id_facultad: facultad._id})
		for t in cursor_facultad:
			id_titulacion = t._id
			cursor_titulacion = Curso.find({Curso.id_titulacion : id_titulacion})
			for c in cursor_titulacion:
				id_curso = c._id
				cursor_asignaturas = Asignatura.find({Asignatura.id_curso : id_curso})
				for asignatura in cursor_asignaturas:
					Archivo.delete_many({Archivo.id_asignatura: asignatura._id})
				Asignatura.delete_many({Asignatura.id_curso : id_curso})
				Curso.delete_one({Curso._id : id_curso})
				Titulacion.delete_one({Titulacion._id : id_titulacion})

	return redirect(url_for('admin/admin_inicio' , nombre = usuario.nombre))
	

@admin.route('/admin/borrar_facultad_titul/<string:titulacion>/<string:usuario>', methods = ["GET","POST"])
def admin_borrar_titul(titulacion, usuario):	
	with Mongo:
		usuario = Usuario.find_one({Usuario._id : ObjectId(usuario)})
		lista_titul= []
		lista_cursos = []
		t = Titulacion.find_one({Titulacion.nombre: ObjectId(titulacion)})
		id_facultad = t.id_facultad
		facultad = Facultad.find_one({Facultad._id : id_facultad })	
		numero = facultad.num_titul
		numero -= 1
		titulaciones = facultad.titulaciones
		for i in range(len(titulaciones)):
			if titulaciones[i]== nombre:
				num = i
			else:
				lista_titul.append(titulaciones[i])
		cursos_x_titul = facultad.cursos_x_titul 
		for i in range(len(cursos_x_titul)):
			if i != num:
				lista_cursos.append(cursos_x_titul[i])
		Facultad.update({Facultad._id : id_facultad },{'$set': {Facultad.num_titul: numero}})
		Facultad.update({Facultad._id : id_facultad },{'$set': {Facultad.titulaciones: lista_titul}})
		Facultad.update({Facultad._id : id_facultad },{'$set': {Facultad.cursos_x_titul: lista_cursos}})
		cursor_titulacion = Curso.find({Curso.id_titulacion : t._id})
		for c in cursor_titulacion:
			id_curso = c._id
			#Se han agregado las 3 lineas siguientes
			cursor_asignaturas = Asignatura.find({Asignatura.id_curso : id_curso})
			for asignatura in cursor_asignaturas:
				Archivo.delete_many({Archivo.id_asignatura: asignatura._id})
			Asignatura.delete_many({Asignatura.id_curso : id_curso})
			Curso.delete_one({Curso._id : id_curso})
		Titulacion.delete_one({Titulacion._id : t._id})
	return redirect(url_for('admin/admin_inicio' , nombre = usuario.nombre))			

@admin.route('/admin/modificar_facul/<string:nombre>', methods = ["GET","POST"])
def admin_modificar(nombre):	
	if request.method == 'GET':
		values = []
		with Mongo: 
			u = Usuario.find_one({Usuario._id: ObjectId(nombre)})
			facultades = Facultad.find().sort("nombre")
			for facultad in facultades:
				values.append(facultad.nombre)
		return render_template("admin/modificar_inicio.html", vs = values, usuario=u)		


@admin.route('/admin/modificar_facultad', methods = ["GET","POST"])
def admin_modificar_facultad():	
		

	if request.method == 'POST':

		values = []
		usuario = request.form['nombre']
		nombre = request.form['facultad']
		with Mongo: 
			u = Usuario.find_one({Usuario._id: ObjectId(usuario)})
			facultad = Facultad.find_one({Facultad.nombre: nombre })
			id_facultad = facultad._id
			titulaciones = Titulacion.find({Titulacion.id_facultad : id_facultad}).sort("nombre")
			#for titulacion in titulaciones:
			#	values.append(titulacion.nombre)	

		return render_template("admin/modificar_facultad.html", vs = titulaciones , facultad = nombre, usuario= u)

###################################################################################################################
#                                                                                                                 #
#                          VIEWS MOSTRAR TITULACION EN ADMIN Y BORRAR UNA ASIGNATURA                                                          #
#                                                                                                                 # 
###################################################################################################################
@admin.route('/admin/mostrar_titul/<string:titulacion>/<string:usuario>', methods = ["GET"])
def admin_modificar_titul(titulacion,usuario):	
	with Mongo: 
		titulacion = Titulacion.find_one({Titulacion._id: ObjectId(titulacion)})
		cursos = Curso.find({Curso.id_titulacion : titulacion._id })
		usuario= Usuario.find_one({Usuario._id : ObjectId(usuario)})
	return render_template("admin/mostrar_titulacion.html", usuario = usuario, titulacion = titulacion, cursos = cursos)	

@admin.route('/admin/agregar_curso/<string:nombre>/<string:usuario>', methods = ["GET"])
def admin_agregar_curso(nombre, usuario):	
	n = 20
	with Mongo: 
		usuario = Usuario.find_one({Usuario._id: ObjectId(usuario)})
		titulacion = Titulacion.find_one({Titulacion._id: ObjectId(nombre)})
		
			
	return render_template("admin/agregar_curso.html", titulacion = titulacion , numero = n, usuario= usuario)	

@admin.route('/admin/agregar_curso/fin', methods = ["POST"])
def admin_agregar_curso_fin():	
	nombre = request.form['titulacion_id']
	n = int(request.form['n_asignaturas'])  
	numero = request.form['numero']  
	u = request.form['usuario']
	asi = []
	for i in range(1,n +1):
		asignatura = request.form['asignatura_'+ str(i)]
		asi.append(asignatura)
	with Mongo: 
		usuario = Usuario.find_one({Usuario._id : ObjectId(u)})
		curso = Curso()
		curso.numero = numero
		curso.id_titulacion = ObjectId(nombre)
		curso.num_asignaturas = n
		curso.asignaturas = asi
		id_curso = Curso.insert(curso)
		for j in range(1,n +1):
			a = Asignatura()
			a.nombre = request.form['asignatura_'+ str(j)]
			a.id_curso = id_curso
			a.nombre_ficheros =[]
			a.num_ficheros = 0
			Asignatura.insert(a)		
		titulacion = Titulacion.find_one({Titulacion._id: ObjectId(nombre)})
		print("TItulacion")
		print(titulacion.nombre)
		facultad = Facultad.find_one({Facultad._id: titulacion.id_facultad})
		n = -1
		c=[]
		for t in facultad.titulaciones:
			n+=1
			if t == titulacion.nombre:
				print(titulacion.nombre)
				print(n)
				print(facultad.cursos_x_titul[n])
				d = facultad.cursos_x_titul[n] + 1
				for l in range(0,len(facultad.cursos_x_titul)):
					if l!=n:
						c.append(facultad.cursos_x_titul[l])
					else:
						c.append(d)
				Facultad.update({Facultad._id: titulacion.id_facultad },{'$set': {Facultad.cursos_x_titul: c  }})

		asig_titulacion = []
		for j in range(0,len(titulacion.asignaturas)):
			s=[]
			for v in range(0,len(titulacion.asignaturas[j])):
				s.append(titulacion.asignaturas[j][v])
			asig_titulacion.append(s)
		asig_titulacion.append(asi)	
		cursos = Curso.find({Curso.id_titulacion : titulacion._id })	
		Titulacion.update({Titulacion._id : ObjectId(nombre) },{'$set': {Titulacion.asignaturas: asig_titulacion }})
		Titulacion.update({Titulacion._id : ObjectId(nombre) },{'$set': {Titulacion.num_cursos: titulacion.num_cursos + 1 }})


	return render_template("admin/mostrar_titulacion.html", titulacion = titulacion, asignaturas = a, cursos = cursos, usuario=usuario)		

@admin.route('/admin/borrar_asignatura', methods = ["POST"])
def borrar_asig():
	# Debemos conocer el id_curso de la asignatura ya que podria existir varias asignaturas con 
	# el mismo nombre y solo podemos distinguirlos por el id_curso. Deberiamos pasarle el id_curso para
	# poder diferencirlos.

	if request.method == 'POST':
		titulacion = str(request.form['titulacion'])
		curso = int(request.form['curso'])  	
		n = str(curso)
		asignatura = request.form['asignatura_'+ n]
		usuario = request.form['usuario']
		with Mongo:
			titul = Titulacion.find_one({Titulacion.nombre : titulacion})
			id_titul = titul._id
			asig_titulacion = []
			
			for a_x_c  in titul.asignaturas:
				asig_curso = []
				for i in range(len(a_x_c)):					
					if a_x_c[i]!= asignatura:
						asig_curso.append(a_x_c[i])
				asig_titulacion.append(asig_curso)

			Titulacion.update({Titulacion._id : id_titul },{'$set': {Titulacion.asignaturas: asig_titulacion }})	
			cursos = Curso.find({Curso.id_titulacion: id_titul})
			for c in cursos:
				if c.numero == curso:
					numero = c.num_asignaturas - 1
					lista_asig= []
					id_curso = c._id
					for i in range(len(c.asignaturas)):
						if c.asignaturas[i]!= asignatura:
							lista_asig.append(c.asignaturas[i])

					Curso.update({Curso._id : id_curso },{'$set': {Curso.num_asignaturas: numero}})
					Curso.update({Curso._id : id_curso },{'$set': {Curso.asignaturas: lista_asig}})
			a = Asignatura.find({Asignatura.nombre : asignatura})

			for a_s in a:
				if a_s.id_curso == id_curso:
					Asignatura.delete_one({Asignatura._id : a_s._id})
					identidad = a_s._id
			Archivo.delete_many({Archivo.id_asignatura: identidad })

			#Las dos ultimas lineas son nuevas para borrar los archivos ligados a esa asignatura


		return redirect(url_for('admin.admin_modificar_titul', titulacion=id_titul,usuario=usuario))		
		

###################################################################################################################
#                                                                                                                 #
#                          VIEWS AGREGAR FACULTAD Y ASIGNATURA                                                      #
#                                                                                                                 # 
###################################################################################################################


@admin.route('/admin/agregar_asignatura/<string:usuario>/<string:titulacion>/<int:curso>', methods = ["GET","POST"])
def agregar_asig(usuario,titulacion,curso):

	with Mongo:
		usuario = Usuario.find_one({Usuario._id: ObjectId(usuario)})


	return render_template("admin/agregar_asignatura.html" ,usuario=usuario,  titulacion = titulacion , curso = curso)



@admin.route('/admin/agregar_asignatura/fin', methods = ["GET","POST"])
def agregar_asignatura_fin():

	if request.method == 'POST':
		titulacion = request.form['titulacion']	
		curso = int(request.form['curso'])  	
		asignatura = request.form['asignatura']
		usuario = request.form['usuario']
		with Mongo:
			titul = Titulacion.find_one({Titulacion.nombre : titulacion})
			id_titul = titul._id
			asig_titulacion = []
			
			for j in range(len(titul.asignaturas)):
				asig_curso = []
				for i in range(len(titul.asignaturas[j])):
					
					asig_curso.append(titul.asignaturas[j][i])
				if j+1 == curso:
					asig_curso.append(asignatura)
				asig_titulacion.append(asig_curso)
				##NO GUARDA BIEN LAS ASIGNATURAS , SOLO GUARDA LA ULTIMA Y LA CREADA
			Titulacion.update({Titulacion._id : id_titul },{'$set': {Titulacion.asignaturas: asig_titulacion }})	
			cursos = Curso.find({Curso.id_titulacion: id_titul})
			for c in cursos:
				if c.numero == curso:
					numero = c.num_asignaturas + 1
					lista_asig= []
					id_curso = c._id
					for i in range(len(c.asignaturas)):
						lista_asig.append(c.asignaturas[i])
					lista_asig.append(asignatura)
					Curso.update({Curso._id : id_curso },{'$set': {Curso.num_asignaturas: numero}})
					Curso.update({Curso._id : id_curso },{'$set': {Curso.asignaturas: lista_asig}})
			a = Asignatura()
			a.nombre = asignatura
			a.id_curso = id_curso
			a.nombre_ficheros =[]
			a.num_ficheros = 0
			Asignatura.insert(a)



		return redirect(url_for('admin.admin_modificar_titul', titulacion=id_titul,usuario=usuario))		


@admin.route('/admin/agregar_facul/<string:nombre>', methods = ["GET","POST"])
def agregar_facult(nombre):
	values = {0,1,2,3,4,5}
	if request.method == 'GET':
		with Mongo:
			usuario = Usuario.find_one({Usuario._id: ObjectId(nombre)})
		return render_template("admin/agregar_facul.html", vs = values, usuario=usuario)		


@admin.route('/admin/agregar_facul', methods = ["GET","POST"])
def agregar_facult_sig():

	if request.method == 'POST':
		facultad = Facultad()
		values = {0,1,2,3,4,5,6,7,8,9,10}
		lista_titulaciones = []
		lista_cursos = []
		facultad.nombre = request.form['nombre']
		numero_titulaciones = int(request.form['titulaciones'])	
		for i in range(1,numero_titulaciones *2 + 1):
			indice = str(i)
			if i % 2 == 1:
				lista_titulaciones.append(request.form['text'+indice])
			else:
				n = int(request.form['text'+indice])
				lista_cursos.append(n)
		facultad.titulaciones = lista_titulaciones
		facultad.num_titul = numero_titulaciones
		facultad.cursos_x_titul = lista_cursos
		with Mongo:
			facul_id = Facultad.insert(facultad)
			u = Usuario.find_one({Usuario._id: ObjectId(request.form['usuario'])})	
			

		num = 0
		ult = False
		if numero_titulaciones == 1:
			ult = True

		return render_template("admin/agregar_titul.html" ,  facultad = facultad, l_cursos = lista_cursos  , numero = num,  vs = values, ultima = ult, usuario = u)

@admin.route('/admin/agregar_facul/titulaciones', methods = ["GET","POST"])
def agregar_titulacion():

	#Encontrar la facultad asociada al nombre pasado por el form
	facul_nombre = request.form['facultad']
	with Mongo:
		facultad = Facultad.find_one({Facultad.nombre : facul_nombre })	
		u = Usuario.find_one({Usuario._id: ObjectId(request.form['usuario'])})	
	
	#Inicializar parametros para el render_template

	values = {0,1,2,3,4,5,6,7,8,9,10}
	titul = facultad.num_titul
	lista_cursos = facultad.cursos_x_titul
	num = int(request.form['numero'])	

	#Creamos la titulacion con los datos aportados por el form
	t = Titulacion()
	t.nombre = facultad.titulaciones[num]
	t.id_facultad = facultad._id
	t.num_cursos = facultad.cursos_x_titul[num]
	t.asignaturas = []
	asign_titul = []

	#Insertamos la titulacion creada anteriormente en Titulaciones
	with Mongo:
		titulacion_id = Titulacion.insert(t)
		
	for i in range(1,lista_cursos[num] + 1):
		lista_asig = []
		indice = str(i)
		numero_asignaturas = int(request.form['asignaturas_'+ indice])	
		for j in range(1 ,numero_asignaturas + 1):
			n = str(j)
			lista_asig.append(request.form['text'+n+indice])
	#Creamos los cursos correspondientes a la titulacion creada y los insertamos en Cursos
		curso = Curso()
		curso.numero = i
		curso.id_titulacion = titulacion_id
		curso.num_asignaturas = j
		curso.asignaturas = lista_asig
		with Mongo:
			curso_id = Curso.insert(curso)
	#Insertamos todas las asignaturas en la bb.dd  con la _id del curso correspondiente
		for j in range(1 ,numero_asignaturas + 1):
			n = str(j)
			asignatura = Asignatura()
			asignatura.nombre = request.form['text'+n+indice]
			asignatura.id_curso = curso_id
			asignatura.num_ficheros = 0
			asignatura.nombre_ficheros = []
			with Mongo:
				Asignatura.insert(asignatura)

		asign_titul.append(lista_asig)  
	#Adaptamos la titulacion con la lista de asignaturas enviadas a traves del form
	with Mongo:
		Titulacion.update({Titulacion._id: titulacion_id },{'$set': {Titulacion.asignaturas: asign_titul}})


	num = num + 1
	#Comprobamos si es la ultima titulacion a insertar para cambiar el valor del boton del formulario de Siguiente a Finalizar
	if num < titul- 1 :
		ult = False
		return render_template("admin/agregar_titul.html" ,  facultad = facultad, l_cursos = lista_cursos  , numero = num,  vs = values, ultima = ult, usuario = u)
	elif num == titul -1:
		ult = True
		return render_template("admin/agregar_titul.html" ,  facultad = facultad, l_cursos = lista_cursos  , numero = num,  vs = values, ultima = ult, usuario = u)
	else:
	#Buscamos los valores para mostrar los datos insertados en la bb.dd
		asign_curso = []
		numero_cursos = []
		as_titul = []
		for titul in facultad.titulaciones:
			with Mongo:
				titulacion = Titulacion.find_one({Titulacion.nombre:  titul })
				numero_cursos.append(titulacion.num_cursos)
				as_titul.append(titulacion.asignaturas)
			
		return render_template("admin/finalizar_registro_facultad.html" ,  facultad = facultad, asign_titul = as_titul , cursos = numero_cursos,  usuario = u)


###################################################################################################################
#                                                                                                                 #
#                          VIEWS MODIFICAR FACULTAD AGREGANDO UNA TITULACION                                                          #
#                                                                                                                 # 
###################################################################################################################

@admin.route('/admin/modificar_titulacion_inicio/<string:facultad>/<string:usuario>', methods = ["GET","POST"])
def modificar_titulacion_inicio(facultad, usuario):
	with Mongo:
		usuario = Usuario.find_one({Usuario._id : ObjectId(usuario)})
	return render_template("admin/agregar_nueva_titulacion.html" , facultad = facultad, usuario= usuario)	


@admin.route('/admin/modificar_titulacion', methods = ["GET","POST"])
def modificar_titulacion():
	values = {0,1,2,3,4,5,6,7,8,9,10}
	if request.method == 'POST':
		lista_titul = []
		lista_cursos = []
		curso = int(request.form['cursos'])
		facul_nombre = request.form['facultad']
		with Mongo:
			facultad = Facultad.find_one({Facultad.nombre : facul_nombre })	
			numero = facultad.num_titul
			numero += 1
			titulaciones = facultad.titulaciones
			for i in range(len(titulaciones)):
				lista_titul.append(titulaciones[i])
			lista_titul.append(request.form['nombre'])
			cursos_x_titul = facultad.cursos_x_titul 
			for i in range(len(cursos_x_titul)):
				lista_cursos.append(cursos_x_titul[i])
			lista_cursos.append(curso)
			Facultad.update({Facultad.nombre: facul_nombre },{'$set': {Facultad.num_titul: numero}})
			Facultad.update({Facultad.nombre: facul_nombre },{'$set': {Facultad.titulaciones: lista_titul}})
			Facultad.update({Facultad.nombre: facul_nombre },{'$set': {Facultad.cursos_x_titul: lista_cursos}})

		return render_template("admin/agregar_nueva_titulacion_fin.html" ,  facultad = facul_nombre, cursos = curso  ,  vs = values, nombre = request.form['nombre'])

@admin.route('/admin/modificar_titulacion_fin', methods = ["GET","POST"])
def modificar_titulacion_fin():
	#Encontrar la facultad asociada al nombre pasado por el form
	facul_nombre = request.form['facultad']
	with Mongo:
		facultad = Facultad.find_one({Facultad.nombre : facul_nombre })	

	#Creamos la titulacion con los datos aportados por el form

	t = Titulacion()
	t.nombre = request.form['nombre']
	t.id_facultad = facultad._id
	t.num_cursos = int(request.form['cursos'])
	t.asignaturas = []
	asign_titul = []

	#Insertamos la titulacion creada anteriormente en Titulaciones
	with Mongo:
		titulacion_id = Titulacion.insert(t)
		


	for i in range(1,t.num_cursos + 1):
		lista_asig = []
		indice = str(i)
		numero_asignaturas = int(request.form['asignaturas_'+ indice])	
		for j in range(1 ,numero_asignaturas + 1):
			n = str(j)
			lista_asig.append(request.form['text'+n+indice])
	#Creamos los cursos correspondientes a la titulacion creada y los insertamos en Cursos
		curso = Curso()
		curso.numero = i
		curso.id_titulacion = titulacion_id
		curso.num_asignaturas = j
		curso.asignaturas = lista_asig
		with Mongo:
			curso_id = Curso.insert(curso)
	#Insertamos todas las asignaturas en la bb.dd  con la _id del curso correspondiente
		for j in range(1 ,numero_asignaturas + 1):
			n = str(j)
			asignatura = Asignatura()
			asignatura.nombre = request.form['text'+n+indice]
			asignatura.id_curso = curso_id
			asignatura.num_ficheros = 0
			asignatura.nombre_ficheros = []
			with Mongo:
				Asignatura.insert(asignatura)

		asign_titul.append(lista_asig)  
	#Adaptamos la titulacion con la lista de asignaturas enviadas a traves del form
	with Mongo:
		Titulacion.update({Titulacion.nombre: t.nombre },{'$set': {Titulacion.asignaturas: asign_titul}})

	values = []
	nombre = request.form['facultad']
	with Mongo: 
		facultad = Facultad.find_one({Facultad.nombre: nombre })
		id_facultad = facultad._id
		titulaciones = Titulacion.find({Titulacion.id_facultad : id_facultad})
		for titulacion in titulaciones:
			values.append(titulacion.nombre)	

	return render_template("admin/modificar_facultad.html", vs = values , facultad = nombre)


@admin.route('/list', methods = ["GET"])
def list():
	with Mongo:
		ops = OP.find()
		ss = ""
		for o in ops:
			try:
				ss+= o["nombre"]
				ss+=", "
				ss+= o["password"]
				ss+=", "
				ss+= o["palabra"]
				ss+= ", "
				ss+= str(o["tamPalabra"]) 
				ss+= ", "
				ss+= o["ellapsed"] 
				ss+= ", "
				ss+= str(o["DT"]) 
				ss+= ", "
				ss+= str(o["FT"]) 
				ss+= "\n"	
			except Exception as e:
				pass	
		output = make_response(ss)
		output.headers["Content-Disposition"] = "attachment; filename=exportPlus.csv"
		output.headers["Content-type"] = "text/csv"
		return output

