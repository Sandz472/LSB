# Sampu Dynamics — Design Doctrine v0.1

> Source: Founder's whiteboarding notes (Laws of UX, Design Masterclass), July 2026.
> Scope: Governs all product surfaces across Sampu Dynamics.
> Position in hierarchy: Lives in `sampu-codex`. Import into project-level CLAUDE.md via `@import`.

---

## 0. Foundation

All design decisions defer to the **Laws of UX** (lawsofux.com) as the baseline reference for interaction patterns. When in doubt, check the law before inventing a pattern. The most load-bearing laws for our products:

- **Hick's Law** — fewer choices, faster decisions. One primary action per screen.
- **Jakob's Law** — our users spend their day in WhatsApp and banking apps. Our products should feel familiar to *those* surfaces, not to Silicon Valley SaaS.
- **Peak-End Rule** — users judge the experience by its peak moment and its ending. Engineer both deliberately (see §3, emotional support).
- **Doherty Threshold** — respond in under 400ms or show progress. Critical under load-shedding and variable connectivity: perceived speed is a designed property, not a network property.

Every design must still clear the **three gates**: Quality (world-class craft under real African constraints), Impact (measurable change for named users), Value (compounding, defensible worth).

---

## 1. Landing Page

The landing page has exactly four jobs. If an element doesn't serve one of them, cut it.

1. **Make a strong impression (Brand).** First contact must feel deliberate, crafted, and unmistakably not template-generated.
2. **Clear value proposition.** One sentence a Soweto entrepreneur understands in three seconds: what the product does and why it matters to *their* business.
3. **Answer to all users.** The page must work for every segment of the product's target market — without splitting focus.
4. **Make it obvious what to do next.** Exactly **one call to action**. One button. Everything on the page funnels toward it.

### Landing page anatomy (per tuffgrowth.com structure)

- **Hero section:** logo, short copy, image or video showing *what the app actually looks like* — the visitor should be able to picture themselves inside it.
- **Heading / description / value prop** as the contrasting elements the eye lands on first.
- **CTA button** in the hero — the single action.
- **Reviews as microcopy** near the CTA (trust at the decision point).
- **Social proof** further down the page: customer logos, testimonials.
- **How it works / Benefits** section closing the argument.

**Application pattern:** Hero shows the product's core outcome being produced in seconds on a phone. Value prop names that outcome in the user's own words. CTA invites the first real outcome, free. Social proof starts with Sampu Dynamics itself (dogfooding is the first case study).

---

## 2. Onboarding — the First User Experience

**Prime directive: show the value *before* asking for conversion.** No paywall, no lengthy form, no compliance admin before the user has felt the product work.

### The flow

```
Account setup → User-selected goal → User data (to improve experience)
      → Give some value → Show where to get started → Into the app
```

1. **Account setup** — minimal. Name, phone, business name. Nothing more.
2. **User-selected goal** — "What do you want to do first?" (offer the product's two or three core outcomes). The goal shapes everything after it.
3. **User data to improve experience** — only what's needed to make the *first output* better. Frame every field as "this makes your output better," never as admin.
4. **Give some value ASAP** — the user must produce something real and finished within the first minutes.
5. **Get users interacting with features** — value comes from doing, not from a tour. No passive walkthroughs.
6. **Orient users** — at every step they know where they are and what to do next. Never a dead end.

**Show, don't tell — in metrics.** When value lands, quantify it: "Done in 90 seconds. Sent via WhatsApp." Metrics make the value undeniable.

**Application pattern:** the aha moment is a professional, real output delivered to a real recipient before the user has paid anything or completed any admin setup.

---

## 3. Key Feature Loop

The main feature people use is the loop that determines **how often they come back** and **how much value the app compounds**. Design the loop before designing the screens.

### Loop structure

```
Objective → Input → Output → Success → Share
    ↑___________________________________|
```

- **Objective:** what is the user trying to achieve? Name it in the user's own terms, not the app's.
- **Input:** as a user, what do I give or do? Keep it minimal — our AI substrate should shrink input to near zero (a voice note, a photo, one tap).
- **Output:** what do I get in return? A crafted, professional result that makes the user look established.
- **Success:** the moment of achievement, made visible and named.
- **Share:** something worth talking about. A summary artifact designed for WhatsApp status and socials. Every share is organic acquisition.

### Loop principles

1. **Make it as intuitive as possible.** The loop must survive a first-time smartphone-only user with no training.
2. **Support the user emotionally as well as functionally.** Congratulate them. Celebrate the first output, the first win, the milestones. For a solo founder grinding alone, the product should be the colleague who notices.
3. **Make it shareable.** Build the share artifact into the loop, not as an afterthought.
4. **Value compounds over time.** Every interaction enriches the user's own record — their history, their data, their trail. Month 6 must be dramatically more valuable than day 1. This is the retention moat and the reason people pay.

---

## 4. Product Identity System

**Problem stated plainly: people can tell when something is AI-generated.** Generic gradients, default fonts, template layouts — they signal "no one crafted this." That fails the Quality gate before a single feature ships.

### The identity pass (run once, maintain forever)

| Element | Method | Tools |
|---|---|---|
| **Name** | Iterate with LLM; test against users | Any LLM |
| **Logo** | Reference-driven; LLM for examples + palette | dribbble.com |
| **Colour scheme** | Curated palette, locked | dribbble.com, coolors.co |
| **Design style** | Named aesthetic direction, documented | dribbble.com |
| **Fonts** | Deliberate pairing (heading / sub / body) | fontshare.com, fonts.google.com |

### Design system as anti-drift infrastructure

Maintain a **high-level design system so the AI never drifts.** Tokens, components, and style rules live in version control (`sampu-codex`), and every AI-assisted build session imports them. The system, not the session, holds the aesthetic.

**Reusable prompt pattern** (from notes): *"Create a prompt I could use to design my app based on the attached UI style — list the dependencies. Keep it concise."* → Generate once, store the resulting design prompt in the codex, reuse across Claude Code sessions.

**Sampu identity standard:** every product identity must read as proudly South African and professionally credible — the aesthetic of a business that belongs in the room, built for sunlight-readable screens, low-end Android devices, and data-light loading.

---

## 5. Constraint-Native Design Rules (the African moat, applied to UX)

These principles filter through Sampu Dynamics' standing commitments:

- **Offline-tolerant loops.** The key feature loop must not break under load-shedding. Draft locally, sync when connected, never lose work.
- **Data-light by default.** Landing page and app shell optimised for low-bandwidth. Perceived performance is a design deliverable.
- **WhatsApp as a first-class surface.** Output (quotes, invoices, share cards) lands where SA business already happens.
- **Trust signals for a low-trust market.** Social proof, POPIA-visible privacy posture, and professional output quality are conversion features, not compliance chores.

---

## 6. Review Checklist (attach to every design PR)

Before any surface ships, answer:

1. Landing: is there exactly one CTA? Can a stranger state the value prop after 5 seconds?
2. Onboarding: does the user reach real value before any conversion ask? Is the aha moment under 3 minutes?
3. Loop: are Objective → Input → Output → Success → Share all present and named? Is the share artifact built?
4. Emotion: where does the design congratulate or acknowledge the user?
5. Identity: does it look crafted, or does it look generated? (If unsure, it looks generated.)
6. Constraints: does it survive load-shedding, low bandwidth, and a R1,500 Android phone?
7. Gates: Quality — Impact — Value. Name the evidence for each.

---

*v0.1 — distilled from founder whiteboarding notes, 11 July 2026. Iterate as products ship.*
