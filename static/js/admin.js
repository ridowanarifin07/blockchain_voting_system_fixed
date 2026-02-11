// Admin Dashboard JavaScript

let currentSection = 'dashboard';
let electionActive = false;
let countdownLocked = false;

// Initialize Dashboard
document.addEventListener('DOMContentLoaded', () => {
    loadDashboardData();
    loadVoters();
    loadAdmins();
    setInterval(loadDashboardData, 10000); // Refresh every 10 seconds
});

// Section Navigation
function showSection(sectionName) {
    // Hide all sections
    document.querySelectorAll('.admin-section').forEach(section => {
        section.classList.remove('active');
    });
    
    // Remove active from nav items
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    
    // Show selected section
    document.getElementById(sectionName + '-section').classList.add('active');
    
    // Add active to nav item
    event.target.classList.add('active');
    
    currentSection = sectionName;
    
    // Load section-specific data
    switch(sectionName) {
        case 'voters':
            loadVoters();
            break;
        case 'admins':
            loadAdmins();
            loadVotersForPromotion();
            break;
        case 'security':
            refreshLogs();
            break;
        case 'results':
            loadResults();
            break;
    }
}

// Load Dashboard Data
async function loadDashboardData() {
    try {
        const response = await fetch('/admin/voting-stats');
        const data = await response.json();
        
        if (data.success) {
            const stats = data.stats;
            
            // Update stats
            document.getElementById('totalVoters').textContent = stats.voter_stats.total_registered;
            document.getElementById('votesCast').textContent = stats.voter_stats.voted_count;
            document.getElementById('pendingVoters').textContent = stats.voter_stats.pending_approval;
            document.getElementById('turnoutRate').textContent = stats.voter_stats.turnout_percentage.toFixed(1) + '%';
            
            // Update election status
            electionActive = stats.election_active;
            countdownLocked = stats.countdown_locked;
            
            const statusDiv = document.getElementById('electionStatus');
            if (stats.election_active) {
                statusDiv.innerHTML = '<p class="status-approved">✓ Election is Active</p>';
            } else {
                statusDiv.innerHTML = '<p class="status-inactive">✗ No Active Election</p>';
            }
            
            // Update countdown lock warning
            const lockWarning = document.getElementById('countdownLockWarning');
            if (lockWarning) {
                lockWarning.style.display = countdownLocked ? 'block' : 'none';
                document.getElementById('electionEndTime').disabled = countdownLocked;
            }
            
            // Update blockchain stats
            const blockchainDiv = document.getElementById('blockchainStats');
            blockchainDiv.innerHTML = `
                <p><strong>Total Blocks:</strong> ${stats.blockchain_stats.total_blocks}</p>
                <p><strong>Total Votes:</strong> ${stats.blockchain_stats.total_votes}</p>
                <p><strong>Chain Valid:</strong> ${stats.blockchain_stats.chain_valid ? '✓ Yes' : '✗ No'}</p>
                <p><strong>Duplicate Attempts:</strong> ${stats.duplicate_attempts}</p>
            `;
        }
    } catch (error) {
        console.error('Failed to load dashboard data:', error);
    }
}

// Candidate Management
function addCandidateInput() {
    const container = document.getElementById('candidatesList');
    const div = document.createElement('div');
    div.className = 'candidate-input';
    div.innerHTML = `
        <input type="text" placeholder="Candidate Name" class="candidate-name">
        <input type="text" placeholder="Party" class="candidate-party">
        <button type="button" onclick="removeCandidateInput(this)" class="btn-danger-small">Remove</button>
    `;
    container.appendChild(div);
}

function removeCandidateInput(btn) {
    btn.parentElement.remove();
}

