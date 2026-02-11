# SecureVote - Quick Start Guide

## 🚀 Get Started in 3 Steps

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

Or use the automated setup script:
```bash
bash setup.sh
```

### Step 2: Run the Application
```bash
python app.py
```

The server will start on `http://localhost:5000`

### Step 3: Access the System
Open your browser and navigate to: **http://localhost:5000**

## 📱 Using the System

### For Voters:

1. **Register** → Go to `/register`
   - Fill in your details
   - Verify phone with OTP
   - Wait for admin approval

2. **Login** → Go to `/login`
   - Enter credentials
   - Verify with OTP
   - Optional: Use biometric auth

3. **Vote** → Go to `/voting`
   - Select your candidate
   - Confirm your choice
   - Vote recorded on blockchain

4. **Verify** → Go to `/verify-vote`
   - Check your vote on blockchain
   - View transaction details

### For Administrators:

1. **Login** → Go to `/admin/login`
   - Username: `admin`
   - Password: `admin123`
   - MFA: `123456`

2. **Manage Election**
   - Start/stop elections
   - Add candidates
   - Set timeframes

3. **Manage Voters**
   - Approve registrations
   - View statistics
   - Monitor activity

4. **View Results**
   - Real-time updates
   - Analytics dashboard
   - Export reports

## 🔐 Default Credentials

**Admin Account:**
- Username: `admin`
- Password: `admin123`
- MFA Code: `123456`

⚠️ **CHANGE THESE IN PRODUCTION!**

## 📊 Features Available

✅ Multi-factor authentication
✅ Blockchain vote recording
✅ End-to-end encryption
✅ Real-time results
✅ Fraud detection
✅ Analytics dashboard
✅ And 25+ more features!

## 🛠️ Troubleshooting

**Port already in use:**
```bash
python app.py  # Try different port with -p flag
```

**Module not found:**
```bash
pip install -r requirements.txt
```

**Permission denied:**
```bash
chmod +x setup.sh
```

## 📖 Full Documentation

See [README.md](README.md) for complete documentation.

## 🆘 Need Help?

- Check the README for detailed information
- Review the code comments
- Test with example data

---

**Happy Voting! 🗳️**
