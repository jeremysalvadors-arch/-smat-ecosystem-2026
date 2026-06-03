class Estacion {
  final int id;
  final String nombre;
  final String ubicacion;
  final double lectura; // double, no int — el backend devuelve Float

  Estacion({
    required this.id,
    required this.nombre,
    required this.ubicacion,
    required this.lectura,
  });

  factory Estacion.fromJson(Map<String, dynamic> json) {
    return Estacion(
      id: json['id'],
      nombre: json['nombre'],
      ubicacion: json['ubicacion'],
      lectura: (json['valor'] ?? 0).toDouble(), // conversión segura a double
    );
  }
}