// Start Election
async function startElection() {
    if (countdownLocked) {
        window.SecureVote.showAlert('Countdown is locked! Cannot modify after election starts.', 'error');
        return;
    }
    
    const electionName = document.getElementById('electionName').value;
    const endTime = document.getElementById('electionEndTime').value;
    
    if (!electionName || !endTime) {
        window.SecureVote.showAlert('Please fill all required fields', 'error');
        return;
    }
    
    // Collect candidates
    const candidates = [];
    document.querySelectorAll('.candidate-input').forEach((div, index) => {
        const name = div.querySelector('.candidate-name').value;
        const party = div.querySelector('.candidate-party').value;
        
        if (name && party) {
            candidates.push({
                id: 'C' + (index + 1),
                name: name,
                party: party,
                photo: '/static/images/default-candidate.png'
            });
        }
    });
    
    if (candidates.length < 2) {
        window.SecureVote.showAlert('Please add at least 2 candidates', 'error');
        return;
    }
    
    try {
        const response = await fetch('/admin/manage-election', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                action: 'start',
                election_name: electionName,
                end_time: endTime,
                candidates: candidates
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            window.SecureVote.showAlert('Election started successfully! Countdown is now locked.', 'success');
            countdownLocked = true;
            document.getElementById('countdownLockWarning').style.display = 'block';
            document.getElementById('electionEndTime').disabled = true;
            loadDashboardData();
        } else {
            window.SecureVote.showAlert(data.message || 'Failed to start election', 'error');
        }
    } catch (error) {
        window.SecureVote.showAlert('An error occurred', 'error');
    }
}

// Stop Election
async function stopElection() {
    if (!confirm('Are you sure you want to stop the election? This will unlock the countdown.')) {
        return;
    }
    
    try {
        const response = await fetch('/admin/manage-election', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                action: 'stop'
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            window.SecureVote.showAlert('Election stopped successfully', 'success');
            countdownLocked = false;
            document.getElementById('countdownLockWarning').style.display = 'none';
            document.getElementById('electionEndTime').disabled = false;
            loadDashboardData();
        } else {
            window.SecureVote.showAlert(data.message || 'Failed to stop election', 'error');
        }
    } catch (error) {
        window.SecureVote.showAlert('An error occurred', 'error');
    }
}

