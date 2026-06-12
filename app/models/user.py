from flask import render_template, request, redirect, url_for, flash, session

from app.models.user import User

from app import db
 
def login():

    if request.method == 'POST':

        # Get data from the login form

        identifier = request.form.get('identifier')  # Handles either email or username

        password = request.form.get('password')
 
        # Find user by username OR email based on your user.py columns

        user = User.query.filter((User.username == identifier) | (User.email == identifier)).first()
 
        if user and user.check_password(password):

            # Log the user in by setting the session

            session['user_id'] = user.id

            session['username'] = user.username

            flash('Welcome back! Your next move awaits.', 'success')

            return redirect('/')  # Redirect to your dashboard/main chess game page

        else:

            flash('Invalid username/email or password.', 'error')

            return redirect(url_for('auth.login_page'))
 
    # If it's a GET request, just render the login page

    return render_template('login.html')
 