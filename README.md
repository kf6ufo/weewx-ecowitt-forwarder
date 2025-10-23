# weewx-ecowitt-forwarder

A lightweight Python bridge that lets Ecowitt weather consoles (HP2551, HP3501, WS2910, and similar models) upload "Customized Upload" data directly to WeeWX through the Interceptor driver. The forwarder emulates an Ecowitt GW1000/GW1100 gateway in software, so your console can stream data to WeeWX without relying on the cloud or extra hardware.

## 🌦️ Overview

`weewx-ecowitt-forwarder` listens for Ecowitt Customized Upload packets on `http://0.0.0.0:8080/data/report` and relays them to the WeeWX Interceptor extension on `http://127.0.0.1:46000/data/report` using the `ecowitt-client` protocol. This setup is ideal for Raspberry Pi users and anyone who wants a private, offline weather station.

## 🚀 Features

- Emulates an Ecowitt GW1000/GW1100 gateway entirely in software
- Sends incoming data straight to WeeWX via the Interceptor driver
- 100% local — no cloud services required
- Simple, dependency-free Python script (no Flask, Docker, or databases)
- Easy to run manually or under `systemd`
- Compatible with WeeWX 5.x+ and Python 3.7+

## 🧰 Requirements

- Python 3.7 or newer
- WeeWX installed and running
- WeeWX Interceptor extension installed
- Ecowitt console with the "Customized Upload" feature (e.g., HP2551, WS2910, etc.)

## ⚙️ Setup

### 1. Clone the repository

```bash
git clone https://github.com/kf6ufo/weewx-ecowitt-forwarder.git
cd weewx-ecowitt-forwarder
```

### 2. Configure WeeWX

Edit `/etc/weewx/weewx.conf` to use the Interceptor driver:

```
[Station]
station_type = Interceptor

[Interceptor]
driver = user.interceptor
device_type = ecowitt-client
port = 46000
```

Restart WeeWX and verify the logs:

```bash
sudo systemctl restart weewx
sudo journalctl -u weewx -f
```

You should see log entries similar to:

```
INFO user.interceptor: using 'yearlyrainin' for rain_total
INFO weewx.engine: Starting main packet loop.
```

### 3. Configure your Ecowitt console

On the console (HP2551, WS2910, etc.), set the Customized Upload destination:

| Setting              | Value                          |
| -------------------- | ------------------------------ |
| Server IP / Domain   | `http://<raspberrypi-ip>`      |
| Port                 | `8080`                         |
| Path                 | `/data/report/`                |
| Upload Interval      | `300` seconds (or as desired)  |

Save the configuration and reboot the console if necessary.

### 4. Run the forwarder manually

```bash
python3 ecowitt-forwarder.py
```

Expected console output:

```
Ecowitt relay listening on http://0.0.0.0:8080/data/report
Forwarding to Interceptor at: http://127.0.0.1:46000/data/report
[relay] Forward -> Interceptor 200
```

## 🔁 Optional: Run as a systemd service

Create `/etc/systemd/system/ecowitt-forwarder.service`:

```
[Unit]
Description=Ecowitt → WeeWX Interceptor Forwarder
After=network-online.target weewx.service
Wants=network-online.target

[Service]
Type=simple
User=username
WorkingDirectory=/home/jerry/dev/weewx-ecowitt-forwarder
ExecStart=/usr/bin/python3 /home/username/dev/weewx-ecowitt-forwarder/ecowitt-forwarder.py
Restart=always
RestartSec=2
NoNewPrivileges=true
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now ecowitt-forwarder
```

Follow the logs:

```bash
sudo journalctl -u ecowitt-forwarder -f
```

## 🌐 View your WeeWX dashboard

If you do not already have a web server hosting the WeeWX site:

```bash
sudo apt install -y lighttpd
sudo systemctl enable --now lighttpd
```

Then open the dashboard in a browser:

```
http://<raspberrypi-ip>/weewx/
```

## 🧪 Troubleshooting

- **No data in WeeWX?**
  - Confirm the console upload path is exactly `/data/report/`.
  - Check the forwarder log for `[relay] Forward -> Interceptor 200` messages.
  - Ensure `device_type = ecowitt-client` is present in `weewx.conf`.
- **Pressure or rain warnings?** These can appear on first startup before baseline data exists. They clear automatically as fresh data arrives.
- **Multiple forwarders running?** Make sure only one process is bound to port 8080:

  ```bash
  sudo ss -ltnp | grep :8080
  ```

## 📜 License

MIT License © 2025 KF6UFO. See [LICENSE](LICENSE) for full details.
