# Smart Home Hardware BOM – Rev-5 (Architecture-Correct Hardware Layout)

Author: Alex Smart Home Project  
Date: 2026-03-07  
Purpose: Reorganize the smart-home hardware bill of materials into a system architecture that matches how the system will actually be built and deployed.

Approved vendors (priority order):
1. McMaster-Carr
2. Mouser
3. DigiKey
4. Amazon

Prices below are planning estimates in USD and should be treated as budgeting guidance rather than exact quotes.

---

## 1. Executive Summary

This revision reorganizes the system by **architecture role** instead of by generic part category.

That means the BOM is now grouped into:

- **Hub hardware**
- **Room nodes**
- **Camera nodes**
- **Sensor network**
- **Networking**
- **Compute / AI nodes**

This layout is closer to how you would actually stage and deploy the system in the real house.

---

## 2. System Architecture Overview

```text
                           [ User Devices ]
                     iPhone / iPad / Desktop / Kiosk
                                  |
                                  v
                           [ Home Network ]
                                  |
            -------------------------------------------------
            |                       |                       |
            v                       v                       v
        [Hub Hardware]         [Compute / AI Node]     [Networking]
            |                       |                       |
            |                       v                       |
            |                 Ollama / Tools /             |
            |                 Summaries / Memory           |
            |                                              
            v
    ---------------------
    |         |         |
    v         v         v
[Room Nodes] [Camera Nodes] [Sensor Network]
```

---

## 3. Hub Hardware

This is the always-on central control plane.

It should host:

- Home Assistant
- Node-RED
- MQTT broker
- dashboards
- telemetry routing
- device state coordination
- voice input/output
- local service health monitoring

### 3.1 Main hub board

| Item | Recommended | Alt 1 | Alt 2 |
|---|---|---|---|
| Main controller | Raspberry Pi 5 8GB – DigiKey – $80 | Raspberry Pi 5 8GB – Amazon – $95 | CanaKit Pi 5 kit – Amazon – $150 |

Recommended vendor link:
- DigiKey: https://www.digikey.com/en/products/detail/raspberry-pi/SC1432

### 3.2 Fast storage

#### NVMe HAT

| Item | Recommended | Alt 1 | Alt 2 |
|---|---|---|---|
| Pi 5 NVMe adapter | Pineberry Pi HatDrive – DigiKey – $45 | Pimoroni NVMe Base – Amazon – $40 | Waveshare NVMe HAT – Amazon – $30 |

Recommended vendor link:
- DigiKey: https://www.digikey.com/en/products/detail/pineberry-pi/hatdrive

#### NVMe SSD

| Item | Recommended | Alt 1 | Alt 2 |
|---|---|---|---|
| NVMe SSD | WD Blue SN570 1TB – Amazon – $65 | Samsung 980 1TB – Amazon – $80 | Crucial P3 1TB – Amazon – $60 |

Recommended vendor link:
- Amazon: https://www.amazon.com/dp/B09HKDQ1RN

### 3.3 Power and thermals

| Item | Recommended | Alt 1 | Alt 2 |
|---|---|---|---|
| PSU | Official Pi 27W PSU – DigiKey – $12 | Official PSU – Amazon – $15 | Anker USB-C PSU – Amazon – $30 |
| Cooling | Official Pi 5 Active Cooler – DigiKey – $5 | Official cooler – Amazon – $10 | Vilros cooler – Amazon – $12 |
| Boot media | SanDisk Extreme 64GB – Amazon – $15 | Samsung EVO Select – Amazon – $13 | Kingston Canvas Go – Amazon – $14 |
| Case | Official Pi 5 Case – DigiKey – $10 | Official case – Amazon – $12 | Aluminum case – Amazon – $25 |

### 3.4 Audio interface

#### Microphones

| Item | Recommended | Alt 1 | Alt 2 |
|---|---|---|---|
| Mic front-end | ReSpeaker 2-Mic HAT – DigiKey – $18 | ReSpeaker 4-Mic Array – DigiKey – $35 | USB mini microphone – Amazon – $12 |

Recommended vendor link:
- DigiKey: https://www.digikey.com/en/products/detail/seeed-technology-co-ltd/107990053

#### Speakers

