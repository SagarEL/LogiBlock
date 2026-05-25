# LogiBlock — Design Rationale

This document explains *why* LogiBlock is structured the way it is. It is intended as a companion to the source code for academic review and future maintainers.

---

## 1. Problem Statement

Modern logistics networks depend on multiple independent parties (warehouses, transporters, last-mile agents) cooperating to move a parcel from origin to destination along a pre-agreed path. Two recurring failure modes are:

1. **Routing fraud** — a parcel is diverted through an unauthorized warehouse, with the records subsequently adjusted to hide the deviation.
2. **Delivery fraud** — an agent marks a parcel as delivered when it was not handed to the legitimate recipient.

LogiBlock addresses both by:

- **Pre-committing** the authorized warehouse sequence as a SHA-256 hash at route creation, then verifying every scan against the next expected hop.
- **Pre-committing** a delivery PIN hash at shipment creation, requiring the agent to submit the cleartext PIN (obtained from the client) to finalize delivery.
- **Appending** every lifecycle event to a hash-chained ledger so post-hoc tampering of any block invalidates every subsequent block.

---

## 2. Why a Hash Chain (and Not a "Real" Blockchain)?

A full distributed blockchain (PoW/PoS, P2P gossip, consensus) was deliberately **not** chosen for this academic project. The reasons:

- **Threat model**: the adversary is an internal operator with DB write access, not a Byzantine network. A hash chain makes any retroactive edit detectable on the next `validate_chain()` call, which is sufficient evidence for the demo.
- **Operational simplicity**: a single SQLite file is reviewable, seedable, and resettable in a classroom setting.
- **Honest scope**: claiming "blockchain" without consensus invites criticism. The implementation is best described as a **tamper-evident cryptographic audit ledger**, and the README and specs are written accordingly.

Path to a stronger design (out of scope for v2, but a natural extension):
- Add ECDSA per-role signing keys; each block carries a signature over its hash by the role that produced it.
- Compute a daily Merkle root and publish to an external append-only log (e.g., a public gist or pinned tweet) — gives an external trust anchor without P2P.

---

## 3. Architectural Decisions

### 3.1 Flask blueprints, one per role

Each role (`admin`, `warehouse`, `delivery`, `user`) is a separate blueprint under `routes/`, mounted at `/admin`, `/warehouse`, etc. The `role_required` decorator in [routes/auth.py](../routes/auth.py) gates every handler.

**Rationale:** keeps role-specific business logic physically separated and makes access control obvious at code review time.

### 3.2 SQLAlchemy with a single-file SQLite DB

The DB is initialized lazily in `app.create_app()` via `db.create_all()`. There is no migration framework; the schema is small and academic.

**Rationale:** zero-setup for demos. For production, swap the URI to Postgres and add Flask-Migrate.

### 3.3 Blockchain as an ORM model

`BlockModel` lives in [models.py](../models.py) alongside the business entities. The `Blockchain` class in [blockchain.py](../blockchain.py) is a thin service that reads/writes `BlockModel` rows.

**Rationale:** the chain *is* persistent state. Modeling it as a separate file/format would add complexity without benefit.

### 3.4 Route optimization decoupled from authorization

[routing.py](../routing.py) computes the shortest path between two warehouses (Dijkstra over a K-nearest-neighbors graph weighted by Haversine distance). This is **suggestion only** — an admin still explicitly picks the warehouse sequence for a route.

**Rationale:** automatic route selection would couple optimization correctness to authorization correctness. Keeping them separate means a bug in the graph can't undermine the security guarantee.

---

## 4. Threat Model

### 4.1 Adversary Model

We assume an internal adversary with one of:
- Warehouse staff credentials
- Delivery agent credentials
- Direct SQLite DB read/write access (but **not** the application secret key)

We do **not** assume:
- Network-level adversaries (no TLS termination is in scope)
- Adversaries with the application's `SECRET_KEY` (would enable session forgery)
- Quantum adversaries (SHA-256 preimage assumed hard)

### 4.2 Defended Threats

