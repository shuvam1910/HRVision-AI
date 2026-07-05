import os
import json
import datetime
import hashlib
from pymongo import MongoClient

class DatabaseManager:
    def __init__(self, uri=None, db_name="hr_analytics_db"):
        self.uri = os.environ.get("MONGODB_URI", uri)
        self.db_name = db_name
        self.use_mongo = False
        self.mongo_client = None
        self.db = None
        
        # Paths for local file database
        self.local_dir = os.path.join(os.getcwd(), "data")
        self.local_file = os.path.join(self.local_dir, "local_db.json")
        os.makedirs(self.local_dir, exist_ok=True)
        
        # Attempt MongoDB connection
        try:
            self.mongo_client = MongoClient(self.uri, serverSelectionTimeoutMS=2500)
            # Trigger exception if connection fails
            self.mongo_client.server_info()
            self.db = self.mongo_client[self.db_name]
            self.use_mongo = True
        except Exception:
            self.use_mongo = False
            self._init_local_db()
            
        # Seed default admin and user
        self._seed_default_users()

    def _init_local_db(self):
        """Initializes local JSON database if not exists or is corrupted."""
        if not os.path.exists(self.local_file):
            data = {
                "users": {},
                "logs": [],
                "notifications": []
            }
            self._save_local_db(data)

    def _load_local_db(self):
        """Loads local database from JSON file."""
        self._init_local_db()
        try:
            with open(self.local_file, "r") as f:
                return json.load(f)
        except Exception:
            return {"users": {}, "logs": [], "notifications": []}

    def _save_local_db(self, data):
        """Saves local database to JSON file."""
        try:
            with open(self.local_file, "w") as f:
                json.dump(data, f, indent=4, default=str)
        except Exception as e:
            print(f"Error saving local DB: {e}")

    def get_status(self):
        """Returns database operational status."""
        return "MongoDB (Connected)" if self.use_mongo else "Local JSON Fallback"

    def _hash_password(self, password):
        """Hashes passwords securely with SHA-256."""
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def _seed_default_users(self):
        """Seeds default user accounts for demonstration if they do not exist."""
        default_users = [
            {
                "username": "admin@hr.com",
                "password": "admin123",
                "name": "Shuvam Nayak",
                "role": "Admin",
                "approved": True
            },
            {
                "username": "user@hr.com",
                "password": "user123",
                "name": "John Doe (HR User)",
                "role": "User",
                "approved": True
            }
        ]
        
        for user in default_users:
            existing = self.find_user(user["username"])
            if not existing:
                self.create_user(
                    username=user["username"],
                    password=user["password"],
                    name=user["name"],
                    role=user["role"],
                    approved=user["approved"]
                )
            elif existing.get("name") == "Alex Mercer (Admin)":
                # Update existing admin name to Shuvam Nayak
                if self.use_mongo:
                    try:
                        self.db.users.update_one(
                            {"username": user["username"]},
                            {"$set": {"name": user["name"]}}
                        )
                    except Exception:
                        pass
                # Update local DB too
                db = self._load_local_db()
                if user["username"] in db["users"]:
                    db["users"][user["username"]]["name"] = user["name"]
                    self._save_local_db(db)

    # --- User Management Methods ---

    def find_user(self, username):
        """Finds a user by username."""
        if self.use_mongo:
            try:
                return self.db.users.find_one({"username": username})
            except Exception:
                pass
        
        # Fallback to local
        db = self._load_local_db()
        user = db["users"].get(username)
        return user

    def create_user(self, username, password, name, role="User", approved=True):
        """Creates a new user account. Approved by default."""
        hashed_password = self._hash_password(password)
        user_doc = {
            "username": username,
            "password": hashed_password,
            "name": name,
            "role": role,
            "approved": approved,
            "created_at": datetime.datetime.now().isoformat()
        }
        
        if self.use_mongo:
            try:
                self.db.users.update_one(
                    {"username": username},
                    {"$set": user_doc},
                    upsert=True
                )
                return True
            except Exception:
                pass
                
        # Fallback to local
        db = self._load_local_db()
        db["users"][username] = user_doc
        self._save_local_db(db)
        return True

    def verify_user(self, username, password):
        """Verifies username and password, returning user document if match."""
        user = self.find_user(username)
        if not user:
            return None
        
        hashed_input = self._hash_password(password)
        if user["password"] == hashed_input:
            return user
        return None

    def get_all_users(self):
        """Returns all registered users."""
        if self.use_mongo:
            try:
                return list(self.db.users.find())
            except Exception:
                pass
                
        db = self._load_local_db()
        return list(db["users"].values())

    def update_user_approval(self, username, approved):
        """Approves or revokes user status."""
        if self.use_mongo:
            try:
                self.db.users.update_one(
                    {"username": username},
                    {"$set": {"approved": approved}}
                )
                return
            except Exception:
                pass
                
        db = self._load_local_db()
        if username in db["users"]:
            db["users"][username]["approved"] = approved
            self._save_local_db(db)

    def update_user_role(self, username, role):
        """Updates user role."""
        if self.use_mongo:
            try:
                self.db.users.update_one(
                    {"username": username},
                    {"$set": {"role": role}}
                )
                return
            except Exception:
                pass
                
        db = self._load_local_db()
        if username in db["users"]:
            db["users"][username]["role"] = role
            self._save_local_db(db)

    def delete_user(self, username):
        """Deletes user from the database."""
        if self.use_mongo:
            try:
                self.db.users.delete_one({"username": username})
                return
            except Exception:
                pass
                
        db = self._load_local_db()
        if username in db["users"]:
            del db["users"][username]
            self._save_local_db(db)

    # --- Activity Logging Methods ---

    def log_activity(self, username, action, details=""):
        """Logs user activities for auditing."""
        log_entry = {
            "username": username,
            "action": action,
            "details": details,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        if self.use_mongo:
            try:
                self.db.logs.insert_one(log_entry)
                return
            except Exception:
                pass
                
        db = self._load_local_db()
        db["logs"].append(log_entry)
        if len(db["logs"]) > 200:
            db["logs"] = db["logs"][-200:]
        self._save_local_db(db)

    def get_logs(self, limit=50):
        """Gets the most recent activity logs."""
        if self.use_mongo:
            try:
                return list(self.db.logs.find().sort("timestamp", -1).limit(limit))
            except Exception:
                pass
                
        db = self._load_local_db()
        logs = sorted(db["logs"], key=lambda x: x["timestamp"], reverse=True)
        return logs[:limit]

    # --- Notifications Methods ---

    def create_notification(self, title, message, severity="info"):
        """Creates a system notification."""
        notif = {
            "title": title,
            "message": message,
            "severity": severity,
            "timestamp": datetime.datetime.now().isoformat(),
            "read": False
        }
        if self.use_mongo:
            try:
                self.db.notifications.insert_one(notif)
                return
            except Exception:
                pass
                
        db = self._load_local_db()
        db["notifications"].append(notif)
        if len(db["notifications"]) > 50:
            db["notifications"] = db["notifications"][-50:]
        self._save_local_db(db)

    def get_notifications(self, unread_only=False):
        """Gets system notifications."""
        if self.use_mongo:
            try:
                query = {"read": False} if unread_only else {}
                return list(self.db.notifications.find(query).sort("timestamp", -1))
            except Exception:
                pass
                
        db = self._load_local_db()
        notifs = sorted(db["notifications"], key=lambda x: x["timestamp"], reverse=True)
        if unread_only:
            return [n for n in notifs if not n.get("read", False)]
        return notifs

    def mark_notifications_as_read(self):
        """Marks all notifications as read."""
        if self.use_mongo:
            try:
                self.db.notifications.update_many({"read": False}, {"$set": {"read": True}})
                return
            except Exception:
                pass
                
        db = self._load_local_db()
        for n in db["notifications"]:
            n["read"] = True
        self._save_local_db(db)

    def get_user_count(self):
        """Returns the number of registered users."""
        if self.use_mongo:
            try:
                return self.db.users.count_documents({})
            except Exception:
                pass
                
        db = self._load_local_db()
        return len(db["users"])
