---
title: NPC Design
slug: npc-design
section: Mechanics
status: published
order: 0
created_by: admin
updated_by: admin
---
# Arcadium NPC Design

> Living document — evolving design for large-scale, society-driven NPC simulation.

* * *

## 1. Glossary & Terms

A quick reference for consistent vocabulary.

-   **NPC**: A simulated individual identity that generates intents and can be modeled at multiple fidelities.

-   **Thin NPC (Tier 2)**: Minimal-state NPC; event-driven; bounded intents; no pathfinding unless promoted.

-   **Thick NPC (Tier 3)**: Expanded-state NPC; richer memory/relationships; higher-frequency updates while relevant.

-   **Narrative NPC (Tier 4)**: Permanently persistent/authored or otherwise protected from demotion.

-   **Cohort (Tier 0/1)**: Population abstraction representing many individuals; emits aggregate pressure/signals.

-   **Cohort Agent**: A cohort representative that behaves like an “agent” for policy, staffing, migration, etc.

-   **Promotion**: Increasing an NPC’s fidelity due to player/system interest.

-   **Demotion**: Reducing fidelity when irrelevant; **history is not deleted** (static history).

-   **Relevance TTL**: Time-to-live timer for interest; expiry triggers demotion under budget pressure.

-   **Anchor**: A stable reference to a place (e.g., `home_anchor`, `work_anchor`, intent destinations).

-   **Place**: A first-class location entity (building/venue/unit) with qualities used by NPCs and systems.

-   **Building / Venue**: A kind of place; building is structural, venue is a service/usage context.

-   **Environment**: “Right here, right now” context derived from place state (crowding, noise, privacy, cleanliness, safety, aesthetics). Can gate actions.

-   **Intent**: NPC expression of _what they want_, not _how it happens_.

-   **Intent Resolution**: Higher-level system chooses outcomes/destinations for intents.

-   **Constraints**: Limits on intent feasibility (budget, legality, access, environment gating).

-   **Event Boundary**: Discrete simulation moment (wake, commute start, shift start/end, meal, interaction end) where Thin NPCs update.

-   **Arbitration**: Selecting which competing intent becomes active.

-   **Scheduling**: Reserving only the next action window for Thin NPCs (no full-day plans).

-   **Failure Pressure**: Priority escalation caused by repeated deferrals/failures.

-   **Demand Signal**: Aggregated expression of intent volume (food demand, leisure demand, labor demand).

-   **Flow Field**: Aggregated movement demand (pedestrian, vehicle, freight) used for infrastructure sizing.

-   **Infrastructure Response**: System adjustments (paths, roads, transit) driven by sustained flows.

-   **Business**: Operating unit attached to a place (or places) that sets prices/wages/hours/quality.

-   **Owner**: Business role that sets long-term strategy; may be remote.

-   **Operator**: Business role that sets shift-level execution.

-   **BusinessDecisionRole**: A capability component attached to an NPC enabling owner/operator decisions.

-   **Competence Vector**: Bounded skill profile (market sense, ops, people mgmt, finance, quality, adaptability, risk).

-   **Shift Event Cycle**: Business decision checkpoints (open, rush, delivery, shift change, close).

-   **Economic Institution**: A resolver that governs acquisition/allocation under a regime.

    -   **Market Exchange**: Prices clear demand.

    -   **Ration/Entitlement**: Quotas/vouchers allocate goods.

    -   **Assignment/Command**: Jobs/housing allocated by authority.

    -   **Patronage/Reciprocity**: Access via reputation/favors.

    -   **Corporate Provisioning**: Benefits with constraints.

    -   **Black Market**: Risk-based alternative access.

-   **Multi-asset Wallet**: NPC holdings across cash, vouchers/entitlements, reputation credit, access rights.

-   **Obligation**: Persistent pressure (rent, debt, quotas, dependents, duties) that shapes behavior across regimes.

-   **Access Constraint**: Eligibility limits (membership, legality, distance, time windows).

-   **Risk Posture**: Willingness to use uncertain/illegal channels.

-   **Strong Tie**: Explicit relationship edge (family, close friend, key coworker).

-   **Bundled Tie**: Compressed group link (neighbors, shift crew, organization) that can expand on promotion.

-   **Relationship Book**: Bounded catalog of other NPCs met and feelings about them.

-   **Memory Item**: Compressed “significant thing” summary with tags, valence, intensity, significance, decay.

-   **Reinforcement**: Refreshing a memory/relationship through repetition, retelling, emotion, or cues.

-   **Decay**: Fading of activation probability/intensity unless reinforced.

-   **Attention Tokens**: Bounded spillover budget granted to participants after interacting with a Thick NPC.

-   **Deterministic Backfilling**: Seeded reconstruction of plausible history/details on promotion.

-   **World Seed**: Global randomness seed for deterministic generation.

-   **Budget**: Global limits that cap active Thick NPCs, expansions, and per-frame query costs.


* * *

## Table of Contents

1.  Glossary & Terms

2.  Overview & Principles

3.  Core Entities & Interfaces

4.  NPC Fidelity Tiers

5.  Promotion, Demotion, and Continuity

6.  NPC State & Information Panels

7.  Places, Buildings, and Environment

