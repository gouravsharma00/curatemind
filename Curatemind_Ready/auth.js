document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements based on auth.html
    const signUpForm = document.getElementById('signUpForm');
    const signInForm = document.getElementById('signInForm');
    const showSignUpBtn = document.getElementById('showSignUpBtn');
    const showSignInBtn = document.getElementById('showSignInBtn');

    // --- 1. TOGGLE LOGIC ---
    if (showSignUpBtn) {
        showSignUpBtn.addEventListener('click', (e) => {
            e.preventDefault();
            signInForm.classList.add('hidden');
            signUpForm.classList.remove('hidden');
        });
    }

    if (showSignInBtn) {
        showSignInBtn.addEventListener('click', (e) => {
            e.preventDefault();
            signUpForm.classList.add('hidden');
            signInForm.classList.remove('hidden');
        });
    }

    // --- 2. SIGN UP LOGIC ---
    if (signUpForm) {
        signUpForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const full_name = document.getElementById('signup-fullname').value.trim();
            const email = document.getElementById('signup-email').value;
            const password = document.getElementById('signup-password').value;
            // Optional catch if field exists
            const adminCodeInput = document.getElementById('signup-admin-code');
            const adminCode = (adminCodeInput && !document.getElementById('admin-code-container').classList.contains('hidden')) ? adminCodeInput.value.trim() : null;
            
            const payload = {
                full_name: full_name,
                email: email,
                password: password,
                admin_code: adminCode === "" ? null : adminCode
            };

            try {
                const response = await fetch('/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                
                if (response.ok) {
                    const data = await response.json();
                    localStorage.setItem('user_id', data.user_id);
                    localStorage.setItem('role', data.role);
                    if (data.role === 'admin') {
                        window.location.href = 'admin_dashboard.html';
                    } else {
                        window.location.href = 'onboarding.html';
                    }
                } else {
                    const data = await response.json();
                    alert("Registration Error: " + (data.detail || "Failed to register."));
                }
            } catch (error) {
                alert("Network error: " + error.message);
            }
        });
    }

    // --- 3. SIGN IN LOGIC ---
    if (signInForm) {
        signInForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const email = document.getElementById('signin-email').value;
            const password = document.getElementById('signin-password').value;

            try {
                const response = await fetch('/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password })
                });

                if (response.ok) {
                    const data = await response.json();
                    // Save JWT token to local storage
                    localStorage.setItem('access_token', data.access_token);
                    localStorage.setItem('user_id', data.user_id);
                    localStorage.setItem('role', data.role);
                    
                    if (data.role === 'admin') {
                        window.location.href = 'admin_dashboard.html';
                    } else {
                        window.location.href = 'dashboard.html';
                    }
                } else {
                    const data = await response.json();
                    alert("Login Failed: " + (data.detail || "Invalid credentials."));
                }
            } catch (error) {
                alert("Network error: " + error.message);
            }
        });
    }
});