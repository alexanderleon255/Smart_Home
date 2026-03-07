# Smart Home AI Hub -- Maximum Push Architecture (Rev‑2)

Author: Alex Smart‑Home Project\
Purpose: Define the **maximum capability architecture** for a
Raspberry‑Pi‑centered smart home system using a MacBook AI node.

------------------------------------------------------------------------

# 1. Design Philosophy

Goals:

• Local‑first intelligence\
• Privacy preserving architecture\
• Modular distributed nodes\
• AI‑assisted reasoning over home telemetry\
• Persistent semantic memory

System roles:

  Node               Role
  ------------------ ----------------------------
  Raspberry Pi Hub   Always‑on automation brain
  MacBook M1         Heavy AI inference
  Camera Nodes       Vision sensors
  IoT Devices        Environmental control
  Router / Network   Communication backbone

------------------------------------------------------------------------

# 2. Core Hardware Architecture

## Hub Node

Raspberry Pi 5 (8GB)

Required upgrades:

• NVMe SSD (512GB--1TB)\
• Active cooling\
• Reliable 5V 5A power supply

Benefits:

• fast databases • large swap capacity • persistent telemetry storage

------------------------------------------------------------------------

# 3. Network Topology

Typical topology:

Router │ ├── Raspberry Pi Hub │ ├── MacBook AI Node │ ├── Camera Nodes │
├── IoT Devices │ └── User Devices

Remote access:

• Tailscale VPN\
• SSH\
• RealVNC

------------------------------------------------------------------------

# 4. Software Stack

Base OS:

Raspberry Pi OS (64‑bit)

Container system:

Docker

Core services:

  Service          Purpose
  ---------------- ----------------------
  Home Assistant   home automation
  Node‑RED         automation workflows
  MQTT             sensor messaging
  Pi‑hole          network filtering
  InfluxDB         telemetry storage
  Grafana          dashboards
  Vector DB        LLM memory layer

------------------------------------------------------------------------

# 5. AI Architecture

Heavy LLM inference runs on **MacBook M1** using Ollama.

Pi performs:

• tool orchestration\
• data aggregation\
• automation execution

Request flow:

User → Hub API → MacBook LLM → structured tool call → home automation
executed

------------------------------------------------------------------------

# 6. Tool Calling Layer

The AI assistant interacts with the home through structured tools.

Example tools:

  Tool                Function
  ------------------- -----------------
  get_weather         fetch forecast
  get_traffic         commute ETA
  control_light       toggle lights
  control_climate     HVAC control
  search_internet     external search
  query_home_memory   semantic recall

Example reasoning:

User: "Should I leave early today?"

AI actions:

1.  check weather\
2.  check traffic\
3.  check calendar\
4.  compute recommendation

------------------------------------------------------------------------

# 7. Internet Data Integrations

Useful APIs:

Weather: • OpenWeather

Traffic: • Google Maps API

Calendar: • Google Calendar

Stocks: • Yahoo Finance API

News: • RSS feeds

These provide **live widgets** for the hub dashboard.

------------------------------------------------------------------------

# 8. Vector Memory System

Vector databases store semantic knowledge.

Recommended:

• Chroma\
• Qdrant

Data stored:

• device states • automation history • camera events • sensor trends

Example query:

"Why did the heater turn on last night?"

AI retrieves relevant event logs and explains the cause.

------------------------------------------------------------------------

# 9. Telemetry Pipeline

Sensors produce continuous data streams.

Pipeline:

Sensors → MQTT → InfluxDB → Vector Memory → AI reasoning

Examples:

• power consumption • temperature • humidity • door open events • camera
detections

------------------------------------------------------------------------

# 10. Camera Node Architecture

Camera nodes can use:

• ESP32‑CAM • Raspberry Pi Zero

Functions:

• motion detection • short clip recording • event publishing

Pipeline:

Camera → motion event → MQTT → hub storage → AI alert

------------------------------------------------------------------------

# 11. Dashboard / Kiosk Display

Wall‑mounted display connected to Pi.

Dashboard content:

• weather • commute time • calendar • camera feeds • system alerts

Frameworks:

• Home Assistant dashboards • custom web dashboard

------------------------------------------------------------------------

# 12. Performance Enhancements

### ZRAM

Compress memory pages to increase usable RAM.

Typical effect:

8GB → \~12GB effective.

Install:

sudo apt install zram-tools

------------------------------------------------------------------------

### NVMe Swap

Recommended swap size:

4GB--8GB

Allows workloads larger than RAM.

------------------------------------------------------------------------

### RAM Disk

Temporary high‑speed storage:

mount -t tmpfs -o size=2G tmpfs /mnt/ramdisk

Useful for:

• embedding generation • temporary inference data

------------------------------------------------------------------------

# 13. Security Model

Principles:

• local network isolation • VPN remote access • minimal cloud dependency

Controls:

• firewall rules • API authentication • encrypted storage • secure SSH
keys

------------------------------------------------------------------------

# 14. Future Expansion

Possible upgrades:

• multiple Pi nodes • Kubernetes orchestration • distributed inference •
anomaly detection on telemetry • predictive home automation

Example:

AI detects unusual overnight power usage and alerts the user.

------------------------------------------------------------------------

# 15. Maximum Capability Vision

Fully realized system provides:

• autonomous home reasoning • persistent memory of events • predictive
automation • privacy‑preserving AI assistant

The Raspberry Pi becomes the **persistent intelligence layer** of the
home while larger compute nodes perform advanced reasoning.
