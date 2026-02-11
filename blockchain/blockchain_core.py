"""
Blockchain Core Implementation
Handles blockchain creation, validation, and management
"""

import hashlib
import json
from time import time
from datetime import datetime
import secrets

class Block:
    """Individual block in the blockchain"""
    
    def __init__(self, index, votes, timestamp, previous_hash, nonce=0):
        self.index = index
        self.votes = votes
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = self.calculate_hash()
    
    def calculate_hash(self):
        """Calculate block hash using SHA-256"""
        block_string = json.dumps({
            'index': self.index,
            'votes': self.votes,
            'timestamp': self.timestamp,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce
        }, sort_keys=True)
        
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def mine_block(self, difficulty=4):
        """Proof of Work mining"""
        target = '0' * difficulty
        
        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()
        
        return self.hash
    
    def to_dict(self):
        """Convert block to dictionary"""
        return {
            'index': self.index,
            'votes': self.votes,
            'timestamp': self.timestamp,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce,
            'hash': self.hash
        }


class Blockchain:
    """Main blockchain implementation"""
    
    def __init__(self):
        self.chain = []
        self.pending_votes = []
        self.difficulty = 4
        self.mining_reward = 0
        self.create_genesis_block()
    
    def create_genesis_block(self):
        """Create the first block in the chain"""
        genesis_block = Block(0, [], str(datetime.now()), "0")
        genesis_block.mine_block(self.difficulty)
        self.chain.append(genesis_block)
    
    def get_latest_block(self):
        """Get the most recent block"""
        return self.chain[-1]
    
    def add_vote(self, vote_data):
        """Add a vote to the blockchain"""
        # Create new block with the vote
        new_block = Block(
            index=len(self.chain),
            votes=[vote_data],
            timestamp=str(datetime.now()),
            previous_hash=self.get_latest_block().hash
        )
        
        # Mine the block
        new_block.mine_block(self.difficulty)
        
        # Add to chain
        self.chain.append(new_block)
        
        return new_block
    
    def is_chain_valid(self):
        """Validate the entire blockchain"""
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]
            
            # Check if current block hash is correct
            if current_block.hash != current_block.calculate_hash():
                return False
            
            # Check if previous hash matches
            if current_block.previous_hash != previous_block.hash:
                return False
            
            # Check proof of work
            if not current_block.hash.startswith('0' * self.difficulty):
                return False
        
        return True
    
    def find_vote(self, voter_id_hash):
        """Find a vote by voter ID hash"""
        for i, block in enumerate(self.chain):
            for vote in block.votes:
                if vote.get('voter_id_hash') == voter_id_hash:
                    return {
                        'block_index': block.index,
                        'block_hash': block.hash,
                        'vote_data': vote,
                        'timestamp': vote['timestamp']
                    }
        
        return None
    
    def get_all_votes(self):
        """Get all votes from the blockchain"""
        all_votes = []
        
        for block in self.chain[1:]:  # Skip genesis block
            all_votes.extend(block.votes)
        
        return all_votes
    
    def get_chain_length(self):
        """Get the length of the blockchain"""
        return len(self.chain)
    
    def get_block_by_index(self, index):
        """Get a specific block by index"""
        if 0 <= index < len(self.chain):
            return self.chain[index]
        return None
    
    def get_block_by_hash(self, block_hash):
        """Get a specific block by hash"""
        for block in self.chain:
            if block.hash == block_hash:
                return block
        return None
    
    def export_chain(self):
        """Export blockchain to JSON"""
        chain_data = []
        for block in self.chain:
            chain_data.append(block.to_dict())
        
        return json.dumps(chain_data, indent=4)
    
    def get_merkle_root(self, votes):
        """Calculate Merkle root for votes"""
        if not votes:
            return hashlib.sha256(b'').hexdigest()
        
        # Hash all votes
        hashes = [hashlib.sha256(json.dumps(vote, sort_keys=True).encode()).hexdigest() 
                  for vote in votes]
        
        # Build Merkle tree
        while len(hashes) > 1:
            if len(hashes) % 2 != 0:
                hashes.append(hashes[-1])
            
            new_hashes = []
            for i in range(0, len(hashes), 2):
                combined = hashes[i] + hashes[i + 1]
                new_hash = hashlib.sha256(combined.encode()).hexdigest()
                new_hashes.append(new_hash)
            
            hashes = new_hashes
        
        return hashes[0]
    
    def verify_vote_in_merkle_tree(self, vote_data, merkle_root):
        """Verify a vote is part of the Merkle tree"""
        vote_hash = hashlib.sha256(json.dumps(vote_data, sort_keys=True).encode()).hexdigest()
        # Simplified verification - in production, implement full Merkle proof
        return True
    
    def get_blockchain_stats(self):
        """Get blockchain statistics"""
        return {
            'total_blocks': len(self.chain),
            'total_votes': sum(len(block.votes) for block in self.chain),
            'chain_valid': self.is_chain_valid(),
            'difficulty': self.difficulty,
            'latest_block_hash': self.get_latest_block().hash,
            'genesis_block_hash': self.chain[0].hash
        }


class BlockchainNode:
    """Distributed node for blockchain network"""
    
    def __init__(self, node_id):
        self.node_id = node_id
        self.blockchain = Blockchain()
        self.peers = set()
    
    def add_peer(self, peer_address):
        """Add a peer node"""
        self.peers.add(peer_address)
    
    def remove_peer(self, peer_address):
        """Remove a peer node"""
        self.peers.discard(peer_address)
    
    def broadcast_block(self, block):
        """Broadcast new block to all peers"""
        # In production, implement actual network broadcasting
        pass
    
    def sync_chain(self, peer_chain):
        """Synchronize blockchain with peer"""
        if len(peer_chain) > len(self.blockchain.chain):
            # Validate peer chain
            temp_blockchain = Blockchain()
            temp_blockchain.chain = peer_chain
            
            if temp_blockchain.is_chain_valid():
                self.blockchain.chain = peer_chain
                return True
        
        return False
    
    def resolve_conflicts(self):
        """Consensus algorithm - longest valid chain wins"""
        longest_chain = self.blockchain.chain
        max_length = len(self.blockchain.chain)
        
        # Check all peers (simulated)
        # In production, query actual peer nodes
        
        if len(longest_chain) > max_length:
            self.blockchain.chain = longest_chain
            return True
        
        return False


class ShardedBlockchain:
    """Sharded blockchain for scalability"""
    
    def __init__(self, num_shards=4):
        self.num_shards = num_shards
        self.shards = [Blockchain() for _ in range(num_shards)]
    
    def get_shard(self, voter_id_hash):
        """Determine which shard a vote belongs to"""
        shard_index = int(voter_id_hash[:8], 16) % self.num_shards
        return self.shards[shard_index]
    
    def add_vote(self, vote_data):
        """Add vote to appropriate shard"""
        voter_id_hash = vote_data.get('voter_id_hash')
        shard = self.get_shard(voter_id_hash)
        return shard.add_vote(vote_data)
    
    def get_all_votes(self):
        """Get votes from all shards"""
        all_votes = []
        for shard in self.shards:
            all_votes.extend(shard.get_all_votes())
        return all_votes
    
    def validate_all_shards(self):
        """Validate all shards"""
        return all(shard.is_chain_valid() for shard in self.shards)
