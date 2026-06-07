from flask import render_template, request, jsonify, redirect, url_for
from app.models.user import UserService, Validator
from app.models.database import DatabaseManager


class AuthController:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.user_service = UserService(self.db_manager)

    def home_page(self):
        return render_template('home.html')

    def signup_page(self):
        return render_template('index.html')

    def login_page(self):
        return render_template('login.html')

    def health(self):
        healthy, detail = self.db_manager.is_healthy()
        if healthy:
            return jsonify({'status': 'ok', 'database': detail})
        return jsonify({'status': 'error', 'database': detail}), 500
    
    def dashboard(self):
        users = self.user_service.get_all_users()
        return render_template('dashboard.html', users=users)

    def check_username(self):
        username = request.args.get('username', '').strip()
        if not username:
            return jsonify({'available': False, 'message': 'Username required'})

        error = Validator.validate_username(username)
        if error:
            return jsonify({'available': False, 'message': error})

        try:
            available, message = self.user_service.is_username_available(username)
            return jsonify({'available': available, 'message': message})
        except Exception:
            return jsonify({'available': False, 'message': 'Server error, try again'}), 500

    def register(self):
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'success': False, 'message': 'Invalid JSON'}), 400

        email = data.get('email', '').strip().lower()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        confirm_password = data.get('confirm_password', '')
        agreed = data.get('agreed', False)

        errors = Validator.validate_registration(email, username, password, confirm_password, agreed)
        if errors:
            return jsonify({'success': False, 'errors': errors}), 400

        try:
            success, result, status = self.user_service.register(email, username, password)
            result['success'] = success
            return jsonify(result), status
        except Exception as e:
            return jsonify({'success': False, 'message': f'Database error: {e}'}), 500

    def login(self):
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'success': False, 'message': 'Invalid JSON'}), 400

        identifier = data.get('identifier', '').strip()
        password = data.get('password', '')

        errors = Validator.validate_login(identifier, password)
        if errors:
            return jsonify({'success': False, 'errors': errors}), 400

        try:
            success, result, status = self.user_service.authenticate(identifier, password)
            result['success'] = success
            return jsonify(result), status
        except Exception as e:
            return jsonify({'success': False, 'message': f'Database error: {e}'}), 500

    def editUsers(self, id):
        if request.method == "POST":
            data = request.get_json(silent=True) or request.form
            name = data.get("name", "").strip()
            email = data.get("email", "").strip().lower()
            password = data.get("password", "")
            
            # Update user logic would go here
            # For now, placeholder implementation
            return jsonify({'success': True, 'message': 'User updated'}), 200

        # For GET, return user edit page
        return render_template("editUser.html", user_id=id)
    
    def deleteUsers(self, id):
        if request.method == "POST":
            self.user_model.delete_by_id(id)

        return redirect(url_for("auth.dashboard"))