8.  Intent System

9.  Intent Arbitration & Scheduling

10.  Aggregate Behavior Systems

11.  Movement, Flows, and Infrastructure Growth

12.  Economic Agency

13.  Social Graph, Relationships, and Memory

14.  Persistence & Save/Load

15.  Deterministic Backfilling

16.  Budgets & Performance Constraints

17.  Design Worklist

18.  Open Questions


* * *

## 2. Overview & Principles

-   Support **millions of NPC identities** with consistent, queryable lives.

-   Allocate simulation detail **only when queried or interacted with**.

-   Preserve **continuity** across promotion/demotion cycles.

-   Bound computational cost via **event-driven updates**, **aggregation**, and **budgets**.

-   Treat NPCs primarily as **sensors and actors**, not omniscient planners.


Core rule:

> NPCs express intent; systems resolve outcomes.

* * *

## 3. Core Entities & Interfaces

Arcadium is built from a small set of first-class entities that interact via signals.

### 3.1 NPC

An identity that:

-   has needs and obligations

-   generates intents at event boundaries

-   can be simulated at multiple fidelities


### 3.2 Cohort

A population abstraction:

-   produces aggregate labor, housing, sentiment, and movement pressure

-   can stand in for absent individuals (Tier 0/1)


### 3.3 Place (building/venue)

A location entity that provides:

-   capacity, privacy, cleanliness, safety, comfort, accessibility, reliability

-   a local context used to compute **Environment** ("right here, right now")


### 3.4 Business

An operating unit attached to a place (or set of places) that:

-   sets prices/wages/hours/quality targets

-   emits capacity and service signals

-   can succeed, stagnate, fail, or be acquired


### 3.5 Economic Institution

A resolver for acquisition/allocation under a given regime (market, rationing, patronage, etc.).

* * *

## 4. NPC Fidelity Tiers

### Tier 0 — Population Mass

-   No individuals.

-   Cohort counts by district, age, occupation, culture, income, schedule.

-   Outputs: labor supply, housing pressure, sentiment, transit demand.


### Tier 1 — Cohort Agents

-   Group representatives (e.g., "Night-shift nurses, District 7").

-   Handle policy response, staffing gaps, migration pressure.


### Tier 2 — Thin NPCs

-   Individual identity with minimal state.

-   Anchors (home/work), schedule archetype, needs & traits.

-   Social graph stored as **strong ties + bundles**.


### Tier 3 — Thick NPCs

-   Expanded memory, preferences, relationships.

-   Higher-frequency updates while relevant.

-   Dialogue, negotiation, deception, planning.


### Tier 4 — Narrative / Named NPCs

-   Permanently persistent or authored characters.


* * *

## 5. Promotion, Demotion, and Continuity

### 5.1 Interaction model (promotion triggers)

NPCs become relevant through explicit interest:

-   **UI interest**: player clicks an NPC to open info panels.

-   **Direct interaction**: player-controlled character engages the NPC.

-   **System queries**: quests, investigations, audits, planning, simulation systems.


Proximity alone does **not** increase fidelity.

### 5.2 Demotion behavior (static history)

-   No data is deleted.

-   NPC stops generating new detail when irrelevant.

-   High-cost state (plans, pathing, dialogue) may be paused or archived.


### 5.3 Demotion triggers

-   Relevance TTL expires.

-   Budget pressure.

-   NPC leaves all active zones of interest.


### 5.4 Continuity guarantee

Promoted NPCs are deterministically backfilled so their history appears consistent.

* * *

## 6. NPC State & Information Panels

### 6.1 Thin NPC state (conceptual)

Thin NPCs should remain cheap and stable:

-   identity (name seed / resolved name)

-   anchors (home/work)

-   schedule archetype

-   traits (small vector)

-   needs vector + last update time (event-driven)

-   social: strong ties + group memberships (bundled)

-   next event time


### 6.2 Basic NPC info panel (Tier 2)

Fast to answer.

-   Name

-   Place of residence

-   Place of occupation or school

-   Needs overview


### 6.3 Needs vector (v1)

-   Hunger

-   Thirst

-   Energy

-   Hygiene

-   Bladder

-   Fun

-   Social

-   Comfort

-   Environment


Notes:

-   Stored as normalized values (0–1).

-   Thin NPCs update needs at event boundaries.

-   Thick NPCs may update needs continuously while active.


* * *

## 7. Places, Buildings, and Environment

Buildings and venues are implied by anchors, but are treated as first-class place entities.

### 7.1 Place anchors

NPCs and businesses reference places by ID:

-   `home_anchor` → typically a residential building/unit

-   `work_anchor` / `role_anchor` → a workplace or school venue

-   intent destinations resolve to venue/building anchors


### 7.2 Building/venue qualities

Places expose a compact set of qualities and problems:

-   capacity (people throughput)

-   privacy tiers (public ↔ private)

-   cleanliness/maintenance

-   comfort (seating, temperature, noise insulation)

-   safety/security

-   accessibility (distance to transit, entrances)

-   reliability (power, elevators, equipment uptime)


### 7.3 Environment ("right here, right now")

-   Derived from immediate place context, not stored long-term.

-   Factors: crowding, noise, privacy, cleanliness, aesthetics, safety.