| # | Threat | Mitigation | Where |
|---|---|---|---|
| T1 | Warehouse claims an out-of-order scan | Sequence-order check against `Shipment.next_warehouse_sequence` | [routes/warehouse.py:29-33](../routes/warehouse.py) |
| T2 | Unauthorized warehouse on the path | Same as T1 — warehouse must match the `RouteWarehouse` row | [routes/warehouse.py:29](../routes/warehouse.py) |
| T3 | Retroactive edit of a block's `data` | Hash chain recomputes and fails on next `validate_chain()` | [blockchain.py:72-97](../blockchain.py) |
| T4 | Agent fakes a delivery | PIN hashlock — SHA-256 of submitted PIN must match the committed hash | [routes/delivery.py:53-65](../routes/delivery.py) |
| T5 | Cross-role privilege escalation | `role_required` on every handler | [routes/auth.py:21-30](../routes/auth.py) |
| T6 | Forged "authorized route" | `route_hash` pinned at route creation; admin route view shows it | [routes/admin.py:62-64](../routes/admin.py) |

### 4.3 Known Gaps

| # | Threat | Why it succeeds | Recommended mitigation |
|---|---|---|---|
| G1 | DB compromise + ability to recompute hashes | Chain has no external anchor; rewriting all blocks from index 1 produces a valid chain | Per-role signatures over each block; periodic Merkle-root publication |
| G2 | Admin–warehouse collusion | Admin can rewrite routes; route_hash check then accepts the colluding path | Multi-signature route approval (N-of-M admins) |
| G3 | QR replay | No per-scan nonce; anyone with a warehouse session can scan a leaked QR | Sign QR payloads with a short-lived TOTP-style token |
| G4 | PIN brute-force | 6-digit PIN, no rate limiting | Lockout after N failures; longer alphanumeric PIN |
| G5 | Plaintext PIN at rest | `Shipment.delivery_pin` is stored alongside the hash | Store only the hash; display PIN once at creation |
| G6 | Session forgery | Hardcoded `SECRET_KEY` in [config.py](../config.py) | Load from environment; rotate on every deploy |
| G7 | CSRF | No tokens on state-changing forms | Flask-WTF `CSRFProtect` |
| G8 | Sniffing on HTTP | PIN and credentials are plaintext on the wire | Enforce HTTPS in production |
| G9 | DoS | No rate limiting | Flask-Limiter on `/auth/login` and `/delivery/finalize_delivery` |

### 4.4 Out of Scope

- Physical tampering with the parcel itself (sealed-bag protocols, IoT tamper-evident tags)
- Sybil attacks on user accounts (no signup; admin provisions accounts)
- Side-channel attacks on the SHA-256 implementation

---

## 5. Data Model Summary

```
User ──┬─< Shipment >── Route ──< RouteWarehouse >── Warehouse
       │
       └── (role: Admin | Warehouse | Delivery | user)

Shipment ─< BlockModel (via shipment_id)
Shipment ─< Alert      (via shipment_id)
```

Genesis block (`block_index = 0`) is created at app startup if absent. All subsequent blocks reference their predecessor's `current_hash` via `previous_hash`.

---

## 6. Lifecycle of a Shipment

1. **Admin** creates a route (picks warehouses, in order). System stores `route_hash`.
2. **Admin** creates a shipment, selects a route + delivery agent. System generates a 6-digit PIN, hashes it, persists both, generates a QR pointing at the warehouse `verify` endpoint, and appends a `SHIPMENT_CREATED` block carrying the PIN hash.
3. **Admin** communicates the PIN to the client out-of-band.
4. **Warehouse 1..N** scan the QR; for each scan the system verifies `RouteWarehouse.sequence_order == Shipment.next_warehouse_sequence`. On success, appends `WAREHOUSE_VERIFIED`; on failure, appends `ROUTE_ALERT` and flags the shipment `Suspicious`.
5. **Delivery agent** reaches the client, collects the PIN, submits it. System compares `SHA256(submitted) == stored hash`. On success appends `DELIVERY_COMPLETED`; on failure appends `DELIVERY_FAILED_ATTEMPT`.
6. **Client** can view the timeline at any time via the tracking page.

---

## 7. Future Work

- Block signatures (ECDSA per-role keypair).
- Daily Merkle-root publication to an external anchor.
- Multi-signature route approval.
- Per-scan QR tokens (TOTP-style).
- Cold-chain / sensor data in `WAREHOUSE_VERIFIED` blocks.
- Geofencing on agent GPS reports with `GEO_VIOLATION` blocks.
- Public read-only verifier endpoint.
- Migration to Postgres + Flask-Migrate.
- Automated test suite (pytest) covering chain validation, route violations, and PIN hashlock.
