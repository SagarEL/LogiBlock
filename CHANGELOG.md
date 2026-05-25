# Changelog

All notable changes to LogiBlock are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project follows informal semantic versioning during its academic lifecycle.

---

## [Unreleased]

### Added
- Architecture diagram (Mermaid) and happy-path sequence diagram in [README.md](README.md).
- Threat model section in [README.md](README.md) summarizing defended and undefended threats.
- `docs/` folder containing:
  - [docs/design.md](docs/design.md) — design rationale, adversary model, full threat table, future work.
  - [docs/blockchain-spec.md](docs/blockchain-spec.md) — block schema, hash composition, validation algorithm, known spec gaps.
  - [docs/route-hash.md](docs/route-hash.md) — route hash construction and scan-time verification.
  - [docs/pin-hashlock.md](docs/pin-hashlock.md) — delivery PIN hashlock protocol and known weaknesses.
- This `CHANGELOG.md`.

### Removed
- Firebase cloud-sync layer (`firebase_config.py`, `firebase_sync.py`, `sync_all.py`, `test_firebase.py`). LogiBlock is now strictly local-SQLite.
- `restore_integrity` admin action is now a no-op flash message since the cloud-sync source-of-truth no longer exists. Slated for full removal or re-implementation against a local snapshot.

### Changed
- README rewritten for clarity and honest framing — the term "blockchain" is qualified as a single-node hash-chain ledger.
- Admin validate template ([templates/admin/validate.html](templates/admin/validate.html)) updated for the post-Firebase flow.
- Base layout ([templates/base.html](templates/base.html)) and global stylesheet ([static/css/style.css](static/css/style.css)) refreshed.

---

## [0.2.0] — Hash-Chain V2 Schema

Commit: `ab08d55` (*"Everthing updated"* — typo preserved in git history).

### Added
- 25-warehouse seed across major Indian cities ([seed_data.py](seed_data.py)), replacing the initial 10-warehouse set.
- Delivery agent map dashboard with Leaflet.js route visualization.
- Client tracking timeline rebuilt from blockchain events.
- Route optimization via Dijkstra + K-nearest-neighbors graph ([routing.py](routing.py)).
- Tamper simulation feature for academic demonstration of chain integrity.
- Per-shipment PIN hashlock for delivery finalization.

### Changed
- Database schema bumped to V2 (`logistics_v2.db`); new columns on `Shipment` (`next_warehouse_sequence`, `delivery_pin`, `delivery_pin_hash`) and on `BlockModel` (`route_hash`, `verification_status`, `digital_proof_hash`).
- Blueprints reorganized under `routes/` with strict role isolation (`admin`, `warehouse`, `delivery`, `user`).

---

## [0.1.1] — Firebase Sync Layer

Commit: `6320b91` (*"Firebase Updated"*).

### Added
- Firebase Firestore sync for blockchain blocks and core entities (later removed — see Unreleased).
- `firestore.indexes.json`, `firestore.rules`, `firebase.json` configuration files.

> This release is preserved for historical reference. The Firebase layer was removed in the next iteration because it added operational complexity without strengthening the academic threat model.

---

## [0.1.0] — Initial Commit

Commit: `b39b9a6` (*"Intial Commit"* — typo preserved in git history).

### Added
- Flask application skeleton with role-based login.
- SHA-256 hash-chain ledger (`Blockchain` class, `BlockModel`).
- Admin, Warehouse, Delivery, and Client dashboards (initial templates).
- SQLite persistence at `database/logistics_v2.db`.
- TailwindCSS + FontAwesome glassmorphism UI.

---

## Notes on Historical Commit Messages

The early git log contains shorthand and typos (*"Intial Commit"*, *"Everthing updated"*) that don't describe the actual scope of the work. This changelog is the authoritative record going forward; future entries will be added under `[Unreleased]` before each release and promoted to a versioned section on tag.
