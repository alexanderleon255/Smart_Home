# Smart Home Maximum Push Architecture – Rev-3 Implementation Blueprint

Author: Alex Smart Home Project  
Date: 2026-03-07  
Purpose: Turn the Rev-2 architecture into a concrete build blueprint for a Raspberry-Pi-centered smart home hub with a heavier MacBook AI sidecar.

---

## 1. Executive Summary

This document defines the practical implementation blueprint for a local-first smart home system built around:

- **Raspberry Pi 5 hub** as the always-on control node
- **MacBook Air M1** as the heavier AI / LLM node
- **MQTT event bus** as the system backbone
- **Dockerized services** for isolation and maintainability
- **Home Assistant** as the main orchestration and dashboard platform
- **Node-RED** as the automation workflow layer
- **Vector memory + telemetry storage** for semantic recall and pattern analysis
- **Camera / sensor nodes** as distributed input devices

The design goal is not just “home automation,” but a **persistent home intelligence stack** that can observe, remember, reason, and act.

---

## 2. Design Priorities

### 2.1 Primary priorities
1. **Local-first operation**
2. **Always-on reliability**
3. **Modular services**
4. **Graceful degradation**
5. **Security by default**
6. **Scalable architecture**

### 2.2 Functional priorities
1. Stable hub and dashboard
2. Sensor / actuator integration
3. Voice / assistant pipeline
4. Retrieval and semantic memory
5. Prediction / anomaly detection
6. Higher autonomy over time

---

## 3. Recommended Hardware Stack

## 3.1 Hub node
Recommended baseline:

- **Raspberry Pi 5, 8 GB RAM**
- **Official active cooler**
- **Official or equivalent 5V 5A PSU**
- **NVMe HAT**
- **512 GB or 1 TB NVMe SSD**
- Optional: touchscreen or kiosk display

### Why this matters
The Pi’s RAM cannot be upgraded, so the real performance strategy is:

- fast NVMe storage
- swap on SSD
- zram compressed RAM
- good thermal control
- careful service separation

## 3.2 AI sidecar node
Recommended:

- **MacBook Air M1, 8 GB RAM**
- **Ollama** running local models
- Optional future upgrade: desktop / mini-PC inference node

Role:

- LLM inference
- embedding generation
- tool-selection logic
- summarization / reasoning jobs
- heavy classification tasks

## 3.3 Camera / edge nodes
Possible nodes:

- **ESP32-CAM** for cheap detection/event snapshots
- **Pi Zero 2 W** for more capable camera processing
- Additional microcontrollers for simple I/O sensing

## 3.4 Core networking
Recommended:

- solid home router
- stable 2.4 GHz coverage for IoT
- strong 5 GHz / wired backhaul for core nodes
- DHCP reservations for critical devices

---

## 4. System Roles

| Node | Role | Notes |
|---|---|---|
| Pi Hub | always-on home brain | dashboards, automation, service bus |
| MacBook AI Node | heavy inference | Ollama, embeddings, advanced reasoning |
| Camera Nodes | vision edges | motion events, snapshots, short clips |
| IoT Devices | actuators + sensors | plugs, thermostats, switches, meters |
| User Devices | UI endpoints | iPhone, iPad, desktop, kiosk |

---

## 5. High-Level Architecture

```text
[User]
   |
   v
[Voice / Dashboard / Mobile UI]
   |
   v
[Pi Hub]
   |-----------------------------|
   |                             |
   v                             v
[Home Assistant]            [Node-RED]
   |                             |
   |                             v
   |                        [MQTT Broker]
   |                             |
   |-------------------|---------|-------------------|
   |                   |                             |
   v                   v                             v
[InfluxDB]      [Vector Memory]                [Device / Sensor Topics]
   |                   |                             |
   |                   v                             v
   |              [AI Query Layer]            [Cameras / Sensors / Actuators]
   |                   |
   |                   v
   |             [MacBook AI Node]
   |                   |
   |                   v
   |              [Ollama + Tools]
   |
   v
[Grafana / HA Dashboard / Alerts]
```

