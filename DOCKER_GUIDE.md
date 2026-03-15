# 🐳 Cudy Hotspot Dockerization Guide

This document explains how the Cudy Hotspot application is containerized and provides a line-by-line breakdown of the configuration files.

## 1. What is Dockerization?
Dockerization is the process of wrapping an application and all its dependencies into a single "container." This ensures that the app runs exactly the same way on your computer, a server, or a Raspberry Pi, without needing to manually install Python or libraries.

---

## 2. Dockerfile Explained
The `Dockerfile` is the blueprint for creating the container image.

| Line | Instruction | Explanation |
| :--- | :--- | :--- |
| `FROM python:3.11-slim` | Base Image | Uses a lightweight, official version of Python 3.11 to keep the container small. |
| `WORKDIR /app` | Working Dir | Sets the folder inside the container where the app will live. |
| `RUN apt-get update...` | System Deps | Installs low-level tools needed for image processing (used by the QR code generator). |
| `COPY requirements.txt .` | Copy Deps | Copies only the library list first (this makes rebuilding faster if you only change code). |
| `RUN pip install...` | Install Libs | Installs Flask, Gunicorn, and other libraries inside the container. |
| `COPY . .` | Copy Code | Copies your actual Python code (`app.py`, `templates/`, etc.) into the container. |
| `RUN mkdir -p /app/data` | Create Folder | Creates a safe place for the SQLite database to live. |
| `EXPOSE 5000` | Open Port | Tells Docker that the app communicates on port 5000. |
| `ENV DATABASE_PATH=...` | Set Env | Tells the Python app to save the database in the `/app/data` folder. |
| `CMD ["gunicorn", ...]` | Start Command | The final command that runs the app using the production-ready Gunicorn server. |

---

## 3. Docker Compose Explained
`docker-compose.yml` is the orchestrator. It manages how the container runs and interacts with your computer.

| Key | Purpose |
| :--- | :--- |
| `build: .` | Tells Docker to build the image using the local `Dockerfile`. |
| `container_name: ...` | Gives a friendly name to the running container. |
| `restart: always` | Automatically starts the app if the server reboots or the app crashes. |
| `ports: "5000:5000"` | Connects your computer's port 5000 to the container's port 5000. |
| `env_file: .env` | Automatically loads your passwords and settings from your `.env` file. |
| `volumes:` | **Crucial:** Maps the database inside the container to a permanent storage area on your disk. Without this, you would lose all vouchers every time you restart the container! |

---

## 4. How to use it

### Build and Start
Run this command in the project root:
```bash
docker-compose up -d --build
```
*   `-d`: Runs it in the background (detached mode).
*   `--build`: Ensures it builds the latest version of your code.

### View Logs
To see what's happening inside the container:
```bash
docker logs -f cudy-hotspot
```

### Stop the App
```bash
docker-compose down
```

---
**Developed by Naboth Tech Solutions &copy; 2026**
