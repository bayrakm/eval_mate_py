# Update Server with Latest GitHub Code

## Step 1: Fetch and Pull Code

```bash
cd /home/zerone/evalmate
git fetch origin
git pull origin main
```

---

## Step 2: Install Dependencies

```bash
# Update Python dependencies
uv sync
```

---

## Step 3: Build Frontend (Next.js)

```bash
cd /home/zerone/evalmate/next_js
npm install
npm run build
```

---

## Step 4: Restart Applications via Systemd

### Restart evalmate API Server (Port 8100)

```bash
# Restart service (akan load kode terbaru)
sudo systemctl restart evalmate.service

# Verifikasi status
sudo systemctl status evalmate.service

# Lihat log untuk memastikan tidak ada error
sudo journalctl -u evalmate.service --lines 50
```

### Restart Frontend (PM2)

```bash
# Restart frontend
pm2 restart evalmate_frontend

# Verifikasi
pm2 status evalmate_frontend

# Lihat log
pm2 logs evalmate_frontend --lines 50
```

### Restart Other Services (jika perlu)

```bash
# Untuk app (port 8000) dan appstg (port 8060) - jika ada systemd service
sudo systemctl restart app.service      # jika ada
sudo systemctl restart appstg.service   # jika ada

# Atau manual restart (jika tidak menggunakan systemd)
sudo pkill -f "gunicorn.*8000"
sudo pkill -f "gunicorn.*8060"
sleep 2
# Lalu start manual sesuai kebutuhan
```

---

## Step 5: Verify

```bash
# Test API endpoints
curl http://localhost:8100/health
curl http://localhost:8100/docs

# Check service status
sudo systemctl status evalmate.service
pm2 status evalmate_frontend

# Check running processes
ps aux | grep -E 'uvicorn|npm' | grep -v grep

# View recent logs
sudo journalctl -u evalmate.service --lines 20
```

---

## Quick Update (All in One)

**Untuk update kode terbaru dan restart semua service:**

```bash
cd /home/zerone/evalmate && \
git fetch origin && \
git pull origin main && \
uv sync && \
cd next_js && \
npm install && \
npm run build && \
cd .. && \
sudo systemctl restart evalmate.service && \
pm2 restart evalmate_frontend && \
echo "✅ Update selesai! Services sudah di-restart."
```

**Verifikasi:**

```bash
sudo systemctl status evalmate.service
pm2 status evalmate_frontend
```

---

## Troubleshooting

### If Service Fails to Start

```bash
# Check service logs
sudo journalctl -u evalmate.service --lines 100

# Check if port 8100 is already in use
lsof -i :8100

# Force stop service
sudo systemctl stop evalmate.service

# Check service file location
systemctl show -p FragmentPath evalmate.service

# Restart service
sudo systemctl restart evalmate.service
```

### If Port is Already in Use

```bash
# Find process using port 8100
lsof -i :8100

# Kill process (gunakan PID dari output di atas)
kill -9 <PID>

# Or restart service
sudo systemctl restart evalmate.service
```

### If Dependency Error Occurs

```bash
# Reset Python environment
cd /home/zerone/evalmate
rm -rf .venv
uv sync

# Restart service
sudo systemctl restart evalmate.service
```

### If Frontend Not Updating

```bash
# Clear PM2 cache and restart
pm2 delete evalmate_frontend
pm2 start npm --name evalmate_frontend -- start

# Or simple restart
pm2 restart evalmate_frontend --force
```

### Check Everything is Running

```bash
# API Server
sudo systemctl status evalmate.service

# Frontend
pm2 status evalmate_frontend

# Test endpoints
curl http://localhost:8100/health
curl http://localhost:3000
```

---

**Done! ✅**
