---
title: NPCs
slug: npcs
section: Mechanics
status: published
order: 0
created_by: admin
updated_by: admin
---
# Arcadium NPC Design

> Living document — evolving design for large-scale, society-driven NPC simulation.

* * *

## Table of Contents

1.  Goals & Design Principles

2.  Interaction Model

3.  Core Strategy

4.  NPC Fidelity Tiers

5.  Promotion & Demotion Model

6.  NPC Information Panels & Needs

7.  Aggregate Behavior & Societal Systems

8.  Consumption & Culture Modeling

9.  Movement, Flows, and Infrastructure Growth

10.  Businesses, Ownership, and Pricing

11.  Business Competence & Adaptation

12.  Feedback Loop (End-to-End)

13.  Buildings, Places, and Anchors

14.  Deterministic Backfilling

15.  Social Graph Compression

16.  Budgets & Performance Constraints

17.  NPC Data Models

18.  NPC Intent Schemas

19.  Intent Arbitration & Scheduling

20.  Persistence, Memory, and Relationships

21.  Open Questions & Next Steps


* * *

## 1. Goals & Design Principles

-   Support **millions of NPC identities** with consistent, queryable lives.

-   Allocate simulation detail **only when queried or interacted with**.

-   Preserve **continuity** across promotion/demotion cycles.

-   Bound computational cost via **event-driven updates**, **aggregation**, and **budgets**.

-   Treat NPCs primarily as **sensors and actors**, not omniscient planners.


* * *

## 2. Interaction Model

NPCs become relevant through explicit interest:

-   **UI interest**: player clicks an NPC to open info panels.

-   **Direct interaction**: player-controlled character engages the NPC.

-   **System queries**: quests, investigations, audits, planning, or simulation systems.


Proximity alone does **not** increase fidelity.

* * *

## 3. Core Strategy

### Multi-fidelity simulation

-   Society is modeled at multiple resolutions simultaneously.

-   Lower tiers describe populations and flows.

-   Higher tiers describe individuals.

-   NPCs can **promote** or **demote** without losing history.


### Event-driven time

-   Most NPCs do not tick continuously.

-   State advances at **significant events** (sleep, work start, commute, recreation).


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

## 5. Promotion & Demotion Model

### Promotion triggers

-   NPC info panel opened.

-   Player-controlled interaction.

-   Quest or investigative query.


### Demotion behavior (static history)

-   No data is deleted.

-   NPC stops generating new detail when irrelevant.

-   High-cost state (plans, pathing, dialogue) may be paused or archived.


### Demotion triggers

-   Relevance TTL expires.

-   Budget pressure.

-   NPC leaves all active zones of interest.


### Continuity guarantee

-   Promoted NPCs are deterministically backfilled so their history appears consistent.


* * *

## 6. NPC Information Panels & Needs

### Basic NPC panel (Tier 2)

Fast to answer.

-   Name

-   Place of residence

-   Place of occupation or school

-   Needs overview


### Needs vector (v1)

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


### Environment ("right here, right now")

-   Derived from immediate context, not stored long-term.

-   Factors: crowding, noise, privacy, cleanliness, aesthetics, safety.

-   Can **gate actions entirely** (e.g., refuse sensitive conversations).


* * *

## 7. Aggregate Behavior & Societal Systems

NPCs do not create society by individual simulation.
They **emit demand signals** which higher-level systems resolve.

Principle:

> NPCs express intent; systems resolve outcomes.

NPCs do **not** directly decide:

-   road sizes

-   cultural dominance

-   business success


* * *

## 8. Consumption & Culture Modeling

### Preferences, not catalogs

NPCs track:

-   taste vectors

-   budget constraints

-   exposure channels


Consumption emits:

-   category

-   brand (optional)

-   intensity


Aggregate systems answer:

-   popularity trends

-   cultural dominance

-   market saturation


* * *

## 9. Movement, Flows, and Infrastructure Growth

### NPC-side movement intent

NPCs emit:

-   origin anchor

-   destination anchor

-   time window

-   transport preference


Thin NPCs do not pathfind.
Thick NPCs pathfind only when relevant.

### Flow aggregation

Movement intents aggregate into flow fields:

-   pedestrian

-   light vehicle

-   freight

-   service/emergency


Tracked by time, season, and origin–destination pairs.

### Infrastructure response

Infrastructure systems use flows to:

-   size roads and paths

-   add or remove transit

-   justify upgrades or decay


NPCs experience these changes via **environment** and accessibility.

* * *

## 10. Businesses, Ownership, and Pricing

### Roles

-   **Owner**: long-term strategy, profit goals (may be remote).

