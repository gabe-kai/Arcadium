---
title: Movement, Routing, & Infrastructure
slug: movement-routing-infrastructure
section: Mechanics
status: published
order: 0
---
# Movement, Routing, and Infrastructure

> Linked document to **Arcadium** [**NPC Design**](/pages/4577146d-de03-4638-b591-ae2e88b55a87). Defines routing, flow aggregation, congestion/queues, and the “auto-improving sci‑fi paths” feedback loop.

* * *

## 1. Purpose and Boundaries

### 1.1 What this document owns

-   Station-scale movement model (network + modes + transfers)

-   Routing service responsibilities and APIs

-   Aggregate flow assignment (OD → edge/node volumes)

-   Congestion and queue proxies (cheap, stable)

-   Infrastructure response: **path escalation** + hub scaling

-   Forecasting and hysteresis (avoid flapping upgrades)


### 1.2 What this document does NOT own

-   NPC intent generation and arbitration (see **Arcadium NPC Design**, Sections 8–9)

-   Candidate sets and utility scoring (see **Arcadium NPC Design**, Sections 10.5–10.6)

-   Business pricing/agency and economic institutions (see **Arcadium NPC Design**, Section 12)


### 1.3 Core principle

> **NPCs express origins/destinations and constraints. The routing layer answers costs and (when needed) route plans.**

* * *

## 2. Station Topology Assumptions

### 2.1 Primary ingress and transfer hubs

Traffic enters and redistributes via:

-   Major **elevator hubs** (vertical distribution)

-   **Maglev hubs** (platforms, gates, transfers)

-   **Spaceports** (security, customs, boarding)

-   Dozens of smaller connectors (local lifts, secondary platforms, service corridors)


### 2.2 Walkability baseline

-   Most destinations are within ~5 km diameter station footprint

-   Walking is always available, but can be enhanced by escalator roads / moving walkways / trams


### 2.3 Auto-improving paths vision

Sustained flows (plus forecasted demand) cause corridors to escalate:

-   Wider pedestrian corridors

-   Moving walkways / escalator roads

-   Trams (higher capacity)
    …and hubs scale similarly (more elevator cars, gates, lanes, scheduling improvements).


* * *

## 3. Network Model

### 3.1 Graph primitives

-   **Node:** junction, hub bank, platform gate, building entrance, tram stop

-   **Edge:** traversable segment between nodes


### 3.2 Edge attributes (minimum)

-   `mode` (walk, moving\_walkway, escalator\_road, tram, elevator\_segment, maglev\_segment, service\_only)

-   `free_time` (empty traversal time)

-   `capacity` (people per bucket; mode-dependent)

-   `comfort_cost` (optional)

-   `access_rules` (e.g., staff-only, ticketed)

-   `reliability` (optional; outages handled in shock rules)


### 3.3 Transfer model

Transfers are modeled as **node-local costs** and/or **queue nodes**:

-   elevator dispatch wait

-   platform gate/security processing

-   tram boarding dwell


* * *

## 4. Routing and Flow Services

### 4.1 Separation of query types

-   **Cost query (cheap):** returns travel + transfer wait proxies, no explicit path

-   **Plan query (expensive):** returns a route plan (steps), used only for relevant Thick NPCs and player-facing UI

-   **Assignment query (aggregate):** consumes OD volumes and produces edge/node volumes and congestion/queue proxies


### 4.2 Service API contracts (design level)

**EstimateTravelCost**

-   Input: origin anchor/zone, destination anchor/zone, time bucket, transport preferences, access constraints

-   Output: `travel_time_proxy`, `transfer_wait_proxy`, `reliability_risk`, optional `dominant_mode`


**GetRoutePlan** (Thick / player-facing)

-   Input: origin node, destination node, bucket, preferences

-   Output: ordered steps (edges + transfers) and an ETA estimate


**AssignFlows** (aggregate)

-   Input: OD demand volumes by bucket + mode preferences

-   Output: edge volumes, node arrivals, congestion proxies


**EstimateQueues**

-   Input: node arrivals by bucket + service configs

-   Output: queue length proxies, wait-time proxies, overflow/backlog signals


### 4.3 Time bucketing and determinism