-   Can **gate actions entirely** (e.g., refuse sensitive conversations).


### 7.4 Cascading effects via places

Places are a primary cascade surface:

-   Understaffing → queues/crowding → Environment drops for everyone nearby

-   Maintenance decline → fewer visits → revenue drop → layoffs → migration pressure


No per-NPC bookkeeping is required beyond updating place state and letting NPCs sample it.

#### 7.5 Place state for aggregation and environment

To compute Environment and support aggregate solvers, each Place maintains lightweight state:

-   **static qualities** (capacity, privacy tier, comfort, safety, accessibility, reliability)

-   **dynamic state by time bucket**

    -   occupancy estimate (people present)

    -   queue estimate (waiting)

    -   noise/crowd proxy

    -   cleanliness/maintenance proxy


Dynamic state is not tracked per individual; it is derived from aggregated demand/flow outputs.

### 7.6 Environment computation model

Environment is derived per place per time bucket as:

-   `environment_score` (0–1)

-   `environment_tags` (discrete labels used for gating/penalties)

-   key **component levels** used for hard gates (privacy, safety, crowding)


#### 7.6.1 Normalized inputs (0–1 "badness")

Inputs are normalized to 0–1 badness levels (0 = good, 1 = bad):

-   `crowding` = transform(occupancy / capacity)

-   `queue_pressure` = transform(queue / service\_capacity)

-   `noise`

-   `unclean` = 1 - cleanliness\_proxy

-   `unsafe` = 1 - safety\_proxy

-   `uncomfortable` = 1 - comfort\_proxy

-   `privacy_low` = 1 - privacy\_tier (privacy\_tier: 0 public → 1 private)


#### 7.6.2 Default weights (environment\_score)

The default `environment_score` is a weighted penalty model:

-   `environment_score = clamp01(1 - Σ(w_i * badness_i))`


Default weights (sum = 1.0):

-   safety (`unsafe`): **0.25**

-   crowding (`crowding`): **0.20**

-   queue pressure (`queue_pressure`): **0.15**

-   privacy deficiency (`privacy_low`): **0.15**

-   cleanliness (`unclean`): **0.10**

-   comfort (`uncomfortable`): **0.10**

-   noise (`noise`): **0.05**


Rationale (design intent): safety dominates, crowding/queues drive immediacy, privacy enables sensitive interactions, and cleanliness/comfort/noise shape leisure and willingness to linger.

#### 7.6.3 Nonlinear transforms (crowding and queue curves)

Crowding and queueing should be **gentle** at low utilization and **steep** near saturation.

Guidance:

-   crowding rises slowly until ~70–80% occupancy, then accelerates sharply at ~85%+

-   queue\_pressure rises sharply as service approaches saturation and should reflect backlog spillover between buckets


These transforms are calibration knobs; the key is stable behavior that produces sudden "too crowded" conditions near capacity.

#### 7.6.4 Tag rules (thresholds)

Tags are derived from stable thresholds and combinations (examples):

-   `crowded` if occupancy/capacity ≥ 0.85

-   `packed` if occupancy/capacity ≥ 1.00

-   `quiet` if noise ≤ 0.25 and crowding ≤ 0.35

-   `loud` if noise ≥ 0.75

-   `private` if privacy\_tier ≥ 0.75

-   `public` if privacy\_tier ≤ 0.25

-   `dirty` if cleanliness\_proxy ≤ 0.35

-   `clean` if cleanliness\_proxy ≥ 0.75

-   `sketchy` if safety\_proxy ≤ 0.35

-   `unsafe` if safety\_proxy ≤ 0.20

-   `queued` if queue\_pressure ≥ 0.70


Useful composites:

-   `overwhelming` if (`crowded` AND `loud`) OR `packed`

-   `serene` if (`quiet` AND `clean` AND NOT `crowded`)


#### 7.6.5 Intent sensitivity (how environment is used)

Environment should influence resolution and behavior through **both** the blended score and tags:

-   `environment_score` provides a smooth baseline preference.

-   `environment_tags` provide decisive gates/penalties.


Suggested sensitivity multipliers (default):

-   Work/School: 0.3

-   Errand/Service: 0.5

-   Food/Drink: 0.7

-   Social/Leisure: 1.0


(Utility scoring uses `environment_score` plus tag penalties scaled by intent sensitivity; see Section 10.5.2.)

### 7.7 Action gating via Environment

Environment can gate or modify actions:

-   **Hard gate**: intent cannot resolve to a place if constraints fail.

-   **Soft penalty**: intent can resolve but loses utility.


**Hard gates should use specific component levels and/or tags** (privacy, safety, crowding), not the blended `environment_score`.

Examples:

-   sensitive conversations require privacy\_tier ≥ 0.7 AND occupancy/capacity ≤ 0.6 AND NOT `loud`

-   leisure/social intents heavily penalized by poor comfort/cleanliness; may hard-gate on `unsafe`

-   errands tolerate poor environment but may increase fatigue/irritation


* * *

## 8. Intent System

NPC **intents** are the primary output of NPC simulation. They represent _what an NPC wants to do_, not _how it is achieved_.

Intents are:

-   lightweight

-   event-driven

