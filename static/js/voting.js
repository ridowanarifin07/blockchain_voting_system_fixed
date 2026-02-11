// Voting Page JavaScript

let selectedCandidate = null;

// Select Candidate
function selectCandidate(candidateId) {
    // Remove previous selection
    document.querySelectorAll('.candidate-card').forEach(card => {
        card.classList.remove('selected');
    });
    
    // Add selection to clicked card
    const card = document.querySelector(`[data-candidate-id="${candidateId}"]`);
    if (card) {
        card.classList.add('selected');
        selectedCandidate = candidateId;
        
        // Show confirmation modal
        showConfirmationModal(candidateId);
    }
}

// Show Confirmation Modal
function showConfirmationModal(candidateId) {
    const modal = document.getElementById('confirmationModal');
    const card = document.querySelector(`[data-candidate-id="${candidateId}"]`);
    const candidateName = card.querySelector('h3').textContent;
    
    document.getElementById('selectedCandidateName').textContent = candidateName;
    modal.style.display = 'flex';
}

// Cancel Vote
function cancelVote() {
    const modal = document.getElementById('confirmationModal');
    modal.style.display = 'none';
    
    // Remove selection
    document.querySelectorAll('.candidate-card').forEach(card => {
        card.classList.remove('selected');
    });
    
    selectedCandidate = null;
}

// Confirm Vote
async function confirmVote() {
    if (!selectedCandidate) {
        window.SecureVote.showAlert('Please select a candidate', 'error');
        return;
    }
    
    try {
        const response = await fetch('/cast-vote', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                candidate_id: selectedCandidate
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Hide confirmation modal
            document.getElementById('confirmationModal').style.display = 'none';
            
            // Show success message
            showVoteSuccess(data);
        } else {
            window.SecureVote.showAlert(data.message || 'Failed to cast vote', 'error');
        }
    } catch (error) {
        window.SecureVote.showAlert('An error occurred while casting your vote', 'error');
    }
}

// Show Vote Success
function showVoteSuccess(data) {
    const successModal = document.createElement('div');
    successModal.className = 'vote-confirmation';
    successModal.innerHTML = `
        <div class="modal-content">
            <div class="vote-success">
                <div class="success-icon">✓</div>
                <div class="success-message">
                    <h2>Vote Cast Successfully!</h2>
                    <p>Your vote has been encrypted and recorded on the blockchain.</p>
                </div>
                <div class="transaction-details">
                    <h3>Transaction Details</h3>
                    <div class="detail-row">
                        <span class="label">Block Hash:</span>
                        <span class="value">${window.SecureVote.formatHash(data.block_hash)}</span>
                    </div>
                    <div class="detail-row">
                        <span class="label">Transaction ID:</span>
                        <span class="value">#${data.transaction_id}</span>
                    </div>
                    <div class="detail-row">
                        <span class="label">Timestamp:</span>
                        <span class="value">${new Date().toLocaleString()}</span>
                    </div>
                </div>
                <div class="modal-actions">
                    <button class="btn-secondary" onclick="window.location.href='/verify-vote'">
                        Verify on Blockchain
                    </button>
                    <button class="btn-primary" onclick="window.location.href='/'">
                        Return Home
                    </button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(successModal);
}

// Initialize voting page
document.addEventListener('DOMContentLoaded', () => {
    // Start election timer if available
    const endTime = document.querySelector('[data-end-time]')?.dataset.endTime;
    if (endTime) {
        window.SecureVote.startElectionTimer(endTime);
    }
    
    // Add hover effects to candidate cards
    document.querySelectorAll('.candidate-card').forEach(card => {
        card.addEventListener('mouseenter', () => {
            card.style.transform = 'translateY(-4px)';
        });
        
        card.addEventListener('mouseleave', () => {
            if (!card.classList.contains('selected')) {
                card.style.transform = 'translateY(0)';
            }
        });
    });
});

// Voice Command Support (Experimental)
if ('webkitSpeechRecognition' in window) {
    const recognition = new webkitSpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    
    // Add voice button
    const voiceButton = document.createElement('button');
    voiceButton.className = 'btn-secondary voice-button';
    voiceButton.innerHTML = '🎤 Voice Command';
    voiceButton.style.position = 'fixed';
    voiceButton.style.bottom = '20px';
    voiceButton.style.right = '20px';
    
    voiceButton.addEventListener('click', () => {
        recognition.start();
        window.SecureVote.showAlert('Listening... Say a candidate name', 'info');
    });
    
    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript.toLowerCase();
        
        // Match transcript to candidate names
        document.querySelectorAll('.candidate-card').forEach(card => {
            const candidateName = card.querySelector('h3').textContent.toLowerCase();
            if (candidateName.includes(transcript) || transcript.includes(candidateName)) {
                const candidateId = card.dataset.candidateId;
                selectCandidate(candidateId);
                window.SecureVote.showAlert(`Selected: ${card.querySelector('h3').textContent}`, 'success');
            }
        });
    };
    
    recognition.onerror = (event) => {
        window.SecureVote.showAlert('Voice recognition error', 'error');
    };
    
    document.body.appendChild(voiceButton);
}

// Accessibility: Keyboard navigation
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        cancelVote();
    }
    
    if (e.key === 'Enter' && selectedCandidate) {
        const modal = document.getElementById('confirmationModal');
        if (modal.style.display === 'flex') {
            confirmVote();
        }
    }
});

// Auto-save vote selection (in case of page refresh)
window.addEventListener('beforeunload', () => {
    if (selectedCandidate) {
        sessionStorage.setItem('selectedCandidate', selectedCandidate);
    }
});

// Restore selection on page load
const savedSelection = sessionStorage.getItem('selectedCandidate');
if (savedSelection) {
    const card = document.querySelector(`[data-candidate-id="${savedSelection}"]`);
    if (card) {
        card.classList.add('selected');
        selectedCandidate = savedSelection;
    }
}