-   **Operator**: local execution and management.


Either may be:

-   NPC

-   cohort agent

-   corporate abstraction


### System vs decision-makers

Systems provide signals:

-   demand estimates

-   baseline costs

-   labor pressure

-   regulation


Owners/operators decide:

-   prices

-   wages

-   hours

-   quality level


Failure is possible.

### Outcomes

-   growth

-   stagnation

-   closure

-   acquisition


Failures propagate to NPC employment, foot traffic, and environment.

* * *

## 11. Business Competence & Adaptation

This section defines **how owners/operators make decisions**, how good they are at it, and how those decisions cascade into NPC life.

### 11.1 Modeling approach (composition over inheritance)

**Recommendation:** do _not_ create a separate NPC subclass like `BusinessManagerNPC`.

Instead:

-   Keep a single NPC model.

-   Add a **Role/Capability component** (e.g., `BusinessDecisionRole`) when an NPC is an owner/operator.


Why:

-   Many NPCs can hold multiple roles over time (operator + parent + union rep).

-   Roles can be temporarily assigned to cohorts or corporate abstractions.

-   Promotes reuse of the same intent/arbitration machinery.


If the codebase prefers OOP inheritance, use it sparingly:

-   A thin wrapper class can exist, but it should delegate to shared role logic.


* * *

### 11.2 Competence model

Owners/operators have a small, bounded competence vector (0–1):

-   **Market sense** (demand estimation, pricing intuition)

-   **Operations** (throughput, queue management, process discipline)

-   **People management** (staffing, morale, conflict)

-   **Financial control** (cost management, cashflow, reinvestment)

-   **Quality discipline** (cleanliness, consistency, compliance)

-   **Adaptability** (how quickly they change strategy)

-   **Risk tolerance** (aggressive expansion vs stability)


Competence influences:

-   decision quality

-   reaction delay to new signals

-   variance (mistakes, overreactions)


* * *

### 11.3 Core questions a business manager resolves each shift

A shift is a repeated decision cycle. The operator (and sometimes owner) answers:

**Demand & positioning**

-   How busy will we be this shift (given day/time/season/events)?

-   Which customer segments are we aiming for today?


**Pricing & offers**

-   Do we change prices today?

-   Do we run specials/discounts? (time-boxed)

-   Are we price-competitive relative to nearby substitutes?


**Staffing & labor**

-   How many staff do we schedule, and when?

-   Do we call in extras, cut early, or reassign roles?

-   What wage/overtime policies apply under pressure?


**Inventory & inputs**

-   Do we have enough supplies for expected demand?

-   What do we substitute if a key input is missing?

-   When do we reorder, and at what quantity?


**Service level & quality**

-   What is the target service speed vs quality tradeoff?

-   Are we maintaining cleanliness and compliance?

-   How do we handle queue spikes (limit menu, simplify, surge staff)?


**Incident response**

-   What do we do with:

    -   equipment failures

    -   safety incidents

    -   unruly customers

    -   staff absence


**Reinvestment & long-term** (owner-heavy)

-   Do we reinvest in equipment/training?

-   Do we expand hours, open a new location, renovate?


These decisions should be resolved **at event boundaries** (opening, rush start/end, delivery arrival, shift change), not continuously.

* * *

### 11.4 Decision outputs (what the business system emits)

Business decisions produce system-facing outputs:

-   `price_schedule` (base prices + time-boxed promos)

-   `wage_policy` (base + overtime/surge)

-   `staffing_plan` (roles, headcount, time blocks)

-   `service_capacity` (throughput estimates)

-   `quality_level_target` (cleanliness, speed vs care)

-   `inventory_orders` (what gets bought, when)

-   `access_rules` (reservations, crowd limits, dress/privacy)


* * *

### 11.5 How decisions cascade to NPCs (clean integration)

Cascades happen through **signals** that other systems already consume.

**1) Customers (demand side)**

-   Price/quality/service speed change the **utility** of choosing the business.

-   NPC Food/Leisure/Social intents resolve differently:

    -   some choose alternatives

    -   some defer

    -   some accept lower quality


**2) Employees (labor side)**

-   Staffing plans create or cancel **Work intents** for employee cohorts.

-   Wage policy affects:

    -   retention

    -   overtime acceptance

    -   migration pressure

-   Poor management increases stress and reduces morale, feeding future intent scoring.


**3) Place environment (local context)**

-   Understaffing → longer lines → higher crowding/noise → lower **Environment**.

-   Cleanliness/quality decisions directly affect perceived environment.

