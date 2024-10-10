create database poldocu;

use poldocu;

create table usuario(
	id_usuario int primary key auto_increment not null,
	area_oficina_id int,
	nombre varchar(500),
	apellido varchar(500),
	ci varchar(500),
	telefono varchar(500),
	edad varchar(500),
	imagen varchar(500),
	sexo varchar(500),
	email varchar(500),
	usuario varchar(500),
	password varchar(500),
	fecha datetime,
	fecha_modeficacion datetime,
	activo boolean default 1,
	admin boolean default 0,
	publico boolean default 0,
	encargado boolean default 0,
    codigo_sesion int default 0,
    fecha_codigo DATETIME
);

CREATE TABLE caso (
    id_caso INT PRIMARY KEY AUTO_INCREMENT NOT NULL,  -- ID autoincrementable como clave primaria
    usuario_id INT,  -- Clave foránea que referencia al usuario
    tipo_caso ENUM('Nuevo', 'Registrado') NOT NULL,  -- Enum para definir si es un caso nuevo o registrado
    nombre_caso VARCHAR(100) NOT NULL,  -- Nombre del caso
    descripcion TEXT,  -- Descripción del caso
    departamento ENUM('La Paz', 'Oruro', 'Potosi', 'Cochabamba', 'Chuquisaca', 'Tarija', 'Santa Cruz', 'Beni', 'Pando') NOT NULL,  -- Departamento seleccionado
    fecha DATETIME,  -- Fecha del caso
    f_dubitada VARCHAR(255),  -- Ruta de la firma dubitada
    f_indubitada VARCHAR(255),  -- Ruta de la firma indubitada
    f_procesada VARCHAR(255),
    activo boolean default 1,
    id_usuario_creado INT,
    id_usuario_modificado INT,
    fecha_creado DATETIME DEFAULT CURRENT_TIMESTAMP,
    fecha_modificado DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuario(id_usuario)  -- Clave foránea que referencia a la tabla usuario
);