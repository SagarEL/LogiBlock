# LogiBlock — Hash-Chain Ledger Specification

This document specifies the on-disk format, hash composition, and validation algorithm of the LogiBlock ledger. Implementation in [blockchain.py](../blockchain.py); persistence model in [models.py](../models.py) (`BlockModel`).

---

## 1. Block Schema

Each block is one row in the `blockchain` table (SQLite). Columns:

| Column | Type | Nullable | Purpose |
|---|---|---|---|
| `id` | INTEGER PK | no | Surrogate primary key (DB-managed; not part of the hash) |
| `block_index` | INTEGER | no | Monotonic, starts at 0 (genesis). The position in the chain. |
| `shipment_id` | STRING(50) | yes | Foreign reference to the shipment this block describes; `"GENESIS"` for block 0, may be `NULL` for system events. |
| `block_type` | STRING(50) | no | One of the event types in §3. |
| `warehouse_id` | STRING(50) | yes | Set for `WAREHOUSE_VERIFIED` and `ROUTE_ALERT` blocks. |
| `data` | TEXT | no | JSON-encoded event payload, **canonicalized with `json.dumps(..., sort_keys=True)`**. |
| `previous_hash` | STRING(64) | no | Hex SHA-256 of the immediately preceding block; `"0"` for genesis. |
| `current_hash` | STRING(64) | no | Hex SHA-256 over the fields listed in §2. |
| `route_hash` | STRING(64) | yes | When applicable, the route hash this event is bound to. |
| `verification_status` | STRING(50) | yes | `"SUCCESS"` or `"FAILED"` for warehouse/delivery events. |
| `digital_proof_hash` | STRING(64) | yes | SHA-256 of the PIN, included on `DELIVERY_COMPLETED`. |
| `timestamp` | FLOAT | no | UNIX epoch seconds at block creation. |

---

## 2. Hash Composition

The `current_hash` of a block is computed by [`Blockchain.calculate_hash`](../blockchain.py):

```
current_hash = SHA256(
    str(block_index)
  + previous_hash
  + str(timestamp)
  + data                       # canonical JSON, sort_keys=True
  + block_type
  + (warehouse_id or "")
  + (route_hash or "")
)
```

Notes:
- Concatenation is **direct string concatenation** with no separator. This is a known weakness (length-extension ambiguity is not a concern for SHA-256, but field-boundary ambiguity is) and is preserved here for fidelity with the implementation; a future version should use length-prefixed framing or a canonical encoding such as protobuf.
- `data` MUST be re-serialized with `sort_keys=True` before hashing or before re-validation, otherwise key-order differences will produce different hashes for semantically identical payloads.
- `verification_status` and `digital_proof_hash` are **persisted but not included in the hash**. This is a known limitation: an attacker editing only `verification_status` would not be detected by `validate_chain()`. A v3 spec should include all persisted columns in the hash.

---

## 3. Event Types (`block_type` values)

| Type | Producer | Payload (`data`) | Fields populated |
|---|---|---|---|
| `GENESIS_BLOCK` | App startup | `{"message": "Genesis Block"}` | `block_index=0`, `previous_hash="0"` |
| `SHIPMENT_CREATED` | Admin | `{action, sender, receiver, route_id, delivery_pin_hash}` | — |
| `WAREHOUSE_VERIFIED` | Warehouse | `{message, warehouse}` | `warehouse_id`, `verification_status="SUCCESS"` |
| `ROUTE_ALERT` | Warehouse (on mismatch) | `{message, actual_warehouse}` | `warehouse_id`, `verification_status="FAILED"` |
| `DELIVERY_COMPLETED` | Delivery agent | `{action, message}` | `digital_proof_hash` |
| `DELIVERY_FAILED_ATTEMPT` | Delivery agent | `{action, message}` | — |

---

## 4. Append Algorithm

Pseudocode for [`Blockchain.add_block`](../blockchain.py):

```
function add_block(shipment_id, block_type, data, warehouse_id?, route_hash?, verification_status?, digital_proof_hash?):
    latest      = SELECT * FROM blockchain ORDER BY block_index DESC LIMIT 1
    new_index   = latest.block_index + 1
    timestamp   = time.time()
    data_str    = json.dumps(data, sort_keys=True)
    prev_hash   = latest.current_hash
    cur_hash    = calculate_hash(new_index, prev_hash, timestamp, data_str,
                                 block_type, warehouse_id, route_hash)
    INSERT ... ; COMMIT
```

Concurrency: SQLite serializes writes, so two simultaneous `add_block` calls cannot interleave on `latest`. Under Postgres, wrap the read + insert in a `SERIALIZABLE` transaction or take an advisory lock on `block_index`.

---

## 5. Validation Algorithm

[`Blockchain.validate_chain`](../blockchain.py) returns `(is_valid: bool, broken_index: int)`:

```
function validate_chain():
    chain = SELECT * FROM blockchain ORDER BY block_index ASC
    if chain is empty: return (True, -1)

    for i in 1 .. len(chain) - 1:
        current  = chain[i]
        previous = chain[i-1]

        # 1. Recompute the block's own hash and compare.
        if calculate_hash(current.block_index,
                          current.previous_hash,
                          current.timestamp,
                          current.data,
                          current.block_type,
                          current.warehouse_id,
                          current.route_hash) != current.current_hash:
            return (False, current.block_index)

        # 2. Verify the linkage to the previous block.
        if current.previous_hash != previous.current_hash:
            return (False, current.block_index)

    return (True, -1)
```

Genesis block (`i = 0`) is intentionally skipped — it has `previous_hash = "0"` by convention.

---

## 6. Tampering Simulation

[`Blockchain.simulate_tampering`](../blockchain.py) picks the lowest non-genesis block, edits its `data` JSON to inject a `tampered: true` marker, and re-commits **without** updating `current_hash`. The next `validate_chain()` call returns `(False, index_of_tampered_block)`.

This is a demonstration aid, not a production code path. It exists to let the admin UI prove the integrity property visually.

---

## 7. Known Specification Gaps

These are intentional limitations of v2; a future v3 should address them:

1. **Hash field boundaries** — fields are concatenated without separators; a malicious payload could in principle straddle boundaries to produce a collision-friendly preimage. *Fix:* length-prefixed framing.
2. **Incomplete field coverage** — `verification_status` and `digital_proof_hash` are not in the hash. *Fix:* include all persisted columns.
3. **No signatures** — anyone with DB write access can append valid blocks. *Fix:* per-role ECDSA keypairs; each block carries `signature = Sign(role_priv, current_hash)`.
4. **No external anchor** — the chain self-validates but has no external trust root. *Fix:* publish daily Merkle root to an immutable external log.
5. **`block_index` is not unique-constrained** at the schema level. *Fix:* add a unique index.
