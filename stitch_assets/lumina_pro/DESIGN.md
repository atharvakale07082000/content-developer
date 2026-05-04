# Design System Specification: The Desktop Precision Engine

## 1. Overview & Creative North Star: "The Digital Architect"
This design system is not a template; it is a high-performance instrument for professionals. Our Creative North Star is **"The Digital Architect."** Much like a physical architectural studio, the UI should feel like a clean, well-lit workspace—expansive, deliberate, and composed of premium materials.

We break the "generic SaaS" mold by rejecting the standard "grid of boxes." Instead, we embrace **Intentional Asymmetry** and **Tonal Depth**. Navigation might live in an offset floating rail; content is grouped by light and shadow rather than lines; and typography is treated as a structural element, not just a label. We aim for a "quiet" interface that speaks through quality, not noise.

---

## 2. Color & Materiality
Our palette is a sophisticated range of cool grays and architectural stones, designed to minimize eye strain while maximizing focus.

### The "No-Line" Rule
**Explicit Instruction:** Traditional 1px solid borders are prohibited for sectioning. We define space through "Material Shifts." 
- To separate a sidebar from a main stage, use a transition from `surface` (#f9f9fb) to `surface-container-low` (#f2f4f6).
- For internal groupings, use `surface-container` (#ebeef2). 

### Surface Hierarchy & Nesting
Treat the UI as a physical stack of paper and glass.
- **Base Layer:** `surface` (#f9f9fb)
- **Secondary Workspaces:** `surface-container-low` (#f2f4f6)
- **Interactive Elements/Cards:** `surface-container-lowest` (#ffffff)
- **Elevated Modals:** `surface-bright` (#f9f9fb)

### The "Glass & Gradient" Rule
To elevate the "SaaS-grade" feel, use **Backdrop Blurs**. Floating panels (like command menus or global headers) should use `surface-container-lowest` at 80% opacity with a `20px` backdrop-blur. 
- **Signature Polish:** For primary CTAs, apply a subtle linear gradient from `primary` (#5f5e60) to `primary_dim` (#535254) at a 145-degree angle. This adds a "milled metal" weight that flat colors lack.

---

## 3. Typography: Editorial Authority
We utilize a bespoke implementation of the **Inter** family to mimic the precision of San Francisco. Typography is our primary tool for hierarchy.

- **Display & Headlines:** Use `display-md` (2.75rem) for high-impact data points or welcome states. These should always have a letter-spacing of `-0.02em` to feel tight and custom.
- **Titles as Anchors:** `title-lg` (1.375rem) serves as the primary anchor for content blocks. Ensure `on_surface` (#2d3338) is used for maximum legibility.
- **The Label Strategy:** Use `label-md` (0.75rem) in `on_surface_variant` (#596065) for metadata. This "fades" secondary information, allowing the user's eye to jump directly to primary content.
- **Contrast Ratios:** Never use pure black. Our darkest "ink" is `on_background` (#2d3338), ensuring a soft, premium "ink-on-paper" feel.

---

## 4. Elevation & Depth
In this system, depth is a function of light, not lines.

### The Layering Principle
Avoid "drop shadows" on every card. Instead, create depth by nesting:
1. **Background:** `surface`
2. **Section:** `surface-container-low`
3. **Card:** `surface-container-lowest` (This creates a natural "pop" without a single shadow pixel).

### Ambient Shadows
When an element must float (e.g., a dropdown or modal), use an **Ambient Shadow**:
- **Offset:** `0px 12px 32px`
- **Color:** `on_surface` (#2d3338) at **4% opacity**.
- **Result:** A shadow so soft it feels like a natural lighting occlusion rather than a digital effect.

### The "Ghost Border" Fallback
If contrast is required for accessibility (e.g., in Dark Mode or on extremely similar surfaces), use a **Ghost Border**:
- **Stroke:** 1px
- **Color:** `outline_variant` (#acb3b8) at **20% opacity**.

---

## 5. Components

### Buttons
- **Primary:** Gradient fill (`primary` to `primary_dim`), `xl` (0.75rem) roundedness, `on_primary` text.
- **Secondary:** `surface-container-highest` (#dde3e9) background. No border.
- **Tertiary:** Ghost style. No background until hover, then `surface-container-low`.

### Cards & Lists
- **Rule:** Absolute prohibition of divider lines (`<hr>`).
- **Separation:** Use **Spacing 4** (1.4rem) between list items or a subtle background toggle between `surface-container-lowest` and `surface-container-low` on hover.

### Input Fields
- **Resting State:** `surface-container-low` background, no border, `md` (0.375rem) roundedness.
- **Focus State:** `surface-container-lowest` background with a 1px `primary` Ghost Border at 40% opacity.
- **Error:** Background stays `surface-container-low`, but the label shifts to `error` (#9f403d).

### Specialized Components: The "Command Rail"
Instead of a standard top-nav, use a floating vertical rail on the left.
- **Material:** `surface-container-lowest` with an 80% opacity and blur.
- **Interaction:** Active states use a `primary` vertical "pill" indicator (2px wide) on the far left edge.

---

## 6. Do's and Don'ts

### Do:
- **Use "Optical Pacing":** Use **Spacing 12** (4rem) or **16** (5.5rem) between major sections to let the UI "breathe."
- **Nesting Logic:** Always place a lighter surface on a darker surface to indicate "lift."
- **Micro-interactions:** Use 200ms "Ease-Out" transitions for all hover states.

### Don't:
- **Don't use 100% Opaque Borders:** This shatters the "Architectural" feel and makes the UI look like a legacy table.
- **Don't use Pure Grey Shadows:** Always tint your shadows with the `on_surface` color to maintain tonal harmony.
- **Don't over-round:** Stick to `md` (0.375rem) for most elements. `full` is reserved exclusively for status chips and tags. High-end design lives in the subtle curve, not the circle.