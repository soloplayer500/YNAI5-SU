# RVC Voice Pipeline — Shami's Voice on Suno Music
_Researched: 2026-03-11 | Hardware: Ryzen 5 5500U, 8GB RAM, integrated GPU only_

> Note: WebSearch/WebFetch unavailable during this session. Research is based on Claude training knowledge (cutoff Aug 2025). Verify links and version numbers live before executing. Key verification points are flagged with [VERIFY].

---

## Summary Verdict

**Yes, RVC + Applio runs on CPU-only.** It is slower, but fully functional on a Ryzen 5. The easiest path to a first result today is the **ElevenLabs voice clone → Suno instrumental → CapCut mix** route — no installation needed, results in under 2 hours. Applio/RVC training is the better long-term solution but takes 4–8+ hours on CPU.

---

## 1. Applio — Current State (2025)

### What It Is
Applio is a GUI wrapper for RVC (Retrieval-based Voice Conversion) built by IAHispano. It is the most actively maintained RVC implementation as of 2025, with a clean web UI, built-in dataset tools, and audio separation.

### Current Version
- As of Aug 2025: **Applio v3.x** (check https://github.com/IAHispano/Applio for latest)
- [VERIFY] Latest release tag on GitHub releases page

### Download
- GitHub: https://github.com/IAHispano/Applio
- Releases page: https://github.com/IAHispano/Applio/releases
- There are two install paths:
  - **Windows .bat installer** (easiest — recommended for Shami)
  - **Google Colab notebook** (free GPU, no local install — best for training)

### CPU-Only Support
**YES — Applio runs on CPU.** Key points:
- During installation, Applio auto-detects hardware. If no CUDA GPU is found, it falls back to CPU mode.
- In `run-applio.bat` or the launcher, there may be a `--device cpu` flag option.
- Training on CPU is slow (see Section 4 for time estimates).
- **Inference (conversion, not training) on CPU is much faster** — applying a trained model to audio takes 30 seconds to a few minutes even on CPU.
- The integrated Radeon Vega 7 GPU will NOT help — RVC requires CUDA (NVIDIA) or ROCm (AMD, experimental). Applio's AMD ROCm support is limited and unreliable on integrated graphics. Stick to pure CPU mode.

### System Requirements (CPU Mode)
- RAM: 8GB minimum — Applio will work but keep other apps closed
- Storage: ~5–10GB for Applio + models + datasets
- Python 3.10 or 3.11 (installed automatically by the .bat installer on Windows)

---

## 2. RVC Voice Training Requirements

### Audio Minutes Needed
| Quality Tier | Minutes of Audio | Expected Model Quality |
|---|---|---|
| Minimum viable | 5–10 min | Recognizable but artifacts |
| Recommended | 15–30 min | Good quality conversion |
| High quality | 45–60 min | Clean, natural output |
| Overkill | 2+ hours | Marginal improvement |

**For a first test: 10 minutes is enough to see if it works.**
**For real content: aim for 20–30 minutes of clean audio.**

### Audio Quality Requirements
- **Format:** WAV (preferred) or FLAC. MP3 is acceptable but avoid high compression.
- **Sample rate:** 44.1kHz or 48kHz — do NOT use 8kHz or 16kHz voice recordings.
- **Bitrate:** 24-bit preferred, 16-bit fine.
- **Channels:** Mono (1 channel) is preferred for training. Stereo works but mono is cleaner.
- **Background noise:** As close to zero as possible. Use a quiet room or a basic mic with pop filter.
- **Content:** Natural speech, varied pitch and pace. Read articles, rap lyrics, sing scales — the more pitch variation, the better the singing model.
- **No music in background** — pure voice only. Applio has a UVR (Ultimate Vocal Remover) built in to strip music if needed.

### Recording Tips for Shami
- Use any smartphone in a closet or quiet room (clothes absorb echo).
- Record 5 files of 2–5 minutes each — easier to manage than one long file.
- Read varied text: news articles, rap verses, spoken word. Vary your pitch intentionally.
- If you have a USB mic or headset mic, use that over phone speaker.
- Save as WAV if possible (most voice recorder apps have WAV/FLAC option in settings).

---

## 3. Full Pipeline: Voice Training Path (Applio RVC)

### Step 1 — Record Voice Dataset
- Record 15–30 min of clean vocal audio (WAV, 44.1kHz, mono)
- Split into 5–15 minute files
- **Time: 30–60 min**

### Step 2 — Install Applio
1. Go to https://github.com/IAHispano/Applio/releases
2. Download the Windows installer zip or clone the repo
3. Run `run-install.bat` — it installs Python + dependencies automatically
4. Launch with `run-applio.bat`
5. Opens at http://localhost:7897 in browser
- **Time: 20–40 min (first install, including download)**

### Step 3 — Prepare Dataset in Applio
1. In Applio UI → **Dataset Maker** tab
2. Upload your WAV recordings
3. Run audio slicing (splits into 3–10 second clips automatically)
4. Applio will de-noise and format clips
5. Result: a dataset folder ready for training
- **Time: 5–15 min**

### Step 4 — Train the Model (CPU — this is the slow part)
1. In Applio UI → **Train** tab
2. Set model name (e.g., `shami-v1`)
3. Select your dataset folder
4. Key settings for CPU:
   - **Batch size:** Set to 2 (lower = less RAM, safer on 8GB)
   - **Epochs:** Start with 100–200 for a test. 300–500 for quality.
   - **Pitch extraction algorithm:** Use **rmvpe** (best quality, slower) or **harvest** (faster, less accurate on CPU)
5. Click Train and wait (see time estimates below)
- **Time: 4–12 hours on CPU (see Section 4)**

### Step 5 — Generate Suno Instrumental
1. In Suno → use **Custom Mode**
2. Write your own lyrics in the lyrics box
3. In the **Style** field, describe the music style but specify: `"no AI vocals, instrumental only"` or enable instrumental toggle if available [VERIFY current Suno UI]
4. Alternatively: generate a song normally, then use Applio's built-in **UVR (audio separator)** to strip Suno's AI vocals, leaving only the instrumental
5. Export the instrumental as WAV/MP3
- **Time: 5–10 min**

### Step 6 — Record Your Actual Vocal Performance
1. Play the Suno instrumental in your headphones
2. Record yourself singing/rapping over it (phone or mic)
3. Export as WAV
- **Time: 15–30 min**

### Step 7 — Apply RVC Voice Conversion (Optional Enhancement)
This step takes your recorded voice and makes it cleaner/more consistent using your trained model:
1. In Applio UI → **Inference** tab
2. Upload your vocal recording
3. Select your trained model (`shami-v1`)
4. Set pitch shift (0 = no change, adjust to match song key)
5. Click Convert
6. Output: converted vocal WAV
- **Time on CPU: 30 seconds to 5 minutes per track**

### Step 8 — Mix in CapCut
1. Import the Suno instrumental track
2. Import your vocal track (raw or RVC-converted)
3. Layer them on the timeline
4. Use CapCut's audio tools:
   - **Volume**: lower instrumental to ~70%, vocal at 100%
   - **Fade in/out** on transitions
   - **Noise reduction** on vocal if needed
   - **EQ/enhance voice**: CapCut has a basic voice enhance filter
5. Export as MP4 or audio-only
- **Time: 15–30 min**

---

## 4. CPU Training Time Estimates — Ryzen 5 5500U

| Epochs | Dataset Size | Estimated Time (CPU) |
|---|---|---|
| 100 epochs | 10 min audio | 3–5 hours |
| 200 epochs | 10 min audio | 6–10 hours |
| 300 epochs | 20 min audio | 10–16 hours |
| 500 epochs | 30 min audio | 18–30 hours |

**Reality check:** CPU training is painful but doable overnight. Set it to train at night, check results in the morning.

**Better alternative for training: Google Colab**
- Applio has an official Colab notebook: [VERIFY current link on GitHub]
- Free Colab gives T4 GPU — 300 epochs on 20 min audio = ~30–60 min
- Upload your dataset to Google Drive, run the notebook, download the `.pth` model file
- Use that model locally in Applio for inference (inference is fast on CPU)
- **Recommended approach: train on Colab (free), run inference locally**

---

## 5. Suno Instrumental Mode

### Current Suno Options (as of mid-2025)
- **Custom Mode:** Write your own lyrics + style prompt. This gives most control.
- **Instrumental toggle:** Suno has an "Instrumental" checkbox in Custom Mode that removes AI vocals entirely and generates pure music.
- **Style prompt tip:** Add words like `"instrumental, no vocals, pure music, beat"` to the style field even with the toggle on — reinforces the output.
- **Stems export:** Suno Pro plan offers stems (separate vocal/instrumental tracks). Free plan = full mix only.
- **UVR workaround (free):** Generate a song normally → use Applio's built-in UVR or a standalone UVR tool to remove the AI vocals → keep the instrumental. Quality loss is minimal.

### Recommended Workflow for Free Tier
1. Generate song in Suno Custom Mode with instrumental toggle ON
2. If Suno vocal bleeds through, run through UVR in Applio to clean it
3. Use result as backing track

---

## 6. Alternative Path: ElevenLabs Voice Clone + Suno Instrumental

### Why This Is the Fastest Path Today
- ElevenLabs is already connected with 10K credits/month
- No GPU or training needed
- Voice clone setup takes ~10 minutes
- Results are professional quality for spoken voice; singing quality varies

### ElevenLabs Voice Clone Setup
1. Go to ElevenLabs → **Voice Lab** → **Add Voice** → **Voice Clone**
2. Upload 1–3 minutes of clean voice recording (WAV preferred)
3. ElevenLabs trains instantly (cloud-side, ~1–2 min)
4. Clone is saved to your voice library

### Workflow: ElevenLabs + Suno
1. Generate Suno instrumental (custom mode, instrumental ON)
2. Write your lyrics as text
3. In ElevenLabs → select your cloned voice → paste lyrics → generate audio
4. Download the ElevenLabs vocal output
5. Import both into CapCut and mix

### Limitations
- ElevenLabs is TTS (text-to-speech), not a singing model — it speaks lyrics, doesn't sing them with musical pitch
- Output will sound like spoken word/rap, not melodic singing
- For rap-style or spoken word content: excellent
- For melodic singing: poor — use RVC instead
- 10K free credits = ~100–200 voice generations depending on length

### Credits Estimate
- 1 credit ≈ 1 character of text generated
- A 16-bar rap verse (~500 characters) = ~500 credits
- 10K credits = ~20 full verse generations/month on free tier

---

## 7. CapCut Audio Mixing — Layering Voice Over Instrumental

### Basic Setup
1. Open CapCut desktop (or mobile)
2. **New Project** → add the Suno instrumental as the main track
3. **Add Audio** (+ button) → upload your vocal file as a second audio track
4. Both tracks appear as separate layers on the timeline

### Key Settings
| Setting | Value | Why |
|---|---|---|
| Instrumental volume | 60–75% | Make room for vocals |
| Vocal volume | 90–100% | Vocals sit on top |
| Vocal noise reduction | ON | Cleans recording artifacts |
| Voice enhance | ON | Basic EQ + presence boost |
| Fade in (intro) | 1–2 sec | Clean entry |
| Fade out (outro) | 2–3 sec | Professional exit |

### Pro Tips for CapCut Mix
- Use **"Detach Audio"** on any video clip to work with audio separately
- **Normalize** both tracks so levels match before adjusting balance
- If vocal sounds echoey: apply **Noise Reduction** + reduce reverb if option available
- Export at **1080p** for video, or audio-only as WAV for further editing

### Limitations of CapCut for Mixing
- No true multitrack mixing (limited EQ, no compressor, no reverb control)
- Good enough for content creation, not professional music production
- If you want more: **Audacity** (free, open source, Windows) — proper multitrack DAW

---

## 8. Easiest Path to First Result TODAY

**Recommended: ElevenLabs + Suno + CapCut route**
No installation, no training, results in 1–2 hours.

### TODAY Action Plan (Step by Step)

#### Step 1 — Record Your Voice Sample (20 min)
- Find a quiet room, use phone or headset mic
- Record 1–3 minutes of natural speech (any text — a news article, lyrics, anything)
- Save as WAV or MP3 — quality matters more than format here
- Keep it clean: no background music, minimal echo

#### Step 2 — Create ElevenLabs Voice Clone (10 min)
- Go to elevenlabs.io → Voice Lab → Add Voice → Voice Clone
- Upload your recording
- Name it "Shami-v1" or similar
- Wait 1–2 min for clone to process
- Test: type a sentence and generate — confirm it sounds like you

#### Step 3 — Generate Suno Instrumental (10 min)
- Go to suno.com
- Custom Mode → check Instrumental toggle ON
- Style: describe your target genre (e.g., `"trap beat, dark, 808 bass, atmospheric"`)
- Leave lyrics blank or write a style guide
- Generate 2–3 variations, pick the best instrumental
- Download it

#### Step 4 — Write and Generate Vocal (20 min)
- Write 8–16 bars of lyrics for the track
- In ElevenLabs → select your Shami-v1 clone → paste lyrics → generate
- Adjust speed/style settings if available
- Download the vocal audio file

#### Step 5 — Mix in CapCut (20 min)
- New project in CapCut
- Import instrumental + vocal as separate audio tracks
- Set instrumental to 65%, vocal to 95%
- Add noise reduction to vocal
- Export as MP4 or audio

**Total time: 80 min** for a complete first test.

---

## 9. Long-Term Recommendation: Colab + Applio Path

Once the ElevenLabs test proves the concept works:

1. **Record 20–30 min of voice dataset** (varied pitch, spoken + sung)
2. **Run Applio training on Google Colab** (free T4 GPU, ~1 hour)
3. **Download the `.pth` model file** to local machine
4. **Install Applio locally** for inference only (fast on CPU)
5. **Use RVC to convert vocal performances** — much higher quality singing voice than ElevenLabs TTS
6. **Mix in CapCut or Audacity**

This path gives a custom singing voice model — proper musical output, not spoken-word TTS.

---

## 10. Tool Stack Summary

| Tool | Purpose | Cost | Where |
|---|---|---|---|
| ElevenLabs | Voice clone → TTS vocals | Free (10K credits/month) | elevenlabs.io |
| Suno | AI instrumentals | Free tier available | suno.com |
| Applio | RVC training + inference | Free, open source | github.com/IAHispano/Applio |
| Google Colab | Free GPU for training | Free (T4 GPU) | colab.research.google.com |
| CapCut | Mix vocal + instrumental | Free | capcut.com |
| Audacity | Advanced audio editing | Free | audacityteam.org |

---

## 11. What to Verify Live (Before Executing)

| Item | Where to Check |
|---|---|
| Applio latest version + CPU mode | github.com/IAHispano/Applio/releases |
| Applio Colab notebook link | GitHub README |
| Suno instrumental toggle location | suno.com Custom Mode UI |
| Suno stems export (Pro vs Free) | suno.com pricing page |
| ElevenLabs voice clone credit cost | elevenlabs.io pricing |
| Applio Windows .bat installer works on Windows 11 | GitHub issues/README |

---

_Research basis: Claude training knowledge (Aug 2025 cutoff). Web search unavailable at time of research — verify live links before executing._
_Saved: 2026-03-11_
