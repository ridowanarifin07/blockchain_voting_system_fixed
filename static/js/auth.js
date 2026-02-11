// Authentication JavaScript

// Login Form Handler
document.getElementById('loginForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const voterId = document.getElementById('voterId').value;
    const password = document.getElementById('password').value;
    const otp = document.getElementById('otp').value;
    
    try {
        const response = await fetch('/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                voter_id: voterId,
                password: password,
                otp: otp
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            window.SecureVote.showAlert('Login successful! Redirecting...', 'success');
            setTimeout(() => {
                window.location.href = '/voting';
            }, 1500);
        } else {
            window.SecureVote.showAlert(data.message || 'Login failed', 'error');
        }
    } catch (error) {
        window.SecureVote.showAlert('An error occurred. Please try again.', 'error');
    }
});

// Registration Form Handler
document.getElementById('registerForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = {
        voter_id: document.getElementById('voterId').value,
        name: document.getElementById('name').value,
        email: document.getElementById('email').value,
        phone: document.getElementById('phone').value,
        password: document.getElementById('password').value,
        national_id: document.getElementById('nationalId').value,
        address: document.getElementById('address')?.value || '',
        date_of_birth: document.getElementById('dob')?.value || ''
    };
    
    // Validate password strength
    if (formData.password.length < 8) {
        window.SecureVote.showAlert('Password must be at least 8 characters long', 'error');
        return;
    }
    
    try {
        const response = await fetch('/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            window.SecureVote.showAlert('Registration successful! Please check your phone for OTP.', 'success');
            
            // Show OTP verification modal
            showOTPModal(formData.voter_id);
        } else {
            window.SecureVote.showAlert(data.message || 'Registration failed', 'error');
        }
    } catch (error) {
        window.SecureVote.showAlert('An error occurred. Please try again.', 'error');
    }
});

// Request OTP
async function requestOTP() {
    const phone = document.getElementById('phone')?.value;
    const voterId = document.getElementById('voterId')?.value;
    
    if (!phone && !voterId) {
        window.SecureVote.showAlert('Please enter phone number or voter ID', 'error');
        return;
    }
    
    try {
        const response = await fetch('/verify-otp', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                phone: phone,
                voter_id: voterId
            })
        });
        
        window.SecureVote.showAlert('OTP sent to your phone', 'success');
    } catch (error) {
        window.SecureVote.showAlert('Failed to send OTP', 'error');
    }
}

// Biometric Scan (Simulated)
async function scanBiometric() {
    window.SecureVote.showAlert('Biometric scan initiated...', 'info');
    
    // Simulate biometric scan
    setTimeout(() => {
        const bioData = 'simulated_biometric_data_' + Math.random().toString(36).substring(7);
        document.getElementById('biometricData').value = bioData;
        window.SecureVote.showAlert('Biometric scan successful!', 'success');
    }, 2000);
}

// QR Code Scanner (Simulated)
async function scanQRCode() {
    window.SecureVote.showAlert('QR scanner activated...', 'info');
    
    // In production, integrate with actual QR scanner library
    setTimeout(() => {
        const qrData = 'simulated_qr_data_' + Math.random().toString(36).substring(7);
        document.getElementById('qrData').value = qrData;
        window.SecureVote.showAlert('QR code scanned successfully!', 'success');
    }, 1500);
}

// Show OTP Verification Modal
function showOTPModal(voterId) {
    const modal = document.createElement('div');
    modal.className = 'vote-confirmation';
    modal.innerHTML = `
        <div class="modal-content">
            <h2>Verify Your Phone</h2>
            <p>Enter the 6-digit OTP sent to your phone</p>
            <form id="otpVerifyForm" class="auth-form" style="margin-top: 20px;">
                <div class="form-group">
                    <input type="text" id="otpInput" placeholder="Enter OTP" maxlength="6" required>
                </div>
                <div class="modal-actions">
                    <button type="button" class="btn-secondary" onclick="this.closest('.vote-confirmation').remove()">Cancel</button>
                    <button type="submit" class="btn-primary">Verify</button>
                </div>
            </form>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    document.getElementById('otpVerifyForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const otp = document.getElementById('otpInput').value;
        
        try {
            const response = await fetch('/verify-otp', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    voter_id: voterId,
                    otp: otp
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                window.SecureVote.showAlert('Phone verified successfully!', 'success');
                modal.remove();
                
                // Redirect to login
                setTimeout(() => {
                    window.location.href = '/login';
                }, 1500);
            } else {
                window.SecureVote.showAlert('Invalid OTP', 'error');
            }
        } catch (error) {
            window.SecureVote.showAlert('Verification failed', 'error');
        }
    });
}

// Password Strength Indicator
document.getElementById('password')?.addEventListener('input', (e) => {
    const password = e.target.value;
    const strengthIndicator = document.getElementById('passwordStrength');
    
    if (!strengthIndicator) return;
    
    let strength = 0;
    if (password.length >= 8) strength++;
    if (/[a-z]/.test(password) && /[A-Z]/.test(password)) strength++;
    if (/\d/.test(password)) strength++;
    if (/[^a-zA-Z\d]/.test(password)) strength++;
    
    const strengthText = ['Weak', 'Fair', 'Good', 'Strong'][strength];
    const strengthColor = ['#ef4444', '#f59e0b', '#10b981', '#0ea5e9'][strength];
    
    strengthIndicator.textContent = strengthText;
    strengthIndicator.style.color = strengthColor;
});

// Admin Login Handler
document.getElementById('adminLoginForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const mfaCode = document.getElementById('mfaCode').value;
    
    try {
        const response = await fetch('/admin/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: username,
                password: password,
                mfa_code: mfaCode
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            window.SecureVote.showAlert('Admin login successful!', 'success');
            setTimeout(() => {
                window.location.href = '/admin/dashboard';
            }, 1500);
        } else {
            window.SecureVote.showAlert(data.message || 'Login failed', 'error');
        }
    } catch (error) {
        window.SecureVote.showAlert('An error occurred', 'error');
    }
});
