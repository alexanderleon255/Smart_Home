# Dossier: Alex's Movie Preferences

**ID:** D001  
**Created:** 2026-03-02  
**Updated:** 2026-03-02  
**Type:** preference  
**User:** alex  
**Expires:** null (permanent)

---

## Summary

Alex prefers specific lighting settings when watching movies or TV in the evening. These preferences have been refined through corrections.

---

## Learned Preferences

| Setting | Value | Source |
|---------|-------|--------|
| Living room brightness | 40% | Correction (was 30%, too dark) |
| Color temperature | Warm (2700K) | Explicit preference |
| Other room lights | Off | Implicit (part of movie mode) |

---

## Behavioral Notes

- Usually watches movies on Friday/Saturday evenings
- Prefers to be asked "Should I dim the lights?" rather than auto-dimming
- Doesn't like sudden changes - prefers gradual transitions

---

## Related Entities

- `light.living_room_ceiling`
- `light.living_room_lamp_1`
- `light.living_room_lamp_2`

---

## Trigger Phrases

- "movie time"
- "let's watch something"
- "put on a movie"
- "netflix and chill" (interpreted as movie mode)

---

## Scene Configuration

When "movie" scene is activated for Alex:
```yaml
light.living_room_ceiling: 
  brightness_pct: 40
  color_temp_kelvin: 2700
light.living_room_lamp_1: off
light.living_room_lamp_2: off
# All other lights: off
```

---

## Keywords

movie, film, watch, netflix, tv, dim, theater, lights, 40%, warm, evening, living room

---

## History

| Date | Change |
|------|--------|
| 2026-03-02 | Created with initial preferences |
| | Correction: 30% → 40% brightness |
