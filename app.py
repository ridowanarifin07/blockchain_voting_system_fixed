"""
Blockchain-Based Voting System
Main Application File
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
from datetime import datetime, timedelta
import hashlib
import json
import os
import secrets
import time
from functools import wraps
import re

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
CORS(app)

# Import custom modules
from blockchain.blockchain_core import Blockchain, Block
from utils.security import (
    SecurityManager, 
    encrypt_vote, 
    decrypt_vote, 
    generate_digital_signature,
    verify_signature,
    hash_password,
    verify_password
)
from utils.voter_management import VoterManager
from utils.analytics import AnalyticsEngine
from utils.fraud_detection import FraudDetector

# Initialize components
blockchain = Blockchain()
security_manager = SecurityManager()
voter_manager = VoterManager()
analytics_engine = AnalyticsEngine()
fraud_detector = FraudDetector()

# Election configuration
ELECTION_CONFIG = {
    'start_time': None,
    'end_time': None,
    'is_active': False,
    'candidates': [],
    'election_name': '',
    'election_id': ''
}

# Rate limiting storage
request_counts = {}
blocked_ips = set()

# Admin management storage
ADMIN_USERS = {
    'admin': {
        'password': hash_password('admin123'),
        'mfa_code': '123456',
        'voter_id': None,
        'is_super_admin': True
    }
}

# Session management
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'voter_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin' not in session or not session['admin']:
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

def super_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin' not in session or not session.get('is_super_admin'):
            return jsonify({'error': 'Super admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

# Rate limiting and DDoS protection
def rate_limit_check(ip_address):
    """Check if IP is rate limited"""
    current_time = time.time()
    
    # Clean old entries
    if ip_address in request_counts:
        request_counts[ip_address] = [
            timestamp for timestamp in request_counts[ip_address]
            if current_time - timestamp < 60
        ]
    
    # Check if IP is blocked
    if ip_address in blocked_ips:
        return False
    
    # Initialize or update request count
    if ip_address not in request_counts:
        request_counts[ip_address] = []
    
    request_counts[ip_address].append(current_time)
    
    # Block if too many requests (100 per minute)
    if len(request_counts[ip_address]) > 100:
        blocked_ips.add(ip_address)
        return False
    
    return True

# Routes
@app.route('/')
def index():
    """Main landing page"""
    return render_template('index.html', election_config=ELECTION_CONFIG)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Voter login with multi-factor authentication"""
    if request.method == 'GET':
        return render_template('login.html')
    
    data = request.json
    voter_id = data.get('voter_id')
    password = data.get('password')
    otp = data.get('otp')
    biometric = data.get('biometric')
    
    # Verify voter credentials
    voter = voter_manager.verify_voter(voter_id, password, otp, biometric)
    
    if voter:
        session['voter_id'] = voter_id
        session['authenticated'] = True
        session['auth_time'] = datetime.now().isoformat()
        
        # Log authentication
        security_manager.log_activity(voter_id, 'login', 'success')
        
        return jsonify({
            'success': True,
            'message': 'Authentication successful',
            'voter_name': voter['name']
        })
    else:
        security_manager.log_activity(voter_id, 'login', 'failed')
        return jsonify({'success': False, 'message': 'Authentication failed'}), 401

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Voter registration"""
    if request.method == 'GET':
        return render_template('register.html')
    
    data = request.json
    
    # Validate registration data
    required_fields = ['voter_id', 'name', 'email', 'phone', 'password', 'national_id']
    if not all(field in data for field in required_fields):
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400
    
    # Register voter
    result = voter_manager.register_voter(data)
    
    if result['success']:
        # Send OTP for verification
        otp = voter_manager.send_otp(data['phone'])
        return jsonify({
            'success': True,
            'message': 'Registration successful. OTP sent to your phone.',
            'otp_sent': True
        })
    else:
        return jsonify(result), 400

@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    """Verify OTP for registration/login"""
    data = request.json
    voter_id = data.get('voter_id')
    otp = data.get('otp')
    
    if voter_manager.verify_otp(voter_id, otp):
        return jsonify({'success': True, 'message': 'OTP verified'})
    else:
        return jsonify({'success': False, 'message': 'Invalid OTP'}), 401

@app.route('/voting', methods=['GET'])
@login_required
def voting_page():
    """Voting interface"""
    voter_id = session.get('voter_id')
    
    # Check if voter has already voted
    if voter_manager.has_voted(voter_id):
        return render_template('already_voted.html')
    
    # Check if election is active
    if not ELECTION_CONFIG['is_active']:
        return render_template('election_closed.html')
    
    return render_template('voting.html', 
                         candidates=ELECTION_CONFIG['candidates'],
                         election_name=ELECTION_CONFIG['election_name'])

@app.route('/cast-vote', methods=['POST'])
@login_required
def cast_vote():
    """Cast and record vote on blockchain"""
    data = request.json
    voter_id = session.get('voter_id')
    candidate_id = data.get('candidate_id')
    
    # CRITICAL: Check if already voted - MULTIPLE LAYERS OF PROTECTION
    if voter_manager.has_voted(voter_id):
        security_manager.log_activity(voter_id, 'vote_cast', 'duplicate_attempt')
        return jsonify({
            'success': False, 
            'message': 'আপনি ইতিমধ্যে ভোট দিয়েছেন। একজন ভোটার শুধুমাত্র একবার ভোট দিতে পারবেন।'
        }), 403
    
    # Check on blockchain as well (double verification)
    voter_id_hash = hashlib.sha256(voter_id.encode()).hexdigest()
    if blockchain.find_vote(voter_id_hash):
        security_manager.log_activity(voter_id, 'vote_cast', 'duplicate_on_blockchain')
        return jsonify({
            'success': False, 
            'message': 'Blockchain-এ আপনার ভোট পাওয়া গেছে। ডুপ্লিকেট ভোটিং সম্ভব নয়।'
        }), 403
    
    # Fraud detection
    if fraud_detector.detect_suspicious_activity(voter_id, request.remote_addr):
        security_manager.log_activity(voter_id, 'vote_cast', 'fraud_detected')
        return jsonify({
            'success': False, 
            'message': 'সন্দেহজনক কার্যকলাপ সনাক্ত করা হয়েছে। আপনার ভোট ব্লক করা হয়েছে।'
        }), 403
    
    # Check election status
    if not ELECTION_CONFIG['is_active']:
        return jsonify({'success': False, 'message': 'ইলেকশন বর্তমানে সক্রিয় নয়'}), 400
    
    # Validate candidate
    if not candidate_id:
        return jsonify({'success': False, 'message': 'প্রার্থী নির্বাচন করুন'}), 400
    
    # Encrypt vote
    encrypted_vote = encrypt_vote(candidate_id)
    
    # Generate digital signature
    signature = generate_digital_signature(voter_id, candidate_id)
    
    # Create vote record with timestamp
    vote_timestamp = datetime.now().isoformat()
    vote_data = {
        'voter_id_hash': voter_id_hash,
        'encrypted_vote': encrypted_vote,
        'signature': signature,
        'timestamp': vote_timestamp,
        'ip_address_hash': hashlib.sha256(request.remote_addr.encode()).hexdigest(),
        'candidate_id': candidate_id  # For analytics (encrypted separately)
    }
    
    # Add to blockchain (permanent record)
    block = blockchain.add_vote(vote_data)
    
    # Mark voter as voted (immediate flag)
    voter_manager.mark_as_voted(voter_id)
    
    # Log activity
    security_manager.log_activity(voter_id, 'vote_cast', 'success', 
                                  f'Block: {block.hash}, Candidate: {candidate_id}')
    
    # Analytics
    analytics_engine.record_vote(voter_id, candidate_id, datetime.now())
    
    return jsonify({
        'success': True,
        'message': 'আপনার ভোট সফলভাবে রেকর্ড করা হয়েছে',
        'block_hash': block.hash,
        'transaction_id': block.index,
        'timestamp': vote_timestamp,
        'warning': 'আপনি আর ভোট দিতে পারবেন না - প্রতি ভোটার শুধুমাত্র একবার ভোট দিতে পারে'
    })

@app.route('/verify-vote', methods=['GET'])
@login_required
def verify_vote():
    """Allow voter to verify their vote on blockchain"""
    voter_id = session.get('voter_id')
    voter_id_hash = hashlib.sha256(voter_id.encode()).hexdigest()
    
    # Find vote in blockchain
    vote_record = blockchain.find_vote(voter_id_hash)
    
    if vote_record:
        return jsonify({
            'success': True,
            'vote_verified': True,
            'block_index': vote_record['block_index'],
            'block_hash': vote_record['block_hash'],
            'timestamp': vote_record['timestamp']
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Vote not found'
        }), 404

@app.route('/results', methods=['GET'])
def results():
    """Display election results"""
    # Check if election has ended
    if ELECTION_CONFIG['is_active']:
        return render_template('results_pending.html')
    
    # Calculate results
    results = analytics_engine.calculate_results(blockchain)
    
    return render_template('results.html', 
                         results=results,
                         election_name=ELECTION_CONFIG['election_name'])

@app.route('/api/results', methods=['GET'])
def api_results():
    """API endpoint for real-time results"""
    results = analytics_engine.get_live_results(blockchain)
    
    return jsonify({
        'success': True,
        'results': results,
        'total_votes': results['total_votes'],
        'timestamp': datetime.now().isoformat()
    })

@app.route('/blockchain-explorer', methods=['GET'])
def blockchain_explorer():
    """Public blockchain explorer"""
    return render_template('blockchain_explorer.html')

@app.route('/api/blockchain', methods=['GET'])
def api_blockchain():
    """Get blockchain data"""
    chain_data = []
    
    for block in blockchain.chain:
        chain_data.append({
            'index': block.index,
            'timestamp': block.timestamp,
            'previous_hash': block.previous_hash,
            'hash': block.hash,
            'votes_count': len(block.votes)
        })
    
    return jsonify({
        'length': len(blockchain.chain),
        'chain': chain_data
    })

@app.route('/analytics', methods=['GET'])
def analytics_page():
    """Analytics dashboard"""
    return render_template('analytics.html')

@app.route('/api/analytics', methods=['GET'])
def api_analytics():
    """Get analytics data"""
    analytics_data = analytics_engine.get_comprehensive_analytics(blockchain)
    
    return jsonify({
        'success': True,
        'analytics': analytics_data
    })

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login"""
    if request.method == 'GET':
        return render_template('admin_login.html')
    
    data = request.json
    username = data.get('username')
    password = data.get('password')
    mfa_code = data.get('mfa_code')
    
    # Verify admin credentials
    if username in ADMIN_USERS:
        admin = ADMIN_USERS[username]
        
        if verify_password(password, admin['password']) and mfa_code == admin['mfa_code']:
            session['admin'] = True
            session['admin_user'] = username
            session['is_super_admin'] = admin.get('is_super_admin', False)
            session['voter_id'] = admin.get('voter_id')
            
            security_manager.log_activity(username, 'admin_login', 'success')
            
            return jsonify({
                'success': True, 
                'message': 'Admin login successful',
                'is_super_admin': admin.get('is_super_admin', False)
            })
    
    security_manager.log_activity(username or 'unknown', 'admin_login', 'failed')
    return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Admin dashboard"""
    return render_template('admin_dashboard.html')

@app.route('/admin/manage-election', methods=['GET', 'POST'])
@admin_required
def manage_election():
    """Manage election settings"""
    if request.method == 'GET':
        return jsonify({
            'success': True,
            'election_config': ELECTION_CONFIG
        })
    
    data = request.json
    action = data.get('action')
    
    if action == 'start':
        if ELECTION_CONFIG['is_active']:
            return jsonify({'success': False, 'message': 'Election is already active'}), 400
        
        ELECTION_CONFIG['is_active'] = True
        ELECTION_CONFIG['start_time'] = datetime.now().isoformat()
        ELECTION_CONFIG['end_time'] = data.get('end_time')
        ELECTION_CONFIG['candidates'] = data.get('candidates', [])
        ELECTION_CONFIG['election_name'] = data.get('election_name', '')
        ELECTION_CONFIG['election_id'] = secrets.token_hex(16)
        ELECTION_CONFIG['countdown_locked'] = True  # Lock countdown after start
        
        security_manager.log_activity(session.get('admin_user'), 'election_started', 'success')
        
        return jsonify({'success': True, 'message': 'Election started', 'countdown_locked': True})
    
    elif action == 'stop':
        ELECTION_CONFIG['is_active'] = False
        ELECTION_CONFIG['countdown_locked'] = False
        
        security_manager.log_activity(session.get('admin_user'), 'election_stopped', 'success')
        
        return jsonify({'success': True, 'message': 'Election stopped'})
    
    elif action == 'update':
        # Prevent countdown changes if election is active or locked
        if ELECTION_CONFIG.get('countdown_locked') and 'end_time' in data.get('config', {}):
            return jsonify({
                'success': False, 
                'message': 'Cannot change countdown after election has started'
            }), 403
        
        config_updates = data.get('config', {})
        
        # Only allow non-countdown updates if locked
        if ELECTION_CONFIG.get('countdown_locked'):
            config_updates.pop('end_time', None)
            config_updates.pop('start_time', None)
        
        ELECTION_CONFIG.update(config_updates)
        
        security_manager.log_activity(session.get('admin_user'), 'election_updated', 'success')
        
        return jsonify({'success': True, 'message': 'Election updated'})
    
    return jsonify({'success': False, 'message': 'Invalid action'}), 400

@app.route('/admin/voters', methods=['GET'])
@admin_required
def manage_voters():
    """Manage voter registrations"""
    voters = voter_manager.get_all_voters()
    return jsonify({
        'success': True,
        'voters': voters
    })

@app.route('/admin/approve-voter', methods=['POST'])
@admin_required
def approve_voter():
    """Approve voter registration"""
    data = request.json
    voter_id = data.get('voter_id')
    
    result = voter_manager.approve_voter(voter_id)
    return jsonify(result)

@app.route('/admin/security-logs', methods=['GET'])
@admin_required
def security_logs():
    """View security logs"""
    logs = security_manager.get_logs()
    return jsonify({
        'success': True,
        'logs': logs
    })

@app.route('/admin/promote-to-admin', methods=['POST'])
@super_admin_required
def promote_to_admin():
    """Promote a voter to admin status"""
    data = request.json
    voter_id = data.get('voter_id')
    
    if not voter_id:
        return jsonify({'success': False, 'message': 'Voter ID required'}), 400
    
    # Check if voter exists
    if voter_id not in voter_manager.voters:
        return jsonify({'success': False, 'message': 'Voter not found'}), 404
    
    # Check if already admin
    if voter_id in ADMIN_USERS:
        return jsonify({'success': False, 'message': 'Already an admin'}), 400
    
    voter = voter_manager.voters[voter_id]
    
    # Create admin account
    admin_username = data.get('admin_username', voter_id)
    admin_password = data.get('admin_password', secrets.token_hex(8))
    admin_mfa = data.get('mfa_code', str(secrets.randbelow(1000000)).zfill(6))
    
    ADMIN_USERS[admin_username] = {
        'password': hash_password(admin_password),
        'mfa_code': admin_mfa,
        'voter_id': voter_id,
        'is_super_admin': False,
        'created_at': datetime.now().isoformat(),
        'created_by': session.get('admin_user')
    }
    
    # Log the promotion
    security_manager.log_activity(
        session.get('admin_user'), 
        'admin_promoted', 
        'success',
        f'Voter {voter_id} promoted to admin as {admin_username}'
    )
    
    return jsonify({
        'success': True,
        'message': 'ভোটারকে সফলভাবে Admin বানানো হয়েছে',
        'admin_username': admin_username,
        'admin_password': admin_password,
        'mfa_code': admin_mfa,
        'warning': 'এই credentials সংরক্ষণ করুন - এগুলো আর দেখানো হবে না'
    })

@app.route('/admin/remove-admin', methods=['POST'])
@super_admin_required
def remove_admin():
    """Remove admin privileges from a user"""
    data = request.json
    admin_username = data.get('admin_username')
    
    if not admin_username:
        return jsonify({'success': False, 'message': 'Admin username required'}), 400
    
    if admin_username not in ADMIN_USERS:
        return jsonify({'success': False, 'message': 'Admin not found'}), 404
    
    if ADMIN_USERS[admin_username].get('is_super_admin'):
        return jsonify({'success': False, 'message': 'Cannot remove super admin'}), 403
    
    # Remove admin
    del ADMIN_USERS[admin_username]
    
    security_manager.log_activity(
        session.get('admin_user'),
        'admin_removed',
        'success',
        f'Admin {admin_username} removed'
    )
    
    return jsonify({
        'success': True,
        'message': 'Admin privileges removed successfully'
    })

@app.route('/admin/list-admins', methods=['GET'])
@admin_required
def list_admins():
    """List all admin users"""
    admins = []
    
    for username, admin_data in ADMIN_USERS.items():
        admins.append({
            'username': username,
            'voter_id': admin_data.get('voter_id'),
            'is_super_admin': admin_data.get('is_super_admin', False),
            'created_at': admin_data.get('created_at', 'N/A'),
            'created_by': admin_data.get('created_by', 'System')
        })
    
    return jsonify({
        'success': True,
        'admins': admins,
        'total': len(admins)
    })

@app.route('/admin/voting-stats', methods=['GET'])
@admin_required
def voting_stats():
    """Get detailed voting statistics"""
    voter_stats = voter_manager.get_voter_statistics()
    blockchain_stats = blockchain.get_blockchain_stats()
    
    # Additional stats
    total_votes = len(analytics_engine.vote_records)
    unique_voters = len(set(record['voter_id'] for record in analytics_engine.vote_records))
    
    return jsonify({
        'success': True,
        'stats': {
            'voter_stats': voter_stats,
            'blockchain_stats': blockchain_stats,
            'total_votes': total_votes,
            'unique_voters': unique_voters,
            'duplicate_attempts': total_votes - unique_voters if total_votes > unique_voters else 0,
            'election_active': ELECTION_CONFIG['is_active'],
            'countdown_locked': ELECTION_CONFIG.get('countdown_locked', False)
        }
    })

@app.route('/logout')
def logout():
    """Logout voter or admin"""
    user_id = session.get('voter_id') or session.get('admin_user')
    if user_id:
        security_manager.log_activity(user_id, 'logout', 'success')
    
    session.clear()
    return redirect(url_for('index'))

@app.errorhandler(429)
def rate_limit_error(e):
    """Handle rate limit errors"""
    return jsonify({'error': 'Too many requests. Please try again later.'}), 429

@app.errorhandler(500)
def internal_error(e):
    """Handle internal errors"""
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
