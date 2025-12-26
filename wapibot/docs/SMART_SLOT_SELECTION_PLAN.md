# Smart Slot Selection - Implementation Plan

## Problem Statement

**Current UX (Bad):** Dumps all 84 slots on customer's WhatsApp after service selection
```
📅 *Available Appointment Slots:*
*2025-12-27*
  1. 06:00 - 08:00
  2. 07:15 - 08:15
  ... (84 total slots!)
```

**Target UX (Good):** Ask preferences first, show filtered & grouped slots
```
Bot: "When would you like to book?"
User: "Monday morning"
Bot: "Great! Here are morning slots for Monday:
  1. 8:00 AM - 9:00 AM
  2. 9:30 AM - 10:30 AM
  3. 11:00 AM - 12:00 PM"
```

---

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Date/Time Parsing** | Hybrid: Regex first, DSPy fallback | 70% regex hit rate, DSPy only when needed |
| **Question Style** | Open-ended first, MCQ fallback | Natural conversation, structured fallback |
| **Incremental Extraction** | Get date OR time, ask for other | User says "Monday" → ask Morning/Afternoon/Evening |
| **Slot Display** | Group by Morning/Afternoon/Evening | Organized, not overwhelming |
| **Parse Failure** | Show MCQ menu | Never fails, just asks structured question |

---

## Architecture Flow

```
SERVICE SELECTION (existing)
        ↓
┌─────────────────────────────────────────┐
│     SLOT PREFERENCE GROUP (NEW)         │
│                                         │
│ [ask_preference] "When would you like?" │
│         ↓                               │
│ [extract_preference] Hybrid regex+DSPy  │
│         ↓                               │
│ [route_extraction]                      │
│   ├── date_only → ask_time (MCQ)        │
│   ├── time_only → ask_date (MCQ)        │
│   ├── both → proceed to slots           │
│   └── neither → show_menu (MCQ)         │
└─────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────┐
│       SLOT GROUP (MODIFIED)             │
│                                         │
│ [fetch_filtered_slots] ← Use prefs      │
│         ↓                               │
│ [group_slots_by_time] Morning/Afternoon │
│         ↓                               │
│ [show_grouped_slots] Organized display  │
│         ↓                               │
│ [process_selection] Numeric from list   │
└─────────────────────────────────────────┘
        ↓
BOOKING CONFIRMATION (existing)
```

---

## State Changes

**Add to `state.py`** (6 new fields):

```python
# Slot Preference Fields
preferred_date: Optional[str]           # "2025-12-28" (YYYY-MM-DD)
preferred_time_range: Optional[str]     # "morning" | "afternoon" | "evening"
slot_preference_raw: Optional[str]      # Original user message
slot_preference_extraction_method: Optional[str]  # "regex" | "dspy" | "menu"
grouped_slots: Optional[Dict[str, List[Dict]]]    # {morning: [...], ...}
filtered_slot_options: Optional[List[Dict]]       # Filtered slots
```

---

## Files to Create (8 new files, ~550 lines total)

### 1. Fallbacks

| File | Lines | Purpose |
|------|-------|---------|
| `fallbacks/time_range_fallback.py` | ~50 | Regex patterns for morning/afternoon/evening |

**Patterns:** `morning|subah`, `afternoon|dopahar|lunch`, `evening|sham|shaam`

### 2. Extractors

| File | Lines | Purpose |
|------|-------|---------|
| `dspy_modules/extractors/slot_preference_extractor.py` | ~60 | Hybrid regex+DSPy extractor |

**Logic:** Try regex first → if fails, call DSPy → normalize to date + time_range

### 3. Transformers

| File | Lines | Purpose |
|------|-------|---------|
| `nodes/transformers/filter_slots_by_preference.py` | ~55 | Filter slots by date/time prefs |
| `nodes/transformers/group_slots_by_time.py` | ~50 | Group into Morning/Afternoon/Evening |

### 4. Message Builders

| File | Lines | Purpose |
|------|-------|---------|
| `nodes/message_builders/date_preference_prompt.py` | ~35 | "When would you like to book?" |
| `nodes/message_builders/time_preference_menu.py` | ~40 | MCQ: 1. Morning 2. Afternoon 3. Evening |
| `nodes/message_builders/date_preference_menu.py` | ~45 | MCQ: 1. Today 2. Tomorrow 3. Next week |
| `nodes/message_builders/grouped_slots.py` | ~65 | Display slots by time of day |

### 5. Node Group

| File | Lines | Purpose |
|------|-------|---------|
| `workflows/node_groups/slot_preference_group.py` | ~95 | New sub-workflow for preference collection |

---