-   aggregatable

-   resolvable by higher-level systems


### 8.1 Intent structure (common fields)

-   `intent_id`

-   `npc_id`

-   `intent_type`

-   `origin_anchor`

-   `preferred_destination_tags`

-   `time_window` (earliest, latest)

-   `base_priority`

-   `constraints` (budget, access, legality, environment gating)

-   `transport_preferences`

-   `intensity`


Higher-level systems may resolve an intent to:

-   a specific destination

-   a deferred outcome

-   a failed or abandoned action


### 8.2 Intent generation (Thin NPC rules)

Thin NPCs generate intents **only at event boundaries**, never per-frame.

Generation triggers:

-   needs crossing thresholds (e.g., hunger < X)

-   upcoming obligation windows (work/school)

-   completion, failure, or expiration of a prior intent

-   major external shocks (job loss, relocation, business closure)

-   explicit system or player query


At any time, a Thin NPC may have:

-   **1 scheduled intent**

-   **up to 2 latent intents** (pressure without commitment)


All other impulses are discarded or folded into priority modifiers.

### 8.3 Thin NPC minimum intent set

Thin NPCs must support only a small canonical set initially:

-   Work / School

-   Food & Drink

-   Social / Leisure (combined)

-   Errand / Service


### 8.4 Intent failure & carryover

When intents are not selected or fail:

-   food/social intents are **deferred** (priority increases)

-   errands typically **expire**

-   leisure intents may **decay**


No long intent backlog is maintained.

* * *

## 9. Intent Arbitration & Scheduling

NPCs often have multiple competing intents. Arbitration determines which intent is acted on, when, and what happens to the rest.

Thin NPC arbitration is deliberately simple and cheap.

### 9.1 Arbitration timing (Thin NPCs)

Arbitration runs only at event boundaries:

-   intent generation

-   intent resolution

-   schedule boundary (e.g., work start)


No continuous reconsideration for Thin NPCs.

### 9.2 Priority scoring (Thin NPCs)

Priority is calculated via a simple weighted sum:

-   need urgency

-   obligation weight

-   deadline proximity

-   accumulated failure pressure

-   small trait modifiers (discipline, impulsivity)


**Determinism policy:** Scoring is deterministic given seeds and macro conditions; only bounded jitter is used for tie-breaking and minor timing variation.

### 9.3 Obligation dominance

Default soft ordering:

1.  emergency physiological needs

2.  work/school (during obligation windows)

3.  food

4.  social/leisure

5.  errands


Rules:

-   suppression increases future priority

-   extreme unmet needs can override obligations


### 9.4 Scheduling model (Thin NPCs)

Thin NPCs schedule only the next selected intent:

-   no full-day planning

-   no future block reservation

-   reschedule only after resolution or failure


### 9.5 Failure feedback

Failure affects future behavior by:

-   increasing priority weight

-   shortening retry intervals

-   eventually triggering higher-level intents (job change, migration)


No explicit stress meter is required at Thin level.

### 9.6 Performance guarantees

-   O(1) arbitration per NPC per event

-   no per-frame cost

-   bounded intent memory


### 9.7 Thin NPC core loop validation targets

What you should be able to observe at scale once Sections 8–9 are implemented:

-   **Daily rhythms emerge** (morning commute, lunch peaks, evening leisure) from large populations.

-   **Basic causality holds:** hunger drives food intents; obligation windows drive work/school intents.

-   **Aggregate intent volumes are stable** across runs and scale up to large NPC counts.

-   **Local shocks propagate at intent level** (e.g., workplace removal shifts schedules and downstream demand without bespoke scripting).


* * *

## 10. Aggregate Behavior Systems

NPCs do not create society by individual simulation; they emit demand signals which higher-level systems resolve.

### 10.1 Consumption & culture

NPCs track preferences, not catalogs:

-   taste vectors

-   budget constraints

-   exposure channels


Consumption signals emit:

-   category

-   brand (optional)

-   intensity


Aggregate systems answer:

-   popularity trends

-   cultural dominance

-   market saturation


### 10.2 Society-wide outputs

Aggregate layers provide:

-   labor availability

-   housing pressure

-   sentiment drift

-   resource scarcity signals


### 10.3 Demand aggregation

Demand aggregation converts intents into time-bucketed demand signals that other systems can consume.

Outputs (examples):

-   **service demand** by category and region (food, errands, leisure)

-   **labor demand** by role type (from businesses/places)

-   **housing pressure** by region


Key rule:

> Demand is counted and bucketed; it is not resolved to individuals at this stage.

### 10.4 Demand resolution baseline

A baseline, system-driven resolver that maps demand to candidates _without_ requiring full business agency.

Examples:

-   Food demand in a region is distributed across candidate venues using:

    -   distance/accessibility

    -   current queue/capacity

    -   rough price/quality proxies (system defaults until business agency is introduced)

    -   Environment constraints (privacy, safety)


Results update place-level dynamic state:

-   occupancy

-   queue estimates

-   effective wait time


These results are used immediately by:

-   Environment computation (Section 7)

-   movement flow estimation (Section 11)


### 10.5 Baseline intent resolution utility

The system needs a consistent way to choose _which place_ an intent resolves to, without simulating detailed deliberation.

