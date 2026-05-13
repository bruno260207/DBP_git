import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../services/auth_service.dart';
import 'login_screen.dart';
import '../models/estacion.dart';
import 'add_estacion.dart';

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  late Future<List<Estacion>> futureEstaciones;
  final ApiService apiService = ApiService();

  @override
  void initState() {
    super.initState();
    futureEstaciones = apiService.fetchEstaciones();
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
                Navigator.pop(context);
                setState(() {
                  futureEstaciones = apiService.fetchEstaciones();
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
            icon: const Icon(Icons.add),
            onPressed: () async {

              final resultado = await Navigator.push(
                context,
                  MaterialPageRoute(
                    builder: (context) => AddEstacionScreen(),
                  ),
              );

              if (resultado == true) {
                setState(() {
                  futureEstaciones = apiService.fetchEstaciones();
              });
              }
            },
          ),
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
            return Center(child: Text(
              snapshot.error.toString(),
              textAlign: TextAlign.center,
              )
            );
          } else {
            final estaciones = snapshot.data!;
            return RefreshIndicator(
              onRefresh: () async {
                setState(() {
                  futureEstaciones = apiService.fetchEstaciones();
                });
              },
              child: ListView.builder(
                itemCount: estaciones.length,
                itemBuilder: (context, index) {
                  final est = estaciones[index];
                  return Dismissible(
                    key: Key(est.id.toString()),
                    direction: DismissDirection.endToStart,
                    background: Container(
                      color: Colors.red,
                      alignment: Alignment.centerRight,
                      padding: const EdgeInsets.only(right: 20),
                      child: const Icon(Icons.delete, color: Colors.white),
                    ),
                    onDismissed: (direction) async {
                      bool ok = await apiService.eliminarEstacion(est.id);
                      if (ok) {
                        ScaffoldMessenger.of(context).showSnackBar(
                          SnackBar(content: Text("${est.nombre} eliminada")),
                        );
                      }
                    },
                    child: FutureBuilder<Map<String, dynamic>>(
                      future: apiService.getRiesgo(est.id),
                      builder: (context, riesgoSnapshot) {
                        Color iconColor = Colors.grey;
                        if (riesgoSnapshot.hasData) {
                          final valor = riesgoSnapshot.data!['valor'];
                          if (valor > 50) {
                            iconColor = Colors.red;
                          } else {
                            iconColor = Colors.green;
                          }
                        }
                        return ListTile(
                          leading: Icon(Icons.satellite_alt, color: iconColor),
                          title: Text(est.nombre),
                          subtitle: Text(est.ubicacion),
                          onTap: () => _mostrarDialogoEdicion(est),
                        );
                      },
                    ),
                  );
                },
              ),
            );
          }
        },
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          setState(() {
            futureEstaciones = apiService.fetchEstaciones();
          });
        },
        child: const Icon(Icons.refresh),
      ),
    );
  }
}