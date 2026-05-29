# Keyword Analysis and Improvements

## 🔍 Current Keyword Weaknesses

### ❌ **Weak Keywords Analysis:**

#### **Day 1 Examples:**
- **Scene 1 (Arrival)**: `["airport", "city skyline", "arrival"]`
  - ❌ Too generic - "airport" exists everywhere
  - ❌ No time of day (sunrise? sunset? day? night?)
  - ❌ No composition style (aerial? wide? close-up?)
  - ❌ No mood/atmosphere (bustling? serene? modern?)
  - ❌ No specific details (terminal? runway? exterior?)

- **Scene 2 (Attractions)**: `["Bangalore Palace", "Vidhana Soudha", "Cubbon Park"]`
  - ✅ Good: Specific location names
  - ❌ Missing: Time of day (morning? golden hour?)
  - ❌ Missing: Composition (exterior? aerial? close-up?)
  - ❌ Missing: Mood (serene? vibrant? lush?)
  - ❌ Missing: Activity (people visiting? empty? crowds?)

- **Scene 3 (Food)**: `["street food", "dosa", "idli sambar"]`
  - ❌ Too generic - "street food" is everywhere
  - ❌ Missing: Time of day (evening? night? morning breakfast?)
  - ❌ Missing: Setting (outdoor? restaurant? close-up?)
  - ❌ Missing: Mood (busy? cozy? vibrant?)
  - ❌ Missing: Action (cooking? serving? eating?)

- **Scene 4 (Stay)**: `["Taj West End", "luxury hotel", "hotel lobby"]`
  - ✅ Good: Specific hotel name
  - ❌ Missing: Time (evening? night? daytime?)
  - ❌ Missing: Composition (interior? exterior? aerial?)
  - ❌ Missing: Mood (elegant? cozy? luxurious?)
  - ❌ Missing: Details (pool? garden? room?)

#### **Day 2 Examples:**
- **Scene 1 (Transit)**: `["highway", "landscape", "countryside"]`
  - ❌ **EXTREMELY GENERIC** - could be anywhere
  - ❌ No time of day (golden hour? morning? afternoon?)
  - ❌ No composition (road view? aerial? wide angle?)
  - ❌ No mood (serene? vibrant? peaceful?)
  - ❌ No details (lush? dry? mountains? fields?)

- **Scene 2 (Attractions)**: `["Mysore Palace", "Chamundi Hill", "St. Philomena's Church"]`
  - ✅ Good: Specific names
  - ❌ Missing: Time (sunset? golden hour? morning?)
  - ❌ Missing: Composition (exterior? aerial? interior?)
  - ❌ Missing: Mood (majestic? colorful? grand?)
  - ❌ Missing: Details (illuminated? traditional? crowds?)

---

## ✅ **What Strong Keywords Should Include:**

### **1. Time of Day** (Critical for mood)
- `sunrise`, `morning`, `golden hour`, `afternoon`, `sunset`, `dusk`, `evening`, `night`, `blue hour`, `dawn`

### **2. Composition & Style** (Critical for image type)
- `aerial view`, `drone shot`, `wide angle`, `panoramic`, `close-up`, `ground level`, `bird's eye view`, `interior`, `exterior`, `overhead shot`

### **3. Mood & Atmosphere** (Critical for feeling)
- `bustling`, `serene`, `vibrant`, `peaceful`, `dramatic`, `lush`, `golden light`, `warm colors`, `blue sky`, `misty`, `sunny`

### **4. Action & Activity** (Critical for context)
- `people walking`, `tourists visiting`, `locals`, `crowds`, `empty`, `cooking`, `serving`, `eating`, `exploring`, `traveling`

### **5. Color & Visual Details** (Important for aesthetics)
- `golden`, `turquoise`, `lush green`, `vibrant colors`, `sunset colors`, `colorful`, `bright`, `warm tones`

### **6. Cultural Elements** (Important for authenticity)
- `traditional`, `modern`, `authentic`, `cultural`, `local`, `Indian architecture`, `heritage`, `historic`

### **7. Quality Descriptors** (Important for image selection)
- `stunning`, `beautiful`, `professional`, `cinematic`, `high quality`, `HD`, `detailed`, `majestic`

### **8. Specific Details** (Important for precision)
- `terminal building`, `runway`, `temple exterior`, `palace facade`, `street vendor`, `restaurant interior`, `hotel pool`, `mountain view`

---

## 📊 **Before vs After Comparison:**

### **Day 1 Scene 1 (Arrival) - Current:**
```
["airport", "city skyline", "arrival"]
```
**Problems:**
- Too generic
- No time/mood/composition
- Will return random airport images

### **Day 1 Scene 1 (Arrival) - Improved:**
```
[
  "Kempegowda International Airport exterior sunrise aerial view",
  "Bengaluru city skyline morning golden hour wide angle",
  "airport terminal modern architecture bustling arrival"
]
```
**Benefits:**
- Specific location name
- Time of day (sunrise, morning, golden hour)
- Composition (aerial, wide angle)
- Mood (bustling, golden hour)
- Details (exterior, terminal, modern architecture)

---

### **Day 1 Scene 2 (Attractions) - Current:**
```
["Bangalore Palace", "Vidhana Soudha", "Cubbon Park"]
```
**Problems:**
- Just names, no descriptors
- No visual guidance
- Will return generic images

