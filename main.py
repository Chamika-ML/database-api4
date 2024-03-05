from flask import Flask, jsonify, request, json
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow 
from sqlalchemy import PrimaryKeyConstraint, text, desc, asc, cast, Integer, or_
from flask import request
from math import ceil

app = Flask(__name__)
db = SQLAlchemy()
ma = Marshmallow()

# Farm details class
class Farm(db.Model):
    __tablename__ = 'farm_details'
    business_id = db.Column(db.String(255), autoincrement=False, nullable=False)
    farm_id = db.Column(db.String(255), primary_key=True, autoincrement=False)
    boundaries = db.Column(db.Text, nullable=False)


    def __init__(self, business_id, farm_id, boundaries):
        self.business_id = business_id
        self.farm_id = farm_id
        self.boundaries = boundaries

class FarmSchema(ma.Schema):
    class Meta:
        fields = ('business_id', 'farm_id', 'boundaries')

Farm_schema = FarmSchema()
Farms_schema = FarmSchema(many=True)

# Hive details class
# Global dictionary to store dynamically created Hive classes
dynamic_hive_classes = {}

# Hive details class
def create_hive_class(business_id, farm_id):
    table_name = f"hive_details_{business_id}_{farm_id}"
    
    # Check if the Hive class for this table already exists
    if table_name in dynamic_hive_classes:
        Hive = dynamic_hive_classes[table_name]
    else:
        class Hive(db.Model): 
            __tablename__ = table_name
            
            area_code = db.Column(db.String(255), nullable=False)
            location_code = db.Column(db.String(255), nullable=False)
            longitude = db.Column(db.Float, nullable=False)
            latitude = db.Column(db.Float, nullable=False)
            total_beehives = db.Column(db.Integer, nullable=False)
            total_active_frames = db.Column(db.Integer, nullable=True)
            img_urls = db.Column(db.Text, nullable=True)


            __table_args__ = (
                PrimaryKeyConstraint('area_code', 'location_code'),
            )

            def __init__(self, area_code, location_code, longitude, latitude, total_beehives, total_active_frames, img_urls):
                self.area_code = area_code
                self.location_code = location_code
                self.longitude = longitude
                self.latitude = latitude
                self.total_beehives = total_beehives
                self.total_active_frames = total_active_frames
                self.img_urls = img_urls

        # Save the class in the global dictionary
        dynamic_hive_classes[table_name] = Hive

    return Hive


class HiveSchema(ma.Schema):
    class Meta:
        fields = ('area_code','location_code','longitude','latitude','total_beehives','img_urls')

Hive_schema = HiveSchema()
Hives_schema  = HiveSchema(many=True)


# MySQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://dilshan:1234@localhost/broodbox'
db.init_app(app)

# Farm details table related  apis

@app.route('/farm/add', methods=['POST'])
def add_Farm():
    try:
        _json = request.json
        business_id = _json['business_id']
        farm_id = _json['farm_id']
        boundaries = _json['boundaries']

        new_Farm = Farm(business_id=business_id, farm_id=farm_id, boundaries=boundaries)
        db.session.add(new_Farm)
        db.session.commit()

        # Check if the corresponding hive_details table already exists
        hive_table_name = f"hive_details_{business_id}_{farm_id}"
        if hive_table_name not in db.metadata.tables:
            # If the table doesn't exist, create it
            Hive = create_hive_class(business_id, farm_id)
            db.create_all()
        
        return jsonify({"message": "the Farm has been added "})

    except Exception as e:
        return jsonify({"error": str(e)})


@app.route('/farm', methods=['GET'])
def get_Farm():
    try:
        Farms = []
        data = Farm.query.all()
        Farms = Farms_schema.dump(data)
        return jsonify(Farms)

    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/farm/<farm_id>', methods=['GET'])
def Farm_byid(farm_id):
    try:
        farm_record = Farm.query.get(farm_id)
        data = Farm_schema.dump(farm_record)
        return jsonify(data)

    except Exception as e:
        return jsonify({"error": str(e)})


@app.route('/farm/delete/<farm_id>', methods=['POST'])
def delete_Farm(farm_id):
    farm_record = Farm.query.get(farm_id)
    if farm_record is None:
        return jsonify(f"Error: the Farm doesn't exist")
    
    # Delete the farm record
    db.session.delete(farm_record)
    db.session.commit()

    # Determine the name of the corresponding hive details table
    hive_table_name = f"hive_details_{farm_record.business_id}_{farm_id}"

    # Drop the corresponding hive details table
    try:
        db.session.execute(text(f"DROP TABLE IF EXISTS {hive_table_name}"))
        db.session.commit()
        return jsonify({"message": "the Farm has been deleted, along with its corresponding hive details table"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)})


@app.route('/farm/edit/<farm_id>', methods=['POST'])
def edit_Farm(farm_id):
    try:
        farm_record = Farm.query.get(farm_id)
        if farm_record is None:
            return jsonify({"error": "the farm doesn't exist"})
        _json = request.json
        farm_record.boundaries = _json['boundaries']
        db.session.commit()
        return jsonify({"message": "the Farm has been edited"})
        
    except Exception as e:
        return jsonify({"error": str(e)})


# hive details table related apis

