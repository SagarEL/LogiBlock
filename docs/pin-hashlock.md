# LogiBlock — Delivery PIN Hashlock Protocol

This document specifies the cryptographic mechanism used to prove that a parcel was delivered to its legitimate recipient and not merely marked as delivered by the agent.

Implementation: [routes/admin.py](../routes/admin.py) (PIN generation at shipment creation) and [routes/delivery.py](../routes/delivery.py) (PIN verification at delivery).

---

## 1. Goal

Prevent **delivery fraud**: a delivery agent claiming a parcel was handed to the recipient when it was not. The protocol gives the system cryptographic evidence — recorded on-chain — that the agent was in physical possession of a secret known only to the legitimate recipient at the moment of delivery.

This is structurally analogous to a **hash time-locked contract (HTLC)** in cryptocurrency systems, minus the time-lock dimension. The agent "unlocks" the delivery by presenting the preimage of a previously committed hash.

---

## 2. Roles

| Role | Knows the PIN | Knows the PIN hash |
|---|---|---|
| **System (admin)** | At generation only (then discards in a hardened design — see §6) | Yes (stored in `Shipment.delivery_pin_hash` and embedded in the `SHIPMENT_CREATED` block) |
| **Client** | Yes (communicated out-of-band by the admin) | Indirectly, via the blockchain timeline |
| **Delivery agent** | Only after the client provides it at handover | Indirectly, via the blockchain timeline |

---

## 3. Generation (at shipment creation)

[routes/admin.py:94-108](../routes/admin.py):

```python
pin       = str(random.randint(100000, 999999))                     # 6-digit decimal PIN
pin_hash  = hashlib.sha256(pin.encode("utf-8")).hexdigest()

shipment.delivery_pin       = pin           # (see §6 — known weakness)
shipment.delivery_pin_hash  = pin_hash
```

The `SHIPMENT_CREATED` blockchain block embeds `pin_hash` (not the PIN) in its payload:

```json
{
  "action": "CREATED",
  "sender": "...",
  "receiver": "...",
  "route_id": "RT-XXXXXXXX",
  "delivery_pin_hash": "<sha256-hex>"
}
```

This pins the commitment publicly on the ledger at shipment creation time, so the agent and admin cannot later swap in a different hash to match a guessed PIN.

---

## 4. Distribution

The PIN is communicated **out-of-band** from the admin to the client. The current implementation flashes the PIN to the admin UI at shipment creation; the admin is expected to relay it to the client via a separate channel (SMS, email, etc.). LogiBlock does not specify the out-of-band channel.

**Security assumption:** the out-of-band channel preserves PIN confidentiality. If the channel is compromised (e.g., shared inbox), the protocol fails.

---

## 5. Verification (at delivery)

[routes/delivery.py:48-65](../routes/delivery.py):

```python
submitted_pin     = request.form.get("pin")
submitted_hash    = sha256(submitted_pin).hexdigest()

if submitted_hash == shipment.delivery_pin_hash:
    shipment.status            = "Delivered"
    shipment.current_location  = "Destination Reached"
    blockchain.add_block(
        shipment_id        = shipment.shipment_id,
        block_type         = "DELIVERY_COMPLETED",
        data               = {"action": "HASHLOCK_VERIFIED", ...},
        digital_proof_hash = submitted_hash,   # equal to stored pin_hash
    )
else:
    blockchain.add_block(
        shipment_id = shipment.shipment_id,
        block_type  = "DELIVERY_FAILED_ATTEMPT",
        data        = {"action": "HASHLOCK_FAILED", ...},
    )
```

Every attempt — successful or failed — is appended to the ledger. A pattern of `DELIVERY_FAILED_ATTEMPT` blocks for a single shipment is itself a signal of suspicious agent behavior.

---

## 6. Known Weaknesses

| # | Weakness | Impact | Recommended fix |
|---|---|---|---|
| W1 | **Plaintext PIN stored in DB** | An attacker with read access to the `shipments` table can read every PIN and complete any delivery. | Drop the `delivery_pin` column entirely; show the PIN once at creation, never persist it. |
| W2 | **6-digit decimal space (10⁶)** | Brute-force feasible offline if the hash leaks; ~17 minutes at 1k attempts/sec online with no rate limit. | Use a longer alphanumeric PIN (e.g., 8 chars base32 ≈ 40 bits) and rate-limit `finalize_delivery`. |
| W3 | **No rate limiting** on `/delivery/finalize_delivery` | Online brute-force is unconstrained. | Flask-Limiter with per-shipment counters; lock after N failures and alert admin. |
| W4 | **No salt** in the hash | A precomputed rainbow table of all 10⁶ SHA-256 hashes (~64 MB) breaks the hash instantly if it leaks. | Use a per-shipment salt or HMAC keyed by a server secret. Better: argon2id or scrypt. |
| W5 | **No expiry** | A PIN remains valid forever, even if the parcel is never delivered. | Bind to an expiry timestamp; invalidate after the SLA window. |
| W6 | **Single-factor** | The agent only needs the PIN, not also a physical token. | Combine with a geofencing check (agent GPS within X meters of the client address). |

---

## 7. Lifecycle Summary

```
[Admin]                                              [Ledger]                       [Client]    [Agent]
   │                                                    │                              │           │
   ├── pin = randint(100000, 999999) ──────────────────►│                              │           │
   ├── pin_hash = SHA256(pin)                           │                              │           │
   ├── add_block(SHIPMENT_CREATED, {pin_hash}) ────────►│  block_n: pin_hash committed │           │
   ├── show PIN once ──── out-of-band ──────────────────┼──────────────────────────────►│           │
                                                        │                              │           │
                                                        │   ... parcel moves ...        │           │
                                                        │                              │           │
                                                        │                              │── PIN ───►│
                                                        │                              │           │
                                                        │◄── submit PIN ──────────────────────────┤
                                                        │   verify SHA256(pin) == pin_hash         │
                                                        │   add_block(DELIVERY_COMPLETED) ◄────────┤
```

---

## 8. Why a Hashlock and Not a Signature?

A signature scheme (agent signs a "delivered" attestation with the client's public key) would be cryptographically cleaner but requires every client to manage a keypair — unrealistic for a logistics end-customer. The hashlock degrades the trust model to a memorizable shared secret while preserving the property that *the agent cannot finalize without the client's cooperation*.
