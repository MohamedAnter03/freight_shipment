# Freight Shipment Management — Task Notes

## Context

The goal was an Odoo 19 module that lets a logistics team register shipment
requests, move each one through its delivery lifecycle with explicit user
actions, and print a shipment order for the driver — nothing more. I kept the
scope deliberately tight (no pricing, no fleet/accounting links, no portal,
per the brief).

Assumptions I made:

- **Origin / destination are free-text fields**, not partner addresses or a
  location master-data model. The brief treats them as simple route
  information; a location model would add configuration burden with no
  requirement behind it. If routes ever need reuse/analytics, this can be
  promoted to a `freight.location` model later without breaking data.
- **Cargo weight and volume are per unit**; each line also shows its computed
  line total (`quantity × unit value`), and the shipment totals sum the line
  totals. I find "10 boxes of 8 kg each" the natural way a clerk enters cargo.
- **Pickup/delivery dates are "requested" dates** (plain dates, not
  datetimes) — they express the customer's wish, not an operational schedule,
  so no time component is needed.
- **The lifecycle only moves forward.** The brief describes a one-way flow, so
  there is no "reset to Preparing" button. Adding one would be a 5-line change.
- **Delivered shipments become read-only** in the form (route, dates, cargo)
  so history can't be silently rewritten; the chatter stays available.

## What you did (outcomes)

- A **Freight** app appears in the main menu with its own icon.
- Managers maintain **shipment types** (name, unique code, category
  Land/Air/Sea/Other) and can **archive** a type without losing history —
  archived types disappear from selection but old shipments keep them.
- Any freight user can **register a shipment request**: the reference
  (`SHP/2026/00001`, yearly sequence) is assigned automatically; customer,
  type, origin, destination and requested pickup/delivery dates are recorded.
  Delivery date can't precede pickup date.
- **Cargo items** (description, quantity, unit weight, unit volume) are edited
  inline; line totals and the shipment's **total weight / total volume**
  recompute automatically on any add / change / remove (stored computed
  fields, so they're also searchable and correct in list-view sums).
- The shipment moves **Preparing → With Courier → On the Way → Delivered**
  through three header buttons. The status field itself is read-only, kanban
  drag & drop is disabled, and stage skipping is blocked server-side (so RPC
  calls can't cheat either).
- Trying to leave *Preparing* with **no cargo items** raises a friendly,
  named error explaining exactly what to do.
- Every status change (and changes to customer, type, route, dates) is
  **tracked in the chatter**, with timestamps and authors.
- **Two roles**: *Freight / User* (manage shipments, read types) and
  *Freight / Manager* (adds full control of shipment types + the
  Configuration menu). Employees outside these groups see nothing — there are
  no ACLs for `base.group_user`.
- **Views**: list (with optional columns + weight/volume sums), kanban grouped
  by status where **all four stages are always visible even when empty**
  (`group_expand`), form with statusbar + chatter, and search with status
  filters, pickup-date filter and group-by status/type/customer.
- A **Shipment Order PDF** (header button or Print menu) shows reference,
  customer block, type, dates, route, the cargo table and the totals.
- **Demo data** (4 types, 2 shipments with cargo) and **10 automated tests**
  covering the sequence, total recomputation, the no-cargo guard, the full
  lifecycle, stage-skip protection, date/quantity constraints, code
  uniqueness, and both roles' access rights.

## Findings, caveats, and setup

**Findings**

- Odoo 19 changed the security plumbing: groups are attached to a
  `res.groups.privilege` (not directly to an `ir.module.category`), and a
  group without a privilege is treated as technical/hidden. The module uses
  the new pattern, so both roles show up properly in the user form.
- Odoo 19's search-view RNG no longer accepts `string` on `<group>` (the
  classic `<group string="Group By">` fails validation) — worth knowing if
  you port older view XML.
- `group_expand=True` on a Selection field is enough in Odoo 19 to keep all
  kanban columns visible; no expand method is needed.

**Caveats / not done**

- No record rules beyond group ACLs (e.g. "salesman sees own shipments
  only") — not requested, easy to add as an `ir.rule` later.
- Weight/volume units are fixed (kg / m³) rather than configurable UoM.
- Ideas deliberately left out per the brief: pricing, carrier APIs, customer
  portal tracking page, fleet/driver assignment.

**Setup**

1. Copy the `freight_shipment` folder into an addons path of a fresh
   Odoo 19 instance and update the apps list.
2. Install **Freight Shipment Management** (installs cleanly, no errors;
   with demo data enabled you get sample types and shipments).
3. Assign users: Settings → Users → "Freight" privilege → *User* or
   *Manager*. (Admin is a Manager automatically.)
4. Try it: Freight → Shipments → New; add cargo lines; use the header
   buttons to advance the lifecycle; *Print Shipment Order* for the PDF.
5. Tests: `odoo-bin -d <db> -u freight_shipment --test-tags /freight_shipment --stop-after-init`.

## Data model and why

Three models, one master-data + one document + one document line — the
smallest shape that satisfies every requirement without denormalising:

```
freight.shipment.type   (master data, archivable)
        ▲ many2one
freight.shipment        (the request/document, chatter + lifecycle)
        ▲ one2many / many2one
freight.cargo.line      (line items, cascade-deleted with the shipment)
```

- **`freight.shipment.type`** is a separate model (not a Selection) because
  the brief requires team leads to *maintain* the list at runtime and archive
  entries — that's master data. `code` has a SQL unique constraint; `active`
  gives archiving for free (archived types stay on historical shipments but
  leave the dropdown). The *category* is a Selection on the type because its
  values (Land/Air/Sea/Other) are a stable classification, not user-managed
  data — a third model would be over-engineering.
- **`freight.shipment`** is the document. It inherits `mail.thread` +
  `mail.activity.mixin` so status history is a first-class audit trail
  (requirement 7) instead of a custom log model — chatter is the standard,
  zero-maintenance way Odoo users expect to read history. `state` is a
  Selection rather than a stages model because the four stages are fixed
  business vocabulary with code attached to transitions; configurable stages
  would move workflow rules into data and weaken the guards.
- **`freight.cargo.line`** is a classic one2many line model (same shape as
  sale/purchase order lines) because cargo is meaningless outside its
  shipment: `ondelete='cascade'`, and totals on the shipment are **stored
  computed fields** depending on the line totals — the ORM recomputes them on
  any line create/write/unlink, which is exactly requirement 4, and storing
  them makes them usable in list sums, search and the PDF without extra
  queries.
- Transitions live in one guarded helper (`_advance_state`) called by the
  three buttons, so every path — UI button, RPC, script — enforces the same
  rules: correct current stage, and cargo present before leaving *Preparing*.