-   Environment gating changes whether NPCs will socialize or have sensitive conversations nearby.


**4) Infrastructure (city side)**

-   Sustained foot traffic changes flow fields.

-   Flow fields drive pathways, transit stops, and road sizing.


**5) Culture (memetic side)**

-   Successful venues increase exposure channels.

-   Trends propagate via group memberships and cohort agents.


* * *

### 11.6 Adaptation loop

Businesses adapt by comparing observed outcomes to expectations.

Inputs (per shift/day):

-   revenue

-   queue time / congestion

-   complaint rate / quality incidents

-   staffing stress (absences, turnover)

-   competitor pressure


Update rules:

-   High **adaptability** → faster changes, higher risk of oscillation

-   Low **adaptability** → slower changes, higher risk of gradual failure


Adaptation can be modeled as:

-   simple hill-climb on price and staffing

-   bounded exploration (try a promo)

-   rule-based heuristics ("raise price if sold out")


* * *

### 11.7 Thin vs Thick decision-making

-   Thin owner/operator: heuristic updates, coarse adjustments, cohort-like behavior.

-   Thick owner/operator: richer memory, narrative goals, interpersonal conflict.


* * *

## 12. Feedback Loop (End-to-End)

1.  Society estimates baseline needs.

2.  Businesses receive demand and constraints.

3.  Owners/operators set prices and operations.

4.  NPCs sample conditions and generate intent.

5.  Aggregate signals emerge (revenue, congestion, popularity).

6.  Society and infrastructure systems adjust.

7.  NPC experience and environment change.


* * *

## 13. Buildings, Places, and Anchors

Buildings and venues are already implied by the design via **anchors** (home/work/destination), but we explicitly treat them as _first-class place entities_.

### 13.1 Place anchors

NPCs and businesses reference places by ID:

-   `home_anchor` → typically a residential building/unit

-   `work_anchor` / `role_anchor` → a workplace or school venue

-   intent destinations resolve to venue/building anchors


### 13.2 Building/venue qualities (affect NPCs and businesses)

Buildings/venues expose a compact set of qualities and problems that other systems consume:

-   capacity (people throughput)

-   privacy tiers (public ↔ private)

-   cleanliness/maintenance

-   comfort (seating, temperature, noise insulation)

-   safety/security

-   accessibility (distance to transit, entrances, ADA-like constraints)

-   reliability (elevators, power, equipment uptime)


These qualities influence:

-   **Environment** ("right here, right now") when an NPC is on-site

-   business service capacity (queue times, churn)

-   utility during intent resolution (why one restaurant wins over another)


### 13.3 Cascading effects via places

Because places sit between decisions and NPC experience, they are a primary cascade pathway:

-   Operator understaffs → queues spill into public areas → crowding/noise rises → Environment drops for everyone nearby

-   Building maintenance declines → cleanliness/safety drops → fewer visits → business revenue drops → layoffs → migration pressure


No per-NPC bookkeeping is required beyond updating place state and letting NPCs sample it.

* * *

## 14. Deterministic Backfilling

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

## 15. Social Graph Compression

### Explicit strong ties

-   family

-   close friends

-   key coworkers


### Bundled ties

-   neighbors

-   shift crews

-   organizations

-   online communities


Bundles expand on promotion and collapse on demotion.

* * *

## 16. Budgets & Performance Constraints

Global limits:

-   Max Thick NPCs

-   Max Thin expansions per minute

-   Max relationship expansions

-   Max query cost per frame


Budget pressure triggers graceful demotion.

* * *

## 17. NPC Data Models

### Thin NPC

-   npc\_id

-   cohort\_id

-   home\_anchor

-   work\_anchor

-   schedule\_archetype\_id

-   traits

-   needs

-   strong\_ties

-   group\_memberships

-   next\_event\_time

-   coarse\_location\_token


### Thick NPC additions

-   memory\_log

-   relationship\_edges

-   current\_plan

-   dialogue\_state

-   reputation\_state


* * *

## 18. NPC Intent Schemas

NPC **intents** are the primary output of NPC simulation. They represent _what an NPC wants to do_, not _how it is achieved_.

Intents are:

-   lightweight

-   event-driven

-   aggregatable

-   resolvable by higher-level systems


NPCs may emit multiple intents over time, but only a small number are active concurrently.

* * *

### Intent Structure (common fields)

All intents share a minimal common schema:

-   `intent_id`

-   `npc_id`

-   `intent_type`

-   `origin_anchor`

-   `preferred_destination_tags`

-   `time_window` (earliest, latest)

-   `priority` (derived from needs, obligations, urgency)