Routing and infrastructure operate in discrete **Simulation Buckets (SB)** aligned to clock time (e.g., :00, :15, :30, :45) to enable caching, aggregation, and readable debugging.

-   **Default SB:** 15 minutes

-   **Allowed SB sizes:** 5, 10, 15, 30, 60 minutes (discrete set)

-   Bucket size may refine/coarsen by region and time-of-day (adaptive bucketing) without changing Thin NPC update cost.


**Arrival spreading (anti-synchronization):** OD volumes are mapped into buckets by time-window overlap (optionally with small deterministic jitter seeded by zone/day/bucket).

**Determinism:** Given world seed + macro conditions + bucket inputs, assignment/queues/congestion are deterministic (stochastic assignment uses seeded randomness).

* * *

## 5. Aggregate Flow Assignment

### 5.1 OD always recorded

OD (origin–destination) volumes are the durable representation.

### 5.2 Assignment strategies (selectable)

-   All-or-nothing shortest-path assignment (fast baseline)

-   Stochastic assignment (reduces brittle single-route domination)

-   Multi-modal assignment (walk vs tram vs elevator mixes)


### 5.3 Determinism policy

-   Assignment is deterministic given seeds and bucket inputs

-   Any stochasticity is seeded per (zone, day, bucket) so runs remain comparable


* * *

## 6. Congestion Proxies

### 6.1 Edge utilization

Per bucket:

-   `utilization = volume / capacity`


### 6.2 Congestion score and travel-time curve

-   `congestion_score` is a bounded function of utilization

-   Travel time grows **gently** until ~70–80% capacity, then sharply near capacity


### 6.3 Smoothing and forecasting signals

Maintain per edge:

-   Recent EWMA utilization

-   Scheduled forecast (time-of-day / event calendar)


These feed both cost queries and infrastructure response.

### 6.4 Travel-time proxy and transfer penalties

The routing layer exposes **proxies**, not per-agent physics:

-   `travel_time_proxy` = edge traversal time adjusted by congestion

-   `transfer_wait_proxy` = expected wait at choke nodes (elevator banks, gates, platforms)


Transfer penalties can include:

-   dwell times (boarding, security processing)

-   accessibility friction (stairs vs ramps, mobility constraints)


Thin NPCs consume these proxies for utility scoring; only Thick NPCs request explicit route plans.

* * *

## 7. Queue Proxies (Choke Nodes)

### 7.1 Queue node model

A queue node has:

-   `service_rate` (μ)

-   `servers` (c)

-   optional priority classes (staff vs public, ticketed vs general)


### 7.2 Output proxies

Per bucket:

-   `queue_length_proxy`

-   `wait_time_proxy`

-   `overflow_backlog` (spills into next buckets)


### 7.3 Key queue nodes for Arcadium

-   elevator banks

-   maglev platform gates / boarding

-   spaceport security / customs

-   tram platforms

-   venue service counters (restaurants, clinics, gov)


* * *

## 8. Infrastructure Response: Auto-Improving Paths

### 8.1 Escalation ladder (corridor upgrade path)

A corridor edge can escalate through discrete tiers:

1.  Walk corridor

2.  Widened corridor

3.  Moving walkway

4.  Escalator road

5.  Tram corridor (with stops)


Each tier changes:

-   capacity ↑

-   free\_time ↓ (effective speed)

-   comfort ↑ (optional)


### 8.2 Hub scaling ladder

Hubs scale similarly:

-   elevator banks: more cars/shafts, better dispatch policies, express routing

-   maglev hubs: more gates, longer platforms, better scheduling

-   spaceports: more lanes, better processing capacity

-   trams: frequency, cars, stop spacing


### 8.3 Upgrade pressure signals

Upgrade pressure should combine:

-   sustained utilization above target (EWMA)

-   forecasted peak overload (calendar + seasonality)

-   strategic importance (ingress hubs, backbone corridors)

-   hub pain multiplier (queues and transfer waits matter more at hubs)


Use hysteresis to prevent flapping.

### 8.4 Level-of-service targets (LOS)

Infrastructure aims for target operating bands rather than perfect optimization.

Suggested default targets (tuneable):

-   `edge_util_target_band`: 0.65–0.80

-   `queue_pressure_target`: < 0.70 most buckets

-   `transfer_wait_targets` by hub type (elevator vs maglev vs spaceport)


