# Device Inventory

**Owner:** Alex  
**Created:** 2026-03-02  
**Status:** DRAFT - Placeholders Only

---

## 1. Inventory Summary

| Category | Count | Protocol | Status |
|----------|-------|----------|--------|
| Lighting | TBD | Zigbee/Z-Wave/WiFi | PLANNED |
| Climate | TBD | Zigbee/Z-Wave/WiFi | PLANNED |
| Security | TBD | Zigbee/Z-Wave/WiFi | PLANNED |
| Sensors | TBD | Zigbee | PLANNED |
| Cameras | TBD | IP (RTSP) | PLANNED |
| Appliances | TBD | WiFi/Smart Plugs | PLANNED |
| Media | TBD | WiFi | PLANNED |

---

## 2. Lighting

### 2.1 Smart Bulbs

| Location | Device | Protocol | Entity ID | Status |
|----------|--------|----------|-----------|--------|
| Living Room - Ceiling | [TBD] | Zigbee | `light.living_room_ceiling` | PLANNED |
| Living Room - Lamp 1 | [TBD] | Zigbee | `light.living_room_lamp_1` | PLANNED |
| Living Room - Lamp 2 | [TBD] | Zigbee | `light.living_room_lamp_2` | PLANNED |
| Bedroom - Ceiling | [TBD] | Zigbee | `light.bedroom_ceiling` | PLANNED |
| Bedroom - Bedside L | [TBD] | Zigbee | `light.bedroom_bedside_left` | PLANNED |
| Bedroom - Bedside R | [TBD] | Zigbee | `light.bedroom_bedside_right` | PLANNED |
| Kitchen - Ceiling | [TBD] | Zigbee | `light.kitchen_ceiling` | PLANNED |
| Kitchen - Under Cabinet | [TBD] | Zigbee | `light.kitchen_under_cabinet` | PLANNED |
| Bathroom | [TBD] | Zigbee | `light.bathroom` | PLANNED |
| Entryway | [TBD] | Zigbee | `light.entryway` | PLANNED |
| Office | [TBD] | Zigbee | `light.office` | PLANNED |
| Outdoor - Front | [TBD] | Zigbee | `light.outdoor_front` | PLANNED |
| Outdoor - Back | [TBD] | Zigbee | `light.outdoor_back` | PLANNED |

### 2.2 Smart Switches (Hardwired)

| Location | Device | Protocol | Entity ID | Status |
|----------|--------|----------|-----------|--------|
| [TBD] | [TBD] | Z-Wave | `switch.[room]` | PLANNED |

### 2.3 Lighting Notes
- **Preferred Protocol:** Zigbee (mesh reliability)
- **Candidate Brands:** Philips Hue, IKEA Tradfri, Sengled
- **Features Needed:** Dimming, color temperature (warm/cool)
- **Color RGB:** Optional - living room only?

---

## 3. Climate Control

### 3.1 Thermostat

| Location | Device | Protocol | Entity ID | Status |
|----------|--------|----------|-----------|--------|
| Hallway | [TBD] | WiFi/Z-Wave | `climate.main_thermostat` | PLANNED |

**Candidates:**
- Ecobee (HomeKit, good HA support)
- Google Nest (requires cloud)
- Honeywell T6 Pro (Z-Wave local)

**Requirements:**
- Local control (no cloud dependency)
- Schedule support
- Away mode detection

### 3.2 Temperature Sensors

| Location | Device | Protocol | Entity ID | Status |
|----------|--------|----------|-----------|--------|
| Living Room | [TBD] | Zigbee | `sensor.living_room_temp` | PLANNED |
| Bedroom | [TBD] | Zigbee | `sensor.bedroom_temp` | PLANNED |
| Office | [TBD] | Zigbee | `sensor.office_temp` | PLANNED |
| Outdoor | [TBD] | Zigbee | `sensor.outdoor_temp` | PLANNED |

