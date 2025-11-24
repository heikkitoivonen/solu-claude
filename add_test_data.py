# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Heikki Toivonen

from app import create_app, db
from app.models import Floorplan, Resource

app = create_app()

with app.app_context():
    # Check if we already have data
    existing_floorplan = Floorplan.query.first()
    if existing_floorplan:
        print("Test data already exists. Skipping...")
        print(f"Floorplans: {Floorplan.query.count()}")
        print(f"Resources: {Resource.query.count()}")
    else:
        # Create a sample floorplan
        floorplan = Floorplan(
            name="First Floor",
            image_filename="sample_floorplan.png"
        )
        db.session.add(floorplan)
        db.session.commit()

        # Create sample resources
        resources = [
            Resource(name="Conference Room A", type="room", x_coordinate=150, y_coordinate=100, floorplan_id=floorplan.id),
            Resource(name="Conference Room B", type="room", x_coordinate=350, y_coordinate=100, floorplan_id=floorplan.id),
            Resource(name="Printer 1", type="printer", x_coordinate=200, y_coordinate=250, floorplan_id=floorplan.id),
            Resource(name="Printer 2", type="printer", x_coordinate=400, y_coordinate=250, floorplan_id=floorplan.id),
            Resource(name="John Doe", type="person", x_coordinate=100, y_coordinate=350, floorplan_id=floorplan.id),
            Resource(name="Jane Smith", type="person", x_coordinate=300, y_coordinate=350, floorplan_id=floorplan.id),
            Resource(name="Kitchen", type="room", x_coordinate=500, y_coordinate=150, floorplan_id=floorplan.id),
            Resource(name="Break Room", type="room", x_coordinate=450, y_coordinate=350, floorplan_id=floorplan.id),
        ]

        for resource in resources:
            db.session.add(resource)

        db.session.commit()

        print(f"Test data added successfully!")
        print(f"Created 1 floorplan and {len(resources)} resources")