Targets are aspirational: persistent scarcity and mismanagement should remain visible.

### 8.5 Pressure → project selection (prioritization)

A corridor/hub becomes a candidate project when pressure exceeds threshold for a sustained window.

Prioritization factors (bounded score):

-   pressure magnitude (how far above target)

-   population affected (flow volume)

-   criticality (hub feeder/backbone)

-   equity modifiers (optional)

-   player priorities (if enabled)


Tie-break using deterministic seeded jitter.

### 8.6 Hysteresis and construction latency

To avoid upgrade/downgrade thrashing:

-   upgrade threshold > downgrade threshold

-   minimum time-in-tier before downgrade is permitted

-   minimum hold time between upgrades

-   upgrades apply after a construction latency (days/weeks/months depending on tier)


Latency is a feature: it creates believable build timelines and makes forecasting meaningful.

### 8.7 Budgets and concurrency limits

Infrastructure changes are budgeted:

-   **Capex budget:** projects started per planning period

-   **Opex budget:** maintenance burden of higher tiers

-   **Concurrency cap:** maximum simultaneous projects (global and per district)


Budgets enforce tradeoffs and keep infrastructure progression legible.

### 8.8 Downgrade and decay policy (slow)

Downgrades are allowed but should be rare and slow.

Drivers:

-   sustained underuse below a lower band

-   high maintenance burden relative to benefit

-   strategic reconfiguration (player or macro policy)


Downgrades should have long minimum dwell times and small per-period limits.

### 8.9 Construction disruption outputs

While projects are active, affected places/edges emit temporary disruptions:

-   reduced capacity / increased traversal time

-   noise/crowding spikes

-   `construction` / `blocked` / `detour` tags


These feed into Environment and travel proxies so NPC behavior adapts without special-casing.

* * *

## 9. Integration Points Back to NPC Design

This document implements the detailed policy behind the NPC-facing contract defined in **Arcadium NPC Design** (see Section 11.3 scope boundary).

The routing/infrastructure layer provides:

-   `travel_time_proxy` and `transfer_wait_proxy` (utility scoring)

-   congestion proxies (cost shaping)

-   queue proxies (choke nodes)

-   **accessibility indices** (how reachable a place is under current network conditions)

-   **disruption tags** (construction/closures/detours) that temporarily affect Environment and routing costs


It also produces aggregate place-adjacent dynamics used by Environment:

-   occupancy estimates

-   queue estimates


Thin NPCs:

-   never request route plans

-   only consume cost proxies and accessibility/disruption signals


Thick NPCs:

-   may request route plans while relevant


* * *

## 10. Design Worklist

This section is a **document worklist** for movement/routing/infrastructure: what to add, expand, or tighten next.

1.  **Choose default flow assignment strategy**

    -   Decide baseline (all-or-nothing vs stochastic vs hybrid) and where multi-modal mixing lives.

2.  **Vertical travel model for elevator hubs**

    -   Define bank selection, dispatch approximation, and how `transfer_wait_proxy` is produced per bucket.

3.  **Tram introduction + stop spacing heuristics**

    -   Define when a corridor graduates to tram, stop spacing rules, and service frequency/capacity knobs.

4.  **Forecasting + event interface**

    -   Define forecast horizon, how the event calendar injects predicted demand, and how forecasts affect both routing costs and upgrade pressure.

5.  **Infrastructure planning budgets + player influence hooks**

    -   Define capex/opex/concurrency limits, prioritization scoring, and the explicit levers the player can set.

6.  **Disruption semantics and propagation**

    -   Define standard disruption tags (construction/blocked/detour) and how they affect travel proxies vs Environment (severity bands).


* * *

## 11. Open Questions

-   Default assignment strategy: all-or-nothing vs stochastic vs hybrid

-   How to model vertical travel within elevator hubs (bank selection + dispatch)

-   Tram stop spacing heuristics and when to introduce new stops

-   Forecast horizon and event scheduling interface

-   Upgrade budgets, concurrency caps, and player influence over build priorities

-   Default LOS targets and threshold bands (edge utilization, transfer waits, queue pressure)

-   Construction latency and downgrade/decay rules (minimum time-in-tier)

-   Disruption tagging: which tags are universal and how strongly they affect Environment vs travel costs