**Baseline model:** each candidate place receives a bounded **utility score** for the intent, then demand is distributed using a probabilistic choice rule (e.g., logit/softmax). This yields stable aggregates while avoiding brittle “everyone picks the same place.”

#### 10.5.1 Two-step evaluation

1.  **Feasibility gate (hard constraints):** candidate is rejected if it violates constraints.

    -   access constraints (membership/eligibility)

    -   legality constraints (closed hours, restricted service)

    -   **Environment hard gates** (privacy required but too public/crowded; safety below minimum)

    -   time window infeasibility (can’t reach within intent window)

2.  **Utility scoring (soft preferences):** remaining candidates are scored.


#### 10.5.2 Utility components (all bounded)

Common components (typical):

-   **Travel cost:** estimated travel time from origin (uses congestion proxies when available).

-   **Queue/wait penalty:** derived from queue estimate and service capacity.

-   **Environment preference:** `environment_score` plus tag penalties/bonuses (crowded/loud/private/clean/sketchy) scaled by intent sensitivity (see Section 7.6.5).

-   **Price/quality proxy:** system defaults initially; business-driven once business agency is introduced.

-   **Preference match:** taste/profile alignment (for food/leisure) and category fit.

-   **Habit / inertia:** small bias toward familiar anchors or frequently chosen nearby venues.


A few components are intent-type specific:

-   **Work/School:** dominated by obligation window + lateness tolerance; low substitution set.

-   **Food/Drink:** strong taste + price sensitivity; moderate substitution.

-   **Social/Leisure:** strong environment sensitivity (privacy/comfort); high substitution.

-   **Errand/Service:** time/availability dominates; environment is low weight.


#### 10.5.3 Probabilistic choice (anti-brittleness)

Instead of always picking the top utility, demand is **distributed** across candidates with probability proportional to their utility.

Controls:

-   **Temperature/noise:** higher temperature spreads demand more evenly; lower makes choices sharper.

-   **Capacity awareness:** candidates nearing capacity naturally lose utility via queue/wait and crowding.


This produces realistic:

-   near-misses (people choose the second-best option)

-   load balancing (crowds shift away from long queues)

-   stable aggregate patterns (peaks and shifts without micro-sim)


#### 10.5.4 Outputs required from the utility layer

For each time bucket, the baseline resolver should output:

-   assigned demand volumes per place and intent category

-   expected arrivals (ingress) per place

-   updated queue/occupancy estimates


These feed:

-   Environment (Section 7)

-   flow estimation (Section 11)

-   later business adaptation (Section 12)


### 10.6 Candidate sets for intent resolution

Candidate sets define **which places are even considered** before utility scoring (Section 10.5). This keeps resolution bounded, stable, and scalable.

#### 10.6.1 Candidate set contract

For each `(intent_type, origin_anchor, time_bucket)` the system produces a `CandidateSet`:

-   `candidates`: bounded list of Place IDs

-   `search_tier_used`: local / district / city-region

-   `filters_applied`: open-hours, category, access, legality, environment hard-gates

-   `fallback_reason` (optional): why the search expanded or degraded constraints


**Hard cap:** the resolver never considers more than `K_max` candidates for an intent resolution.

#### 10.6.2 Two-stage filtering (before scoring)

1.  **Eligibility filter (hard constraints, cheap):**

    -   reachable within intent time window (via travel-time proxies)

    -   open/available in the current bucket

    -   access constraints (membership/eligibility/institution rules)

    -   legality constraints (restricted goods/services)

    -   environment hard gates when absolute (privacy/safety minimums)

2.  **Diversity / representativeness selection:**
    If too many candidates remain, select a subset that is:

    -   geographically diverse

    -   not overly concentrated in a single cluster

    -   inclusive of a few "non-optimal but plausible" alternatives


This prevents brittle outcomes where everyone chooses the same top option.

#### 10.6.3 Progressive search envelope

Candidate search expands outward only when needed.

Tiers:

1.  **Local neighborhood** (walkable/short-trip)

2.  **District**

3.  **City/region**


Stop when:

-   at least `K_min` feasible candidates exist for the intent type, or

-   the largest tier is reached


If still insufficient, use intent-type fallback rules (Section 10.6.6).

#### 10.6.4 Caching for stability and scale

Candidate sets are cached per:

-   `(intent_type, origin_zone, time_bucket, constraint_signature)`


Where `constraint_signature` is a compact tag bundle such as:

-   needs\_privacy

-   budget\_low

-   members\_allowed

-   must\_be\_open\_now


Caching creates stable aggregate patterns and avoids recomputation at high population counts.

#### 10.6.5 Intent-type candidate rules (defaults)

These defaults are tunable and act as baseline behavior.

**Work / School (low substitution)**

-   Candidates: `{work_anchor}` / `{school_anchor}` (typically `K=1`)

-   Fallback candidates (if invalid): alternate sites for same employer/school system; assignment authority; trigger job-change intent if repeatedly invalid


**Food & Drink (high frequency)**

-   Candidate channels: market venues, cafeterias/canteens, groceries, ration pickup points, corporate provisioning nodes, (optionally) black market nodes

-   Filters: open now, reachable, access eligible

