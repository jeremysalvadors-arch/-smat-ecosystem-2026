class Estacion {
  final int id;
  final String nombre;
  final String ubicacion;
  final int lectura; // <--- AGREGAMOS ESTO

  Estacion({
    required this.id, 
    required this.nombre, 
    required this.ubicacion,
    required this.lectura, // <--- TAMBIÉN AQUÍ
  });

  factory Estacion.fromJson(Map<String, dynamic> json) {
    return Estacion(
      id: json['id'],
      nombre: json['nombre'],
      ubicacion: json['ubicacion'],
      lectura: json['valor'] ?? 0,
    );
  }
}