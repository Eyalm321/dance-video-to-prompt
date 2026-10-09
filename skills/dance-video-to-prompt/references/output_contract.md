# Output Contract

The final `prompt.md` must contain exactly the following 7 second-level headings, and nothing else:

1. `## Visual Style` — image quality, composition, light and shadow, color tone  
2. `## Scene Narrative` — the person (including **body features and build**), **outfit (colors and styles)**, overall expression and demeanor  
3. `## Shooting Scene` — venue, spatial relationships, background, floor, furnishings, time/place and ambient light, atmosphere  
4. `## Cinematography` — **shooting method, camera movement, focal emphasis**, camera position, focal length, lighting, mood  
5. `## Action List` — a timed, generatable action sequence + **per-segment expressions** + **beat-sync alignment**  
6. `## Dialogue/Text` — dialogue and subtitles  
7. `## Background Audio` — BGM style, **BPM**, relationship to the beats  

## Output Files (Agent Mode)

| File | Written by | Meaning |
|------|------|------|
| `frames/` + `frames_meta.json` | Frame-extraction script | Keyframes (including the sharpness field) |
| `frame_quality.json` | **Sharpness-check script** | Laplacian scores, sharp/rescued/blurry, priority analysis list |
| `frame_quality_brief.md` | Sharpness-check script | Human-readable brief |
| `rhythm_analysis.json` | **Local rhythm script** | BPM/beats/energy (numeric facts) |
| `rhythm_brief.md` | Rhythm script | Human-readable brief |
| `analysis.json` | **Visual agent** | Visual fact layer |
| `rhythm_plan.json` | **Rhythm sub-agent** | Beat-sync strategy (interpretation layer) |
| `prompt.md` | **Fusion stage (main agent)** | Final 7-section generation prompt |

## Sharpness (mandatory before viewing frames)

1. Read `frame_quality.json` first  
2. **Prioritize** analyzing `sharp_for_analysis`  
3. Frames with `status=blurry`: do not write confirmable-level finger shapes or precise brows/eyes; you may write "blurred due to fast motion"  
4. `rescued`: base the description on the substituted sharp image, but keep the timestamp of the original extracted frame (the report includes `rescued_offset`)

## Body Features (view frames + output, mandatory)

The generation side depends heavily on "consistency of the person's body shape". The visual agent and the fusion stage **must** observe clear frames and write a reproducible body description; using only empty phrases like "great figure" or "very thin" is forbidden.

### Record at least the following when viewing frames (write if visible; do not invent what is not visible)

