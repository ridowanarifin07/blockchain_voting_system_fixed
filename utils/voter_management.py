"""
Voter Management Module
Handles voter registration, authentication, and profile management
"""

import json
import secrets
from datetime import datetime, timedelta
from utils.security import hash_password, verify_password, generate_otp, verify_qr_data

class VoterManager:
    """Manages voter registration and authentication"""
    
    def __init__(self):
        self.voters = {}
        self.voted_voters = set()
        self.pending_registrations = {}
        self.otp_storage = {}
        self.feedback_storage = []
    
    def register_voter(self, voter_data):
        """Register a new voter"""
        voter_id = voter_data.get('voter_id')
        
        # Check if voter already exists
        if voter_id in self.voters:
            return {'success': False, 'message': 'Voter already registered'}
        
        # Validate required fields
        required_fields = ['voter_id', 'name', 'email', 'phone', 'password', 'national_id']
        if not all(field in voter_data for field in required_fields):
            return {'success': False, 'message': 'Missing required fields'}
        
        # Hash password
        hashed_password = hash_password(voter_data['password'])
        
        # Create voter record
        voter_record = {
            'voter_id': voter_id,
            'name': voter_data['name'],
            'email': voter_data['email'],
            'phone': voter_data['phone'],
            'password': hashed_password,
            'national_id': voter_data['national_id'],
            'address': voter_data.get('address', ''),
            'date_of_birth': voter_data.get('date_of_birth', ''),
            'registration_date': datetime.now().isoformat(),
            'approved': False,
            'active': True,
            'biometric_registered': False,
            'qr_code': self.generate_voter_qr(voter_id)
        }
        
        # Store in pending registrations
        self.pending_registrations[voter_id] = voter_record
        
        return {'success': True, 'message': 'Registration submitted for approval'}
    
    def approve_voter(self, voter_id):
        """Approve voter registration"""
        if voter_id in self.pending_registrations:
            voter_record = self.pending_registrations[voter_id]
            voter_record['approved'] = True
            voter_record['approval_date'] = datetime.now().isoformat()
            
            # Move to active voters
            self.voters[voter_id] = voter_record
            del self.pending_registrations[voter_id]
            
            return {'success': True, 'message': 'Voter approved'}
        
        return {'success': False, 'message': 'Voter not found in pending registrations'}
    
    def verify_voter(self, voter_id, password, otp=None, biometric=None):
        """Verify voter credentials with multi-factor authentication"""
        # Check if voter exists
        if voter_id not in self.voters:
            return None
        
        voter = self.voters[voter_id]
        
        # Check if voter is active and approved
        if not voter['approved'] or not voter['active']:
            return None
        
        # Verify password
        if not verify_password(password, voter['password']):
            return None
        
        # Verify OTP if provided
        if otp:
            if not self.verify_otp(voter_id, otp):
                return None
        
        # Verify biometric if provided
        if biometric:
            if not self.verify_biometric(voter_id, biometric):
                return None
        
        return voter
    
    def send_otp(self, phone):
        """Generate and send OTP to phone number"""
        otp = generate_otp()
        
        # Store OTP with expiration (5 minutes)
        self.otp_storage[phone] = {
            'otp': otp,
            'expires_at': (datetime.now() + timedelta(minutes=5)).isoformat()
        }
        
        # In production, integrate with SMS gateway
        print(f"OTP for {phone}: {otp}")
        
        return otp
    
    def verify_otp(self, voter_id, otp):
        """Verify OTP"""
        if voter_id not in self.voters:
            return False
        
        phone = self.voters[voter_id]['phone']
        
        if phone not in self.otp_storage:
            return False
        
        stored_otp_data = self.otp_storage[phone]
        
        # Check expiration
        if datetime.now() > datetime.fromisoformat(stored_otp_data['expires_at']):
            del self.otp_storage[phone]
            return False
        
        # Verify OTP
        if stored_otp_data['otp'] == otp:
            del self.otp_storage[phone]
            return True
        
        return False
    
    def generate_voter_qr(self, voter_id):
        """Generate QR code data for voter"""
        from utils.security import generate_qr_data
        return generate_qr_data(voter_id, datetime.now().isoformat())
    
    def verify_qr_code(self, qr_data):
        """Verify QR code and extract voter info"""
        voter_info = verify_qr_data(qr_data)
        
        if voter_info and voter_info['voter_id'] in self.voters:
            return self.voters[voter_info['voter_id']]
        
        return None
    
    def register_biometric(self, voter_id, biometric_type, biometric_data):
        """Register biometric data for voter"""
        if voter_id in self.voters:
            if 'biometrics' not in self.voters[voter_id]:
                self.voters[voter_id]['biometrics'] = {}
            
            self.voters[voter_id]['biometrics'][biometric_type] = biometric_data
            self.voters[voter_id]['biometric_registered'] = True
            
            return True
        
        return False
    
    def verify_biometric(self, voter_id, biometric_data):
        """Verify biometric data"""
        if voter_id not in self.voters:
            return False
        
        voter = self.voters[voter_id]
        
        if not voter.get('biometric_registered'):
            return False
        
        # In production, use actual biometric matching algorithms
        # This is a simplified version
        return True
    
    def has_voted(self, voter_id):
        """Check if voter has already voted"""
        return voter_id in self.voted_voters
    
    def mark_as_voted(self, voter_id):
        """Mark voter as having voted"""
        self.voted_voters.add(voter_id)
    
    def get_all_voters(self):
        """Get all registered voters"""
        voters_list = []
        
        for voter_id, voter in self.voters.items():
            voters_list.append({
                'voter_id': voter_id,
                'name': voter['name'],
                'email': voter['email'],
                'phone': voter['phone'],
                'registration_date': voter['registration_date'],
                'approved': voter['approved'],
                'active': voter['active'],
                'has_voted': voter_id in self.voted_voters
            })
        
        return voters_list
    
    def get_pending_registrations(self):
        """Get all pending voter registrations"""
        return list(self.pending_registrations.values())
    
    def update_voter_profile(self, voter_id, updates):
        """Update voter profile information"""
        if voter_id in self.voters:
            # Only allow certain fields to be updated
            allowed_fields = ['email', 'phone', 'address']
            
            for field in allowed_fields:
                if field in updates:
                    self.voters[voter_id][field] = updates[field]
            
            self.voters[voter_id]['last_updated'] = datetime.now().isoformat()
            
            return {'success': True, 'message': 'Profile updated'}
        
        return {'success': False, 'message': 'Voter not found'}
    
    def deactivate_voter(self, voter_id):
        """Deactivate a voter account"""
        if voter_id in self.voters:
            self.voters[voter_id]['active'] = False
            self.voters[voter_id]['deactivation_date'] = datetime.now().isoformat()
            
            return {'success': True, 'message': 'Voter deactivated'}
        
        return {'success': False, 'message': 'Voter not found'}
    
    def reactivate_voter(self, voter_id):
        """Reactivate a voter account"""
        if voter_id in self.voters:
            self.voters[voter_id]['active'] = True
            self.voters[voter_id]['reactivation_date'] = datetime.now().isoformat()
            
            return {'success': True, 'message': 'Voter reactivated'}
        
        return {'success': False, 'message': 'Voter not found'}
    
    def store_feedback(self, feedback_data):
        """Store voter feedback"""
        feedback_data['feedback_id'] = secrets.token_hex(16)
        self.feedback_storage.append(feedback_data)
        return True
    
    def get_feedback(self):
        """Retrieve all feedback"""
        return self.feedback_storage
    
    def get_voter_statistics(self):
        """Get voter statistics"""
        total_voters = len(self.voters)
        pending_voters = len(self.pending_registrations)
        voted_count = len(self.voted_voters)
        active_voters = sum(1 for v in self.voters.values() if v['active'])
        
        return {
            'total_registered': total_voters,
            'pending_approval': pending_voters,
            'active_voters': active_voters,
            'voted_count': voted_count,
            'turnout_percentage': (voted_count / total_voters * 100) if total_voters > 0 else 0
        }
    
    def export_voters(self, format='json'):
        """Export voter data"""
        if format == 'json':
            return json.dumps(list(self.voters.values()), indent=4)
        elif format == 'csv':
            csv_data = 'voter_id,name,email,phone,registration_date,approved,active,has_voted\n'
            for voter_id, voter in self.voters.items():
                has_voted = 'Yes' if voter_id in self.voted_voters else 'No'
                csv_data += f"{voter_id},{voter['name']},{voter['email']},{voter['phone']},{voter['registration_date']},{voter['approved']},{voter['active']},{has_voted}\n"
            return csv_data
        
        return None
    
    def search_voters(self, query):
        """Search voters by name, email, or voter ID"""
        results = []
        
        query_lower = query.lower()
        
        for voter_id, voter in self.voters.items():
            if (query_lower in voter['name'].lower() or 
                query_lower in voter['email'].lower() or 
                query_lower in voter_id.lower()):
                
                results.append({
                    'voter_id': voter_id,
                    'name': voter['name'],
                    'email': voter['email'],
                    'phone': voter['phone']
                })
        
        return results
    
    def validate_voter_eligibility(self, voter_id):
        """Validate if voter is eligible to vote"""
        if voter_id not in self.voters:
            return False, 'Voter not registered'
        
        voter = self.voters[voter_id]
        
        if not voter['approved']:
            return False, 'Voter registration not approved'
        
        if not voter['active']:
            return False, 'Voter account is inactive'
        
        if voter_id in self.voted_voters:
            return False, 'Voter has already voted'
        
        return True, 'Voter is eligible'
