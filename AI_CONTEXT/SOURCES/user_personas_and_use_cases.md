# User Personas & Use Cases

**Owner:** Alex  
**Created:** 2026-03-02  
**Status:** Active

---

## 1. Household Overview

| Attribute | Value |
|-----------|-------|
| Household Size | 2 adults |
| Property Type | [TBD - House/Apartment/Condo] |
| Primary Users | Alex, Partner |
| Technical Expertise | Alex: High, Partner: Medium |

---

## 2. User Personas

### Persona 1: Alex (Primary Administrator)

| Attribute | Value |
|-----------|-------|
| Role | System Administrator, Primary User |
| Technical Level | High - comfortable with CLI, APIs, automation logic |
| Primary Devices | MacBook, iPhone, iPad |
| Usage Pattern | Voice commands, dashboard, direct HA configuration |
| Key Priorities | System reliability, security, extensibility |

**Daily Interaction Style:**
- Morning: Voice queries for traffic, weather, calendar
- Daytime: Occasional remote monitoring via Tailscale
- Evening: Voice-driven web searches, appliance control, research assistance
- Maintenance: Weekly system checks, monthly updates

**Pain Points to Solve:**
- Reduce friction for routine information gathering
- Automate repetitive tasks (lights, climate)
- Quick access to contextual information without opening apps

---

### Persona 2: Partner

| Attribute | Value |
|-----------|-------|
| Role | Daily User |
| Technical Level | Medium - comfortable with apps, voice assistants |
| Primary Devices | iPhone, iPad |
| Usage Pattern | Voice commands, mobile dashboard |
| Key Priorities | Simplicity, reliability, "it just works" |

**Daily Interaction Style:**
- Morning: Weather and traffic checks via voice
- Daytime: Light control, thermostat adjustments
- Evening: Entertainment queries, recipe assistance, shopping research
- Maintenance: None (relies on Alex)

**Pain Points to Solve:**
- Consistent voice command experience
- Clear feedback when actions succeed/fail
- No need to understand underlying system

---

## 3. Daily Use Case Scenarios

### 3.1 Morning Routine (6:30 AM - 8:00 AM)

#### Scenario: Wake-Up Information Briefing

**Trigger:** Wake word detected OR scheduled automation at 6:30 AM

**User Says:** "Good morning" / "What's my morning briefing?"

**System Response:**
1. Turn on bedroom/kitchen lights to 50%
2. Provide spoken briefing:
   - Current weather + high/low for the day
   - Precipitation probability
   - Traffic conditions to work (commute time estimate)
   - Any calendar events for today
3. Start coffee maker (if connected)

**Example Dialog:**
```
User: "Hey Jarvis, good morning"
System: "Good morning! It's 45 degrees and partly cloudy. 
        High of 62 today with a 20% chance of afternoon showers.
        Your commute to downtown looks clear - about 25 minutes.
        You have a 10 AM meeting with the design team."
```

**Success Criteria:**
- Response < 5 seconds
- Traffic data accurate within 5 minutes
- Weather data current (< 1 hour old)

---

#### Scenario: Quick Traffic Check

**Trigger:** Voice command

**User Says:** "How's traffic to work?" / "What's my commute look like?"

**System Response:**
- Commute time estimate
- Any incidents or delays
- Suggested departure time

**Example Dialog:**
```
User: "How's traffic?"
System: "Traffic to downtown is moderate. 
        28 minutes via I-5, or 32 minutes via surface streets.
        There's a minor slowdown near the 520 interchange."
```

---

#### Scenario: Weather Detail

**Trigger:** Voice command

**User Says:** "What's the weather?" / "Do I need an umbrella?"

**System Response:**
- Current conditions
- Forecast relevant to question
- Practical recommendation

**Example Dialog:**
```
User: "Do I need a jacket?"
System: "It's 45 degrees now but warming to 62 by afternoon.
        I'd bring a light jacket for this morning."
```

---

### 3.2 Evening Routine (6:00 PM - 11:00 PM)

#### Scenario: Arrival Home

**Trigger:** Phone geofence OR manual voice command

**User Says:** "I'm home" / (automatic trigger)

**System Response:**
1. Disarm security (if armed)
2. Turn on entryway/living room lights
3. Adjust thermostat to "home" setting
4. (Optional) Play welcome music or news briefing

---

#### Scenario: Appliance Control

**Trigger:** Voice command

**User Says:** Examples:
- "Turn on the living room lights"
- "Set the thermostat to 70"
- "Turn off the bedroom fan"
- "Start the dishwasher" (if supported)

**System Response:**
- Execute action
- Confirm completion
- Report any issues

**Example Dialog:**
```
User: "Dim the living room lights to 40%"
System: "Living room lights set to 40 percent."
```

---

#### Scenario: Web Search / Research Assistance

**Trigger:** Voice command

**User Says:** Examples:
- "Search for best pizza places nearby"
- "What are the reviews for [product]?"
- "Compare prices for [item]"
- "Find a recipe for chicken parmesan"