@app.route('/hive/<business_id>/<farm_id>', methods=['GET'])
def get_hive_details(business_id, farm_id):
    # Use the dynamically created Hive class based on farm_id
    Hive = create_hive_class(business_id, farm_id)
    try:
        # Extracting query parameters
        limit = int(request.args.get('limit', 1000))  # Default limit is 1000 if not provided
        page = int(request.args.get('page', 1))  # Default page is 1 if not provided
        sort_by = request.args.get('sortBy', 'area_code:asc')  # Default sorting by area_code in acending order if not provided
        search_term = request.args.get('search', '')  # Default empty search term if not provided
        
        # Split sort_by parameter into field and order
        sort_field, sort_order = sort_by.split(':')

        # Calculate offset for pagination
        offset = (page - 1) * limit

        # Retrieve records with optional sorting, search, and pagination
        if search_term:
            hive_records = Hive.query.filter(
                or_(
                    Hive.area_code.like(f'%{search_term}%'),
                    Hive.location_code.like(f'%{search_term}%')
                )
            ).order_by(
                cast(getattr(Hive, sort_field), Integer).desc() if sort_order == 'desc' else cast(getattr(Hive, sort_field), Integer).asc()
            ).offset(offset).limit(limit).all()
  
        else:
            hive_records = Hive.query.order_by(
                cast(getattr(Hive, sort_field), Integer).desc() if sort_order == 'desc' else cast(getattr(Hive, sort_field), Integer).asc()
            ).offset(offset).limit(limit).all()
    


        # Serialize the records using the HiveSchema
        hive_details = Hives_schema.dump(hive_records)
        
        # Count total number of records
        total_records = Hive.query.count()
        
        # Calculate total pages
        total_pages = ceil(total_records / limit)

        # Return paginated results along with pagination metadata
        return jsonify({
            "hive_details": hive_details,
            "pagination": {
                "page": page,
                "limit": limit,
                "total_pages": total_pages,
                "total_records": total_records
            }
        })
    
    except:
        return jsonify({"error": "the farm doesn't exist"})



@app.route('/hive/get/<business_id>/<farm_id>/<area_code>/<location_code>', methods=['GET'])
def get_single_hive(business_id, farm_id, area_code, location_code):
    try:
        Hive = create_hive_class(business_id, farm_id)
        hive = Hive.query.filter_by(area_code=area_code, location_code=location_code).first()

        if hive is None:
            return jsonify({"error": "Hive not found"})

        hive_data = Hive_schema.dump(hive)
        return jsonify(hive_data)
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route('/hive/area-location-codes/<business_id>/<farm_id>', methods=['GET'])
def get_location_codes(business_id, farm_id):
    # Use the dynamically created Hive class based on farm_id
    Hive = create_hive_class(business_id, farm_id)
    
    try:
        # Retrieve all area_code values from the corresponding hive_details_xx table
        area_codes = Hive.query.with_entities(Hive.area_code).distinct().all()

        # Retrieve all location_code values from the corresponding hive_details_xx table
        location_codes = Hive.query.with_entities(Hive.location_code).distinct().all()

        # Convert the result to a list of area_code values
        area_codes_list = [area_code[0] for area_code in area_codes]

        # Convert the result to a list of location_code values
        location_codes_list = [location_code[0] for location_code in location_codes]

        return jsonify({"area_codes": area_codes_list, "location_codes": location_codes_list})
    
    except:
        return jsonify({"error": "the farm doesn't exist"})



@app.route('/hive/add/<business_id>/<farm_id>', methods=['POST'])
def add_hive(business_id, farm_id):
    try:
        Hive = create_hive_class(business_id, farm_id)
        _json = request.json.get('data', [])  # Get the list of hive data from the JSON, default to empty list if not provided

        # Add hive details to the dynamically created hive table
        for hive_item in _json:
            new_hive = Hive(
                area_code=hive_item['area_code'],
                location_code=hive_item['location_code'],
                longitude=hive_item['longitude'],
                latitude=hive_item['latitude'],
                total_beehives=hive_item['total_beehives'],
                total_active_frames=None,  # Set to None for nullable column
                img_urls=None # Set to None for nullable column
            )

            db.session.add(new_hive)

        db.session.commit()

        return jsonify({"message": "Hive(s) added successfully"})
    except Exception as e:
        return jsonify({"error": str(e)})



@app.route('/hive/update/<business_id>/<farm_id>/<area_code>/<location_code>', methods=['POST'])
def update_hive(business_id, farm_id, area_code, location_code):
    try:
        Hive = create_hive_class(business_id, farm_id)
        hive = Hive.query.filter_by(area_code=area_code, location_code=location_code).first()

        if hive is None:
            return jsonify({"error": "Hive not found"})

        _json = request.json
        hive.area_code = _json['area_code']
        hive.location_code = _json['location_code']
        hive.longitude = _json['longitude']
        hive.latitude = _json['latitude']
        hive.total_beehives = _json['total_beehives']
        hive.img_urls = _json['img_urls']
        db.session.commit()

        return jsonify({"message": "Hive updated successfully"})
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route('/hive/delete/<business_id>/<farm_id>/<area_code>/<location_code>', methods=['POST'])
def delete_hive(business_id, farm_id, area_code, location_code):
    try:
        Hive = create_hive_class(business_id, farm_id)
        hive = Hive.query.filter_by(area_code=area_code, location_code=location_code).first()

        if hive is None:
            return jsonify({"error": "Hive not found"})

        db.session.delete(hive)
        db.session.commit()

        return jsonify({"message": "Hive deleted successfully"})
    except Exception as e:
        return jsonify({"error": str(e)})


if __name__ == "__main__":
    app.run(debug=True)