## Files to Modify (3 files, ~65 lines changed)

| File | Changes |
|------|---------|
| `workflows/shared/state.py` | Add 6 new fields |
| `workflows/existing_user_booking.py` | Add slot_preference step between service and slot |
| `workflows/node_groups/slot_group.py` | Use filtering, grouping, new message builder |

---

## Message Templates

### Open-Ended Prompt
```
Great choice, {first_name}!

When would you like to schedule your {service_name}?

You can say things like:
- 'Tomorrow morning'
- 'Next Monday afternoon'
- 'This weekend evening'

Or just tell me what works for you!
```

### Time MCQ (when date known)
```
Got it! For *Monday, Dec 30*, which time works best?

1. Morning (8 AM - 12 PM)
2. Afternoon (12 PM - 5 PM)
3. Evening (5 PM - 8 PM)

Reply with 1, 2, or 3
```

### Date MCQ (when time known)
```
Perfect for the morning! Which day works for you?

1. Today (Friday, Dec 27)
2. Tomorrow (Saturday, Dec 28)
3. Sunday, Dec 29
4. Next week

Reply with 1, 2, 3, or 4
```

### Grouped Slots Display
```
Here are the morning slots for *Monday, Dec 30*:

*Morning*
  1. 8:00 AM - 9:00 AM
  2. 9:30 AM - 10:30 AM

*Afternoon*
  3. 1:00 PM - 2:00 PM
  4. 2:30 PM - 3:30 PM

Reply with the slot number to book.
```

---

## Regex Patterns

### Date Patterns
| Pattern | Example | Result |
|---------|---------|--------|
| `today\|aaj` | "today", "aaj" | Today's date |
| `tomorrow\|kal` | "tomorrow", "kal" | Tomorrow |
| `next monday\|tuesday...` | "next Monday" | Next week's Monday |
| `monday\|tuesday...` | "Monday" | This week's Monday |
| `this weekend` | "weekend" | Next Saturday |

### Time Patterns
| Pattern | Example | Range |
|---------|---------|-------|
| `morning\|subah\|8-11 am` | "morning", "10 am" | 6:00-12:00 |
| `afternoon\|dopahar\|12-3 pm` | "afternoon", "2 pm" | 12:00-17:00 |
| `evening\|sham\|4-7 pm` | "evening", "5 pm" | 17:00-21:00 |

---

## Edge Cases

| Case | Handling |
|------|----------|
| "I'm free anytime" | Show date MCQ |
| "Maybe evening or morning" | Extract first ("evening"), ask date |
| "2 PM" | Map to "afternoon", ask date |
| Hindi: "kal subah" | Regex handles "kal" + "subah" |
| No slots for preference | "Sorry, no slots. See all?" |
| Garbage input | Show structured MCQ menu |

---

## Implementation Order

### Phase 1: Foundation
1. `state.py` - Add 6 new fields
2. `time_range_fallback.py` - New regex patterns
3. Update `date_fallback.py` - Add weekend/Hindi patterns

### Phase 2: Core Logic
4. `slot_preference_extractor.py` - Hybrid extractor
5. `filter_slots_by_preference.py` - Filtering transformer
6. `group_slots_by_time.py` - Grouping transformer

### Phase 3: Messages
7. `date_preference_prompt.py` - Open question
8. `time_preference_menu.py` - Time MCQ
9. `date_preference_menu.py` - Date MCQ
10. `grouped_slots.py` - Grouped display

### Phase 4: Integration
11. `slot_preference_group.py` - New node group
12. `existing_user_booking.py` - Wire new group
13. `slot_group.py` - Use filtering/grouping

---

## Success Criteria

- [ ] Customer asked "When would you like to book?" after service selection
- [ ] "Tomorrow morning" → extracts date + time, shows filtered slots
- [ ] "Monday" → extracts date, asks time MCQ
- [ ] "Evening" → extracts time, asks date MCQ
- [ ] Garbage input → shows structured MCQ menu
- [ ] Slots displayed grouped by Morning/Afternoon/Evening
- [ ] All files under 100 lines (Blender principle)
- [ ] No DSPy calls for simple inputs (regex handles 70%)

---

## Cost Analysis

| Scenario | DSPy Calls | Est. Cost |
|----------|------------|-----------|
| "tomorrow morning" | 0 | $0 |
| "kal subah" (Hindi) | 0 | $0 |
| "next Monday afternoon" | 0 | $0 |
| "sometime next week maybe" | 1 | ~$0.01 |
| "I'm flexible" | 0 | $0 (MCQ fallback) |

**Expected: 70% regex, 30% DSPy** → ~$0.003 average per booking

---

**Ready for implementation!**
