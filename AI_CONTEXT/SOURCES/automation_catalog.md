# Automation Catalog

**Owner:** Alex  
**Created:** 2026-03-02  
**Status:** DRAFT - Placeholder

---

## 1. Automation Overview

| Priority | Category | Count | Status |
|----------|----------|-------|--------|
| P1 | Lighting | X | PLANNED |
| P1 | Climate | X | PLANNED |
| P1 | Security | X | PLANNED |
| P2 | Convenience | X | PLANNED |
| P3 | Advanced | X | FUTURE |

---

## 2. Priority 1 Automations (Core)

### 2.1 Lighting Automations

#### AUTO-L01: Sunset Lights On
**Trigger:** Sun sets (with offset)  
**Conditions:** Someone home  
**Actions:** Turn on living room lights to 70%  
**Status:** PLANNED

```yaml
# Placeholder YAML
alias: "Sunset Lights On"
trigger:
  - platform: sun
    event: sunset
    offset: "-00:30:00"
condition:
  - condition: state
    entity_id: [TBD - presence sensor]
    state: "home"
action:
  - service: light.turn_on
    target:
      entity_id: light.living_room
    data:
      brightness_pct: 70
```

---

#### AUTO-L02: Motion-Activated Hallway
**Trigger:** Motion detected in hallway  
**Conditions:** After sunset, before sunrise  
**Actions:** Turn on hallway light, turn off after 3 min  
**Status:** PLANNED

---

#### AUTO-L03: All Lights Off (Night Mode)
**Trigger:** Voice command OR 11:00 PM  
**Conditions:** [TBD]  
**Actions:** Turn off all lights except bedroom nightlight  
**Status:** PLANNED

---

#### AUTO-L04: Morning Wake Lights
**Trigger:** Time (6:30 AM weekdays)  
**Conditions:** [TBD]  
**Actions:** Gradually brightening bedroom lights  
**Status:** PLANNED

---

### 2.2 Climate Automations

#### AUTO-C01: Away Mode (Nobody Home)
**Trigger:** Everyone leaves (phone GPS/presence)  
**Conditions:** [TBD]  
**Actions:** Set thermostat to 65°F  
**Status:** PLANNED

---

#### AUTO-C02: Welcome Home
**Trigger:** First person arrives home  
**Conditions:** [TBD]  
**Actions:** Set thermostat to 72°F  
**Status:** PLANNED

---

#### AUTO-C03: Sleep Temperature
**Trigger:** 10:00 PM OR "Good night" command  
**Conditions:** [TBD]  
**Actions:** Set thermostat to 66°F  
**Status:** PLANNED

---

#### AUTO-C04: Wake Temperature
**Trigger:** 30 min before wake alarm  
**Conditions:** Weekday  
**Actions:** Set thermostat to 70°F  
**Status:** PLANNED

---

### 2.3 Security Automations

#### AUTO-S01: Lock Doors at Night
**Trigger:** 10:00 PM OR "Good night" command  
**Conditions:** [TBD]  
**Actions:** Lock all doors  
**Status:** PLANNED

---

#### AUTO-S02: Unlock on Arrival (Optional)
**Trigger:** [TBD - phone proximity?]  
**Conditions:** [TBD - verified identity]  
**Actions:** Unlock front door  
**Status:** FUTURE (security concerns)

---

#### AUTO-S03: Alert on Door Open (Away Mode)
**Trigger:** Door opens while security armed  
**Conditions:** System in "Away" mode  
**Actions:** Send push notification, log event  
**Status:** PLANNED

---

#### AUTO-S04: Garage Left Open Alert
**Trigger:** Garage door open > 15 minutes  
**Conditions:** [TBD]  
**Actions:** Send notification  
**Status:** PLANNED

---

## 3. Priority 2 Automations (Convenience)

### 3.1 Morning Routine

#### AUTO-M01: Morning Briefing
**Trigger:** "Good morning" voice command  
**Conditions:** Before 10 AM  
**Actions:**  
1. Turn on kitchen lights
2. Start coffee maker (if connected)
3. Speak: weather, traffic, calendar summary  
**Status:** PLANNED (Phase 2-3)

---

### 3.2 Evening Routine

