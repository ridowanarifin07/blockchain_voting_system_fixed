"""
Analytics Engine and Fraud Detection
Handles election analytics, statistics, and fraud detection
"""

from datetime import datetime, timedelta
from collections import Counter
import json

class AnalyticsEngine:
    """Election analytics and data visualization"""
    
    def __init__(self):
        self.vote_records = []
        self.temporal_data = []
    
    def record_vote(self, voter_id, candidate_id, timestamp):
        """Record vote for analytics"""
        self.vote_records.append({
            'voter_id': voter_id,
            'candidate_id': candidate_id,
            'timestamp': timestamp.isoformat()
        })
        
        self.temporal_data.append({
            'timestamp': timestamp.isoformat(),
            'hour': timestamp.hour,
            'day': timestamp.day,
            'month': timestamp.month
        })
    
    def calculate_results(self, blockchain):
        """Calculate final election results"""
        votes = blockchain.get_all_votes()
        
        # Decrypt and count votes
        from utils.security import decrypt_vote
        
        vote_counts = Counter()
        
        for vote in votes:
            encrypted_vote = vote.get('encrypted_vote')
            decrypted = decrypt_vote(encrypted_vote)
            
            if decrypted:
                vote_counts[decrypted] += 1
        
        # Calculate percentages
        total_votes = sum(vote_counts.values())
        
        results = []
        for candidate_id, count in vote_counts.most_common():
            percentage = (count / total_votes * 100) if total_votes > 0 else 0
            results.append({
                'candidate_id': candidate_id,
                'votes': count,
                'percentage': round(percentage, 2)
            })
        
        return {
            'results': results,
            'total_votes': total_votes,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_live_results(self, blockchain):
        """Get real-time election results"""
        return self.calculate_results(blockchain)
    
    def get_temporal_analysis(self):
        """Analyze voting patterns over time"""
        hourly_votes = Counter()
        daily_votes = Counter()
        
        for record in self.temporal_data:
            hourly_votes[record['hour']] += 1
            daily_votes[record['day']] += 1
        
        return {
            'hourly_distribution': dict(hourly_votes),
            'daily_distribution': dict(daily_votes),
            'peak_hour': hourly_votes.most_common(1)[0] if hourly_votes else None,
            'peak_day': daily_votes.most_common(1)[0] if daily_votes else None
        }
    
    def get_demographic_analysis(self, voter_demographics):
        """Analyze voting patterns by demographics"""
        age_groups = Counter()
        gender_distribution = Counter()
        regional_distribution = Counter()
        
        for voter_id, demographics in voter_demographics.items():
            age_groups[demographics.get('age_group', 'unknown')] += 1
            gender_distribution[demographics.get('gender', 'unknown')] += 1
            regional_distribution[demographics.get('region', 'unknown')] += 1
        
        return {
            'age_groups': dict(age_groups),
            'gender_distribution': dict(gender_distribution),
            'regional_distribution': dict(regional_distribution)
        }
    
    def get_turnout_statistics(self, total_registered_voters):
        """Calculate voter turnout statistics"""
        total_votes = len(self.vote_records)
        turnout_percentage = (total_votes / total_registered_voters * 100) if total_registered_voters > 0 else 0
        
        return {
            'total_registered_voters': total_registered_voters,
            'total_votes_cast': total_votes,
            'turnout_percentage': round(turnout_percentage, 2),
            'abstention_rate': round(100 - turnout_percentage, 2)
        }
    
    def get_comprehensive_analytics(self, blockchain):
        """Get all analytics data"""
        results = self.calculate_results(blockchain)
        temporal = self.get_temporal_analysis()
        
        return {
            'election_results': results,
            'temporal_analysis': temporal,
            'total_votes': len(self.vote_records),
            'votes_per_hour': len(self.vote_records) / 24 if self.vote_records else 0
        }
    
    def generate_election_report(self, blockchain, voter_manager):
        """Generate comprehensive election report"""
        results = self.calculate_results(blockchain)
        voter_stats = voter_manager.get_voter_statistics()
        temporal = self.get_temporal_analysis()
        
        report = {
            'report_id': datetime.now().strftime('%Y%m%d%H%M%S'),
            'generated_at': datetime.now().isoformat(),
            'election_results': results,
            'voter_statistics': voter_stats,
            'temporal_analysis': temporal,
            'blockchain_stats': blockchain.get_blockchain_stats()
        }
        
        return report
    
    def export_analytics(self, format='json'):
        """Export analytics data"""
        if format == 'json':
            return json.dumps({
                'vote_records': self.vote_records,
                'temporal_data': self.temporal_data
            }, indent=4)
        
        return None
    
    def predict_final_results(self, current_results, total_expected_voters, confidence_interval=0.95):
        """Predict final election results based on current data"""
        total_votes = current_results['total_votes']
        
        if total_votes < 100:  # Need minimum sample size
            return {'error': 'Insufficient data for prediction'}
        
        predictions = []
        
        for candidate in current_results['results']:
            current_percentage = candidate['percentage']
            
            # Simple prediction with margin of error
            # In production, use more sophisticated statistical methods
            margin_of_error = 5  # Simplified
            
            predictions.append({
                'candidate_id': candidate['candidate_id'],
                'predicted_percentage': current_percentage,
                'margin_of_error': margin_of_error,
                'confidence_interval': confidence_interval
            })
        
        return {
            'predictions': predictions,
            'sample_size': total_votes,
            'total_expected': total_expected_voters
        }


class FraudDetector:
    """AI-based fraud detection system"""
    
    def __init__(self):
        self.suspicious_activities = []
        self.ip_tracking = {}
        self.voting_patterns = {}
        self.blocked_entities = set()
    
    def detect_suspicious_activity(self, voter_id, ip_address):
        """Detect potential fraudulent activities"""
        suspicious = False
        reasons = []
        
        # Check for multiple votes from same IP
        if ip_address in self.ip_tracking:
            self.ip_tracking[ip_address] += 1
            
            if self.ip_tracking[ip_address] > 5:
                suspicious = True
                reasons.append('Multiple votes from same IP address')
        else:
            self.ip_tracking[ip_address] = 1
        
        # Check voting pattern anomalies
        if voter_id in self.voting_patterns:
            last_attempt = self.voting_patterns[voter_id][-1]
            time_diff = (datetime.now() - datetime.fromisoformat(last_attempt)).seconds
            
            if time_diff < 10:  # Less than 10 seconds between attempts
                suspicious = True
                reasons.append('Rapid successive voting attempts')
        else:
            self.voting_patterns[voter_id] = []
        
        self.voting_patterns[voter_id].append(datetime.now().isoformat())
        
        if suspicious:
            self.log_suspicious_activity(voter_id, ip_address, reasons)
        
        return suspicious
    
    def log_suspicious_activity(self, voter_id, ip_address, reasons):
        """Log suspicious activities"""
        activity = {
            'timestamp': datetime.now().isoformat(),
            'voter_id': voter_id,
            'ip_address': ip_address,
            'reasons': reasons,
            'severity': 'high' if len(reasons) > 1 else 'medium'
        }
        
        self.suspicious_activities.append(activity)
    
    def check_duplicate_votes(self, voter_id, blockchain):
        """Check if voter has already voted"""
        import hashlib
        voter_id_hash = hashlib.sha256(voter_id.encode()).hexdigest()
        
        existing_vote = blockchain.find_vote(voter_id_hash)
        
        return existing_vote is not None
    
    def detect_pattern_anomalies(self, voting_data):
        """Detect unusual voting patterns using ML algorithms"""
        # Simplified anomaly detection
        # In production, use actual ML models
        
        anomalies = []
        
        # Check for voting clusters
        time_clusters = {}
        
        for record in voting_data:
            timestamp = datetime.fromisoformat(record['timestamp'])
            minute_key = timestamp.strftime('%Y-%m-%d %H:%M')
            
            if minute_key not in time_clusters:
                time_clusters[minute_key] = 0
            
            time_clusters[minute_key] += 1
        
        # Flag unusual clusters (more than 100 votes per minute)
        for minute, count in time_clusters.items():
            if count > 100:
                anomalies.append({
                    'type': 'vote_clustering',
                    'timestamp': minute,
                    'count': count,
                    'severity': 'high'
                })
        
        return anomalies
    
    def analyze_blockchain_integrity(self, blockchain):
        """Analyze blockchain for tampering attempts"""
        issues = []
        
        # Check chain validity
        if not blockchain.is_chain_valid():
            issues.append({
                'type': 'chain_integrity',
                'severity': 'critical',
                'message': 'Blockchain integrity compromised'
            })
        
        # Check for suspicious block times
        for i in range(1, len(blockchain.chain)):
            current_block = blockchain.chain[i]
            previous_block = blockchain.chain[i - 1]
            
            time_diff = (datetime.fromisoformat(current_block.timestamp) - 
                        datetime.fromisoformat(previous_block.timestamp)).seconds
            
            if time_diff < 1:  # Blocks created too quickly
                issues.append({
                    'type': 'suspicious_timing',
                    'block_index': i,
                    'severity': 'medium',
                    'message': f'Block {i} created suspiciously quickly'
                })
        
        return issues
    
    def get_fraud_report(self):
        """Generate fraud detection report"""
        return {
            'suspicious_activities': self.suspicious_activities,
            'total_incidents': len(self.suspicious_activities),
            'blocked_entities': list(self.blocked_entities),
            'high_severity_count': sum(1 for a in self.suspicious_activities if a['severity'] == 'high'),
            'generated_at': datetime.now().isoformat()
        }
    
    def block_entity(self, entity_id):
        """Block suspicious entity"""
        self.blocked_entities.add(entity_id)
    
    def is_blocked(self, entity_id):
        """Check if entity is blocked"""
        return entity_id in self.blocked_entities
    
    def calculate_fraud_risk_score(self, voter_id, ip_address, voting_history):
        """Calculate fraud risk score for a vote"""
        risk_score = 0
        
        # Check IP reputation
        if ip_address in self.ip_tracking and self.ip_tracking[ip_address] > 3:
            risk_score += 30
        
        # Check voter history
        if voter_id in self.voting_patterns and len(self.voting_patterns[voter_id]) > 1:
            risk_score += 20
        
        # Check against suspicious activities
        voter_incidents = [a for a in self.suspicious_activities if a['voter_id'] == voter_id]
        risk_score += len(voter_incidents) * 15
        
        # Normalize to 0-100 scale
        risk_score = min(risk_score, 100)
        
        risk_level = 'low'
        if risk_score > 70:
            risk_level = 'high'
        elif risk_score > 40:
            risk_level = 'medium'
        
        return {
            'risk_score': risk_score,
            'risk_level': risk_level,
            'factors': {
                'ip_reputation': ip_address in self.ip_tracking,
                'voting_history': len(self.voting_patterns.get(voter_id, [])),
                'past_incidents': len(voter_incidents)
            }
        }
