from datetime import datetime, timedelta
from controller.tracker_controller import HardwareAuthController
from controller.hardware_controller import HardwareController
from models.database import init_hardware_db


def main():
    db_name = "hardware_inventory.db"
    init_hardware_db(db_name=db_name)

    auth = HardwareAuthController()
    hc = HardwareController()

    # Create admin and user accounts (ignore errors if they exist)
    print("Registering admin...")
    success, msg = auth.register("admin", "Admin123!", email="admin@example.com", role="ADMIN")
    print("admin register:", success, msg)

    print("Registering student user...")
    success, msg = auth.register("student1", "Student123!", email="stud@example.com", role="USER")
    print("student register:", success, msg)

    # Add an item
    print("Adding hardware item...")
    success, msg = hc.add_item("Arduino Uno", "Electronics", 10, 150.0)
    print("add item:", success, msg)

    # Fetch items to get item_id
    items = hc.fetch_all_items()
    print("Items:", items)
    if not items:
        print("No items available, aborting test.")
        return
    item_id = items[0][0]

    # Student requests borrow of 3 units (pending)
    print("Student submits borrow request...")
    pay_by = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    success, msg = hc.borrow_item("Student One", "S001", item_id, 3, pay_by)
    print("borrow request:", success, msg)

    # Admin reviews pending borrows
    auth_ctrl = auth
    borrows = auth_ctrl.get_borrow_requests()
    print("Pending borrows:", borrows)
    if borrows:
        borrow_id = borrows[0][0]
        print("Approving borrow id", borrow_id)
        ok, m = auth_ctrl.approve_borrow_request(borrow_id, "admin")
        print("approve result:", ok, m)

    # Check stock decreased
    items_after = hc.fetch_all_items()
    print("Items after approval:", items_after)

    # Request return for the borrow
    print("Requesting return for borrow...")
    success, msg = hc.request_return(borrow_id, 3)
    print("request return:", success, msg)

    # Admin approves return
    returns = hc.get_return_requests()
    print("Return requests:", returns)
    if returns:
        return_id = returns[0][0]
        ok, m = hc.review_return_request(return_id, "admin", True)
        print("approve return:", ok, m)

    # Final stock
    final_items = hc.fetch_all_items()
    print("Final items:", final_items)


if __name__ == "__main__":
    main()
