import 'package:flutter/material.dart';
import '../services/auth_service.dart';
import '../services/api_service.dart';
import '../models/estacion.dart';
import 'login_screen.dart';

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  final ApiService apiService = ApiService();

  // --- PASO 3: DIÁLOGO DE EDICIÓN ---
  void _mostrarDialogoEdicion(Estacion estacion) {
    final nombreCtrl = TextEditingController(text: estacion.nombre);
    final ubicacionCtrl = TextEditingController(text: estacion.ubicacion);

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text("Editar Estación"),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: nombreCtrl,
              decoration: const InputDecoration(labelText: "Nombre"),
            ),
            TextField(
              controller: ubicacionCtrl,
              decoration: const InputDecoration(labelText: "Ubicación"),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text("Cancelar"),
          ),
          ElevatedButton(
            onPressed: () async {
              bool ok = await apiService.editarEstacion(
                estacion.id,
                nombreCtrl.text,
                ubicacionCtrl.text,
              );
              if (ok) {
                if (mounted) {
                  Navigator.pop(context);
                  setState(() {}); // Refrescar lista
                }
              }
            },
            child: const Text("Guardar"),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Estaciones SMAT'),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () async {
              await AuthService().logout();
              if (mounted) {
                Navigator.pushAndRemoveUntil(
                  context,
                  MaterialPageRoute(builder: (context) => const LoginScreen()),
                  (route) => false,
                );
              }
            },
          )
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () async {
          setState(() {}); // Recarga el FutureBuilder
        },
        child: FutureBuilder<List<Estacion>>(
          future: apiService.getEstaciones(),
          builder: (context, snapshot) {
            if (snapshot.connectionState == ConnectionState.waiting) {
              return const Center(child: CircularProgressIndicator());
            } else if (snapshot.hasError) {
              return Center(child: Text('Error: ${snapshot.error}'));
            } else if (!snapshot.hasData || snapshot.data!.isEmpty) {
              return const Center(child: Text('No hay estaciones.'));
            }

            final estaciones = snapshot.data!;

            return ListView.builder(
              itemCount: estaciones.length,
              physics: const AlwaysScrollableScrollPhysics(),
              itemBuilder: (context, index) {
                final estacion = estaciones[index];

                final Color colorAlerta = (estacion.valor > 50) 
                    ? Colors.red 
                    : Colors.green;

                // GESTIÓN DE INTERFAZ: Swipe-to-Dismiss
                return Dismissible(
                  key: Key(estacion.id.toString()),
                  direction: DismissDirection.endToStart,
                  background: Container(
                    color: Colors.red,
                    alignment: Alignment.centerRight,
                    padding: const EdgeInsets.only(right: 20),
                    child: const Icon(Icons.delete, color: Colors.white),
                  ),
                  onDismissed: (direction) async {
                    bool ok = await apiService.eliminarEstacion(estacion.id);
                    if (ok) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(content: Text("${estacion.nombre} eliminada")),
                      );
                    }
                  },
                  child: ListTile(
                    leading: Icon(
                      Icons.sensors, 
                      color: colorAlerta,
                    ),
                    title: Text(estacion.nombre),
                    subtitle: Text("${estacion.ubicacion} • Valor: ${estacion.lectura}"),
                    onTap: () => _mostrarDialogoEdicion(estacion),
                  ),
                );
              },
            );
          },
        ),
      ),
    );
  }
}