-   Target sizes: `K_min≈8`, `K_target≈20–40`, `K_max≈60`

-   Diversity: include a mix of quick/cheap/quality options (proxies until business agency is active)

-   Fallback: resolve to home/nearest always-available provider archetype, or defer with failure pressure


**Social / Leisure (environment sensitive)**

-   Candidate channels: parks, cafés, homes, community spaces, venues, etc.

-   Filters: open now + environment compatibility (privacy/comfort)

-   Target sizes: `K_min≈6`, `K_target≈15–30`, `K_max≈50`

-   Fallback: degrade sensitivity (lower-stakes interaction), or resolve to home leisure / outdoor walk archetypes


**Errand / Service (availability dominates)**

-   Candidate channels: service venues by category (bank, clinic, shipping, repairs, gov)

-   Filters: service availability window + reachable

-   Target sizes: `K_min≈3`, `K_target≈8–15`, `K_max≈30`

-   Fallback: defer to next open bucket; may expire if missed


#### 10.6.6 Institution-aware channels

Candidate generation treats **acquisition channels** as first-class, not just “stores.”

Example: a Food intent may consider multiple channels depending on region and NPC eligibility:

-   market venues

-   ration distribution points

-   corporate provisioning cafeterias

-   patronage/private invitations (if available)

-   black market nodes (if risk posture allows)


This preserves economy-agnostic NPC behavior: NPCs express needs; institutions determine viable channels.

* * *

## 11. Movement, Flows, and Infrastructure Growth

### 11.1 Movement intent

NPCs emit:

-   origin anchor

-   destination anchor

-   time window

-   transport preference


Thin NPCs do not pathfind. Thick NPCs only request route plans while relevant.

**Design rule:** routing is a **separate system service**, not embedded in NPC logic.

-   Thin NPCs and aggregate solvers consume **travel-time and transfer-wait proxies**.

-   Thick NPCs (and player-facing UI) may request an explicit **route plan**.


(See linked document: **Arcadium** [**Movement, Routing, and Infrastructure**](/pages/814b2d54-8e20-45eb-ade8-68f333c7c2a8).)

### 11.2 Flow aggregation

Movement intents aggregate into flow fields:

-   pedestrian

-   light vehicle

-   freight

-   service/emergency


Tracked by time, season, and origin–destination pairs.

### 11.3 Infrastructure response

Infrastructure systems use flows to:

-   size roads and paths

-   add or remove transit

-   justify upgrades or decay


NPCs experience these changes via Environment and accessibility.

### 11.4 Time bucketing

All flow and demand computations run in discrete time buckets (e.g., 5–60 minutes, tuneable).

-   Thin NPCs emit intents with time windows.

-   Solvers accumulate within the bucket.

-   Places expose dynamic state per bucket (occupancy, queues).


#### 11.4.1 Time scale separation

Arcadium uses two time scales with distinct responsibilities:

-   **Simulation Buckets (SB):** drive aggregates (demand aggregation/resolution, flow estimation, place occupancy/queues, Environment).

-   **Event Boundaries (EB):** drive Thin NPC updates (wake, commute start/end, shift start/end, meals, interaction end).


Thin NPCs do **not** update every bucket; they update only at event boundaries.

#### 11.4.2 Default bucket sizes

-   **Default SB:** 15 minutes

-   **Allowed SB sizes:** 5, 10, 15, 30, 60 minutes (discrete set for stable caching and debugging)


#### 11.4.3 Adaptive bucketing (region + time-of-day)

Bucket size may refine or coarsen by **region** and **time-of-day** without changing Thin NPC update cost.

**Refinement triggers (e.g., 15 → 5):**

-   high demand/flow variance

-   sustained high congestion proxy

-   place occupancy near capacity

-   major event flags (concert, stadium, emergency)


**Coarsening triggers (e.g., 15 → 30/60):**

-   low activity

-   low variance

-   quiet late-night periods


#### 11.4.4 Bucket alignment and arrival spreading

To avoid "everyone arrives at exactly :00":

-   SB boundaries align to clock time (:00, :15, :30, :45) for readability.

-   Intents are mapped into buckets by **time-window overlap**, distributing arrival volume across the bucket (optionally with small deterministic jitter).


#### 11.4.5 Determinism and stability

-   Bucket computations are deterministic given seeds and macro conditions.

-   Only bounded distribution noise is allowed, and should be deterministic per (zone, day, bucket, cohort) so runs remain comparable.


#### 11.4.6 History retention and downsampling

To avoid unbounded storage of per-bucket fields:

-   keep high-resolution SB history for a rolling short horizon (e.g., 6–24 hours)

-   downsample for longer horizons (e.g., 1-hour buckets for a week; daily averages beyond)


These retention horizons are design knobs and may vary by world size and save-file targets.

### 11.5 Flow representations

The system supports two compatible representations:

-   **OD demand** (origin–destination pairs with volume)

-   **Network flow** (volume on edges/nodes for a transport layer)


OD demand is always recorded; network flow is produced when a network model exists.

### 11.6 Flow solvers

Thin NPCs do not pathfind. Instead, the system estimates flows using cheap solvers.

Acceptable solver families:

-   **Gravity / choice models** for destination selection (distance + attractiveness)

