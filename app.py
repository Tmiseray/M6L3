from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_cors import CORS
from marshmallow import fields, validate
from marshmallow import ValidationError
from password import my_password

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+mysqlconnector://root:{my_password}@localhost/e_commerce_db'
CORS(app)
db = SQLAlchemy(app)
ma = Marshmallow(app)

class CustomerSchema(ma.Schema):
    name = fields.String(required=True)
    email = fields.String(required=True)
    phone = fields.String(required=True)

    class Meta:
        fields = ('name', 'email', 'phone', 'id')

customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many=True)


class ProductSchema(ma.Schema):
    name = fields.String(required=True, validate=validate.Length(min=1))
    price = fields.Float(required=True, validate=validate.Range(min=0))

    class Meta:
        fields = ('name', 'price', 'id')

product_schema = ProductSchema()
products_schema = ProductSchema(many=True)

class Customer(db.Model):
    __tablename__ = 'Customers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(320))
    phone = db.Column(db.String(15))
    orders = db.relationship('Order', backref='customer')
                # ^ Establishing our relationship

class Order(db.Model):
    __tablename__ = 'Orders'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('Customers.id'))

# One-to-One Relationship
class CustomerAccount(db.Model):
    __tablename__ = 'Customer_Accounts'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('Customers.id'))
    customer = db.relationship('Customer', backref='customer_account', uselist=False)

# Many-to-Many Relationship Association Table
order_product = db.Table('Order_Product',
        db.Column('order_id', db.Integer, db.ForeignKey('Orders.id'), primary_key=True),
        db.Column('product_id', db.Integer, db.ForeignKey('Products.id'), primary_key=True)
        )

# Many-to-Many Relationship
class Product(db.Model):
    __tablename__ = 'Products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Float, nullable=False)
    orders = db.relationship('Order', secondary=order_product, backref=db.backref('products'))


### Customer Endpoints & Methods ###

@app.route('/customers', methods=['GET'])
def get_customers():
    customers = Customer.query.all()
    return customers_schema.jsonify(customers)

@app.route('/customers', methods=['POST'])
def add_customer():
    try:
        # Validate & deserialize input
        customer_data = customer_schema.load(request.json)
    except ValidationError as ve:
        return jsonify(ve.messages), 400
    
    new_customer = Customer(name = customer_data['name'], 
                            email = customer_data['email'], 
                            phone = customer_data['phone']
                            )
    db.session.add(new_customer)
    db.session.commit()
    return jsonify({"message": "New customer added successfully"}), 201

@app.route('/customers/<int:id>', methods=['GET'])
def get_customer_by_id(id):
    customer = Customer.query.get_or_404(id)
    return customer_schema.jsonify(customer)

@app.route('/customers/<int:id>', methods=['PUT'])
def update_customer(id):
    customer = Customer.query.get_or_404(id)
    try:
        customer_data = customer_schema.load(request.json)
    except ValidationError as ve:
        return jsonify(ve.messages), 400
    
    customer.name = customer_data['name']
    customer.email = customer_data['email']
    customer.phone = customer_data['phone']
    db.session.commit()
    return jsonify({"message": "Customer details updated successfully"}), 200

@app.route('/customers/<int:id>', methods=['DELETE'])
def delete_customer(id):
    customer = Customer.query.get_or_404(id)
    db.session.delete(customer)
    db.session.commit()
    return jsonify({"message": "Customer removed successfully"}), 200


### Products Endpoints & Methods ###

@app.route('/products', methods=['POST'])
def add_product():
    try:
        # Validate & deserialize input
        product_data = product_schema.load(request.json)
    except ValidationError as ve:
        return jsonify(ve.messages), 400
    new_product = Product(name = product_data['name'], price = product_data['price'])
    db.session.add(new_product)
    db.session.commit()
    return jsonify({"message": "Product added successfully"}), 201

@app.route('/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    return products_schema.jsonify(products)

@app.route('/products/<int:id>', methods=['PUT'])
def update_product(id):
    product = Product.query.get_or_404(id)
    try:
        # Validate & deserialize input
        product_data = product_schema.load(request.json)
    except ValidationError as ve:
        return jsonify(ve.messages), 400
    
    product.name = product_data['name']
    product.price = product_data['price']
    db.session.commit()
    return jsonify({"message": "Product updated successfully"}), 200

@app.route('/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    return jsonify({"message": "Product deleted successfully"}), 200


### Queries ###

@app.route('/customers/by-email', methods=['GET'])
def query_customer_by_email():
    email = request.args.get('email')
    customer = Customer.query.filter_by(email = email).first()
    if customer:
        return customer_schema.jsonify(customer)
    else:
        return jsonify({"message": "Customer not found"}), 404

@app.route('/products/by-name', methods=['GET'])
def query_product_by_name():
    name = request.args.get('name')
    product = Product.query.filter(Product.name == name).first()
    if product:
        return product_schema.jsonify(product)
    else:
        return jsonify({"message": "Customer not found"}), 404


# Initialize the database and create tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)