| Item | Recommended | Alt 1 | Alt 2 |
|---|---|---|---|
| Speaker output | Pimoroni Speaker pHAT – DigiKey – $15 | Adafruit I2S amp + speaker – DigiKey – $20 | USB speaker – Amazon – $18 |

Recommended vendor link:
- DigiKey: https://www.digikey.com/en/products/detail/pimoroni-ltd/PIM213

### 3.5 Optional hub display

| Item | Recommended | Alt 1 | Alt 2 |
|---|---|---|---|
| Kiosk display | Official 7" Pi display – DigiKey – $70 | Official 7" display – Amazon – $80 | Waveshare 10" display – Amazon – $120 |

Recommended vendor link:
- DigiKey: https://www.digikey.com/en/products/detail/raspberry-pi/SC1220

### 3.6 Hub hardware subtotal

| Subsystem | Estimated Cost |
|---|---|
| Pi 5 board | $80 |
| NVMe HAT | $45 |
| NVMe SSD | $65 |
| PSU | $12 |
| Cooling | $5 |
| microSD | $15 |
| Case | $10 |
| Microphone | $18 |
| Speaker | $15 |
| Display | $70 |

**Estimated hub subtotal:** **$335** without display  
**Estimated hub subtotal:** **$405** with display

---

## 4. Room Nodes

Room nodes are optional satellite devices placed in individual rooms or zones.

Their job is to provide:

- room-level sensing
- room-level voice or button interfaces
- local display/status
- occupancy awareness
- simple automation edge logic

These should be lighter and cheaper than the main hub.

### 4.1 Typical room node roles

A room node might be:

- a small environmental monitor
- a bedside or office status panel
- a room microphone/speaker endpoint
- a button + display control station
- a lightweight assistant terminal

### 4.2 Suggested room-node hardware

| Item | Recommended | Alt 1 | Alt 2 |
|---|---|---|---|
| Small controller | Raspberry Pi Zero 2 W – DigiKey – $15 | ESP32 dev board – Mouser – $10 | ESP32 dev board – Amazon – $10 |
| Local display | Small SPI/I2C display – DigiKey – $15 | Mini HDMI display – Amazon – $35 | none | 
| Local mic | USB mini microphone – Amazon – $12 | ReSpeaker option if Pi-based – DigiKey – $18 | none |
| Local speaker | USB powered speaker – Amazon – $18 | small amplified speaker – DigiKey – $20 | none |
| Input | pushbuttons / encoder / touch buttons – DigiKey – $5–15 | | |

### 4.3 Recommended room-node patterns

#### Pattern A – Minimal room sensor node
- ESP32 dev board
- temp / humidity sensor
- PIR or occupancy input
- optional small display

Estimated cost: **$20–35**

#### Pattern B – Room assistant endpoint
- Pi Zero 2 W
- mini mic
- small speaker
- optional small display

Estimated cost: **$45–80**

#### Pattern C – Status/control panel
- ESP32 or Pi Zero 2 W
- small display
- buttons / rotary encoder
- LED indicators

Estimated cost: **$30–60**

### 4.4 When to use room nodes
Use these when you want:
- distributed interfaces
- per-room occupancy or environmental data
- room-specific audio interaction
- reduced wiring back to the hub

---

## 5. Camera Nodes

Camera nodes are separate from the hub because they have different placement, compute, storage, and reliability needs.

Their job is to provide:

- motion detection
- snapshots or clips
- event publishing
- occupancy/security context

### 5.1 Camera node classes

#### Class A – Cheap edge event node
- ESP32-CAM
- Wi-Fi connected
- publishes snapshots or events
- good for cheap experimentation

#### Class B – Better smart camera node
- Pi Zero 2 W + camera
- better software flexibility
- more robust clip handling
- better integration path

### 5.2 Camera hardware options

#### ESP32 camera nodes

| Item | Recommended | Alt 1 | Alt 2 |
|---|---|---|---|
| ESP32-CAM | Amazon 2-pack – $20 | ESP32-CAM dev kit – Amazon – $15 | ESP32-CAM – Mouser – $12 |

Recommended use:
- basic motion snapshots
- low-cost prototypes
- low criticality spaces

#### Pi camera nodes

| Item | Recommended | Alt 1 | Alt 2 |
|---|---|---|---|
| Camera processor | Pi Zero 2 W – DigiKey – $15 | Raspberry Pi 5 if high capability – DigiKey – $80 | |
| Camera module | Pi Camera Module 3 – DigiKey – $25 | Pi Camera Module 3 – Amazon – $30 | Arducam – Amazon – $35 |