### 3.3 Fans

| Location | Device | Protocol | Entity ID | Status |
|----------|--------|----------|-----------|--------|
| Bedroom - Ceiling Fan | [TBD] | Z-Wave/WiFi | `fan.bedroom` | PLANNED |
| Living Room - Fan | [TBD] | Smart Plug | `switch.living_room_fan` | PLANNED |

---

## 4. Security

### 4.1 Door Locks

| Location | Device | Protocol | Entity ID | Status |
|----------|--------|----------|-----------|--------|
| Front Door | [TBD] | Z-Wave | `lock.front_door` | PLANNED |
| Back Door | [TBD] | Z-Wave | `lock.back_door` | PLANNED |
| Garage Entry | [TBD] | Z-Wave | `lock.garage_entry` | PLANNED |

**Candidates:**
- Schlage Connect (Z-Wave, reliable)
- Yale Assure (Z-Wave/Zigbee)
- Kwikset 916 (Z-Wave)

**Requirements:**
- Z-Wave preferred (local, no cloud)
- PIN code support
- Auto-lock capability

### 4.2 Door/Window Sensors

| Location | Device | Protocol | Entity ID | Status |
|----------|--------|----------|-----------|--------|
| Front Door | [TBD] | Zigbee | `binary_sensor.front_door` | PLANNED |
| Back Door | [TBD] | Zigbee | `binary_sensor.back_door` | PLANNED |
| Garage Door | [TBD] | Zigbee | `binary_sensor.garage_door` | PLANNED |
| Window - Living Room | [TBD] | Zigbee | `binary_sensor.window_living` | PLANNED |
| Window - Bedroom | [TBD] | Zigbee | `binary_sensor.window_bedroom` | PLANNED |

### 4.3 Motion Sensors

| Location | Device | Protocol | Entity ID | Status |
|----------|--------|----------|-----------|--------|
| Living Room | [TBD] | Zigbee | `binary_sensor.motion_living` | PLANNED |
| Entryway | [TBD] | Zigbee | `binary_sensor.motion_entry` | PLANNED |
| Hallway | [TBD] | Zigbee | `binary_sensor.motion_hallway` | PLANNED |
| Garage | [TBD] | Zigbee | `binary_sensor.motion_garage` | PLANNED |
| Outdoor - Front | [TBD] | Zigbee | `binary_sensor.motion_outdoor_front` | PLANNED |

### 4.4 Garage Door

| Location | Device | Protocol | Entity ID | Status |
|----------|--------|----------|-----------|--------|
| Garage | [TBD] | WiFi/Z-Wave | `cover.garage_door` | PLANNED |

**Candidates:**
- Ratgdo (local, ESPHome)
- GoControl Linear (Z-Wave)

---

## 5. Cameras

| Location | Device | Protocol | Entity ID | Status |
|----------|--------|----------|-----------|--------|
| Front Door | [TBD] | RTSP/ONVIF | `camera.front_door` | PLANNED |
| Backyard | [TBD] | RTSP/ONVIF | `camera.backyard` | PLANNED |
| Garage | [TBD] | RTSP/ONVIF | `camera.garage` | PLANNED |
| Indoor (optional) | [TBD] | RTSP/ONVIF | `camera.indoor` | PLANNED |

**Candidates:**
- Reolink RLC-810A (PoE, local, AI detection)
- Amcrest IP cameras
- Ubiquiti UniFi G4 series

**Requirements:**
- RTSP support (local streaming)
- ONVIF for PTZ/control
- No mandatory cloud
- PoE preferred
- Local recording support

---

## 6. Appliances

### 6.1 Smart Plugs

| Location | Device | Protocol | Entity ID | Status |
|----------|--------|----------|-----------|--------|
| Coffee Maker | [TBD] | Zigbee | `switch.coffee_maker` | PLANNED |
| Living Room - TV | [TBD] | Zigbee | `switch.tv_plug` | PLANNED |
| Office - Monitor | [TBD] | Zigbee | `switch.office_monitor` | PLANNED |
| Seasonal - Holiday Lights | [TBD] | Zigbee | `switch.holiday_lights` | PLANNED |

