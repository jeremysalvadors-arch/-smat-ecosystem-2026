class Estacion {
  final int id;
  final String nombre;
  final String ubicacion;
<<<<<<< HEAD
  final int lectura; // <--- AGREGAMOS ESTO

  Estacion({
    required this.id, 
    required this.nombre, 
    required this.ubicacion,
    required this.lectura, // <--- TAMBIÉN AQUÍ
  });
=======

  Estacion({required this.id, required this.nombre, required this.ubicacion});
>>>>>>> 05846b20bbf23e3108ac5391bcbaf6405f02c8b3

  factory Estacion.fromJson(Map<String, dynamic> json) {
    return Estacion(
      id: json['id'],
      nombre: json['nombre'],
      ubicacion: json['ubicacion'],
<<<<<<< HEAD
      lectura: json['valor'] ?? 0,
    );
  }
}
=======
    );
  }
}
>>>>>>> 05846b20bbf23e3108ac5391bcbaf6405f02c8b3
