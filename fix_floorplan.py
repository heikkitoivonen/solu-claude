from app import create_app, db
from app.models import Floorplan

app = create_app()

with app.app_context():
    # Update the sample floorplan filename
    floorplan = Floorplan.query.filter_by(image_filename='sample_floorplan.png').first()
    if floorplan:
        floorplan.image_filename = 'sample_floorplan.svg'
        db.session.commit()
        print(f"✓ Updated floorplan '{floorplan.name}' to use sample_floorplan.svg")
    else:
        print("✗ Floorplan not found")
