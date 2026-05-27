import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import '../models/estacion.dart';
import '../services/api_service.dart';
import 'package:http/http.dart' as http;

class HistorialEstacionPage extends StatefulWidget {
  final Estacion estacion;
  const HistorialEstacionPage({super.key, required this.estacion});

  @override
  State<HistorialEstacionPage> createState() => _HistorialEstacionPageState();
}

class _HistorialEstacionPageState extends State<HistorialEstacionPage> {
  final ApiService apiService = ApiService();
  List<double> _lecturas = [];
  double _promedio = 0.0;
  bool _isLoading = true;
  String _errorMsg = '';
  Timer? _timer;

  // Realiza la petición al endpoint del reto en tu Backend
  Future<void> _cargarHistorial() async {
    try {
      // Nota: Si no tienes mapeado este método en tu ApiService, puedes consumirlo 
      // usando directamente http.get o agregando el método en tu clase service.
      final url = Uri.parse('http://127.0.0.1:8000/estaciones/${widget.estacion.id}/historial');
      
      // Suponiendo un consumo directo veloz para el laboratorio:
      final response = await http.get(url); 
      
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final List<dynamic> lecturasRaw=data['lecturas'] ?? [];
        setState(() {
          // Mapeamos los datos de la respuesta de FastAPI
          _lecturas = lecturasRaw.map((item) => double.parse(item.toString())).toList();
          _promedio = double.parse((data['promedio'] ?? 0.0).toString());
          _errorMsg = '';
          _isLoading = false;
        });
      } else {
        setState(() => _errorMsg = "Error de servidor: ${response.statusCode}");
      }
    } catch (e) {
        print("🚨 ERROR CRÍTICO EN FLUTTER: $e"); 
        setState(() {
          _errorMsg = "Conectando con la telemetría... (Error: $e)";
          _isLoading = false;
        });
      }
  }

  @override
  void initState() {
    super.initState();
    _cargarHistorial();

    // RETO SEMANA 9: Consulta automática cada 3 segundos para reaccionar al IoT
    _timer = Timer.periodic(const Duration(seconds: 3), (timer) {
      _cargarHistorial();
    });
  }

  @override
  void dispose() {
    _timer?.cancel(); // Apagamos el reloj al salir de la pantalla
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    // Monitoreamos el último valor que ingresó por el sensor emulado
    double ultimoValor = _lecturas.isNotEmpty ? _lecturas.last : 0.0;
    
    // LÓGICA DE ALERTA: Si supera los 70.0 cm el sistema se tiñe de rojo
    bool esCritico = ultimoValor > 70.0;
    Color colorAlerta = esCritico ? Colors.red.shade700 : Colors.teal.shade700;

    return Scaffold(
      appBar: AppBar(
        title: Text("Telemetría: ${widget.estacion.nombre}"),
        backgroundColor: colorAlerta,
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _errorMsg.isNotEmpty && _lecturas.isEmpty
              ? Center(child: Text(_errorMsg))
              : Column(
                  children: [
                    // Panel Superior Dinámico de Alerta Temprana
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(20),
                      color: colorAlerta.withOpacity(0.12),
                      child: Column(
                        children: [
                          Icon(
                            esCritico ? Icons.warning_amber_rounded : Icons.check_circle_outline,
                            color: colorAlerta,
                            size: 48,
                          ),
                          const SizedBox(height: 8),
                          Text(
                            esCritico ? "⚠️ ALERTA DE INUNDACIÓN" : "SITUACIÓN NORMAL",
                            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: colorAlerta),
                          ),
                          const SizedBox(height: 12),
                          Text("$ultimoValor cm", style: TextStyle(fontSize: 36, fontWeight: FontWeight.w900, color: colorAlerta)),
                          const Text("Nivel del Agua actual", style: TextStyle(color: Colors.grey)),
                          const Divider(height: 24),
                          Text("Promedio de lecturas: ${_promedio.toStringAsFixed(2)} cm", style: const TextStyle(fontWeight: FontWeight.bold)),
                        ],
                      ),
                    ),
                    
                    // Listado Histórico de registros de Edge Computing
                    Expanded(
                      child: _lecturas.isEmpty
                          ? const Center(child: Text("Sin telemetría. Encienda el script emisor."))
                          : ListView.builder(
                              itemCount: _lecturas.length,
                              itemBuilder: (context, index) {
                                final valorItem = _lecturas[index];
                                return ListTile(
                                  leading: Icon(Icons.water, color: valorItem > 70.0 ? Colors.red : Colors.teal),
                                  title: Text("Lectura N° ${index + 1}"),
                                  trailing: Text("$valorItem cm", style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                                );
                              },
                            ),
                    ),
                  ],
                ),
    );
  }
}