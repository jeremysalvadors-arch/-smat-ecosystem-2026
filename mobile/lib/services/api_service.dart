import 'dart:convert';
import 'package:http/http.dart' as http;
import 'auth_service.dart';
import '../models/estacion.dart';

class ApiService {
  // Usa 10.0.2.2 para emulador Android, 127.0.0.1 para web/desktop
  final String baseUrl = "http://127.0.0.1:8000";

  Future<List<Estacion>> fetchEstaciones() async {
    try {
      final response = await http
          .get(Uri.parse('$baseUrl/estaciones/'))
          .timeout(const Duration(seconds: 5));

      if (response.statusCode == 200) {
        List jsonResponse = json.decode(response.body);
        return jsonResponse.map((data) => Estacion.fromJson(data)).toList();
      } else {
        throw Exception('Error del servidor: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('No se pudo conectar con SMAT. ¿Está el servidor activo?');
    }
  }

  // Alias para home_page.dart que llama getEstaciones()
  Future<List<Estacion>> getEstaciones() => fetchEstaciones();

  Future<bool> crearEstacion(String nombre, String ubicacion) async {
    final token = await AuthService().getToken();
    final response = await http.post(
      Uri.parse('$baseUrl/estaciones/'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
      body: jsonEncode({'nombre': nombre, 'ubicacion': ubicacion}),
    );
    return response.statusCode == 201; // el backend devuelve 201, no 200
  }

  Future<bool> eliminarEstacion(int id) async {
    final token = await AuthService().getToken();
    final response = await http.delete(
      Uri.parse('$baseUrl/estaciones/$id'),
      headers: {'Authorization': 'Bearer $token'},
    );
    return response.statusCode == 200;
  }

  Future<bool> editarEstacion(int id, String nombre, String ubicacion) async {
    final token = await AuthService().getToken();
    final response = await http.put(
      Uri.parse('$baseUrl/estaciones/$id'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
      body: jsonEncode({'nombre': nombre, 'ubicacion': ubicacion}),
    );
    return response.statusCode == 200;
  }
}