| Dimension | Writing requirement | Example words (pick the best, don't pile them up) |
|------|----------|------------------------|
| **Overall build** | Height impression + slim/full / frame | tall and slender, petite and well-proportioned, medium-slim, full and curvy, athletic and toned, slightly plump and rounded |
| **Height-proportion impression** | Sense of proportion relative to the frame/shot size (not exact cm) | high leg-to-body ratio, short upper body, long head-to-body ratio, petite and compact |
| **Shoulders, neck, and collarbones** | Shoulder width, sloping/broad shoulders, whether collarbones are defined | narrow shoulders, defined collarbones, swan neck |
| **Chest contour** | Describe the contour and garment fit tastefully; avoid vulgarity | natural chest contour, flat and elongated upper body, clothing outlines a gentle curve |
| **Waist and abdomen** | Waistline position, thickness, whether cinched | slim waist, high waistline, flat stomach, slightly cinched waist |
| **Hips** | Hip width and hip shape (in dance/outfit videos this often affects the skirt hem and stance) | narrow hips, rounded hip line, hourglass waist-to-hip ratio |
| **Leg shape** | Thickness, straight/curved, sense of length | long straight slender legs, toned calves, long thighs |
| **Arms** | Thickness and line | slender arms, smooth shoulder-to-arm line, slim forearms |
| **Posture and stance** | Upright / rounded chest / slight forward lean / S-curve, etc. | upright stance, slightly arched lower back, languid rounded shoulders |
| **Skin tone and texture** | Visible skin tone and sheen (optional) | cool fair skin, warm wheat-toned skin, fine skin texture |

### analysis.json (required fields)

- `subject.body_type`: one sentence on overall build (height + slim/full / curve type)  
- `subject.body_proportions`: proportion impressions such as head-to-body ratio / leg length / shoulders vs. hips  
- `subject.body_details`: **per-body-part** description of shoulders/neck, chest contour, waist/abdomen, hips, legs, arms, etc. (only if visible)  
- `subject.posture_habit`: posture common throughout the video (upright, slightly arched lower back, rounded chest, etc.)  
- `subject.appearance`: may keep an appearance summary such as hairstyle and face shape; **must not replace** the body fields above  
- `segments[].body_focus`: the body part or posture change emphasized in this segment (e.g. "side angle emphasizes the slim waist and long legs", "the turn reveals the hip line under the skirt hem"); if none, write "overall body proportions maintained"

### prompt.md "Scene Narrative" (mandatory)

The person paragraph must contain a **continuous identity anchor** that can be fed directly to the video model; suggested order:

1. Age/gender impression (if discernible) + overall build  
2. Proportions (leg length, waistline, shoulders vs. hips)  
3. Per-part contours (shoulders/neck, chest, waist/abdomen, hips, legs/arms)  
4. Posture habits  
5. Hairstyle, makeup  
6. **Outfit**: style tag + item-by-item **color + style** (see the next section)  
7. Overall expression and demeanor  

Environment, background, floor, and furnishings go under **"Shooting Scene"**; do not pile them up here.

**Minimum requirement**: write at least "overall build + ≥2 visible details from waist/legs/shoulders/hips + posture"; when the full body is on camera, aim for 4 or more. Minimum outfit requirements are in the next section.

Example (structural illustration, do not copy verbatim):

> A tall, slender young woman with a long head-to-body ratio and noticeably long legs, narrow shoulders and defined collarbones, a slim waist and flat stomach, a clean hip line, long straight slender legs, slender arms, and an upright stance with a slight dancer's poise; light-brown curly hair reaching the shoulders; wearing an OL office style: a white fitted short-sleeve collared shirt buttoned at the neck, a black high-waisted bodycon mini skirt, and black patent pointed-toe stiletto heels; smiling softly at the camera.

Forbidden:

- Empty, uninformative phrases such as `great figure`, `very thin`, `alluring curves`, `perfect body`  
- Inventing precise contours for blurry frames / half-body shots / occluded parts  
- Vulgar or explicit descriptions; wording such as "contour/line/proportion/garment fit" is enough  

### Relationship to the Action List

- Body features are **primarily written in the Scene Narrative** (the whole-video identity anchor); the Action List **does not re-pile** the full body description  
- An action entry may mention it in one phrase when posture is involved (e.g. "arch the lower back and push the hip out about 15°, the slim waist more visible in profile"), echoing `body_focus`  

## Outfit Colors and Styles (view frames + output, mandatory)

The generation side depends on reproducible clothing. Writing only the garment category without the color, or glossing over it with just "fashionable outfit" or "nice clothes", is forbidden.

### Record at least the following when viewing frames (write if visible; do not invent what is not visible)

| Dimension | Writing requirement | Example words (pick the best, don't pile them up) |
|------|----------|------------------------|
| **Overall style** | Outfit type tag | OL office, sweet floral, sporty casual, swimwear, JK uniform, streetwear, loungewear, evening gown |
| **Color palette** | Main color + secondary color + accent | white + black + silver accessories; pale pink floral + off-white |
| **Top** | Color + style/cut + visible material | white fitted short-sleeve collared shirt, buttoned at the neck, sleeves rolled to the forearms |
| **Bottom** | Color + style/length/waistline | black high-waisted bodycon mini skirt |
| **One-piece/outerwear** | Same as above | beige knee-length trench coat, worn open and unbuttoned |
| **Footwear** | Color + shoe type | black patent pointed-toe stiletto heels |
| **Socks/hosiery** | Color + thickness | sheer nude stockings |
| **Accessories** | Color + type and where worn | thin silver bracelet on the left wrist |
| **Outfit change** | If any, write the time point and a before/after comparison | at t=3.2s takes off the jacket, revealing a white tank top |

### analysis.json (required fields)

- `subject.outfit.summary`: one sentence on the overall outfit (**must include colors and styles**)  
- `subject.outfit.style`: outfit style tag  
- `subject.outfit.palette`: main / secondary / accent colors  
- `subject.outfit.items[]`: visible items; each includes `slot` (top/bottom/one-piece/outerwear/shoes/socks/accessory), `name`, `color`, `style` (style/cut); add `material` and `fit` if visible  
- `subject.outfit.change`: none / the outfit-change moment with before and after  
- `segments[].outfit_note`: write in detail only if the outfit changes in this segment, otherwise "same as whole video"

If the legacy field `subject.outfit` is written as a string, it must still include color + style; writing only "white shirt, black skirt" without the cut is not allowed.

### Clothing in prompt.md "Scene Narrative" (mandatory)

After writing the body and hairstyle, you **must write item by item** the **color + style (style/cut/length/waistline)** of each visible garment; visible material and fit may be added.

**Minimum requirement**: every visible main item (top, bottom or one-piece, shoes) has a color and a style; at least 1 style tag.

Forbidden:

- Empty, uninformative phrases such as `fashionable outfit`, `nice clothes`, `a whole look`, `simple outfit`  
- Writing only the category without the color (e.g. only "shirt + skirt")  
- Writing only the color without the style (e.g. only "white shirt, black skirt", without short-sleeve/high-waisted/bodycon/mini)  
- Inventing invisible brands, printed text, or inner linings  

For outfit changes: the Scene Narrative clearly describes both outfits (or "changes from A to B"); the Action List mentions it lightly in the change entry without repeating the full description.

## Shooting Scene (view frames + output, mandatory)

A standalone module recording "what place is being filmed". It is not merged into the Scene Narrative and not mixed with the camera movement/lighting operations of Cinematography.

### Record at least the following when viewing frames (write if visible; do not invent what is not visible)

| Dimension | Writing requirement | Example words (pick the best) |
|------|----------|----------------|
| **Indoor/outdoor** | Indoor / outdoor / in-car / studio / mixed | indoor |
| **Location type** | A reproducible place, not vague | stairwell corridor, bedroom, city pedestrian street, seaside boardwalk, vanity spot in a white-walled corner |
| **Spatial structure** | Open/narrow, depth, sense of ceiling height | long narrow corridor, low corner, open plaza |
| **Subject placement** | The person's position and orientation relative to the space | against the off-white wall on the right, about half a step from a half-open white door |
| **Background layer** | Walls/sky/buildings/furnishings, with color and material | off-white wall with pencil graffiti, black baseboard |
| **Floor** | Material and color | gray concrete floor, light wood flooring |
| **Foreground** | Occluding or close-up objects; write "none" if none | none |
| **Furnishings** | Objects not worn on the body | half-open white door, black office chair, acrylic storage box |
| **Time of day / weather** | Only if visible | daytime indoors, dusk backlight, neon night scene |
| **Spatial light sources** | Position of lamps/windows in the environment (a spatial fact) | an overexposed patch from the ceiling light, window light from the left |
| **Atmosphere** | The character of the space | cool gray office corridor, cozy bedroom |
| **Scene changes** | Single scene or scene cut | single scene throughout; or cut to outdoors at t=4.0 |

### analysis.json (required fields)

| Field | Meaning |
|------|------|
| `scene.setting_type` | indoor / outdoor / in-car / studio / mixed |
| `scene.location` | location type (do not invent landmark names that are not seen) |
| `scene.space` | spatial structure |
| `scene.subject_placement` | subject placement and orientation |
| `scene.background` | background layer: color + material + elements |
| `scene.ground` | floor material and color |
| `scene.foreground` | foreground; write "none" if none |
| `scene.props` | environmental furnishings and interactive objects |
| `scene.time_weather` | time of day and weather (only if visible) |
| `scene.ambient_light` | position of spatial light sources |
| `scene.atmosphere` | character of the space |
| `scene.changes` | single scene throughout / scene-cut time points |
| `segments[].scene_note` | write in detail only if the scene changes in this segment, otherwise "same as whole video" |

### prompt.md "Shooting Scene" (mandatory structure)

The following entries must be used (you may add entries, but must not remove core items):

```markdown
## Shooting Scene
- Location: {indoor/outdoor + location type + spatial structure}
- Spatial relationships: {subject placement and orientation; distance from walls/doors/furniture}
- Background: {color + material + main elements}
- Floor: {material and color}
- Furnishings and props: {environmental objects; interactive non-clothing props}
- Time and ambient light: {time of day/weather + positions of spatial light sources}
- Atmosphere: {character of the space}
- Scene changes: {single scene throughout / scene-cut time points}
```

**Minimum requirements**:

1. "Location" must not be empty and must include indoor/outdoor + location type  
2. "Background" has at least 2 visible elements and includes color or material  
3. "Spatial relationships" must state the subject placement  
4. With multiple scenes, "Scene changes" must state the scene-cut time points  

Forbidden:

- Empty, uninformative phrases such as `nice scene`, `classy background`, `strong vibe`, `photogenic environment`  
- Inventing city names, shop names, or landmarks that cannot be seen in the frame  
- Writing camera movement/camera position in this section (that belongs to "Cinematography")  
- Writing body and outfit in this section (that belongs to "Scene Narrative")  

### Boundaries with Adjacent Modules

| Module | What to write |
|------|--------|
| **Scene Narrative** | The person: body, hair and makeup, outfit colors and styles, demeanor |
| **Shooting Scene** | The place: venue, placement, background and floor, furnishings, time and space |
| **Cinematography** | How it is shot: camera position, camera movement, camera focus, lighting setup |

Handheld props (cups, phones) may be named under "Furnishings and props" in Shooting Scene; the Action List only writes how the hand grips/raises them.

## Shooting Method / Camera Movement / Focal Emphasis (view frames + output, mandatory)

The generation side depends on executable camera language. The visual agent must infer camera movement by **comparing across frames** (a single frame is not enough); writing only empty phrases like "shot on a phone" or "nice camera work" is forbidden.

### Record at least the following when viewing frames

| Dimension | Writing requirement | Example words (pick the best) |
|------|----------|----------------|
| **Device/texture** | Straight-from-phone vertical / stabilizer / slight handheld shake / cinematic-like | vertical phone, gimbal follow shot, slight handheld breathing feel |
| **Camera height** | Relative to the person's eye level | eye level, slightly low angle, low-angle upward shot, slightly high angle, high-angle downward shot |
| **Shooting angle** | Horizontal bearing relative to the subject's facing direction | frontal, 3/4 side, full profile, slight over-the-shoulder, a portion of an orbit |
| **Shot size** | Proportion of the frame occupied by the subject (may write main shot size + changes) | full body, knee-up, half body, medium close-up, close-up, foot close-up |
| **Composition** | Subject placement and negative space | centered, left/right third, space below the lower body to emphasize leg length, headroom above |
| **Camera movement type** | Main camera movement for the whole video + key changes (judged across frames) | static, slight handheld shake, truck/lateral move, push in/pull out, crane up/down, orbit, follow, whip pan |
| **Camera movement rhythm** | Speed, whether it hugs the beats | steady slow push, micro-pause on strong beats, follow move on weak beats, quick half-step push on a beat-sync hit |
| **Focus/depth of field** | Sharp subject and degree of blur | full body sharp, background lightly blurred, face in focus, foreground/background separation |
| **Focal emphasis** | What the camera **is shooting / wants to show** (core) | see the table below |
| **Stability** | Degree of steadiness or shake | gimbal rock-steady, slight tremor from a walking follow shot, slight motion blur caused by the movement |

### Camera Focal Emphasis (`camera_focus` / per-segment `shot_focus`)

You must clearly state "where the camera's attention lands"; choose at least 1 primary focus, and optionally a secondary focus:

| Focus type | Applicable scenarios | Writing example |
|----------|----------|----------|
| **Full-body proportions/posture** | Dance, pose showcase | always frame the full body, emphasize the head-to-body ratio and stance lines |
| **Legs/footwork** | Steps, stepping on the beat, skirt hem | slightly low camera position to capture toe landings and step paths |
| **Waist/hips/turns** | Hip sways, body turns, beat-sync hits | waistline and hip line centered, profile emphasizing the S-curve |
| **Upper body/gestures** | Hand movements, finger hearts, adjusting the collar | half-body shot size, hand shapes clearly in frame |
| **Face/expression** | Expression-driven acting, talking-to-camera feel | medium close-up, eyes in focus, expression readable |
| **Clothing/material** | Outfits, outfit changes | follow the fabric drape, print and cut details |
| **Environment/scene** | Travel check-ins, street photography | person and background equally weighted, establishing the space |
| **Props/interaction** | Phone, cup, door, mirror | keep the contact point between prop and hand sharp |

### How to Infer Camera Movement from Keyframes (mandatory method)

1. Compare adjacent sharp frames: the subject's **position/scale** in the frame → push/pull; **left/right offset** → truck/follow; **up/down** → crane/tilt changes  
2. Direction and speed of the background sliding relative to the person → distinguish "the camera moves" from "the person moves while the camera stays fixed"  
3. Abrupt shot-size change with no continuous displacement → possibly a **cut/jump cut** (note it in Cinematography; do not disguise it as one continuous camera move)  
4. Many blurry frames, edge smearing → you may write fast motion or a whip pan, but **do not invent** a precise path  
5. When rhythm data exists: check whether camera pauses/accelerations align with accents (the fusion stage may enhance this as "camera micro-pause on strong beats")

### analysis.json (required fields)

Whole-video `camera`:

| Field | Meaning |
|------|------|
| `camera.device_feel` | device and sense of stability (phone/gimbal/handheld, etc.) |
| `camera.height` | camera height (eye level/slightly low angle/low camera position, etc.) |
| `camera.angle` | shooting angle (frontal/3/4 side, etc.) |
| `camera.framing` | main shot size + composition habits |
| `camera.movement` | main camera movement type + speed/path (one executable sentence) |
| `camera.movement_rhythm` | relationship between camera movement and rhythm (steady/micro-pause on strong beats/no rhythmic link) |
| `camera.depth_of_field` | depth of field and in-focus subject |
| `camera.focus_priority` | **Whole-video camera focal emphasis** (primary + secondary, corresponding to the table above) |
| `camera.shot_method` | **Shooting method overview** (2~4 sentences: how it is shot, why it is shot this way, what it wants to highlight) |

Per segment (required when camera movement or focus changes; if unchanged, you may write "same as whole video"):

| Field | Meaning |
|------|------|
| `segments[].shot_size` | shot size of this segment |
| `segments[].camera_move` | camera movement of this segment (static/push/follow...) |
| `segments[].shot_focus` | camera focal emphasis of this segment (face/hands/legs/full body/clothing...) |

### prompt.md "Cinematography" (mandatory structure)

The following entries must be used (you may add entries, but must not remove core items):

```markdown
## Cinematography
- Shooting method: {device/stabilization + camera height and angle + how it is shot overall and what it wants to highlight}
- Camera movement: {main camera movement path and speed; if it changes, summarize by time range; may write micro-pause on strong beats / follow move on weak beats}
- Focal emphasis: {primary focus + secondary focus; what the camera always prioritizes keeping in frame/sharp}
- Camera: {camera height, horizontal angle, stability}
- Lens: {shot size / focal-length impression / depth of field / composition}
- Lighting: {light direction, hard/soft, whether backlit/top-lit, etc.}
- Mood: {keywords}
```

**Minimum requirements**:

1. "Shooting method" must not be empty and must state **camera position + stabilization + shooting intent**  
2. "Camera movement" must describe an executable move (direction/push-pull/follow); just "dynamic camera" is forbidden  
3. "Focal emphasis" must specify the subject focus (at least 1 primary and 1 secondary, or explicitly "full body only")  
4. When there is rhythm and `ok=true`, describe the relationship between camera movement and beats as clearly as possible  

Forbidden:

- Empty, uninformative phrases such as `smooth camera movement`, `cinematic shots`, `professional filming`, `great camera sense`  
- Writing a cut as an impossible continuous long take  
- Inventing aerial/dolly-track/cinema-grade equipment that cannot be seen in the frame (unless the texture clearly supports it, in which case write "...-like texture")

### Relationship to the Action List

- Camera movement and focal emphasis are **primarily written in Cinematography**  
- An action entry may lightly mention a shot-size switch or focus change (e.g. "camera dips slightly to catch the right foot landing on the beat") without repeating the whole cinematography paragraph  

## Facial Expression (view frames + output, mandatory)

### Record at least the following per frame/segment when viewing frames

| Feature | Optional descriptions |
|------|----------|
| Brows | relaxed / slightly furrowed / raised / tightly knitted |
| Eyes | wide open / squinting / downcast / looking straight ahead / sidelong glance / smiling eyes |
| Mouth | closed with pursed lips / slightly open / toothy smile / laughing / pouting / biting lip |
| Emotion tag | cool and glamorous, sweet smile, innocent, languid, playful, confident, gentle, etc. |
| Change | Relative to the previous segment: from A to B; or "expression holds..." |

### analysis.json

- `subject.expression_gaze`: whole-video baseline (expression + gaze habits)  
- `segments[].expression`: main expression of this segment (brows/eyes/mouth + emotion + change)  
- `segments[].action`: limb description ending with where the gaze and expression land  
- `segments[].beat_hint`: the fusion stage may fill in the aligned beats  
- `segments[].body_focus`: body/posture focus emphasized in this segment (see the body section)  
- `segments[].outfit_note`: outfit change in this segment (see the outfit section)  
- `segments[].scene_note`: scene change in this segment (see the Shooting Scene section)  
- `segments[].shot_size` / `camera_move` / `shot_focus`: shot size, camera movement, and camera focal emphasis of this segment (see the cinematography section)  

### prompt.md Action List

Each entry must end with an executable expression sentence.  
The timeline is **preferentially aligned** to `rhythm_plan.accent_times` / `beats` (if `rhythm_analysis.ok=true`).

Forbidden: empty phrases such as `natural expression`, `good look`, `has feeling`.

## Visuals × Rhythm Fusion (mandatory)

When `ok=true` in `rhythm_analysis.json`:

1. **Action List timings** should land near beats as much as possible (rounding of ±0.05~0.1s allowed)  
2. **Strong beats / accents** must have a perceptible accented move: firm step, micro-pause, skirt flick, arm swing, half-beat freeze, etc.  
3. **Background Audio** must state the **BPM number** + the beat-sync relationship (one step per beat / timestamps of major beat-sync hits in seconds)  
4. Visual facts take priority: do not invent clothing/props absent from the frames for the sake of beat-sync; you may shift the **timing and force** of existing moves onto the beat  
5. If the original footage's moves are steady but the music has a beat → write the generation prompt as a "beat-sync enhancement" and note this in Background Audio  

When `ok=false` (no audio track / analysis failed):

- Do not force a fake BPM  
- Actions follow the visual timeline  
- Background Audio is a conservative guess  

## Action List Specification (mandatory)

### Entry Count and Timing

- Split by duration: roughly one entry every 0.5~1.5 seconds; when beats exist, group by **1~2 beats** or by key accents  
- For ≤10s, 6~12 entries are recommended; longer videos may use 12~16  
- Format of each step: `N. start–end seconds (beat/strong beat, optional): ...`  
- Vague words are forbidden: e.g. "dance", "strike a pose", "make a gesture"

### Every Action Entry Must Include All 5 of the Following

| Required item | Writing requirement | Example |
|--------|----------|------|
| **Left/right limbs** | Specify left/right hand, left/right leg, supporting leg | right knee bent and raised, left leg supporting |
| **Angle/amplitude** | Approximate angle or amplitude of the leg lift/body turn/arm opening | right leg raised forward about 45° |
| **Hand shape** | Palm orientation, finger shape, fist/open, etc. | right index finger touches the cheek, left palm facing up |
| **Gaze** | Looking at the camera / looking down / looking sideways, etc. | looking straight into the camera |
| **Facial expression** | Brows + eyes + mouth + emotion; for changes write "from ... to ..." | brows raised, toothy smile |

When rhythm data exists, the following is also recommended:

| Item | Requirement |
|----|------|
| **Beat-sync** | State the relationship to strong beats: stepping on the beat / micro-pause / limb flick, etc. |

### Checklist (self-check after writing)

- [ ] Does the Scene Narrative include **overall build + ≥2 per-part/proportion body details + posture**  
- [ ] Are `body_type` / `body_proportions` / `body_details` / `posture_habit` filled in `analysis.json`  
- [ ] Does the Scene Narrative outfit include **color + style for each item**; at least 1 style tag  
- [ ] Are `summary` / `style` / `palette` / `items` (each with `color`+`style`) filled in `subject.outfit` of `analysis.json`  
- [ ] Is there a standalone **Shooting Scene** section (venue + ≥2 background elements + subject placement)  
- [ ] Are core fields such as `setting_type` / `location` / `subject_placement` / `background` filled in `scene` of `analysis.json`  
- [ ] Shooting Scene does not redundantly repeat the Scene Narrative/Cinematography  
- [ ] Does Cinematography include **shooting method + camera movement + focal emphasis** (not empty phrases)  
- [ ] Are core fields such as `shot_method` / `movement` / `focus_priority` filled in `camera` of `analysis.json`  
- [ ] Was the camera movement derived from cross-frame comparison; cuts not disguised as long takes  
- [ ] Does every action have a time range  
- [ ] Does every entry clearly state left/right, angle, hand shape, gaze, face  
- [ ] If there is a rhythm file: is the BPM written into Background Audio  
- [ ] If there are accents: are the major beat-sync hits reflected in the Action List  
- [ ] No key content invented that is not in the frames (including invisible body parts, undetectable professional equipment, unseen landmarks, invisible brands)  
