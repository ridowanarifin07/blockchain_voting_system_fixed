"""
Security Management Module
Handles encryption, digital signatures, authentication, and security logging
"""

import hashlib
import hmac
import secrets
import json
from datetime import datetime
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization
import base64

# Generate encryption key (in production, use secure key management)
ENCRYPTION_KEY = Fernet.generate_key()
cipher_suite = Fernet(ENCRYPTION_KEY)

class SecurityManager:
    """Manages security operations and logging"""
    
    def __init__(self):
        self.activity_log = []
        self.failed_attempts = {}
        self.max_failed_attempts = 5
    
    def log_activity(self, user_id, action, status, details=''):
        """Log security-related activities"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id,
            'action': action,
            'status': status,
            'details': details,
            'ip_address': '',  # Should be passed from request
            'log_id': secrets.token_hex(16)
        }
        
        self.activity_log.append(log_entry)
        
        # Track failed attempts
        if status == 'failed':
            if user_id not in self.failed_attempts:
                self.failed_attempts[user_id] = []
            
            self.failed_attempts[user_id].append(datetime.now())
            
            # Check if account should be locked
            if len(self.failed_attempts[user_id]) >= self.max_failed_attempts:
                self.lock_account(user_id)
    
    def lock_account(self, user_id):
        """Lock user account after too many failed attempts"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id,
            'action': 'account_locked',
            'status': 'security_measure',
            'details': f'Account locked after {self.max_failed_attempts} failed attempts'
        }
        self.activity_log.append(log_entry)
    
    def get_logs(self, filters=None):
        """Retrieve security logs with optional filters"""
        if not filters:
            return self.activity_log[-100:]  # Return last 100 entries
        
        filtered_logs = self.activity_log
        
        if 'user_id' in filters:
            filtered_logs = [log for log in filtered_logs if log['user_id'] == filters['user_id']]
        
        if 'action' in filters:
            filtered_logs = [log for log in filtered_logs if log['action'] == filters['action']]
        
        if 'start_date' in filters:
            filtered_logs = [log for log in filtered_logs if log['timestamp'] >= filters['start_date']]
        
        return filtered_logs
    
    def export_logs(self, format='json'):
        """Export security logs"""
        if format == 'json':
            return json.dumps(self.activity_log, indent=4)
        elif format == 'csv':
            # Convert to CSV format
            csv_data = 'timestamp,user_id,action,status,details\n'
            for log in self.activity_log:
                csv_data += f"{log['timestamp']},{log['user_id']},{log['action']},{log['status']},{log['details']}\n"
            return csv_data
        
        return self.activity_log
    
    def detect_anomalies(self):
        """Detect anomalous activities"""
        anomalies = []
        
        # Check for rapid successive login attempts
        user_activities = {}
        for log in self.activity_log:
            user_id = log['user_id']
            if user_id not in user_activities:
                user_activities[user_id] = []
            user_activities[user_id].append(log)
        
        for user_id, activities in user_activities.items():
            # Check for more than 10 actions in 1 minute
            recent_activities = [a for a in activities if 
                               (datetime.now() - datetime.fromisoformat(a['timestamp'])).seconds < 60]
            
            if len(recent_activities) > 10:
                anomalies.append({
                    'user_id': user_id,
                    'type': 'rapid_actions',
                    'count': len(recent_activities),
                    'severity': 'high'
                })
        
        return anomalies


def encrypt_vote(vote_data):
    """Encrypt vote data using Fernet symmetric encryption"""
    vote_string = json.dumps(vote_data)
    encrypted = cipher_suite.encrypt(vote_string.encode())
    return base64.b64encode(encrypted).decode()


def decrypt_vote(encrypted_vote):
    """Decrypt vote data"""
    try:
        encrypted_bytes = base64.b64decode(encrypted_vote.encode())
        decrypted = cipher_suite.decrypt(encrypted_bytes)
        return json.loads(decrypted.decode())
    except Exception as e:
        return None


def generate_digital_signature(voter_id, vote_data):
    """Generate digital signature for vote"""
    # In production, use actual private key
    message = f"{voter_id}:{vote_data}:{datetime.now().isoformat()}"
    signature = hashlib.sha256(message.encode()).hexdigest()
    return signature


