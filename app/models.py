from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db, login_manager
from app.exceptions import EmployeeFacebookEmailAlreaadyExistsException, EmployeeFacebookNotVerifiedProfileException, \
    EmployeeUsernameAlreadyExistsException, EmployeeFacebookEmailNotProvidedException


class Employee(UserMixin, db.Model):
    """
    Create an Employee table
    """

    # Ensures table will be named in plural and not in singular
    # as is the name of the model
    __tablename__ = 'employees'

    NETWORK_TYPE_NATIVE = 'Native'
    NETWORK_TYPE_FACEBOOK = 'Facebook'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(60), index=True, unique=True)
    username = db.Column(db.String(60), index=True, unique=True)
    first_name = db.Column(db.String(60), index=True)
    last_name = db.Column(db.String(60), index=True)
    password_hash = db.Column(db.String(128))
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    is_admin = db.Column(db.Boolean, default=False)

    network_id = db.Column(db.String(60), index=True)
    network_type = db.Column(db.String(60), default=NETWORK_TYPE_NATIVE, index=True)

    @staticmethod
    def create_facebook_user(facebook_data):
        if not facebook_data.get('verified'):
            raise EmployeeFacebookNotVerifiedProfileException("Your profile is not verified")

        # Check email
        email = facebook_data.get('email')
        if not email:
            raise EmployeeFacebookEmailNotProvidedException("You not provided email")

        if email and not Employee.is_valid_email(email):
            raise EmployeeFacebookEmailAlreaadyExistsException("User with this email already exists")

        employee = Employee()
        employee.email = facebook_data.get('email', '')
        employee.first_name = facebook_data.get('first_name', '')
        employee.last_name = facebook_data.get('last_name', '')
        employee.network_id = facebook_data.get('id')
        employee.network_type = Employee.NETWORK_TYPE_FACEBOOK
        db.session.add(employee)
        db.session.commit()
        return employee

    @staticmethod
    def is_valid_email(email):
        employee = Employee.query.filter_by(email=email).first()
        return not bool(employee)

    @property
    def password(self):
        """
        Prevent password from being accessed
        """
        raise AttributeError('password is not a readable attribute.')

    @password.setter
    def password(self, password):
        """
        Set password to a hashed password
        """
        self.password_hash = generate_password_hash(password)

    def generate_username(self):
        username = "{}_{}".format(
            self.first_name.lower(),
            self.last_name.lower()
        )

        username_id = 0

        while True:
            full_username = "{}{}".format(username, username_id)

            if username_id == 0:
                # For first iteration we can try to check available username without ID
                full_username = username

            try:
                Employee.validate_username(full_username)
            except EmployeeUsernameAlreadyExistsException:
                username_id += 1
            else:
                return full_username

    def verify_password(self, password):
        """
        Check if hashed password matches actual password
        """
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def validate_username(username):
        if Employee.query.filter_by(username=username).first():
            raise EmployeeUsernameAlreadyExistsException('Username is already in use.')
        return True

    def __repr__(self):
        return '<Employee: {}>'.format(self.username)


# Set up user_loader
@login_manager.user_loader
def load_user(user_id):
    return Employee.query.get(int(user_id))


class Department(db.Model):
    """
    Create a Department table
    """

    __tablename__ = 'departments'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), unique=True)
    description = db.Column(db.String(200))
    employees = db.relationship('Employee', backref='department',
                                lazy='dynamic')

    def __repr__(self):
        return '<Department: {}>'.format(self.name)


class Role(db.Model):
    """
    Create a Role table
    """

    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), unique=True)
    description = db.Column(db.String(200))
    employees = db.relationship('Employee', backref='role',
                                lazy='dynamic')

    def __repr__(self):
        return '<Role: {}>'.format(self.name)