### 5.3 Recommended deployment strategy

| Use Case | Recommended Node Type |
|---|---|
| Cheap testing / broad coverage | ESP32-CAM |
| Front door / important zones | Pi Zero 2 W + Camera Module 3 |
| Higher-end future node | Pi 5 + camera stack |

### 5.4 Camera-node cost estimate

| Camera Node Type | Estimated Cost |
|---|---|
| ESP32-CAM node | $10–20 each |
| Pi Zero 2 W + Camera 3 | $40–55 each |
| Pi 5 + Camera 3 | $105+ each |

---

## 6. Sensor Network

The sensor network is the distributed measurement layer of the house.

This should cover:

- temperature
- humidity
- air quality
- occupancy
- power
- contact sensors
- eventually water / leak / environmental alarms

### 6.1 Environmental sensors

#### Temperature / humidity

| Item | Recommended | Alt 1 | Alt 2 |
|---|---|---|---|
| Temp/humidity sensor | SHT31 breakout – DigiKey – $15 | BME280 – Amazon – $12 | DHT22 – Amazon – $8 |

Recommended use:
- SHT31 for better quality
- BME280 when pressure is useful
- DHT22 only for low-cost noncritical applications

#### Air quality / CO2

| Item | Recommended | Alt 1 | Alt 2 |
|---|---|---|---|
| VOC sensor | Sensirion SGP30 – DigiKey – $20 | CCS811 – Amazon – $15 | |
| CO2 sensor | MH-Z19 – Amazon – $30 | other NDIR modules – Amazon – $35+ | |

### 6.2 Occupancy and state sensors

Potential additions:
- PIR motion sensors
- reed switches for doors/windows
- beam-break sensors
- pressure mats
- contact switches

Suggested sourcing:
- DigiKey for discrete/prototyping parts
- Amazon for low-cost multipacks when acceptable

### 6.3 Power and energy sensing

| Item | Recommended | Alt 1 | Alt 2 |
|---|---|---|---|
| DC current/power sensing | INA219 – DigiKey – $10 | INA226 – DigiKey – $15 | |
| AC load observation | Smart plug with monitoring – Amazon – $20 | higher-end plug meter – Amazon – $25 | |

### 6.4 Sensor network topology

Recommended pattern:
- ESP32 nodes or room nodes gather local sensor inputs
- MQTT used as the common bus
- hub stores telemetry and summaries
- avoid running long analog lines when possible

### 6.5 Sensor network estimated cost

| Sensor Group | Estimated Cost |
|---|---|
| Temp/humidity node | $8–15 each |
| Air quality node | $15–30 each |
| CO2 node | $30–40 each |
| Power monitor node | $10–20 each |
| Door/window state node | $5–15 each |

---

## 7. Networking

This category covers the backbone that keeps the whole system reliable.

### 7.1 Networking goals

You want:
- stable Wi-Fi coverage
- strong LAN for core nodes
- reliable addressing
- easy remote access
- future scale for more endpoints

### 7.2 Router options

| Item | Recommended | Alt 1 | Alt 2 |
|---|---|---|---|
| Main router | TP-Link AX3000 – Amazon – $120 | ASUS AX5400 – Amazon – $180 | Netgear AX5400 – Amazon – $200 |

### 7.3 Practical networking notes

Recommended:
- reserve IPs for hub, AI node, cameras, printers, and major nodes
- keep 2.4 GHz available for IoT
- prefer wired connections for the hub and AI node when possible
- use Tailscale for remote access rather than exposing services publicly

### 7.4 Optional networking additions
You may eventually want:
- unmanaged switch
- PoE switch
- VLAN-capable router/switches
- UPS for the hub stack

These were not deeply priced in earlier revisions but are worth planning for.

### 7.5 Networking subtotal

| Subsystem | Estimated Cost |
|---|---|
| Main router | $120–200 |
| Small switch optional | $20–50 |
| UPS optional | $60–120 |

---

## 8. Compute / AI Nodes

These are not the always-on automation hub.  
They are the heavier reasoning, inference, summarization, and memory-processing layer.

### 8.1 Primary AI node