---

## 6. Storage and Memory Strategy

## 6.1 What can and cannot be upgraded
- **RAM:** cannot be physically upgraded
- **Storage:** can and should be upgraded
- **Usable memory:** can be improved with zram and swap

## 6.2 Recommended storage plan
- Boot and primary data on **NVMe SSD**
- Keep SD card only as fallback / recovery if desired
- Put databases, logs, clips, embeddings, and cache on SSD

## 6.3 Recommended memory plan
- Enable **zram**
- Configure **4–8 GB swap** on NVMe
- Limit container memory footprints where useful
- Keep only critical services permanently active

## 6.4 Result
This does not turn 8 GB into true physical 16 GB RAM, but it makes the system far more capable and less fragile under burst loads.

---

## 7. Docker Container Stack

The Pi should run services in containers where practical. This gives isolation, cleaner upgrades, and more predictable recovery.

## 7.1 Core stack
Recommended first-wave containers:

| Container | Purpose | Priority |
|---|---|---|
| mosquitto | MQTT broker | critical |
| nodered | automation logic | critical |
| homeassistant | automation platform / dashboard | critical |
| influxdb | time-series telemetry storage | high |
| grafana | telemetry dashboards | high |
| whisper / speech helper optional | local speech tooling | medium |
| vector DB (Qdrant or Chroma) | semantic memory | high |
| nginx / caddy optional | reverse proxy | medium |
| frigate or lighter camera service | camera event handling | medium-high |
| pihole optional | network filtering | optional |

## 7.2 Container philosophy
Separate services by function:

- control plane
- telemetry plane
- AI / memory plane
- camera plane
- optional network services

Do **not** start with everything at once. Build in layers.

---

## 8. Suggested Directory Layout

```text
/srv/smart-home/
├── compose/
│   ├── core/
│   ├── telemetry/
│   ├── ai/
│   ├── camera/
│   └── optional/
├── configs/
│   ├── mosquitto/
│   ├── nodered/
│   ├── homeassistant/
│   ├── grafana/
│   ├── influxdb/
│   ├── qdrant/
│   └── proxy/
├── data/
│   ├── influxdb/
│   ├── grafana/
│   ├── qdrant/
│   ├── homeassistant/
│   ├── nodered/
│   ├── mqtt/
│   ├── camera/
│   └── logs/
├── scripts/
├── backups/
└── docs/
```

This keeps persistent data, configs, and deployment files cleanly separated.

---

## 9. Home Assistant Role

Home Assistant should serve as:

- primary dashboard
- device/entity registry
- automation integration layer
- mobile notification source
- kiosk display backend

### Best uses
- integrating smart plugs, thermostats, weather, calendars, dashboards
- exposing entity states to the rest of the stack
- central place for user-visible automation state

### Avoid
Do not bury all complex logic directly in Home Assistant automations if Node-RED can manage it more cleanly.

---

## 10. Node-RED Role

Node-RED should serve as:

- event routing layer
- automation brain for multi-step logic
- protocol translator
- AI tool invocation orchestrator
- safety / gating logic executor

### Best uses
- “if X then check Y and maybe do Z”
- orchestrating camera alerts
- enriching raw sensor events
- combining weather + time + occupancy + device states
- calling the AI node only when needed

---

## 11. MQTT Topic Structure

MQTT is the message spine of the system. Keep the topic schema predictable.

## 11.1 Topic design principles
- use a small number of consistent levels
- include site / zone / device / metric
- keep commands separate from state
- define retained vs non-retained intentionally

## 11.2 Suggested topic schema

