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
  // Definimos la variable para el Future como pide el reto de Refresh
  late Future<List<Estacion>> futureEstaciones;

  @override
  void initState() {
    super.initState();
    // Inicializamos el future al cargar la página
    futureEstaciones = apiService.getEstaciones();
  }

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
            TextField(controller: nombreCtrl, decoration: const InputDecoration(labelText: "Nombre")),
            TextField(controller: ubicacionCtrl, decoration: const InputDecoration(labelText: "Ubicación")),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text("Cancelar")),
          ElevatedButton(
            onPressed: () async {
              bool ok = await apiService.editarEstacion(estacion.id, nombreCtrl.text, ubicacionCtrl.text);
              if (ok) {
                Navigator.pop(context);
                setState(() {
                  // Volvemos a disparar el Future para traer datos frescos
                  futureEstaciones = apiService.getEstaciones();
                });
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
              Navigator.pushAndRemoveUntil(
                context,
                MaterialPageRoute(builder: (context) => const LoginScreen()),
                (route) => false,
              );
            },
          )
        ],
      ),
      body: FutureBuilder<List<Estacion>>(
        future: futureEstaciones,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          } else if (snapshot.hasError) {
            // Aquí se mostrará el error del Try-Catch que agregaste al ApiService
            return Center(child: Text('${snapshot.error}'));
          } else if (!snapshot.hasData || snapshot.data!.isEmpty) {
            return const Center(child: Text("No hay datos"));
          }

          return RefreshIndicator(
            onRefresh: () async {
              setState(() {
                // Volvemos a disparar el Future para traer datos frescos
                futureEstaciones = apiService.getEstaciones();
              });
            },
            child: ListView.builder(
              itemCount: snapshot.data!.length,
              // physics asegura que siempre se pueda arrastrar aunque haya pocos items
              physics: const AlwaysScrollableScrollPhysics(), 
              itemBuilder: (context, index) {
                final estacion = snapshot.data![index];
                
                // Lógica de colores (Reto Fase Mobile)
                final Color colorAlerta = (estacion.lectura > 50) ? Colors.red : Colors.green;

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
                    await apiService.eliminarEstacion(estacion.id);
                  },
                  child: ListTile(
                    leading: Icon(Icons.sensors, color: colorAlerta),
                    title: Text(estacion.nombre),
                    subtitle: Text(estacion.ubicacion),
                    onTap: () => _mostrarDialogoEdicion(estacion),
                  ),
                );
              },
            ),
          );
        },
      ),
    );
  }
}