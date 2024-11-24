import os
import psycopg2
import bcrypt
from datetime import date

class UserManager:
    def __init__(self, db_url):
        self.conn = psycopg2.connect(db_url)
        self.cursor = self.conn.cursor()

    def hash_password(self, password):
        """Hashes a password using bcrypt."""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    def verify_password(self, password, hashed):
        """Verifies a password against a hashed password."""
        return bcrypt.checkpw(password.encode('utf-8'), hashed)

    def register_user(self, username, email, phone, name, description, avatar, birth, city, sports, events, password, root=False, admin=False):
        try:
            hashed_password = self.hash_password(password)
            self.cursor.execute("""
                INSERT INTO users (username, email, phone, name, description, avatar, birth, city, sports, events, password, root, admin)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (username, email, phone, name, description, avatar, birth, city, sports, events, hashed_password, root, admin))
            self.conn.commit()
            print("User  registered successfully.")
        except Exception as e:
            print(f"Error registering user: {str(e)}")
            self.conn.rollback()

    def edit_user(self, user_id, **kwargs):
        try:
            update_fields = []
            values = []
            
            for key, value in kwargs.items():
                if key in ['username', 'email', 'phone', 'name', 'description', 'avatar', 'birth', 'city', 'sports', 'events', 'root', 'admin']:
                    update_fields.append(f"{key} = %s")
                    values.append(value)

            values.append(user_id)
            query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = %s"
            self.cursor.execute(query, values)
            self.conn.commit()
            print("User  updated successfully.")
        except Exception as e:
            print(f"Error updating user: {str(e)}")
            self.conn.rollback()

    def delete_user(self, user_id):
        try:
            self.cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            self.conn.commit()
            print("User  deleted successfully.")
        except Exception as e:
            print(f"Error deleting user: {str(e)}")
            self.conn.rollback()

    def login_user(self, username, password):
        try:
            self.cursor.execute("SELECT password FROM users WHERE username = %s", (username,))
            user = self.cursor.fetchone()
            if user:
                hashed_password = user[0]
                if self.verify_password(password, hashed_password):
                    print("Login successful.")
                    return True  # User logged in successfully
                else:
                    print("Invalid password.")
                    return False
            else:
                print("User  not found.")
                return False
        except Exception as e:
            print(f"Error logging in user: {str(e)}")
            return False

    def get_user(self, multiple=False, **kwargs):
        """Fetches user details based on any given parameters."""
        try:
            # Construct the base query
            base_query = "SELECT username, email, phone, name, description, avatar, birth, city, sports, events, root, admin FROM users WHERE "
            conditions = []
            values = []

            # Build the conditions based on the provided keyword arguments
            for key, value in kwargs.items():
                if key in ['username', 'email', 'phone', 'name', 'description', 'avatar', 'birth', 'city', 'sports', 'events', 'root', 'admin']:
                    conditions.append(f"{key} = %s")
                    values.append(value)

            if not conditions:
                print("No search parameters provided.")
                return None

            # Combine conditions into the query
            query = base_query + " AND ".join(conditions)
            self.cursor.execute(query, values)
            users = self.cursor.fetchall()

            if multiple:
                # Return a list of users
                user_list = []
                for user in users:
                    user_data = {
                        "username": user[0],
                        "email": user[1],
                        "phone": user[2],
                        "name": user[3],
                        "description": user[4],
                        "avatar": user[5],
                        "birth": user[6],
                        "city": user[7],
                        "sports": user[8],
                        "events": user[9],
                        "root": user[10],
                        "admin": user[11]
                    }
                    user_list.append(user_data)
                return user_list
            
            elif users:
                # Return a single user
                user = users[0]
                return {
                    "username": user[0],
                    "email": user[1],
                    "phone": user[2],
                    "name": user[3],
                    "description": user[4],
                    "avatar": user[5],
                    "birth": user[6],
                    "city": user[7],
                    "sports": user[8],
                    "events": user[9],
                    "root": user[10],
                    "admin": user[11]
                }
            else:
                print("User  not found.")
                return None
        except Exception as e:
            print(f"Error fetching user: {str(e)}")
            return None

    def close(self):
        self.cursor.close()
        self.conn.close()


# Example usage
if __name__ == "__main__":
    POSTGRES_URL = os.getenv("DB_URL")
    user_manager = UserManager(POSTGRES_URL)

    # Register a new user
    user_manager.register_user(
        username="john_doe",
        email="john@example.com",
        phone="1234567890",
        name="John Doe",
        description="A passionate sportsman.",
        avatar="path/to/avatar.png",
        birth=date(1990, 1, 1),
        city="New York",
        sports=["Soccer", "Basketball"],  # Assuming this is stored as a string array in the database
        events=[1, 2, 3],  # List of event IDs
        password="securepassword123",  # Password to be hashed
        root=False,
        admin=False
    )

    # Edit user details
    user_manager.edit_user(1, name="Johnathan Doe", city="Los Angeles", events=[1, 4, 5])  # Updating events

    # Login a user user_manager.login_user("john_doe", "securepassword123")  # Attempting to log in with the correct password

    # Delete a user
    user_manager.delete_user(1)

    # Close the database connection
    user_manager.close()