-   `constraints` (budget, access, legality, environment gating)

-   `transport_preferences`

-   `intensity` (how strongly this intent competes with others)


Higher-level systems may resolve an intent to:

-   a specific destination

-   a deferred outcome

-   a failed or abandoned action


* * *

### Core Intent Types

#### Work / School Intent

Represents obligation-driven activity.

-   Triggered by schedule archetype or role requirements

-   High priority, low flexibility

-   Emits predictable, recurring flows


Fields:

-   `role_anchor` (workplace or school)

-   `attendance_importance`

-   `lateness_tolerance`


* * *

#### Food & Drink Intent

Represents hunger/thirst satisfaction.

-   Triggered by hunger/thirst thresholds

-   Flexible destination resolution


Fields:

-   `meal_type` (snack, meal)

-   `taste_profile`

-   `price_sensitivity`

-   `privacy_requirement`


* * *

#### Leisure / Fun Intent

Represents recreation and entertainment.

-   Driven by fun, comfort, social needs

-   Highly sensitive to culture and availability


Fields:

-   `activity_category` (media, physical, social)

-   `energy_requirement`

-   `group_size_preference`


* * *

#### Social Interaction Intent

Represents desire for interaction.

-   May target individuals or venues

-   Strongly gated by **environment**


Fields:

-   `target_type` (person, group, public)

-   `sensitivity_level`

-   `privacy_requirement`


* * *

#### Errand / Service Intent

Represents short, utilitarian tasks.

-   Low emotional weight

-   Sensitive to convenience and congestion


Fields:

-   `service_type`

-   `urgency`


* * *

#### Travel / Migration Intent

Represents medium- or long-term relocation.

-   Rare, high-impact

-   Often cohort-influenced


Fields:

-   `destination_region`

-   `motivation` (economic, family, safety)

-   `commitment_level`


* * *

### Intent Resolution & Failure

Intents may:

-   resolve successfully

-   be deferred

-   be partially satisfied

-   fail outright


Failure feeds back into:

-   needs

-   mood and stress

-   future intent priority


* * *

### Intent Aggregation

At scale, intents aggregate into:

-   demand curves

-   flow fields

-   cultural signals

-   economic pressure


No individual intent is critical; **patterns are**.

* * *

## 19. Intent Arbitration & Scheduling

NPCs often have **multiple competing intents**. Arbitration determines _which intent is acted on_, _when_, and _what happens to the rest_.

This system must:

-   be cheap for Thin NPCs

-   be expressive for Thick NPCs

-   preserve believable routine and failure


* * *

### Intent Lifecycle

1.  **Generation** – intent emitted based on needs, obligations, or triggers

2.  **Scoring** – intent assigned a dynamic priority score

3.  **Arbitration** – top intent selected for execution window

4.  **Scheduling** – selected intent reserves time/resources

5.  **Resolution** – success, partial success, deferral, or failure

6.  **Feedback** – needs and future priorities updated


* * *

### Priority Scoring

Intent priority is derived from:

-   need urgency (distance from satisfied state)

-   obligation strength (work/school/legal)

-   deadline proximity

-   past failures

-   NPC traits (discipline, impulsivity, stress tolerance)


Thin NPCs use a **simple weighted sum**.
Thick NPCs may use richer context and memory.

* * *

### Obligation Dominance

Certain intents override others by default:

-   work/school during scheduled hours

-   emergency needs (bladder, health-equivalent systems)


Overrides are _soft_, not absolute:

-   repeated suppression of needs increases stress

-   extreme unmet needs can override obligations


* * *

### Scheduling Model

NPCs maintain a **rolling short-horizon schedule**:

-   typically hours to a single day

-   represented as reserved time blocks


Thin NPCs:

-   schedule only the next significant intent

-   everything else remains unscheduled


Thick NPCs:

-   may schedule multiple future blocks

-   may rearrange plans when interrupted


* * *

### Deferral & Backlog

Unselected intents are:

-   deferred

-   decayed

-   or escalated


Rules:

-   repeated deferral increases priority

-   some intents expire (missed shows, store closing)

-   others accumulate pressure (social isolation, hunger)


* * *

### Failure Cascades

Failure to resolve intents can cascade:

-   missed work → income stress → migration intent

-   repeated social deferral → loneliness → riskier behavior

-   chronic overload → burnout → schedule collapse


These cascades occur **without scripting**, driven by priority feedback.

* * *

### Player Interaction Effects

Player actions can:

-   inject new intents

-   suppress existing intents

-   temporarily override arbitration


After intervention, NPCs resume normal arbitration with updated state.

* * *

### Performance Notes