Recommended:
- MacBook Air M1 (already owned)
- Ollama
- local models
- embeddings / summaries / higher-level reasoning

This is the best immediate leverage because it avoids trying to force all heavy AI tasks onto the Pi.

### 8.2 Secondary future AI nodes
Possible future expansions:
- mini PC
- small x86 box
- used workstation
- additional Pi only for specialized services, not primary inference

### 8.3 Compute-node roles

| Role | Recommended Platform |
|---|---|
| Main automation/control | Pi 5 hub |
| Heavy LLM inference | MacBook Air M1 |
| Cheap room intelligence | ESP32 / Pi Zero 2 W |
| Camera edge node | ESP32-CAM or Pi Zero 2 W |
| Future stronger local AI | mini PC / desktop |

### 8.4 Why this matters
The Pi should be the **persistent orchestrator**, not the sole heavy thinker.

That architecture gives you:
- better responsiveness
- fewer crashes
- more practical scaling
- easier upgrades later

---

## 9. Recommended Deployment Packages

### 9.1 Package A – Minimal starter architecture
Includes:
- Hub hardware without display
- 1–2 simple room/sensor nodes
- existing MacBook as AI node

Estimated cost:
- hub without display: **$335**
- room/sensor additions: **$30–70**
- total starter deployment: **$365–405**

### 9.2 Package B – Voice-enabled home pilot
Includes:
- Hub hardware with display
- microphone + speaker
- 2 room nodes
- 1 camera node
- sensor network starter set

Estimated cost:
- hub with display: **$405**
- 2 room nodes: **$60–120**
- 1 camera node: **$15–55**
- starter sensors: **$40–80**

Estimated total:
**$520–660**

### 9.3 Package C – Broader house rollout
Includes:
- full hub
- 3–5 room nodes
- 2–4 camera nodes
- distributed sensor network
- better network backbone

Estimated total:
**~$750–1,400+** depending on node count and camera approach

---

## 10. Architecture-Correct Recommended Build

If the goal is the most rational near-term version of your system, the recommended structure is:

### Hub hardware
- Raspberry Pi 5 8GB
- NVMe HAT
- 1TB NVMe SSD
- Official PSU
- Official active cooler
- microSD
- official case
- ReSpeaker 2-Mic HAT
- Pimoroni Speaker pHAT
- optional 7" display

### Room nodes
- start with 1–2 ESP32-based or Pi Zero 2 W nodes
- use them for environmental sensing and local interfaces

### Camera nodes
- start with 1 cheap ESP32-CAM for experimentation
- use Pi Zero 2 W + Camera 3 for more important zones

### Sensor network
- SHT31/BME280 temp-humidity nodes
- one air-quality sensor where it matters
- one or two monitored power devices
- door/contact sensing where useful

### Networking
- decent router
- reserved IPs
- Tailscale
- wired hub if possible

### Compute / AI
- MacBook Air M1 as the heavy AI sidecar
- Pi stays the always-on orchestrator

---

## 11. Concise Bottom Line

This reorganization reflects the system the way it should actually be built:

- **Hub hardware** = central control plane
- **Room nodes** = distributed interfaces and local zone logic
- **Camera nodes** = vision/event devices
- **Sensor network** = house telemetry layer
- **Networking** = backbone and reliability layer
- **Compute / AI nodes** = heavy reasoning layer

That split is the cleanest path to making the smart-home stack expandable without turning the main Pi into a fragile all-in-one bottleneck.

---

## 12. Quick Cost Summary

| Architecture Block | Estimated Cost |
|---|---|
| Hub hardware (no display) | $335 |
| Hub hardware (with display) | $405 |
| Room node | $20–80 each |
| Camera node | $10–55 each |
| Sensor node | $8–40 each |
| Networking baseline | $120–200 |
| Compute / AI node | existing MacBook |

### Example pilot deployment
- Hub with display: $405
- 2 room nodes: ~$80
- 1 ESP32-CAM: ~$15
- starter sensors: ~$50
- router baseline: ~$120

**Example pilot total:** **~$670**

---

## 13. File Notes

This document is intended to become the BOM reference that maps directly to the actual smart-home architecture.

The next logical revision would be a **deployment-mapped BOM** that adds:
- physical installation locations
- per-room deployment counts
- wiring / power notes
- MQTT/device naming conventions
- phased purchase order