def verify_signature(voter_id, vote_data, signature):
    """Verify digital signature"""
    expected_signature = generate_digital_signature(voter_id, vote_data)
    return hmac.compare_digest(signature, expected_signature)


def hash_password(password, salt=None):
    """Hash password using SHA-256 with salt"""
    if salt is None:
        salt = secrets.token_hex(16)
    
    pwd_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}${pwd_hash}"


def verify_password(password, hashed_password):
    """Verify password against hash"""
    try:
        salt, pwd_hash = hashed_password.split('$')
        expected_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return hmac.compare_digest(pwd_hash, expected_hash)
    except:
        return False


def generate_otp():
    """Generate 6-digit OTP"""
    return str(secrets.randbelow(1000000)).zfill(6)


def generate_qr_data(voter_id, timestamp):
    """Generate QR code data for voter authentication"""
    data = {
        'voter_id': voter_id,
        'timestamp': timestamp,
        'nonce': secrets.token_hex(16)
    }
    
    # Sign the data
    data_string = json.dumps(data, sort_keys=True)
    signature = hashlib.sha256(data_string.encode()).hexdigest()
    data['signature'] = signature
    
    return base64.b64encode(json.dumps(data).encode()).decode()


def verify_qr_data(qr_data):
    """Verify QR code data"""
    try:
        decoded_data = json.loads(base64.b64decode(qr_data.encode()).decode())
        
        # Extract signature
        signature = decoded_data.pop('signature')
        
        # Verify signature
        data_string = json.dumps(decoded_data, sort_keys=True)
        expected_signature = hashlib.sha256(data_string.encode()).hexdigest()
        
        if hmac.compare_digest(signature, expected_signature):
            return decoded_data
        
        return None
    except:
        return None


class BiometricAuth:
    """Biometric authentication handler"""
    
    def __init__(self):
        self.registered_biometrics = {}
    
    def register_fingerprint(self, voter_id, fingerprint_data):
        """Register fingerprint data"""
        # Hash fingerprint data for storage
        fingerprint_hash = hashlib.sha256(fingerprint_data.encode()).hexdigest()
        
        if voter_id not in self.registered_biometrics:
            self.registered_biometrics[voter_id] = {}
        
        self.registered_biometrics[voter_id]['fingerprint'] = fingerprint_hash
        return True
    
    def verify_fingerprint(self, voter_id, fingerprint_data):
        """Verify fingerprint"""
        if voter_id not in self.registered_biometrics:
            return False
        
        fingerprint_hash = hashlib.sha256(fingerprint_data.encode()).hexdigest()
        stored_hash = self.registered_biometrics[voter_id].get('fingerprint')
        
        return hmac.compare_digest(fingerprint_hash, stored_hash)
    
    def register_face(self, voter_id, face_data):
        """Register face recognition data"""
        face_hash = hashlib.sha256(face_data.encode()).hexdigest()
        
        if voter_id not in self.registered_biometrics:
            self.registered_biometrics[voter_id] = {}
        
        self.registered_biometrics[voter_id]['face'] = face_hash
        return True
    
    def verify_face(self, voter_id, face_data):
        """Verify face recognition"""
        if voter_id not in self.registered_biometrics:
            return False
        
        face_hash = hashlib.sha256(face_data.encode()).hexdigest()
        stored_hash = self.registered_biometrics[voter_id].get('face')
        
        return hmac.compare_digest(face_hash, stored_hash)


class EncryptionManager:
    """Advanced encryption management"""
    
    def __init__(self):
        # Generate RSA key pair for asymmetric encryption
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        self.public_key = self.private_key.public_key()
    
    def encrypt_with_public_key(self, data):
        """Encrypt data with public key"""
        encrypted = self.public_key.encrypt(
            data.encode(),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return base64.b64encode(encrypted).decode()
    
    def decrypt_with_private_key(self, encrypted_data):
        """Decrypt data with private key"""
        try:
            encrypted_bytes = base64.b64decode(encrypted_data.encode())
            decrypted = self.private_key.decrypt(
                encrypted_bytes,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            return decrypted.decode()
        except:
            return None
    
    def export_public_key(self):
        """Export public key for sharing"""
        pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return pem.decode()
