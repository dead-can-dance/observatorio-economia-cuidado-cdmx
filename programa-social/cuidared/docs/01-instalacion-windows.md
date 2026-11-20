# Instalación en Windows

## 1. Herramientas
1. **Git para Windows** (git-scm.com).
2. **Python 3.12** (python.org). Marca "Add python.exe to PATH" al instalar.
3. **Docker Desktop** con WSL 2 activado (docker.com).
4. **Visual Studio Code** con las extensiones Python, Dart y Flutter.
5. **Flutter SDK** y **Android Studio** (con Android SDK y un emulador). Sigue la guía oficial en docs.flutter.dev para Windows y comprueba con `flutter doctor`.

> iOS no se puede compilar desde Windows. Para iOS se usará un servicio de compilación en la nube (Paso 7).

## 2. Levantar el backend con Docker
```powershell
copy .env.example .env
docker compose up --build
```
Abre http://localhost:8000/health y http://localhost:8000/docs.

## 3. Ejecutar las pruebas del backend sin Docker
```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
pytest
```

## 4. Subir el proyecto a GitHub
```powershell
git init
git add .
git commit -m "Paso 1: estructura inicial del proyecto"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/cuidared.git
git push -u origin main
```
Antes, crea un repositorio vacío en github.com (sin README) y sustituye `TU_USUARIO`.
