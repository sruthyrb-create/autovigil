# AutoVigil: video demo script (about 2:45)

**Title:** "You're not imagining it"
**Setup:** Record your screen at 1080p with a headset mic. Open these tabs beforehand: the deck, `/driver`, `/analyst`, the Orchestrate Defect Analyst chat, and `/research`. Speak slowly and leave half a second of silence between sections.

---

## 0:00–0:20 · The moment (deck: cover, then the "moment" slide)

**SAY (quiet, personal):**
> "Picture this. You're on the highway, kids in the back, nothing in front of you.
> And your car slams on the brakes. By itself.
> The truck behind you swerves. You take it to the dealer. They say, 'We can't reproduce it.'
> So you start to wonder if you imagined it."

*(pause)*

> "You didn't. And you weren't the only one."

## 0:20–0:45 · It really happened (story slide, then tucson slide)

**SAY:**
> "This happened to Hyundai Tucson owners. From early 2025, hundreds of them reported the same thing publicly, each one thinking they were alone.
> In May 2026 Hyundai recalled 421,078 cars. By then there had been four crashes and four injuries.
> The warning signs were public the whole time. Nobody was connecting them.
> AutoVigil did. Its alarm for the Tucson went off in February 2025, sixty-six weeks before the recall, using only public reports."

**ON SCREEN:** Hold on the timeline and point at the red dot.

## 0:45–1:00 · What it does (insight slide)

**SAY:**
> "AutoVigil reads every complaint drivers file with the government. IBM's Granite AI works out what each one is really about, and AutoVigil raises an alarm when one car model has far more reports than it should.
> Hundreds of lonely complaints become one clear warning."

## 1:00–1:40 · Driver demo: just talk (switch to `/driver`)

**DO:** Tap the big red microphone. Wait for the greeting, then say:
> "My Tucson braked hard on the highway with nothing in front of me."

**ON SCREEN (happens by itself):** The Tucson appears: "40× more than a typical car", the red bars, the chart, the recall and owner stories.

**LET THE AGENT ANSWER**, then **SAY to camera** while it talks or right after:
> "I didn't fill in a form. I just told it what happened, and it pulled up my car: other owners are reporting this far more than normal. You're not imagining it."

**DO:** Answer two follow-ups, e.g. "About 65 miles an hour, adaptive cruise was on." The safety report card appears and its ring fills up.

**SAY:**
> "While we talk, it writes the safety report investigators actually need, and shows me what's still missing. One tap to copy, one tap to submit."

## 1:40–2:10 · Analyst demo (switch to `/analyst`)

**SAY:**
> "Drivers can't order a recall. Safety analysts and regulators can, but they're buried in tens of thousands of complaints."

**DO:** Click the **Tucson** row, then **Draft memo with IBM Granite**.

**SAY:**
> "Here's this week's ranked list, including problems with no recall yet, like this Chevy Equinox EV.
> One click, and IBM Granite writes the investigation memo: reports, crashes and real quotes.
> Hours of reading become one minute."

**DO (5 seconds):** Show the Orchestrate Defect Analyst chat with one question already answered.

> "The same work runs as agents in IBM watsonx Orchestrate. That's IBM's theme: make work less boring."

## 2:10–2:30 · Proof (results slide, or `/research` showing the Tesla chart)

**SAY:**
> "This isn't one lucky guess. I replayed ten years of complaints week by week, so the system only knew what was known at the time.
> Eight of eight past government investigations seen coming, almost a year early on average. Tesla phantom braking: sixty-five weeks early.
> Granite cut false alarms in half. And I publish the misses too."

## 2:30–2:45 · Close (close slide)

**SAY (slow, confident):**
> "Automatic emergency braking is about to be required on every new car. More cars making split-second decisions means more people asking, 'Did that just happen?'
> AutoVigil is free, built on public data, and live today.
> You're not imagining it.
> And now, you'll know.
> I'm Sruthy. This is AutoVigil."

---

### Tips
- If the voice agent is slow, cut the pause in editing. Don't re-record.
- If the hall is noisy, type the same sentence into the "Type instead" box; the car and report still appear on screen.
- Make sure the memo label reads "IBM Granite" (meaning the watsonx env vars are set), not "template".
- Never show `.env`, Code Engine env vars, or any API key on screen.
- If a judge asks whether the method is proven, answer: it's the same signal-detection math drug-safety teams use for medicines, adapted to cars.
- Use captions if you can; judges often watch muted.
- Upload to YouTube as Unlisted and paste the link into Devpost.