```text
home/<zone>/<device>/state
home/<zone>/<device>/command
home/<zone>/<device>/event
home/<zone>/<device>/telemetry/<metric>
home/system/<service>/status
home/system/<service>/event
home/assistant/request
home/assistant/response
home/camera/<node>/motion
home/camera/<node>/snapshot
home/camera/<node>/clip
```

## 11.3 Examples

```text
home/living_room/thermostat/state
home/garage/door/event
home/office/air_sensor/telemetry/co2
home/system/mqtt/status
home/assistant/request
home/camera/front_door/motion
```

---

## 12. Telemetry Architecture

## 12.1 Data classes
Telemetry should be separated into categories:

- environmental
- occupancy / presence
- power / energy
- device health
- network health
- camera events
- external context

## 12.2 Example telemetry sources
- temperature
- humidity
- CO2 / air quality
- smart plug wattage
- door/window state
- motion state
- router latency / uptime
- weather and forecast
- commute time
- service health

## 12.3 Flow
```text
Sensor / API
   -> MQTT
   -> Node-RED normalization
   -> InfluxDB
   -> dashboard + alerting
   -> semantic summarization
   -> vector memory
```

---

## 13. Vector Memory Schema

This is where the system starts to become more than automation.

## 13.1 Purpose
Store semantically searchable home knowledge such as:

- event summaries
- automation actions
- explanations
- patterns
- failures
- user preferences
- interpreted sensor history

## 13.2 Recommended stores
- **Qdrant** if you want a stronger, more scalable vector DB
- **Chroma** if you want a lighter entry point

## 13.3 Suggested memory record types

### A. Event memory
Examples:
- “Front door opened at 6:11 PM.”
- “HVAC turned on because indoor temp dropped below target.”

Fields:
- timestamp
- category
- source
- zone
- summary
- raw references
- embedding

### B. Daily summary memory
Examples:
- “Office was occupied from 8:02 AM to 5:35 PM.”
- “Power usage was unusually high overnight.”

Fields:
- date
- summary
- involved devices
- anomalies
- embedding

### C. Preference memory
Examples:
- “User prefers bedroom to cool before sleep.”
- “Commute widget should be visible on weekday mornings.”

Fields:
- preference class
- statement
- confidence
- last confirmed
- embedding

### D. Failure / troubleshooting memory
Examples:
- “Camera node dropped off Wi-Fi at 2:13 AM.”
- “MQTT broker restarted after memory pressure.”

Fields:
- service
- failure type
- context
- resolution
- recurrence count
- embedding

---

## 14. AI Tool-Calling Layer

The AI node should not directly “do anything it wants.” It should reason through tools.

## 14.1 Tool categories
- read-only informational tools
- home-state query tools
- command / actuation tools
- memory tools
- internet tools
- safety / confirmation gates

## 14.2 Suggested tool inventory

| Tool | Role |
|---|---|
| get_weather | current conditions + forecast |
| get_traffic_eta | commute estimate |
| get_calendar_events | near-term schedule |
| get_home_state | entity states and summaries |
| get_camera_events | recent motion / detections |
| query_telemetry | numeric history lookups |
| query_home_memory | semantic recall |
| control_device | issue a device command |
| run_scene | trigger a named scene |
| search_web | external search when needed |
| summarize_day | daily digest generation |
| diagnose_service | service health analysis |

## 14.3 Suggested JSON tool schema concept

```json
{
  "tool": "control_device",
  "arguments": {
    "entity_id": "light.office_lamp",
    "action": "turn_on",
    "parameters": {
      "brightness": 180
    }
  }
}
```

## 14.4 Safety gating
Potential actuation classes:

- **Safe autonomous:** read queries, dashboards, summaries
- **Low-risk autonomous:** lights, media, notifications
- **Guarded:** locks, HVAC extremes, alarms
- **Never autonomous without explicit approval:** garage door, security disarm, destructive actions

---

## 15. Voice Assistant Pipeline