-   **All-or-nothing shortest-path assignment** on a simplified network (when available)

-   **Stochastic assignment** with limited noise to avoid brittle singular routes


Outputs per bucket:

-   edge volumes by transport layer

-   place ingress/egress volumes

-   congestion proxies


### 11.7 Congestion and travel-time proxies

The system produces bounded proxies (not full microsim):

-   `congestion_score` on edges/regions

-   estimated travel times by transport layer

-   `transfer_wait_proxy` at choke points (elevator banks, gates, platforms)


These proxies influence:

-   intent resolution utility (choose closer / less congested)

-   place occupancy timing (arrival spread)

-   Environment indirectly (crowding, queues)


Detailed congestion/queue calibration, routing APIs, and auto-improving path logic live in the linked document:

-   **Arcadium Movement, Routing, and Infrastructure**.


* * *

## 12. Economic Agency

Economic agency is split into:

-   **Business Agency** (venue-level decisions)

-   **Economy Institutions** (system-agnostic exchange/access rules)


### 12.1 Businesses, ownership, and pricing

Each business has two decision-makers:

-   **Owner**: long-term strategy, profit goals (may be remote)

-   **Operator**: local execution and management


Either role may be:

-   NPC

-   cohort agent

-   corporate abstraction


Systems provide signals (not outcomes):

-   demand estimates

-   baseline costs

-   labor pressure

-   regulation


Owners/operators decide:

-   prices/promos

-   wages/overtime

-   hours

-   staffing plans

-   quality targets

-   access rules


Failure is possible (closure/acquisition), with consequences.

### 12.2 Business competence & adaptation

**Modeling approach:** composition over inheritance.

-   Keep a single NPC model.

-   Add a Role/Capability component (e.g., `BusinessDecisionRole`) when an NPC is an owner/operator.


Competence vector (0–1):

-   market sense

-   operations

-   people management

-   financial control

-   quality discipline

-   adaptability

-   risk tolerance


Shift decision cycle (event boundaries):

-   demand & positioning

-   pricing & offers

-   staffing

-   inventory/inputs

-   service level & quality

-   incident response

-   reinvestment (owner-heavy)


Decision outputs (signals):

-   `price_schedule`, `wage_policy`, `staffing_plan`, `service_capacity`, `quality_level_target`, `inventory_orders`, `access_rules`


Adaptation inputs:

-   revenue

-   queue time / congestion

-   complaint / incident rates

-   turnover/absences

-   competitor pressure


### 12.3 Economy institutions (system-agnostic layer)

Institution types (minimum set):

-   Market exchange (prices)

-   Ration/entitlement distribution (quotas)

-   Assignment/command allocation (jobs/housing assigned)

-   Patronage/reciprocity (reputation/favors)

-   Corporate provisioning (benefits with constraints)

-   Black market (risk-based access)


NPC-facing economic interface (stable across regimes):

-   assets/entitlements (multi-asset "wallet")

-   obligations (rent/quotas/debt/favors/dependents)

-   access constraints (membership, legality, distance, time)

-   risk posture (willingness to use illegal/uncertain channels)


### 12.4 Cascades (how decisions affect many NPCs)

Cascades happen through signals and shared systems:

-   Customers: price/quality/queue alter intent resolution

-   Employees: staffing and wages alter work intents, retention, stress pressure

-   Places: queues/crowding change Environment for nearby NPCs

-   Infrastructure: sustained flows justify upgrades/decay

-   Culture: successful venues amplify exposure channels


* * *

## 13. Social Graph, Relationships, and Memory

### 13.1 Social graph compression

Explicit strong ties:

-   family

-   close friends

-   key coworkers


Bundled ties:

-   neighbors

-   shift crews

-   organizations

-   online communities


Bundles expand on promotion and collapse on demotion.

### 13.2 Relationship book ("people I've met")

Each NPC maintains a bounded relationship book keyed by other NPC IDs.

Entry fields (suggested):

-   `other_npc_id`

-   `first_met_time`

-   `last_interaction_time`

-   `familiarity` (0–1)

-   `affinity` (like/dislike)

-   `trust`

-   `respect`

-   `fear`

-   `obligation`

-   `notes` (compressed tags)

-   `decay_rates`


Decay guidance:

-   familiarity decays slowly

-   emotions decay unless reinforced

-   strong ties decay far more slowly and are rarely dropped


### 13.3 Memory model ("significant things")

NPC memory is stored as a bounded set of Memory Items (summaries), not raw logs.

Each memory item:

-   `memory_id`

-   `summary` (short text or structured token)

-   `tags` (people, places, themes)

-   `valence` (positive/negative)

-   `intensity` (felt strength)

-   `significance` (life-shaping weight)

-   `created_time`

-   `last_reinforced_time`

-   `decay_rate`


### 13.4 Fading and reinforcement

-   Activation probability decreases with time since reinforcement.

-   Intensity decays faster than significance.

-   Most events become low-impact background.

-   Rarely, traits + context + reinforcement make an event identity-shaping.


Reinforcement sources:

-   repeated related events

-   frequent retelling (social interactions)

-   strong emotion coupling (fear, pride, shame)

-   proximity cues (returning to places, seeing people, familiar media)