#### AUTO-E01: Movie Mode
**Trigger:** Voice command "Movie time"  
**Conditions:** [None]  
**Actions:**  
1. Dim living room lights to 20%
2. Turn off other room lights
3. [Optional] Turn on TV  
**Status:** PLANNED

---

#### AUTO-E02: Dinner Scene
**Trigger:** Voice command "Dinner time"  
**Conditions:** [None]  
**Actions:**  
1. Set dining area lights to warm 60%
2. Play background music (optional)  
**Status:** PLANNED

---

### 3.3 Presence-Based

#### AUTO-P01: Room Occupancy Lighting
**Trigger:** Motion in room  
**Conditions:** Lights currently off  
**Actions:** Turn on lights, auto-off after X minutes  
**Status:** PLANNED

---

#### AUTO-P02: Vacation Mode
**Trigger:** Enabled manually OR extended absence  
**Conditions:** [TBD]  
**Actions:**  
1. Randomize light patterns
2. Adjust thermostat to minimal
3. Enhanced security monitoring  
**Status:** FUTURE

---

## 4. Priority 3 Automations (Advanced)

### 4.1 Camera-Based

#### AUTO-CAM01: Person Detected at Door
**Trigger:** AI detection of person (not car, animal)  
**Conditions:** Front door camera  
**Actions:** Send notification with snapshot  
**Status:** FUTURE (requires camera AI)

---

#### AUTO-CAM02: Package Delivery
**Trigger:** Person detected + lingers + leaves  
**Conditions:** Front door camera  
**Actions:** Notify "Package may have been delivered"  
**Status:** FUTURE

---

### 4.2 Energy Management

#### AUTO-EN01: Peak Rate Avoidance
**Trigger:** Time-of-use rate window starts  
**Conditions:** Summer months  
**Actions:** Pre-cool house, delay appliances  
**Status:** FUTURE

---

#### AUTO-EN02: High Energy Alert
**Trigger:** Daily energy above threshold  
**Conditions:** [TBD]  
**Actions:** Send notification with breakdown  
**Status:** FUTURE (requires energy monitoring)

---

### 4.3 Calendar Integration

#### AUTO-CAL01: Meeting Mode
**Trigger:** Calendar event starts  
**Conditions:** Event title contains "focus" or "meeting"  
**Actions:** Enable DND, dim distracting lights  
**Status:** FUTURE

---

## 5. Scene Definitions

### SCENE-01: Morning
- Living room: 80%, warm white
- Kitchen: 100%, neutral
- Bedroom: Off

### SCENE-02: Day
- All lights: Off (natural light)

### SCENE-03: Evening
- Living room: 70%, warm
- Kitchen: 50%, warm
- Entryway: 50%

### SCENE-04: Movie
- Living room: 20%, warm
- All others: Off

### SCENE-05: Night
- All lights: Off
- Bedroom nightlight: 5%
- Bathroom: 10% (motion-activated)

### SCENE-06: Away
- All lights: Off
- Security: Armed

### SCENE-07: Romantic
- Living room: 30%, warm
- Candle-like effect if RGB

---

## 6. Automation Dependencies

```
AUTO-L01 ──► Requires: Lights, presence detection
AUTO-C01 ──► Requires: Thermostat, presence detection
AUTO-S01 ──► Requires: Smart locks
AUTO-M01 ──► Requires: Voice pipeline, weather API, calendar
AUTO-CAM01 ─► Requires: Camera with AI detection
```

---

## 7. Implementation Order

### Phase 1 (Basic Hardware)
1. AUTO-L01: Sunset lights
2. AUTO-L03: Night mode
3. AUTO-S01: Lock at night

### Phase 2 (AI Integration)
4. AUTO-M01: Morning briefing
5. AUTO-E01: Movie mode
6. AUTO-P01: Room occupancy

### Phase 3+ (Advanced)
7. Camera-based automations
8. Energy management
9. Calendar integration

---

## 8. Automation Template

```yaml
# Template for new automations
alias: "AUTO-XXX: [Name]"
description: "[Description]"
mode: single

trigger:
  - platform: [state/time/sun/event]
    # trigger details

condition:
  - condition: [state/time/template]
    # condition details

action:
  - service: [service.action]
    target:
      entity_id: [entity_id]
    data:
      # parameters
```

---

**END OF DOCUMENT**
