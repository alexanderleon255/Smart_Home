
# Raspberry Pi Hybrid Boot Architecture
## SD Card Safety Net + SSD Main System

Author: Alex Smart Home Project  
Date: 2026-03-07  
Purpose: Document a robust storage architecture for a Raspberry Pi smart‑home hub where the SD card acts as a recovery system and the SSD provides the main operating system and storage.

---

# 1. Overview

This configuration uses **two storage devices simultaneously**:

| Device | Role |
|------|------|
SD card | Bootloader + rescue operating system |
USB / NVMe SSD | Main operating system, data, models, databases |

The system normally runs entirely from the SSD, but if the SSD fails or is disconnected, the Raspberry Pi can still boot from the SD card into a **recovery environment**.

This design is ideal for:

- Smart‑home hubs
- Home servers
- AI orchestration nodes
- Systems running 24/7

---

# 2. Architecture Concept

Normal operation:

```
Raspberry Pi
   │
   ├── SD Card
   │      ├ bootloader
   │      └ minimal rescue OS
   │
   └── SSD
          ├ main Linux OS
          ├ AI models
          ├ telemetry storage
          ├ logs
          ├ databases
          └ swap
```

---

# 3. Boot Flow

### Step 1 – Boot ROM

The Raspberry Pi SoC contains a small boot ROM that starts the boot process.

```
Boot ROM
   ↓
Bootloader
```

### Step 2 – Bootloader (SD card)

The bootloader is stored on the **SD card**.

```
SD card
 └ /boot
```

### Step 3 – Kernel loads

The bootloader loads the Linux kernel.

```
kernel.img
```

### Step 4 – Root filesystem mounted

The kernel mounts the **root filesystem**.

Normally:

```
root = SSD
```

Fallback:

```
root = SD card
```

---

# 4. Normal Boot (SSD Present)

```
Boot ROM
   ↓
SD bootloader
   ↓
Kernel loads
   ↓
Root filesystem mounted from SSD
   ↓
System runs entirely from SSD
```

All runtime operations occur on the SSD:

- package installs
- logs
- model loading
- telemetry
- swap
- databases

---

# 5. Failure Boot (SSD Missing)

If the SSD cannot be mounted:

```
Boot ROM
   ↓
SD bootloader
   ↓
Kernel loads
   ↓
SSD not found
   ↓
Fallback root filesystem on SD
   ↓
Recovery system starts
```

This allows:

- repairing filesystem corruption
- replacing the SSD
- restoring backups
- debugging the system

---

# 6. Recommended Disk Layout

## SD Card

Small and stable system.

```
SD CARD
│
├ /boot
│   ├ firmware
│   ├ bootloader
│   └ kernel
│
└ /rescue-root
    ├ ssh
    ├ disk tools
    └ recovery scripts
```

Typical size:

```
8–16 GB
```

---

## SSD Layout

Primary system storage.

```
SSD
│
├ /
│   ├ home
│   ├ var
│   │   └ log
│   ├ opt
│   │   └ models
│   ├ data
│   │   ├ telemetry
│   │   ├ vector-db
│   │   └ backups
│   └ swapfile
```

Typical size:

```
1 TB SSD
```

---

# 7. Hub File Server Structure

Suggested structure for a smart‑home hub:

```
/data
│
├ models
│   ├ qwen
│   └ llama
│
├ telemetry
│
├ vector-db
│
├ camera
│   ├ clips
│   └ snapshots
│
├ logs
│
└ backups
```

This allows the hub to act as a lightweight file server for:

- AI models
- telemetry history
- camera footage
- system backups

---

# 8. Swap Configuration

SSD allows safe swap usage.

Example configuration:

```
CONF_SWAPSIZE=4096
```

or

```
CONF_SWAPSIZE=8192
```

This helps the system survive memory pressure from:

- LLM inference
- vector databases
- telemetry analysis

---

# 9. Advantages of Hybrid Boot

| Feature | Benefit |
|------|------|
SSD performance | Much faster than SD card |
SD rescue system | Safe recovery environment |
Write endurance | SSD handles heavy writes |
System reliability | Hub survives storage failures |
Debugging | Easy repair when filesystem breaks |

---

# 10. Disadvantages

| Issue | Impact |
|------|------|
Slightly more complex setup | One-time configuration |
Requires two storage devices | Small cost increase |

---

# 11. Typical Smart‑Home Hub Deployment

```
Raspberry Pi Hub
│
├ SD Card
│   └ Rescue OS
│
└ SSD
    ├ Home automation software
    ├ AI routing logic
    ├ local LLM (3B class)
    ├ telemetry storage
    ├ vector database
    └ swap
```

External compute node:

```
MacBook AI Node
 └ 7B+ models
```

---

# 12. Recommended Hardware

| Component | Recommendation |
|------|------|
Pi Board | Raspberry Pi 5 (8GB) |
SSD | 1 TB external SSD |
SD card | 16–32 GB |
Cooling | Active cooler |
Power | Official 27W PSU |

---

# 13. Summary

Hybrid boot provides a **best‑of‑both‑worlds architecture** for a Raspberry Pi smart‑home hub.

Normal operation:

```
System runs from SSD
```

Failure recovery:

```
System boots from SD card
```

This gives the system:

- high performance
- safe recovery
- better reliability
- easier maintenance