### 13.5 Trickle-down attention (interaction propagation)

When a Thick NPC interacts with others, participants get bounded spillover detail.

Rules:

-   Each interaction emits a micro-event.

-   Participants receive a small promotion budget ("attention tokens") to:

    -   update relationship entry

    -   add/refresh a memory item

    -   optionally expand a bundled tie into an explicit tie


Constraints:

-   capped per interaction and per time window

-   prefer updating existing entries over creating new ones


* * *

## 14. Persistence & Save/Load

We store stable identity and meaningful deltas, and recompute everything else.

### 14.1 Persisted (all NPC tiers)

-   `npc_id`

-   identity seed / resolved name

-   anchors (home/work)

-   cohort/culture tags

-   traits

-   needs baseline + `last_update_time`

-   strong ties + group memberships (bundled)


### 14.2 Persisted when generated (monotonic)

-   significant memories (compressed)

-   relationship book entries (bounded)

-   major life events (graduation, marriage, job change, relocation)


### 14.3 Ephemeral / recomputable

-   current plan and micro-schedule blocks

-   pathing state

-   short-lived emotions/impulses

-   transient dialogue context


### 14.4 World save contents

-   macro society state (cohorts, prices/availability, culture weights)

-   place/building state

-   business state and histories

-   NPC persistent state


### 14.5 Load behavior

-   Thin NPCs restore from persisted state

-   Thick NPCs are instantiated on demand

-   Ephemeral state is rebuilt from the last stable event boundary


* * *

## 15. Deterministic Backfilling

Backfilling uses seeds:

-   npc\_id

-   district\_id

-   cohort\_id

-   world\_seed

-   epoch/timeline


Backfillable elements:

-   work history

-   education

-   weak social ties

-   habits and preferences


* * *

## 16. Budgets & Performance Constraints

Global limits:

-   Max Thick NPCs

-   Max Thin expansions per minute

-   Max relationship expansions

-   Max query cost per frame


Budget pressure triggers graceful demotion.

* * *

## 17. Design Worklist

This section is a **document worklist**: what to add, expand, or tighten next to keep the design coherent.

1.  **Baseline economic interface details**

    -   Expand assets/entitlements, obligations, access constraints, and risk posture with clear examples across multiple regimes.

2.  **Business decision surface**

    -   Expand owner/operator decision outputs and adaptation metrics (what is observable, how fast adaptation occurs, what is bounded).

3.  **Infrastructure response policy**

    -   Define how sustained flow fields translate into construction/upgrade/decay decisions (thresholds, hysteresis, budgets).

4.  **Fallback behaviors and shock handling**

    -   Define standard fallbacks for closures, outages, special events, and shortages (how demand/flows reroute; how Environment responds; what intents are deferred vs replaced).

5.  **Aggregate history retention policy**

    -   Define retention horizons, downsampling rules, and what aggregate history is persisted vs recomputed on load.

6.  **Routing integration notes**

    -   Keep NPC design and movement design aligned: what Thin NPCs can query (cost proxies only), what Thick NPCs can request (route plans), and where transfer waits/queues enter utility scoring.


* * *

## 18. Open Questions

### Milestones (design)

-   ✅ Thin NPC core loop specified (Sections 8–9; validation targets in 9.7)


### Resolved / Stable

-   Multi-fidelity NPC model with promotion/demotion and static history

-   Event-driven needs, intent generation, arbitration, and scheduling

-   Place/building anchors as first-class cascade surfaces

-   Business ownership, competence, adaptation, and cascading effects

-   Persistent memory and relationship systems with decay and reinforcement


### Open design questions

-   **Memory limits & summarization:** How many Memory Items per NPC before forced merging, and what heuristics merge memories into life "chapters"?

-   **Relationship caps:** Maximum explicit relationships before collapsing back into bundles.

-   **Intent timing granularity:** How fine the time windows must be for believable schedules without increasing cost.

-   **Stress / mood model:** Whether stress remains implicit (derived from failures) or becomes an explicit tracked state.

-   **Business learning rate tuning:** How fast adaptation should occur to avoid oscillation or stagnation.

-   **Time bucket size:** What bucket length (5–60 min) balances stability vs responsiveness?

-   **Flow solver selection:** Which default solver family is used first (gravity, shortest-path assignment, stochastic), and what data is required?

-   **Congestion proxy calibration:** How congestion translates to travel-time penalties and destination drift.

-   **Demand resolution policy:** How the baseline resolver distributes demand before business agency exists.

-   **Environment calibration:** How thresholds, nonlinear transforms, and tag rules should be tuned per culture/district/place type beyond the defaults.

-   **Economic institution set:** Minimum viable institution types and how they compose within a region.

-   **Multi-asset wallet:** Which assets/entitlements are universal (cash, vouchers, reputation, access rights) and how they are bounded.

-   **Illicit channels:** How risk, enforcement, and black markets interact with place/environment.

-   **Player leverage:** Which systems the player can directly influence (prices, zoning, labor law, transit priority, institution rules).

-   **Simulation authority boundaries:** Which answers are authoritative vs probabilistic at low fidelity.

-   **Save-file size targets:** Practical limits for large worlds with millions of NPCs.
