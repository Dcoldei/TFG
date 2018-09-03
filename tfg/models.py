

from humbledb import Mongo, Document, Index, Embed
from flask_login import UserMixin
from humbledb.array import Array
import datetime

class Usuario(Document):
	config_database = 'trabajofingrado'
	config_collection = 'usuarios'

	nombre = 'nombre'
	password = 'password'
	role = 'role'
	email = 'email'
	facultad = 'facultad'
	titulacion = 'titulacion'
	archivos_subidos = 'archivos_subidos'
	descargas = 'descargas'
	activo = 'activo'
	foto = 'foto'
	activo_desde = 'activo_desde'
	comentarios = 'comentarios'
	posts = 'posts'
	no_leidos = 'no_leidos'
	horario = Embed('horario')

	def crearUsuario(self,filename,nombre,password,email,facultad,titulacion):
		self.foto = filename
		self.nombre = nombre
		self.password = password
		self.email = email
		self.role = "Usuario"
		self.facultad = facultad
		self.titulacion = titulacion
		self.archivos_subidos = 0
		self.activo = True
		self.descargas = 0
		d = datetime.date.today()
		self.activo_desde = d.isoformat()
		self.no_leidos = 0
		self.posts = 0
		self.comentarios = 0
		self.horario={}

class Buzon:
	def __init__(self, nombre):
		self.no_leidos = nombre

class Mensaje(Document):
	config_database = 'trabajofingrado'
	config_collection = 'buzon'

	asunto = 'asunto'
	id_usuario = 'id_usuario'
	autor = 'autor'
	autor_avatar = 'autor_avatar'
	body = "body"
	fecha = "fecha"
	estado = 'estado'
	denuncia = 'denuncia'

class Horario(Document):
	config_database = 'trabajofingrado'
	config_collection = 'horario'

	hora = 'hora'

   	l = 'l'
   	m= 'm'
   	x = 'x'
   	j= 'j'
   	v = 'v'

   	id_usuario = 'id_usuario'




class Post(Document):
	config_database = 'trabajofingrado'
	config_collection = 'posts'

	tema = 'tema'
	titulo = 'titulo'
	id_titulacion = 'id_titulacion'
	likes = 'likes'
	unlikes = "unlikes"
	autor = 'autor'
	autor_avatar = 'autor_avatar'
	body = "body"
	votos= "votos"
	fecha = "fecha"
	denuncia = 'denuncia'
	votos = "votos"

class Notas(Document):
	config_database = 'trabajofingrado'
	config_collection = 'notas'

	titulo = 'titulo'
	fecha = 'fecha'
	descripcion = 'descripcion'
	asunto = 'asunto'
	autor = 'autor'
	formato = "formato"



class Facultad(Document):
	config_database = 'trabajofingrado'
	config_collection = 'facultades'

	nombre = 'nombre'
	titulaciones = 'titulaciones'
	num_titul = 'num_titulaciones'
	cursos_x_titul = 'cursos_x_titul'


class Titulacion(Document):
	config_database = 'trabajofingrado'
	config_collection = 'titulaciones'


	nombre = 'nombre'
	id_facultad = 'id_facultad'
	num_cursos = 'cursos'
	asignaturas = 'asignaturas'





class Curso(Document):

	config_database = 'trabajofingrado'
	config_collection = 'cursos'

	numero = 'numero'
	id_titulacion = 'id_titulacion'
	num_asignaturas = 'num_asignaturas'
	asignaturas = 'asignaturas'


class Enlaces(Document):

	config_database = 'trabajofingrado'
	config_collection = 'enlaces'

	id_titulacion = 'id_titulacion'
	enlace = 'enlace'
	nombre = 'nombre'



class Asignatura(Document):

	config_database = 'trabajofingrado'
	config_collection = 'asignaturas'

	nombre = 'nombre'
	id_curso = 'id_curso'
	num_ficheros = 'num_ficheros'
	nombre_ficheros = 'nombre_ficheros'



class Archivo(Document):

	config_database = 'trabajofingrado'
	config_collection = 'archivos'

	nombre = 'nombre'
	id_asignatura = 'id_asignatura'
	asignatura = 'asignatura'
	valoracion = 'valoracion'
	valor_dec = "valor_dec"
	valor_entero = "valor_entero"
	sum_valor = 'sum_valor'
	autor = 'autor'
	num_descargas = 'num_descargas'
	num_votos = "numero_votos"
	autorizado = 'autorizado'
	tipo = 'tipo'
	fichero = 'fichero'
	num_comen = 'num_comen'
	id_titulacion = 'id_titulacion'
	#titulo = 'titulo'
	fecha = 'fecha'
	formato = 'formato'
	#descripcion = 'descripcion'

class Comentario(Document):

	config_database = 'trabajofingrado'
	config_collection = 'comentarios'

	titulo = 'titulo'
	id_archivo = 'id_archivo'
	likes = 'likes'
	unlike = "unlike"
	autor = 'autor'
	autor_avatar = 'autor_avatar'
	body = "body"
	fecha = "fecha"
	denuncia = 'denuncia'
	votos = 'votos'

class Comments(Array):
	config_database = 'trabajofingrado'
	config_collection = 'comentarios'
	config_padding = 1000 # Number of bytes to pad with
	config_max_size = 3  # Number of entries per page
	titulo = 'titulo'
	id_archivo = 'id_archivo'
	likes = 'likes'
	unlike = "unlike"
	autor = 'autor'
	body = "body"
	fecha = "fecha"



class User(UserMixin):
    def __init__(self,password, username,role):
        self.username = username
        self.role = role
        self._id = password

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self._id
    def get_urole(self):
            return self.urole