## 15.1 Basic flow
```text
Wake / Trigger
  -> speech capture
  -> speech-to-text
  -> intent / reasoning
  -> tool calling
  -> response generation
  -> optional text-to-speech
```

## 15.2 Practical role split
Pi handles:
- microphone / audio capture
- trigger handling
- UI feedback
- dispatch to AI node

MacBook handles:
- heavier LLM reasoning
- summarization
- deeper tool orchestration
- embedding generation

## 15.3 Degraded mode
If the MacBook AI node is unavailable:

- Pi still runs automations
- dashboards still work
- prebuilt rule automations continue
- assistant falls back to deterministic commands or reduced feature mode

That degraded-mode behavior is extremely important.

---

## 16. Dashboard / Kiosk Blueprint

The Pi kiosk display should show useful information at a glance.

## 16.1 Primary dashboard zones
1. Time / date
2. Weather
3. Traffic / commute
4. Calendar
5. Cameras
6. Critical home states
7. Active alerts
8. AI summary card

## 16.2 Suggested dashboard pages
- **Home overview**
- **Security / cameras**
- **Environment / HVAC**
- **Energy / power**
- **Service health**
- **AI assistant / memory**

## 16.3 Example morning dashboard
- current weather
- today’s forecast
- commute ETA
- next calendar event
- overnight alerts
- front door / garage state
- summary: “Nothing abnormal overnight”

---

## 17. Camera Architecture

## 17.1 Minimum viable camera model
For each camera node:

- capture motion trigger
- snapshot or short clip
- publish metadata to MQTT
- optionally upload file reference to Pi

## 17.2 Event model
Camera node publishes:
- timestamp
- node ID
- detection type
- confidence
- storage path
- preview image or link

## 17.3 Processing path
```text
Camera node
  -> motion event
  -> MQTT
  -> Node-RED / camera service
  -> store clip / index metadata
  -> send alert if needed
  -> summarize to vector memory
```

## 17.4 AI uses
- explain what happened overnight
- search for repeated motion patterns
- detect false-positive periods
- build incident summaries

---

## 18. External Data Integrations

Your system becomes much more useful when it mixes internal state with external context.

## 18.1 High-value integrations
- weather
- traffic / commute
- calendar
- market / stock widgets if desired
- news headlines if desired

## 18.2 Why this matters
The assistant becomes more than a home switchboard. It becomes a context-aware dashboard and reasoning system.

Example:
“Should I leave early?”
can combine:
- weather
- traffic
- calendar
- known user preferences

---

## 19. Reliability and Graceful Recovery

## 19.1 Core principle
The system must remain useful even when one layer fails.

## 19.2 Failure cases and expected behavior

### MacBook AI offline
- automations continue
- dashboards continue
- semantic memory queries unavailable or reduced
- Pi surfaces “AI node unavailable”

### MQTT broker restarts
- devices reconnect
- retained states rehydrate
- alerts sent if downtime exceeds threshold

### InfluxDB offline
- real-time automation continues
- telemetry history temporarily unavailable
- buffering or delayed writes if implemented

### Camera node offline
- service health alert
- other systems continue normally

### Internet outage
- local automations continue
- external widgets fail gracefully
- assistant declares data may be stale

---

## 20. Security Model

## 20.1 Security priorities
1. keep dangerous controls gated
2. minimize open ports
3. require authentication on management interfaces
4. prefer VPN over public exposure
5. log critical actions

## 20.2 Practical controls
- Tailscale for remote access
- SSH keys only
- disable default passwords
- firewall rules
- container network segmentation where appropriate
- backup encryption where useful
- per-service credentials
- audit logs for command actions

## 20.3 Critical command classes
Extra caution for:
- door / lock / garage controls
- alarm disarming
- destructive power relays
- anything safety-related

---

## 21. Backup and Recovery Plan

## 21.1 What to back up
- Home Assistant config
- Node-RED flows
- Docker compose files
- container configs
- vector memory metadata
- dashboards
- scripts
- service credentials references
- important camera indexes and event logs

