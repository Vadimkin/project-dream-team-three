from flask import flash, redirect, render_template, url_for, request, session, current_app
from flask_login import login_required, login_user, logout_user, current_user

from app.auth.oauth.facebook import facebook
from app.exceptions import EmployeeFacebookEmailAlreaadyExistsException, EmployeeFacebookNotVerifiedProfileException, \
    EmployeeFacebookEmailNotProvidedException
from forms import RegistrationForm, LoginForm, FacebookUsernameForm
from . import auth
from .. import db
from ..models import Employee


@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home.dashboard'))

    form = RegistrationForm()
    if form.validate_on_submit():
        employee = Employee(email=form.email.data,
                            username=form.username.data,
                            first_name=form.first_name.data,
                            last_name=form.last_name.data,
                            password=form.password.data)

        # add employee to the database
        db.session.add(employee)
        db.session.commit()
        flash('You have successfully registered! You may now login.')

        # redirect to the login page
        return redirect(url_for('auth.login'))

    # load registration template
    return render_template('auth/register.html', form=form, title='Register')


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home.dashboard'))

    form = LoginForm()
    if form.validate_on_submit():

        # check whether employee exists in the database and whether
        # the password entered matches the password in the database
        employee = Employee.query.filter_by(email=form.email.data).first()
        if employee is not None and employee.verify_password(
                form.password.data):
            # log employee in
            login_user(employee)

            # redirect to the appropriate dashboard page
            if employee.is_admin:
                return redirect(url_for('home.admin_dashboard'))
            else:
                return redirect(url_for('home.dashboard'))

        # when login details are incorrect
        else:
            flash('Invalid email or password.')

    # load login template
    return render_template('auth/login.html', form=form, title='Login')


@auth.route('/login/facebook')
def login_facebook():
    return facebook.authorize(callback=url_for('auth.oauth_authorized',
                                               next=request.args.get('next') or request.referrer or None,
                                               _external=True))


@auth.route('/login/facebook/username', methods=['GET', 'POST'])
@login_required
def facebook_username_choice():
    if current_user.username:
        return redirect(url_for('home.dashboard'))

    form = FacebookUsernameForm()
    if not form.username.data:
        form.username.data = current_user.generate_username()

    if form.validate_on_submit():
        current_user.username = form.username.data
        db.session.add(current_user)
        db.session.commit()

        return redirect(url_for('home.dashboard'))

    # load login template
    return render_template('auth/username_choice.html', form=form, title='Select your username')


@auth.route('/oauth-authorized')
@facebook.authorized_handler
def oauth_authorized(resp):
    next_url = request.args.get('next') or url_for('index')
    if resp is None:
        flash(u'You denied the request to sign in.')
        return redirect(next_url)

    session['logged_in'] = True
    session['facebook_token'] = (resp['access_token'], '')

    facebook_data = facebook.get('/me?fields={}'.format(current_app.config.get('FACEBOOK_SCOPE'))).data

    # Profile is valid and verified, now we need create user if it not exists
    employee = Employee.query.filter_by(network_type=Employee.NETWORK_TYPE_FACEBOOK,
                                        network_id=facebook_data.get('id')).first()
    if employee:
        login_user(employee)
        return redirect(next_url)

    try:
        employee = Employee.create_facebook_user(facebook_data)
    except (
            EmployeeFacebookNotVerifiedProfileException,
            EmployeeFacebookEmailAlreaadyExistsException,
            EmployeeFacebookEmailNotProvidedException
    ) as e:
        flash(str(e))
        return redirect(next_url)

    login_user(employee)

    if not employee.username:
        return redirect(url_for('auth.facebook_username_choice'))

    return redirect(next_url)


@facebook.tokengetter
def get_facebook_oauth_token():
    return session.get('facebook_token')


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have successfully been logged out.')

    # redirect to the login page
    return redirect(url_for('home.homepage'))
