from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timedelta

db = SQLAlchemy()

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(20), nullable=False)  # 'usuario', 'aprobador', 'admin'
    dias_vacaciones = db.Column(db.Integer, default=25)
    fecha_alta = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    fichajes = db.relationship('Fichaje', backref='usuario', lazy=True, cascade='all, delete-orphan')
    
    solicitudes_vacaciones = db.relationship(
        'SolicitudVacaciones', 
        foreign_keys='SolicitudVacaciones.usuario_id',  # Especifica qué FK usar
        backref='usuario', 
        lazy=True, 
        cascade='all, delete-orphan'
    )

    solicitudes_bajas = db.relationship(
        'SolicitudBaja',
        foreign_keys='SolicitudBaja.usuario_id',
        back_populates='usuario', # back_populates en lugar de backref
        lazy=True,
        cascade='all, delete-orphan'
    )
    
    # Relaciones de aprobadores
    aprobadores = db.relationship('Aprobador', foreign_keys='Aprobador.usuario_id', 
                                 backref='usuario_rel', lazy=True, cascade='all, delete-orphan')
    usuarios_a_cargo = db.relationship('Aprobador', foreign_keys='Aprobador.aprobador_id',
                                      backref='aprobador_rel', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Usuario {self.nombre}>'
    
    def dias_vacaciones_disponibles(self):
        """Calcula los días de vacaciones disponibles"""
        # Esta función no se modifica, por lo que las bajas no afectan
        dias_usados = sum([s.dias_solicitados for s in self.solicitudes_vacaciones if s.estado == 'aprobada'])
        return self.dias_vacaciones - dias_usados


class Fichaje(db.Model):
    __tablename__ = 'fichajes'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    hora_entrada = db.Column(db.Time, nullable=False)
    hora_salida = db.Column(db.Time, nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    editado = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<Fichaje {self.fecha} - {self.usuario.nombre}>'
    
    def horas_trabajadas(self):
        """Calcula las horas trabajadas en este fichaje"""
        entrada = datetime.combine(self.fecha, self.hora_entrada)
        salida = datetime.combine(self.fecha, self.hora_salida)
        
        # Si la salida es menor que la entrada, asumimos que es del día siguiente
        if salida < entrada:
            salida += timedelta(days=1)
        
        diferencia = salida - entrada
        return diferencia.total_seconds() / 3600  # Convertir a horas


class FichajeLog(db.Model):
    __tablename__ = 'fichajes_log'
    
    id = db.Column(db.Integer, primary_key=True)
    fichaje_id = db.Column(db.Integer, db.ForeignKey('fichajes.id'), nullable=False)
    editor_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    fecha_cambio = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Valores antiguos
    anterior_entrada = db.Column(db.Time)
    anterior_salida = db.Column(db.Time)
    anterior_pausa = db.Column(db.Integer) # En minutos
    
    motivo = db.Column(db.Text)
    
    # Relaciones
    fichaje = db.relationship('Fichaje', backref=db.backref('logs', lazy=True))
    editor = db.relationship('Usuario', foreign_keys=[editor_id])
    
    def __repr__(self):
        return f'<FichajeLog {self.id} - Fichaje {self.fichaje_id}>'


class SolicitudVacaciones(db.Model):
    __tablename__ = 'solicitudes_vacaciones'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date, nullable=False)
    dias_solicitados = db.Column(db.Integer, nullable=False)
    motivo = db.Column(db.Text)
    estado = db.Column(db.String(20), nullable=False)  # 'pendiente', 'aprobada', 'rechazada'
    fecha_solicitud = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_respuesta = db.Column(db.DateTime)
    aprobador_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    comentarios = db.Column(db.Text)
    
    google_event_id = db.Column(db.String(255))
    
    aprobador = db.relationship('Usuario', foreign_keys=[aprobador_id])
    
    def __repr__(self):
        return f'<SolicitudVacaciones {self.usuario.nombre} - {self.fecha_inicio}>'


class SolicitudBaja(db.Model):
    __tablename__ = 'solicitudes_bajas'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date, nullable=False)
    
    # Mantenemos los días laborables por consistencia
    dias_solicitados = db.Column(db.Integer, nullable=False)
    motivo = db.Column(db.Text, nullable=False) # Motivo obligatorio
    estado = db.Column(db.String(20), nullable=False)  # 'pendiente', 'aprobada', 'rechazada'
    fecha_solicitud = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_respuesta = db.Column(db.DateTime)
    aprobador_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    comentarios = db.Column(db.Text)

    google_event_id = db.Column(db.String(255))
    
    # Relaciones
    aprobador = db.relationship('Usuario', foreign_keys=[aprobador_id])
    usuario = db.relationship('Usuario', foreign_keys=[usuario_id], back_populates='solicitudes_bajas')
    
    def __repr__(self):
        return f'<SolicitudBaja {self.usuario.nombre} - {self.fecha_inicio}>'


class Aprobador(db.Model):
    __tablename__ = 'aprobadores'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    aprobador_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    fecha_asignacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones adicionales para acceder a los objetos Usuario
    usuario = db.relationship('Usuario', foreign_keys=[usuario_id], overlaps='usuario_rel,aprobadores')
    aprobador = db.relationship('Usuario', foreign_keys=[aprobador_id], overlaps='aprobador_rel,usuarios_a_cargo')
    
    def __repr__(self):
        return f'<Aprobador {self.aprobador.nombre} aprueba a {self.usuario.nombre}>'


class Festivo(db.Model):
    __tablename__ = 'festivos'
    
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.Date, nullable=False, unique=True)
    descripcion = db.Column(db.String(200), nullable=False)
    
    def __repr__(self):
        return f'<Festivo {self.fecha} - {self.descripcion}>'