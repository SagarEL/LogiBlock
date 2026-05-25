# LogiBlock — Route Hash Specification

This document specifies how authorized warehouse routes are committed cryptographically and how each warehouse scan is verified against that commitment.

Implementation: [`Blockchain.generate_route_hash`](../blockchain.py) and the scan path in [routes/warehouse.py](../routes/warehouse.py).

---

## 1. Purpose

When an admin creates a route, they choose a strictly-ordered list of warehouses the parcel must pass through. The system computes a **route hash** that pins this sequence at creation time. Any subsequent attempt to claim a different sequence (whether by tampering with the route record or by a warehouse scanning out of order) is detectable.

---

## 2. Construction

Given an ordered list of warehouse identifiers `[w1, w2, ..., wn]` (as supplied by the admin form), the route hash is:

```
route_string = "w1->w2->w3->...->wn"           # literal "->" separator
route_hash   = SHA256(route_string).hexdigest()
```

Reference implementation:

```python
def generate_route_hash(self, route_warehouses_list):
    route_str = "->".join([str(wh_id) for wh_id in route_warehouses_list])
    return hashlib.sha256(route_str.encode("utf-8")).hexdigest()
```

The `warehouse_id` values are the *business* warehouse identifiers (e.g., `WH-MUM-01`), **not** the SQL surrogate primary keys. This keeps the hash stable across database re-seeds as long as the warehouse codes are stable.

---

## 3. Storage

| Location | Field | Notes |
|---|---|---|
| `routes` table | `route_hash` | Stored at route creation, never updated. |
| `routes` table | `id`, `route_id`, `source`, `destination` | Identifiers and human-readable labels. |
| `route_warehouses` table | `(route_id, warehouse_id, sequence_order)` | The ordered list. `sequence_order` is 1-based. |

The `route_hash` and the `route_warehouses` rows redundantly describe the same authorized sequence. The hash is the **commitment**; the rows are the **operational representation** used at scan time.

---

## 4. Verification at Scan Time

When a warehouse scans a shipment's QR and submits its `warehouse_id`, the verification flow ([routes/warehouse.py:21-67](../routes/warehouse.py)) is:

```
1. Load shipment by shipment_id.
2. Look up the expected RouteWarehouse:
       SELECT * FROM route_warehouses
        WHERE route_id        = shipment.route_id
          AND sequence_order  = shipment.next_warehouse_sequence
3. Resolve the submitted warehouse_id to its row.
4. If submitted.id == expected.warehouse_id:
       - status = "In Transit"
       - current_location = warehouse.name
       - next_warehouse_sequence += 1
       - Append WAREHOUSE_VERIFIED block (carries route's hash via the shipment).
   Else:
       - status = "Suspicious"
       - Create an Alert row (ROUTE_VIOLATION).
       - Append ROUTE_ALERT block.
```

The `next_warehouse_sequence` counter on the shipment is the moving cursor; the route's hash is the static commitment. Together they enforce: *the parcel must pass each hop, in order, exactly once*.

---

## 5. Properties

| Property | Holds? | Notes |
|---|---|---|
| **Order-sensitive** | ✓ | `"WH-A->WH-B" ≠ "WH-B->WH-A"`. |
| **Length-sensitive** | ✓ | Adding or removing a hop produces a different hash. |
| **Collision-resistant** | ✓ | Per SHA-256 assumptions. |
| **Forward-secure** | ✗ | A compromised DB can have its `route_hash` recomputed. The route hash is a commitment to the *plan*, not a signed authorization. |
| **Replay-resistant** | ✗ | The same QR can be re-scanned by a colluding warehouse with valid credentials. Per-scan nonces would be required. |

---

## 6. Known Gaps

1. **Direction ambiguity** — the `"->"` separator could appear inside a warehouse_id in a malicious deployment. *Fix:* enforce warehouse_id charset (alphanumeric + `-`) at admin form validation, or use a length-prefixed encoding.
2. **No salt** — the hash is deterministic and short. For 25 warehouses and routes of length ≤ 5, an attacker can precompute hashes for all permutations to *recognize* (not break) routes. Not a security boundary, but worth noting.
3. **Hash not enforced in scan path** — the scan path checks `RouteWarehouse` rows directly. If those rows are tampered with, the `route_hash` is the only witness; but the system does not currently recompute `generate_route_hash(rows)` and compare against the stored `route_hash`. *Fix:* on every scan, recompute and compare; alert on mismatch.

---

## 7. Example

Admin creates a route:

```
source       = "Mumbai"
destination  = "Delhi"
warehouses   = ["WH-MUM-01", "WH-PNQ-01", "WH-JAI-01", "WH-DEL-01"]

route_string = "WH-MUM-01->WH-PNQ-01->WH-JAI-01->WH-DEL-01"
route_hash   = SHA256(route_string)
             = "a8f1...e93b"   (illustrative)
```

A shipment is created on this route. Scans must arrive in the order `WH-MUM-01, WH-PNQ-01, WH-JAI-01, WH-DEL-01`. Any other order — or any warehouse not in the list — triggers a `ROUTE_ALERT`.