-   Arbitration runs only at event boundaries for Thin NPCs

-   Thick NPCs may arbitrate continuously while active

-   No per-frame arbitration for inactive NPCs


* * *

## 20. Persistence, Memory, and Relationships

This section defines what gets saved, how NPC memories evolve and fade, and how interactions propagate attention to nearby NPCs.

### 20.1 Persistence tiers (what we actually store)

We store **stable identity** and **meaningful deltas**, and recompute everything else.

**Always persisted (all NPC tiers):**

-   `npc_id`

-   core identity (name seed or resolved name)

-   anchors (home/work)

-   cohort\_id / culture tags

-   traits (small vector)

-   needs baseline + `last_update_time` (event-driven)

-   strong ties + group memberships (bundled)


**Persisted when generated (monotonic history):**

-   significant memories (compressed)

-   relationship book entries (bounded)

-   major life events (graduation, marriage, job change, relocation)


**Ephemeral / recomputable (persist only for active Thick NPCs, otherwise rebuild):**

-   current plan and micro-schedule blocks

-   pathing state

-   short-lived emotions/impulses

-   transient dialogue context


Rule of thumb:

> Save what changes slowly and matters narratively; recompute what changes fast and is cheap.

* * *

### 20.2 Memory model ("significant things")

NPC memory is stored as a bounded set of **Memory Items**.

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


Memories are summaries created at:

-   major life events

-   interaction boundaries

-   promotion moments (when we need detail)


* * *

### 20.3 Fading and reinforcement

Memories and relationships **fade** unless reinforced.

Mechanics:

-   Activation probability decreases with time since reinforcement.

-   Intensity decays faster than significance.

-   Most events become low-impact background.


Life-changing outcomes are rare but possible:

-   A 5th grade soccer championship usually decays into a mild positive memory.

-   Sometimes, traits + context + reinforcement make it identity-shaping.


Reinforcement sources:

-   repeated related events

-   frequent retelling (social interactions)

-   strong emotion coupling (fear, pride, shame)

-   proximity cues (returning to places, seeing people, familiar media)


* * *

### 20.4 Relationship book ("people I've met")

Each NPC maintains a bounded **Relationship Book** keyed by other NPC IDs.

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


* * *

### 20.5 Trickle-down attention (interaction propagation)

When a Thick NPC interacts with others, the system grants **bounded spillover detail** to participants.

Rules:

-   Each interaction emits a **micro-event**.

-   Participants receive a small promotion budget ("attention tokens") to:

    -   update relationship book entry

    -   add/refresh a memory item

    -   optionally expand a bundled tie into an explicit tie


Constraints:

-   Spillover depth is capped per interaction and per time window.

-   Prefer updating existing entries over creating new ones.


This yields realistic social ripples without promoting entire crowds.

* * *

### 20.6 Save/load strategy

**World save** stores:

-   macro society state (cohorts, prices, culture weights)

-   place/building state

-   business state and histories

-   NPC persistent state (per 20.1)


On load:

-   Thin NPCs restore from persisted state

-   Thick NPCs are instantiated on demand

-   Ephemeral state is rebuilt from last stable event boundary


* * *

## 21. Open Questions & Next Steps

### Resolved / Stable

-   Multi-fidelity NPC model with promotion/demotion and static history

-   Event-driven needs, intent generation, arbitration, and scheduling

-   Business ownership, competence, adaptation, and cascading effects

-   Place/building anchors as first-class cascade surfaces

-   Persistent memory and relationship systems with decay and reinforcement


### Open Design Questions

-   **Memory limits & summarization:** How many Memory Items per NPC before forced merging, and what heuristics merge memories into life "chapters"?

-   **Relationship caps:** Maximum explicit relationships before collapsing back into bundles.

-   **Intent timing granularity:** How fine the time windows must be for believable schedules without increasing cost.

-   **Stress / mood model:** Whether stress remains implicit (derived from failures) or becomes an explicit tracked state.

-   **Business learning rate tuning:** How fast adaptation should occur to avoid oscillation or stagnation.

-   **Player leverage:** Which systems the player can directly influence (prices, zoning, labor law, transit priority).

-   **Simulation authority boundaries:** Which answers are authoritative vs probabilistic at low fidelity.

-   **Save-file size targets:** Practical limits for large worlds with millions of NPCs.


### Implementation Sequencing

1.  Implement Thin NPC intent generation + arbitration

2.  Implement aggregate flow solvers (movement, demand)

3.  Implement place/building quality sampling → Environment

4.  Implement business shift events + adaptation loop

5.  Implement memory/relationship persistence with decay