### **Day 1 Scene 2 (Attractions) - Improved:**
```
[
  "Bangalore Palace exterior morning golden hour architectural detail",
  "Vidhana Soudha majestic building lush greenery Cubbon Park wide angle",
  "Cubbon Park lush green trees people walking morning sunlight"
]
```
**Benefits:**
- Specific locations
- Time (morning, golden hour, sunlight)
- Composition (exterior, wide angle, architectural detail)
- Mood (majestic, lush, vibrant)
- Activity (people walking)
- Details (trees, greenery, building)

---

### **Day 1 Scene 3 (Food) - Current:**
```
["street food", "dosa", "idli sambar"]
```
**Problems:**
- Too generic
- No time/setting/mood
- Will return random food images

### **Day 1 Scene 3 (Food) - Improved:**
```
[
  "Bengaluru street food evening bustling vendors cooking dosa close-up",
  "MTR restaurant dosa crispy golden serving hot traditional breakfast",
  "idli sambar traditional South Indian breakfast morning colorful vibrant"
]
```
**Benefits:**
- Time (evening, morning)
- Setting (street, restaurant)
- Mood (bustling, vibrant, colorful)
- Activity (cooking, serving)
- Details (crispy, golden, hot, traditional)
- Composition (close-up)

---

### **Day 2 Scene 1 (Transit) - Current:**
```
["highway", "landscape", "countryside"]
```
**Problems:**
- **EXTREMELY GENERIC** - could be anywhere in the world
- No location, time, mood, or composition
- Will return completely random images

### **Day 2 Scene 1 (Transit) - Improved:**
```
[
  "Bengaluru to Mysuru highway Karnataka golden sun lush landscapes morning",
  "Karnataka countryside rural road fields green rice paddies aerial view",
  "India highway travel scenic route mountains fields peaceful journey"
]
```
**Benefits:**
- Specific route (Bengaluru to Mysuru)
- Location (Karnataka, India)
- Time (morning, golden sun)
- Composition (aerial view)
- Mood (peaceful, scenic, lush)
- Details (fields, rice paddies, mountains, green)

---

### **Day 2 Scene 2 (Attractions) - Current:**
```
["Mysore Palace", "Chamundi Hill", "St. Philomena's Church"]
```
**Problems:**
- Just names
- No visual guidance
- Will return generic images

### **Day 2 Scene 2 (Attractions) - Improved:**
```
[
  "Mysore Palace exterior kaleidoscope colors intricate designs golden hour majestic",
  "Chamundi Hill view Mysuru city aerial vista sunset panoramic breathtaking",
  "St. Philomena's Church neo-gothic architecture serene peaceful people visiting"
]
```
**Benefits:**
- Specific locations
- Time (golden hour, sunset)
- Composition (exterior, aerial, vista, panoramic)
- Mood (majestic, breathtaking, serene, peaceful)
- Details (kaleidoscope colors, intricate designs, neo-gothic architecture)
- Activity (people visiting)

---

## 🎯 **Keyword Enhancement Strategy:**

### **For Itinerary Generator:**
- Include **time of day** (sunrise, morning, golden hour, sunset, evening)
- Include **composition style** (aerial, wide angle, close-up, panoramic)
- Include **mood descriptors** (bustling, serene, vibrant, majestic)
- Include **action/activity** (people visiting, cooking, serving, traveling)
- Include **visual details** (lush, golden, colorful, vibrant, warm)
- Include **cultural elements** (traditional, authentic, heritage, local)

### **For Script Generator:**
- Extract **time references** from narration (e.g., "dusk descends" → "evening", "golden sun" → "golden hour")
- Extract **mood references** from narration (e.g., "vibrant" → "vibrant colors", "serene" → "peaceful")
- Extract **composition hints** from visual_order (e.g., "aerial", "panoramic", "close-up")
- Add **quality descriptors** (stunning, beautiful, cinematic, professional)
- Combine with itinerary keywords to create rich, searchable terms

---

## 📝 **Recommended Keyword Format:**

### **Format Structure:**
```
[Location/Specific Name] + [Time of Day] + [Composition] + [Mood/Atmosphere] + [Details] + [Activity]
```

### **Examples:**

**Arrival:**
- ✅ `"Kempegowda International Airport exterior morning aerial view modern architecture"`
- ✅ `"Bengaluru city skyline sunrise golden hour wide angle urban landscape"`

**Attractions:**
- ✅ `"Bangalore Palace exterior morning golden hour architectural detail heritage building"`
- ✅ `"Mysore Palace kaleidoscope colors intricate designs sunset majestic royal architecture"`

**Food:**
- ✅ `"Bengaluru street food evening bustling vendors cooking dosa close-up traditional"`
- ✅ `"Mysore Pak sweets colorful traditional Indian dessert close-up vibrant display"`

**Transit:**
- ✅ `"Karnataka highway rural road lush green fields morning peaceful scenic journey"`
- ✅ `"Bengaluru to Mysuru travel golden sun countryside aerial view beautiful landscape"`

**Stay:**
- ✅ `"Taj West End luxury hotel Bengaluru elegant lobby evening warm lighting interior"`
- ✅ `"Radisson Blu Mysuru modern hotel room comfortable amenities night peaceful rest"`

---

## 🚀 **Implementation Plan:**

1. **Update Itinerary Generator Prompt** - Add detailed keyword requirements
2. **Update Script Generator Prompt** - Enhance keyword extraction with descriptors
3. **Add Keyword Enhancement Logic** - Post-process keywords to add missing elements
4. **Test with Real Examples** - Verify improved keyword quality

