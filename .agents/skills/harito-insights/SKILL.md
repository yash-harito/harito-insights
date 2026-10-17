---
name: harito-insights
description: Harito business intelligence and data analytics assistant for querying visits, orders, customers, cohort retention, and partner metrics.
---

# Harito Insights Skill

This skill guides the extraction, analysis, and reporting of business data for Harito.

## 1. Quickstart & Core Client

Instead of creating ad-hoc network scripts with duplicate boilerplate, always import and use the pre-built **`HaritoClient`**:

```python
from harito_client import HaritoClient

client = HaritoClient()

# Fetch order items (handles pagination, 0.25s rate-limit throttling, test accounts, and status filtering automatically)
order_items = client.get_order_items(start_date="2026-09-01", end_date="2026-09-30", valid_only=True)

# Fetch orders
orders = client.get_orders(start_date="2026-09-01", end_date="2026-09-30")

# Fetch attendance visits
visits = client.get_visits(start_date="2026-09-01", end_date="2026-09-30")
```

## 2. Authentication & Security

1. **Token Access**: Read `TOKEN` strictly programmatically from `.env` via `python-dotenv`.
2. **Security**: **NEVER** print, log, or display the token in chat or reports under any circumstances.
3. **Expired Token (401 Unauthorized)**: If an API call fails with `401 Unauthorized`, notify the user that their `TOKEN` in `.env` has expired and request an updated token.
4. **Throttling**: The backend enforces strict rate limits. A mandatory `0.25` second delay (`time.sleep(0.25)`) is built into `HaritoClient` between every request, along with exponential retry logic on HTTP 429.

## 3. Workspace Conventions

Maintain workspace cleanliness by following these folder rules:

* **Reports & Exports (`reports/`)**: All user deliverables (`.csv`, `.xlsx`, `.html`, `.md` analysis reports) MUST be saved in `reports/`.
* **Raw Data Dumps (`data/raw/`)**: Large bulk API JSON dumps must be saved in `data/raw/`.
* **Processed Data (`data/processed/`)**: Transformed or intermediate datasets must be saved in `data/processed/`.
* **Root Directory Cleanliness**: Do NOT save temporary scripts, sample JSON dumps, or output CSVs in the workspace root. Use scratch scripts or place them in `reports/` and `data/`.

## 4. Business Rules & Domain Nuances

### Rule 1: The "Valid Orders Only" Rule
When calculating revenue, top services, customer counts, or order volumes, filter out `CANCELLED` and `REJECTED` orders by default. Only analyze valid orders (e.g., `PLACED`, `ACTIVE`, `COMPLETED`, `ONLINE_PAYMENT_PENDING`) unless the user explicitly requests cancellation metrics.

### Rule 2: Test Accounts Filtering
Always exclude internal testing numbers and dummy names:
* Test phone numbers: `2109999999`, `8770011426`, `2209999999`, `99995031960`, `9999503196`, `9363129501`, `9886761275`, `7000125334`, `7470546275`, `9620921909`, `8864904164`, `9999999999`, `0000000000`, `1234567890`, `1111111111`.
* Names containing `"test"` or `"dummy"` (case-insensitive).

### Rule 3: Order Attribution (Booking Channel)
Determine who booked each order by checking `order.meta`:
1. **CRM**: If `"crm"` key exists in `order.meta`.
2. **SUPER_ADMIN**: If `"crm"` is not present and `order.meta.createdBy.role == "SUPER_ADMIN"`.
3. **DISPATCHER**: If `order.meta.createdBy.role == "DISPATCHER"`.
4. **CUSTOMER (Self-Booking)**: If `order.meta.createdBy.role` is `"CARE_SEEKER"`, `"CUSTOMER"`, or if `createdBy` is absent.

### Rule 4: Assisted Cart vs. Direct Payment Links
* Cart links generated via `/admin/cart` and `/admin/deeplinks` (`https://www.harito.life/c/{cartId}`) are **assisted pre-filled carts** configured by staff to allow customers to self-checkout.
* They are **not** direct payment links or invoices.

### Rule 5: Note Capture Adherence
For `CHECKED_OUT` visits (especially in Physiotherapy), track whether the clinical note was submitted (`visit.visitNoteId` or attached note record).

## 5. Domain Resources & Schemas

* Detailed endpoint specifications: Refer to [references/domain.md](references/domain.md).
* Service category mappings: Refer to [resources/service_mapping.json](resources/service_mapping.json).
