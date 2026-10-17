# Harito API Domain Knowledge

This document summarizes the known Harito API endpoints, concepts, and behaviors based on the analysis and data extraction scripts.

## Core Concepts
* **Base URL:** `https://www.harito.life/api/v1/`
* **Authentication:** Uses Bearer Tokens passed in the `Authorization` header. Keys are typically stored in environment variables (e.g., `.env`).
* **Pagination Strategy:** Standard offset pagination using `page` (1-indexed) and either `pageSize` or `limit` query parameters.
* **Response Format:** JSON payloads, typically returning arrays of data objects or nested `data.items` structures depending on the endpoint.

## 1. Visits API (Attendance)
* **Endpoint:** `GET /attendance/visits`
* **Purpose:** Retrieves patient visit and appointment records. Used heavily for calculating dropped users, funnel metrics, and completed appointments.
* **Pagination:** `page` and `pageSize` (typically set to 50 or 100 for bulk extraction).
* **Key Query Parameters:**
  * `startDate` (YYYY-MM-DD)
  * `endDate` (YYYY-MM-DD)
* **Visit Statuses:**
  * **Successful / Valid:**
    * `CHECKED_OUT`: Visit completed successfully.
    * `ATTENDED`: Patient arrived and was attended to.
    * `MID_VISIT_CHECKOUT`: Visit concluded early or partially.
  * **Dropped / Invalid:**
    * `ADMIN_CANCELLED` / `admin_cancelled`: Cancelled by clinic staff (usually ignored in funnel metrics).
    * `REJECTED`: Appointment could not be fulfilled.
    * `UNASSIGNED`: Visit was booked but no staff/service was assigned.
* **Example cURL:**
  ```bash
  curl -X GET "https://www.harito.life/api/v1/attendance/visits?startDate=2026-07-01&endDate=2026-07-31&page=1&pageSize=50" \
       -H "Authorization: Bearer <YOUR_TOKEN>" \
       -H "Content-Type: application/json"
  ```

## 2. Orders API
* **Endpoint:** `GET /order/orderItems`
* **Purpose:** Retrieves order items (services/packages purchased by users). Used for revenue tracking and reconciliation.
* **Pagination:** `page` and `limit`.
* **Key Query Parameters:**
  * `startDate`, `endDate`
  * `search` (text-based searching)
  * `status` (filter by specific order status)
  * `category` (filter by service category)
  * `paymentMethod`
* **Order Statuses:**
  * `PLACED`: Order created successfully.
  * `ONLINE_PAYMENT_PENDING`: Awaiting payment gateway confirmation.
  * `ACTIVE`: Service/subscription is currently active.
  * `COMPLETED`: Order fully fulfilled.
  * `CANCELLED`: Order was cancelled.
* **Example cURL:**
  ```bash
  curl -X GET "https://www.harito.life/api/v1/order/orderItems?startDate=2026-07-01&endDate=2026-07-31&page=1&limit=50&status=PLACED" \
       -H "Authorization: Bearer <YOUR_TOKEN>" \
       -H "Content-Type: application/json"
  ```

## 3. Services API
* **Endpoint:** `GET /service`
* **Purpose:** Retrieves a catalog of available services and treatments.
* **Pagination:** `page` and `pageSize`.
* **Key Query Parameters:**
  * `locationId` (e.g., `cm7rufzkp0006p5bzykaczk2v`) - Filters services available at a specific clinic branch.
* **Example cURL:**
  ```bash
  curl -X GET "https://www.harito.life/api/v1/service?locationId=<LOCATION_ID>&page=1&pageSize=100" \
       -H "Authorization: Bearer <YOUR_TOKEN>" \
       -H "Content-Type: application/json"
  ```

## 4. Service Categories API
* **Endpoint:** `GET /serviceCategory`
* **Purpose:** Fetches broader categories that group individual services (e.g., Physiotherapy, Chiropractic).
* **Pagination:** Assumed to support standard `page`/`pageSize` but often fetched in one go if the list is small.
* **Example cURL:**
  ```bash
  curl -X GET "https://www.harito.life/api/v1/serviceCategory" \
       -H "Authorization: Bearer <YOUR_TOKEN>" \
       -H "Content-Type: application/json"
  ```

## 5. Cart & Assisted Booking Deeplinks (Not Payment Links)
* **Concept:** Assisted cart creation allows Central Ops staff to pre-configure a service package, schedule, and offers for a customer, generating a pre-filled cart link (`https://www.harito.life/c/{cartId}`).
* **Purpose:** Staff fills the cart on behalf of the customer and sends the link to them (via WhatsApp or SMS) so the customer can open it, review their cart, and complete the self-booking and payment themselves.
* **Important Distinction:** This is **NOT** a direct payment link or gateway invoice; it is an **assisted cart link** that lets the customer complete self-checkout.
* **Endpoints:**
  * `POST /admin/cart` - Initializes an assisted cart session.
  * `PUT /admin/cart/{cartId}/items` - Adds pre-configured service packages, schedules, and applied offers to the cart.
  * `POST /admin/deeplinks` - Generates the customer-facing cart deeplink (`{ screen: "cart", payload: { cartId: ... }, phoneNo: ... }`).
* **Audit Trail:** Logged in `GET /centralOps/audit-logs` with `rawEndpoint == "/v1/admin/deeplinks"`.

