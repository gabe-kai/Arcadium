---
title: Movement, Routing, & Infrastructure
slug: movement-routing-infrastructure
section: Mechanics
status: published
order: 0
---
# Arcadium Movement, Routing, and Infrastructure

> Linked document to **Arcadium** [**NPC Design**](/pages/7eb2ad0f-28db-4c2e-8217-af00e0551235). Defines routing, flow aggregation, congestion/queues, and the “auto-improving sci‑fi paths” feedback loop.

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

-   sustained utilization above target

-   forecasted peak overload

-   strategic importance (ingress hubs, backbone corridors)


Use hysteresis to prevent flapping.

* * *

## 9. Integration Points Back to NPC Design

The routing layer provides:

-   travel\_time\_proxy and transfer\_wait\_proxy (used in utility scoring)

-   queue proxies and congestion proxies (feed Environment indirectly via place occupancy/queues)


Thin NPCs:

-   never request route plans

-   only consume cost proxies


Thick NPCs:

-   may request route plans while relevant


* * *

## 10. Open Questions

-   Default assignment strategy: all-or-nothing vs stochastic vs hybrid

-   How to model vertical travel within elevator hubs (bank selection + dispatch)

-   Tram stop spacing heuristics and when to introduce new stops

-   Forecast horizon and event scheduling interface

-   Upgrade budgets and player influence over build priorities