## 21.2 Backup cadence
- daily config backup
- weekly full backup
- pre-upgrade snapshot
- export flows before major edits

## 21.3 Recovery priority order
1. network + SSH
2. MQTT broker
3. Home Assistant
4. Node-RED
5. telemetry DB
6. AI / vector services
7. optional services

---

## 22. Phased Build Plan

## Phase 0 – Foundation
Goal: stable Pi platform

- Pi 5 assembled
- cooling installed
- NVMe installed
- Pi OS configured
- remote access working
- static / reserved IPs defined
- Docker installed

## Phase 1 – Core service spine
Goal: message bus + automation basics

- Mosquitto
- Home Assistant
- Node-RED
- first dashboards
- first device integrations

## Phase 2 – Telemetry and observability
Goal: measurable home data

- InfluxDB
- Grafana
- service health metrics
- basic historical charts

## Phase 3 – External context
Goal: useful daily dashboard

- weather integration
- traffic integration
- calendar integration
- morning status dashboard

## Phase 4 – AI sidecar integration
Goal: real assistant behavior

- Ollama on MacBook
- structured tool calling
- assistant request / response flow
- simple query handling

## Phase 5 – Semantic memory
Goal: searchable home recall

- vector DB
- event summarization
- daily digest indexing
- memory query tool

## Phase 6 – Cameras and richer events
Goal: vision-aware home intelligence

- camera event publishing
- snapshot indexing
- alert flows
- AI summaries of incidents

## Phase 7 – Predictive / anomaly layer
Goal: truly smart behavior

- unusual power detection
- device health prediction
- occupancy pattern analysis
- failure forecasting

---

## 23. Recommended First Implementation Order

To avoid overload, the most rational order is:

1. Pi 5 + NVMe + cooling
2. Docker baseline
3. Mosquitto
4. Home Assistant
5. Node-RED
6. one or two real sensors / devices
7. weather + calendar dashboard
8. InfluxDB + Grafana
9. MacBook Ollama integration
10. vector memory
11. camera events
12. anomaly detection

That sequence gives useful value early instead of delaying usefulness until the “full AI dream” is finished.

---

## 24. What “More Powerful” Really Means for the Pi

Since your original question was about making the Pi “more powerful,” here is the honest engineering answer:

### You cannot:
- upgrade the soldered RAM
- turn the Pi into a true high-end inference machine
- expect desktop-class AI performance from the Pi alone

### You can:
- dramatically improve I/O performance with NVMe
- increase usable memory with zram + swap
- keep the CPU at full speed with cooling
- move heavy reasoning to the MacBook
- make the whole system feel vastly more capable by architecture rather than raw hardware

So the right move is not “make the Pi a supercomputer.”  
It is: **make the Pi the persistent orchestrator of a larger distributed intelligence stack.**

---

## 25. Final Target State

In the fully realized version, your system can do things like:

- show live weather, traffic, calendar, and home state on a kiosk
- answer questions about what happened in the house
- explain why automations fired
- detect unusual patterns
- surface service issues early
- control devices through structured, gated AI tools
- continue functioning even when the AI sidecar is offline
- grow over time into a genuinely useful local intelligence platform

This is the practical path to a “Jarvis-like” home system without pretending the Pi itself must do everything.

---

## 26. Concise Bottom Line

**Best practical performance stack for your Pi hub:**

- Raspberry Pi 5 (8 GB)
- NVMe HAT
- 512 GB or 1 TB NVMe SSD
- active cooling
- zram enabled
- 4–8 GB SSD swap
- Dockerized core services
- MacBook Air M1 for Ollama / heavy AI
- MQTT + Home Assistant + Node-RED as the backbone
- InfluxDB + Grafana + vector DB layered on afterward

That setup gives you the highest leverage path: not just a faster Pi, but a **more capable system architecture**.