**Candidates:**
- Sonoff S31 (Zigbee, energy monitoring)
- IKEA Tradfri plugs
- Aqara smart plugs

### 6.2 Major Appliances (If Smart)

| Appliance | Device | Protocol | Entity ID | Status |
|-----------|--------|----------|-----------|--------|
| Washer | [TBD] | WiFi | `sensor.washer_status` | FUTURE |
| Dryer | [TBD] | WiFi | `sensor.dryer_status` | FUTURE |
| Dishwasher | [TBD] | WiFi | `sensor.dishwasher_status` | FUTURE |

---

## 7. Media & Entertainment

| Device | Protocol | Entity ID | Status |
|--------|----------|-----------|--------|
| TV - Living Room | WiFi/HDMI-CEC | `media_player.living_room_tv` | PLANNED |
| Speakers | WiFi/AirPlay | `media_player.speakers` | PLANNED |
| [TBD] | | | |

---

## 8. Hub & Infrastructure

| Component | Device | Location | Status |
|-----------|--------|----------|--------|
| Automation Hub | Raspberry Pi 5 (8GB) | [TBD] | PLANNED |
| AI Sidecar | MacBook Air M1 | Office/Living | PLANNED |
| Zigbee Coordinator | [TBD - DEC-001] | Pi USB | PLANNED |
| Z-Wave Controller | [TBD - DEC-002] | Pi USB | PLANNED |
| NVMe Storage | [TBD - 500GB+] | Pi HAT | PLANNED |
| UPS/Battery Backup | [TBD] | With Pi | PLANNED |

---

## 9. Network Infrastructure

| Component | Device | Notes | Status |
|-----------|--------|-------|--------|
| Router | [Existing] | | EXISTING |
| WiFi AP | [Existing] | | EXISTING |
| Ethernet Switch | [TBD] | For PoE cameras | PLANNED |
| PoE Injector/Switch | [TBD] | If not using PoE switch | PLANNED |

---

## 10. Protocol Distribution

| Protocol | Device Count | Coordinator |
|----------|--------------|-------------|
| Zigbee | ~XX | [DEC-001] |
| Z-Wave | ~XX | [DEC-002] |
| WiFi | ~XX | Router |
| IP (Cameras) | ~XX | Direct LAN |

---

## 11. Budget Estimate

| Category | Estimated Cost | Notes |
|----------|----------------|-------|
| Hub Hardware | $150-200 | Pi 5 + NVMe + case |
| Zigbee Dongle | $15-40 | |
| Z-Wave Controller | $30-50 | Optional |
| Lighting (10 bulbs) | $100-200 | |
| Thermostat | $100-200 | |
| Locks (2-3) | $200-400 | |
| Sensors (5-10) | $50-150 | |
| Cameras (2-3) | $150-300 | |
| Smart Plugs (4-6) | $40-80 | |
| **TOTAL ESTIMATE** | **$835-1620** | |

---

## 12. Acquisition Checklist

### Priority 1 (Phase 1)
- [ ] Raspberry Pi 5 (8GB)
- [ ] NVMe HAT + SSD
- [ ] Power supply (5V/5A)
- [ ] Zigbee coordinator
- [ ] Test bulb (1)
- [ ] Test sensor (1)

### Priority 2 (Phase 1-2)
- [ ] Remaining bulbs
- [ ] Motion sensors
- [ ] Door/window sensors
- [ ] Smart plugs

### Priority 3 (Phase 2+)
- [ ] Thermostat
- [ ] Door locks
- [ ] Z-Wave controller (if needed)

### Priority 4 (Phase 5)
- [ ] Cameras
- [ ] PoE switch

---

**END OF DOCUMENT**
