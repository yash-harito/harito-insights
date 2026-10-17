import os
import time
import json
import logging
from typing import Dict, List, Any, Optional
import requests
from dotenv import load_dotenv

# Setup basic logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("harito_client")

# Known test accounts to exclude from analytical aggregations
TEST_ACCOUNTS = {
    "2109999999", "8770011426", "2209999999", "99995031960", "9999503196",
    "9363129501", "9886761275", "7000125334", "7470546275", "9620921909", "8864904164",
    "9999999999", "0000000000", "1234567890", "1111111111"
}

VALID_ORDER_STATUSES = {"PLACED", "ACTIVE", "COMPLETED", "ONLINE_PAYMENT_PENDING"}
INVALID_ORDER_STATUSES = {"CANCELLED", "REJECTED"}
INVALID_ITEM_STATUSES = {"REJECTED", "USER_CANCELLED"}

SUCCESSFUL_VISIT_STATUSES = {"CHECKED_OUT", "ATTENDED", "MID_VISIT_CHECKOUT"}
DROPPED_VISIT_STATUSES = {"ADMIN_CANCELLED", "admin_cancelled", "REJECTED", "UNASSIGNED"}


class HaritoClient:
    """Client for interacting with Harito Internal APIs."""

    def __init__(self, base_url: str = "https://www.harito.life/api/v1"):
        load_dotenv(override=True)
        self.base_url = base_url.rstrip("/")
        self.token = os.getenv("TOKEN")
        if not self.token:
            raise ValueError("TOKEN not found in .env file. Please add your Bearer token to .env.")

        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json"
        }
        self.delay_seconds = 0.25

    def _request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Executes a GET request with throttling, retries on 429, and 401 error handling."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        max_attempts = 5

        for attempt in range(max_attempts):
            try:
                response = requests.get(url, headers=self.headers, params=params, timeout=30)
            except requests.exceptions.RequestException as e:
                wait_time = (attempt + 1) * 2
                logger.warning(f"Network error ({e}). Retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue

            if response.status_code == 429:
                wait_time = (attempt + 1) * 2
                logger.warning(f"Rate limited (429). Backing off for {wait_time}s...")
                time.sleep(wait_time)
                continue

            if response.status_code == 401:
                raise PermissionError("401 Unauthorized: Session TOKEN in .env is invalid or expired. Please update .env with a fresh token.")

            if response.status_code != 200:
                raise RuntimeError(f"API Error {response.status_code}: {response.text}")

            # Respect server rate limit
            time.sleep(self.delay_seconds)
            return response.json()

        raise RuntimeError(f"Failed to fetch {url} after {max_attempts} attempts.")

    @staticmethod
    def is_test_user(phone: Optional[str] = None, name: Optional[str] = None) -> bool:
        """Determines if a user or order belongs to a test account."""
        if phone and phone in TEST_ACCOUNTS:
            return True
        if name and ("test" in name.lower() or "dummy" in name.lower()):
            return True
        return False

    @staticmethod
    def is_valid_order_item(item: Dict[str, Any]) -> bool:
        """Determines if an order item is valid (non-cancelled, non-rejected)."""
        order_status = item.get("order", {}).get("status")
        item_status = item.get("status")
        if order_status in INVALID_ORDER_STATUSES:
            return False
        if item_status in INVALID_ITEM_STATUSES:
            return False
        return True

    @staticmethod
    def get_order_attribution(order: Dict[str, Any]) -> str:
        """Identifies who booked the order (CRM, SUPER_ADMIN, DISPATCHER, CUSTOMER)."""
        meta = order.get("meta") or {}
        if "crm" in meta:
            return "CRM"
        created_by = meta.get("createdBy") or {}
        role = created_by.get("role")
        if role == "SUPER_ADMIN":
            return "SUPER_ADMIN"
        elif role == "DISPATCHER":
            return "DISPATCHER"
        elif role in ["CARE_SEEKER", "CUSTOMER"] or not role:
            return "CUSTOMER"
        return role

    def get_order_items(
        self,
        start_date: str,
        end_date: str,
        valid_only: bool = True,
        exclude_test_accounts: bool = True,
        status: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Fetches order items between start_date and end_date with automatic pagination and filtering."""
        page = 1
        all_items: List[Dict[str, Any]] = []

        logger.info(f"Fetching order items: {start_date} -> {end_date}")
        while True:
            params = {
                "startDate": start_date,
                "endDate": end_date,
                "page": page,
                "limit": limit
            }
            if status:
                params["status"] = status
            if category:
                params["category"] = category

            data = self._request("order/orderItems", params=params)
            items = data.get("orderItems", [])
            if not items:
                break

            for item in items:
                order = item.get("order") or {}
                user = order.get("user") or {}
                phone = user.get("phoneNumber")
                name = user.get("name")

                if exclude_test_accounts and self.is_test_user(phone, name):
                    continue
                if valid_only and not self.is_valid_order_item(item):
                    continue

                all_items.append(item)

            pagination = data.get("pagination") or {}
            total_pages = pagination.get("totalPages", 1)
            logger.info(f"Page {page}/{total_pages} processed (accumulated {len(all_items)} records)")

            if page >= total_pages:
                break
            page += 1

        return all_items

    def get_orders(
        self,
        start_date: str,
        end_date: str,
        valid_only: bool = True,
        exclude_test_accounts: bool = True,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Fetches orders between start_date and end_date with automatic pagination."""
        page = 1
        all_orders: List[Dict[str, Any]] = []

        logger.info(f"Fetching orders: {start_date} -> {end_date}")
        while True:
            params = {
                "startDate": start_date,
                "endDate": end_date,
                "page": page,
                "limit": limit
            }
            data = self._request("order", params=params)
            orders = data.get("orders", [])
            if not orders:
                break

            for order in orders:
                user = order.get("user") or {}
                phone = user.get("phoneNumber")
                name = user.get("name")
                status = order.get("status")

                if exclude_test_accounts and self.is_test_user(phone, name):
                    continue
                if valid_only and status in INVALID_ORDER_STATUSES:
                    continue

                all_orders.append(order)

            pagination = data.get("pagination") or {}
            total_pages = pagination.get("totalPages", 1)

            if page >= total_pages:
                break
            page += 1

        return all_orders

    def get_visits(
        self,
        start_date: str,
        end_date: str,
        successful_only: bool = False,
        page_size: int = 100
    ) -> List[Dict[str, Any]]:
        """Fetches attendance visits between start_date and end_date with pagination."""
        page = 1
        all_visits: List[Dict[str, Any]] = []

        logger.info(f"Fetching visits: {start_date} -> {end_date}")
        while True:
            params = {
                "startDate": start_date,
                "endDate": end_date,
                "page": page,
                "pageSize": page_size
            }
            data = self._request("attendance/visits", params=params)
            visits = data.get("visits") or data.get("data") or []
            if not visits:
                break

            for visit in visits:
                status = visit.get("status")
                if successful_only and status not in SUCCESSFUL_VISIT_STATUSES:
                    continue
                all_visits.append(visit)

            total_pages = data.get("totalPages", 1)
            logger.info(f"Page {page}/{total_pages} processed (accumulated {len(all_visits)} records)")

            if page >= total_pages:
                break
            page += 1

        return all_visits
