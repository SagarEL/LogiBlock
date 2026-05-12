from app import app, db
from models import Warehouse, Route, RouteWarehouse, User, Shipment
import random
from werkzeug.security import generate_password_hash

def seed_data():
    with app.app_context():
        # Create 10 warehouses
        warehouses_data = [
            ("Mumbai Central Hub", "WH-MUM-01", 19.0760, 72.8777),
            ("Delhi North Distribution", "WH-DEL-01", 28.7041, 77.1025),
            ("Bangalore Tech Park", "WH-BLR-01", 12.9716, 77.5946),
            ("Chennai Port Terminal", "WH-MAA-01", 13.0827, 80.2707),
            ("Kolkata East Logistics", "WH-CCU-01", 22.5726, 88.3639),
            ("Hyderabad Pharma Hub", "WH-HYD-01", 17.3850, 78.4867),
            ("Ahmedabad Industrial", "WH-AMD-01", 23.0225, 72.5714),
            ("Pune Auto Hub", "WH-PNQ-01", 18.5204, 73.8567),
            ("Jaipur Transit Center", "WH-JAI-01", 26.9124, 75.7873),
            ("Surat Textile Hub", "WH-STV-01", 21.1702, 72.8311)
        ]
        
        warehouses = []
        for name, code, lat, lng in warehouses_data:
            wh = Warehouse.query.filter_by(warehouse_code=code).first()
            if not wh:
                wh = Warehouse(warehouse_id=code, warehouse_name=name, location=name, warehouse_code=code, lat=lat, lng=lng)
                db.session.add(wh)
            warehouses.append(wh)
            
        db.session.commit()
        print("10 Warehouses seeded.")

        # Create more users
        staff = User.query.filter_by(username="warehouse2").first()
        if not staff:
            db.session.add(User(username="warehouse2", password_hash=generate_password_hash("warehouse123"), role="warehouse"))
            db.session.commit()

        # We will create routes and shipments via the browser to test the UI, or just seed routes and test shipments.
        # Let's seed 1 route to test the rest via browser.
        # Or better, just let the subagent create a route.

if __name__ == '__main__':
    seed_data()
