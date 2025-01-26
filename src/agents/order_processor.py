from ..events import order_events as ord_ev
from ..events import inventory_events as inv_ev
from ..models.order import Order

class OrderProcessor:
    """Handles order creation, approval, and updates."""

    def __init__(self, event_bus):
        self.event_bus = event_bus
        self.orders = {}  # order_id -> Order

        # Register event listeners
        event_bus.register_listener(ord_ev.ORDER_CREATED, self.on_order_created)

    def on_order_created(self, order_id, items):
        """When a new order is created, let's check inventory for each item."""
        new_order = Order(order_id, items)
        self.orders[order_id] = new_order
        print(f"[OrderProcessor] Received new order: {new_order}")

        # For each item in the order, remove from inventory (if in stock)
        # If any item is out of stock, we might set the order as CANCELED or PENDING
        can_fulfill = True
        for item_line in items:
            item_id = item_line["item_id"]
            quantity = item_line["quantity"]
            # Emit an event to remove from inventory
            # In a robust system, we'd first check actual stock, but let's keep it straightforward:
            self.event_bus.emit(inv_ev.ITEM_REMOVED, item_id=item_id, quantity=quantity)

        # If we haven't found a reason to fail the order, approve it
        if can_fulfill:
            new_order.status = "APPROVED"
            print(f"[OrderProcessor] Order {order_id} has been approved.")
            self.event_bus.emit(ord_ev.ORDER_APPROVED, order_id=order_id, items=items)

    def get_all_orders(self):
        return list(self.orders.values())

    def get_order(self, order_id):
        return self.orders.get(order_id)