**System Response:**
- Perform web search
- Summarize top results
- Offer to provide more detail

**Example Dialog:**
```
User: "Find me a good Thai restaurant nearby"
System: "I found 3 highly-rated Thai restaurants within 2 miles:
        1. Thai Ginger - 4.5 stars, known for their pad thai
        2. Bahn Thai - 4.3 stars, authentic northern Thai cuisine
        3. Siam Palace - 4.4 stars, great lunch specials
        Would you like more details on any of these?"
```

---

#### Scenario: Shopping Research

**Trigger:** Voice command

**User Says:** Examples:
- "What's a good vacuum cleaner under $300?"
- "Compare the iPhone 16 and Galaxy S26"
- "Find deals on running shoes"

**System Response:**
- Search for products
- Summarize options with ratings and prices
- Note: Does NOT make purchases (no payment tools)

---

#### Scenario: Night Mode

**Trigger:** Voice command OR scheduled time

**User Says:** "Good night" / "Bedtime"

**System Response:**
1. Turn off all lights except bedroom
2. Set bedroom lights to 10% (nightlight mode)
3. Lock all doors
4. Arm security system (away sensors)
5. Set thermostat to sleep temperature
6. Confirm actions

**Example Dialog:**
```
User: "Good night"
System: "Good night! I've turned off the lights, locked the doors,
        and set the thermostat to 66 degrees. Sleep well."
```

---

## 4. Weekly/Occasional Use Cases

### 4.1 Stock Market Check

**User Says:** "How's the market?" / "What's [TICKER] at?"

**System Response:**
- Market summary (indices)
- Specific stock quotes if requested
- Daily change percentage

---

### 4.2 Photo Album Display

**User Says:** "Show photos from [event/date]"

**System Response:**
- Display photo slideshow on dashboard
- (Or send to specific display device)

---

### 4.3 Calendar Integration

**User Says:** "What's on my calendar?" / "Add [event] to my calendar"

**System Response:**
- Read upcoming events
- Add events (with confirmation)

---

### 4.4 Package Tracking

**User Says:** "Where's my package?" / "Any deliveries today?"

**System Response:**
- Check tracking status
- Expected delivery time
- Camera alert when delivered (future)

---

## 5. Use Case Priority Matrix

| Use Case | Frequency | Priority | Phase |
|----------|-----------|----------|-------|
| Morning weather briefing | Daily | P1 | Phase 2 |
| Traffic check | Daily | P1 | Phase 2 |
| Light control | Daily | P1 | Phase 1 |
| Thermostat control | Daily | P1 | Phase 1 |
| Web search/research | Daily | P1 | Phase 2 |
| Night mode routine | Daily | P1 | Phase 1 |
| Stock quotes | Weekly | P2 | Phase 2-3 |
| Photo display | Weekly | P3 | Phase 3+ |
| Calendar integration | Daily | P2 | Phase 2-3 |
| Shopping research | Weekly | P2 | Phase 2 |

---

## 6. Voice Command Design Principles

### Natural Language Flexibility
The system should understand variations:
- "Turn on the lights" / "Lights on" / "Can you turn on the lights?"
- "What's the weather" / "How's the weather" / "Weather report"

### Confirmation Strategy
| Action Risk | Confirmation Required |
|-------------|----------------------|
| Lights, info queries | No - just execute and confirm |
| Thermostat changes | No - confirm new setting |
| Lock doors | Confirm: "Locking all doors" |
| Unlock doors | YES - "Are you sure you want to unlock the front door?" |
| Arm security | Confirm: "Arming security system" |
| Disarm security | Voice PIN or confirmation required |

### Error Handling
```
User: "Turn on the kitchen lights"
System (if no entity): "I don't see a light called 'kitchen'. 
                        Did you mean 'kitchen ceiling' or 'kitchen counter'?"
```

---

## 7. Information Sources Required

| Data Type | Source | Update Frequency |
|-----------|--------|------------------|
| Weather | OpenWeatherMap API or local sensor | 15 min |
| Traffic | Google Maps API / Apple Maps | On-demand |
| Stocks | Yahoo Finance / Alpha Vantage | 5-15 min (market hours) |
| Web Search | SearXNG (local) or DuckDuckGo | On-demand |
| Calendar | CalDAV / iCloud / Google | Real-time sync |
| News | RSS feeds / news API | Hourly |

---

## 8. Success Metrics (Per Persona)

### Alex
| Metric | Target |
|--------|--------|
| Voice command success rate | 95%+ |
| Morning briefing completion | < 30 seconds |
| Remote access reliability | 99% |
| System maintenance time | < 1 hour/week |

### Partner
| Metric | Target |
|--------|--------|
| Voice command success rate | 95%+ |
| "It just works" satisfaction | High |
| Need to ask Alex for help | < 1x/month |
| Frustration incidents | 0 |

---

**END OF DOCUMENT**
