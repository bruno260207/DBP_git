# SMAT Ecosystem

Proyecto académico basado en FastAPI y Flutter para el monitoreo de estaciones SMAT.

---

## Tecnologías usadas

- FastAPI
- Flutter
- SQLite
- JWT Authentication

---

# Backend

## Crear entorno virtual

```bash
python -m venv venv
```

## Activar entorno virtual (Windows)

```bash
.\venv\Scripts\activate
```

## Instalar dependencias

```bash
pip install -r requirements.txt
```

## Ejecutar servidor

```bash
cd backend
uvicorn app.main:app --reload
```

---

# Mobile

## Instalar dependencias Flutter

```bash
cd mobile
flutter pub get
```

## Ejecutar aplicación

```bash
flutter run
```

---

# Funcionalidades

- Login con JWT
- Persistencia de sesión
- CRUD de estaciones
- Pull-to-refresh
- Manejo de errores de red
- Logout
- Interoperabilidad FastAPI + Flutter