// Load Voters
async function loadVoters() {
    try {
        const response = await fetch('/admin/voters');
        const data = await response.json();
        
        if (data.success) {
            const tbody = document.getElementById('votersTableBody');
            tbody.innerHTML = '';
            
            data.voters.forEach(voter => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${voter.voter_id}</td>
                    <td>${voter.name}</td>
                    <td>${voter.email}</td>
                    <td><span class="status-badge ${voter.approved ? 'status-approved' : 'status-pending'}">
                        ${voter.approved ? 'Approved' : 'Pending'}
                    </span></td>
                    <td>${voter.has_voted ? '✓ Yes' : '✗ No'}</td>
                    <td>
                        ${!voter.approved ? 
                            `<button class="action-btn btn-approve" onclick="approveVoter('${voter.voter_id}')">Approve</button>` 
                            : ''}
                        ${voter.active ? 
                            `<button class="action-btn btn-reject" onclick="deactivateVoter('${voter.voter_id}')">Deactivate</button>` 
                            : `<button class="action-btn btn-approve" onclick="reactivateVoter('${voter.voter_id}')">Reactivate</button>`}
                    </td>
                `;
                tbody.appendChild(tr);
            });
        }
    } catch (error) {
        console.error('Failed to load voters:', error);
    }
}

// Approve Voter
async function approveVoter(voterId) {
    try {
        const response = await fetch('/admin/approve-voter', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ voter_id: voterId })
        });
        
        const data = await response.json();
        
        if (data.success) {
            window.SecureVote.showAlert('Voter approved successfully', 'success');
            loadVoters();
            loadDashboardData();
        } else {
            window.SecureVote.showAlert(data.message || 'Failed to approve voter', 'error');
        }
    } catch (error) {
        window.SecureVote.showAlert('An error occurred', 'error');
    }
}

// Load Admins
async function loadAdmins() {
    try {
        const response = await fetch('/admin/list-admins');
        const data = await response.json();
        
        if (data.success) {
            const container = document.getElementById('adminsList');
            container.innerHTML = '';
            
            data.admins.forEach(admin => {
                const div = document.createElement('div');
                div.className = 'admin-item';
                div.innerHTML = `
                    <div class="admin-item-header">
                        <strong>${admin.username}</strong>
                        ${admin.is_super_admin ? '<span class="super-admin-badge">Super Admin</span>' : ''}
                    </div>
                    <div class="admin-item-details">
                        <p>Voter ID: ${admin.voter_id || 'N/A'}</p>
                        <p>Created: ${new Date(admin.created_at).toLocaleDateString() || 'N/A'}</p>
                        ${!admin.is_super_admin ? 
                            `<button class="action-btn btn-reject" onclick="removeAdmin('${admin.username}')">Remove Admin</button>` 
                            : ''}
                    </div>
                `;
                container.appendChild(div);
            });
        }
    } catch (error) {
        console.error('Failed to load admins:', error);
    }
}

// Load Voters for Promotion
async function loadVotersForPromotion() {
    try {
        const response = await fetch('/admin/voters');
        const data = await response.json();
        
        if (data.success) {
            const select = document.getElementById('voterToPromote');
            select.innerHTML = '<option value="">Choose a voter...</option>';
            
            data.voters.forEach(voter => {
                if (voter.approved && voter.active) {
                    const option = document.createElement('option');
                    option.value = voter.voter_id;
                    option.textContent = `${voter.name} (${voter.voter_id})`;
                    select.appendChild(option);
                }
            });
        }
    } catch (error) {
        console.error('Failed to load voters for promotion:', error);
    }
}

// Promote Admin Form Handler
document.getElementById('promoteAdminForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const voterId = document.getElementById('voterToPromote').value;
    const username = document.getElementById('newAdminUsername').value;
    const password = document.getElementById('newAdminPassword').value;
    
    if (!voterId || !username) {
        window.SecureVote.showAlert('Please fill all required fields', 'error');
        return;
    }
    
    try {
        const response = await fetch('/admin/promote-to-admin', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                voter_id: voterId,
                admin_username: username,
                admin_password: password || undefined
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Show credentials modal
            document.getElementById('newAdminUser').textContent = data.admin_username;
            document.getElementById('newAdminPass').textContent = data.admin_password;
            document.getElementById('newAdminMFA').textContent = data.mfa_code;
            document.getElementById('promoteSuccessModal').style.display = 'flex';
            
            // Reset form
            document.getElementById('promoteAdminForm').reset();
            
            // Reload admins list
            loadAdmins();
        } else {
            window.SecureVote.showAlert(data.message || 'Failed to promote admin', 'error');
        }
    } catch (error) {
        window.SecureVote.showAlert('An error occurred', 'error');
    }
});

function closePromoteModal() {
    document.getElementById('promoteSuccessModal').style.display = 'none';
}

// Remove Admin
async function removeAdmin(username) {
    if (!confirm(`Are you sure you want to remove admin privileges from ${username}?`)) {
        return;
    }
    
    try {
        const response = await fetch('/admin/remove-admin', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ admin_username: username })
        });
        
        const data = await response.json();
        
        if (data.success) {
            window.SecureVote.showAlert('Admin removed successfully', 'success');
            loadAdmins();
        } else {
            window.SecureVote.showAlert(data.message || 'Failed to remove admin', 'error');
        }
    } catch (error) {
        window.SecureVote.showAlert('An error occurred', 'error');
    }
}

// Refresh Security Logs
async function refreshLogs() {
    try {
        const response = await fetch('/admin/security-logs');
        const data = await response.json();
        
        if (data.success) {
            const tbody = document.getElementById('securityLogsBody');
            tbody.innerHTML = '';
            
            data.logs.slice(-50).reverse().forEach(log => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${new Date(log.timestamp).toLocaleString()}</td>
                    <td>${log.user_id}</td>
                    <td>${log.action}</td>
                    <td><span class="status-badge ${log.status === 'success' ? 'status-approved' : 'status-inactive'}">
                        ${log.status}
                    </span></td>
                    <td>${log.details || '-'}</td>
                `;
                tbody.appendChild(tr);
            });
        }
    } catch (error) {
        console.error('Failed to load security logs:', error);
    }
}

// Load Results
async function loadResults() {
    try {
        const response = await fetch('/api/results');
        const data = await response.json();
        
        if (data.success && data.results) {
            const container = document.getElementById('liveResults');
            container.innerHTML = '';
            
            data.results.results.forEach(result => {
                const div = document.createElement('div');
                div.className = 'result-item';
                div.innerHTML = `
                    <h4>${result.candidate_id}</h4>
                    <p>Votes: ${result.votes}</p>
                    <p>Percentage: ${result.percentage}%</p>
                    <div class="progress-bar">
                        <div style="width: ${result.percentage}%; background: var(--color-primary); height: 8px; border-radius: 4px;"></div>
                    </div>
                `;
                container.appendChild(div);
            });
            
            const totalDiv = document.createElement('div');
            totalDiv.innerHTML = `<h3>Total Votes: ${data.results.total_votes}</h3>`;
            container.appendChild(totalDiv);
        } else {
            document.getElementById('liveResults').innerHTML = '<p>No results available yet</p>';
        }
    } catch (error) {
        console.error('Failed to load results:', error);
    }
}
