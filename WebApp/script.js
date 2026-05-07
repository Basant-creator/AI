/* ============================================================
   BobAI — Interactive UI Logic
   ============================================================ */

// ── Dropdown management ──────────────────────────────────────
const DROPDOWN_IDS = ['loginDropdown', 'signupDropdown', 'tokenDropdown'];
const API_BASE = '';
const AUTH_STORAGE_KEY = 'bobai_session_token';
let loginRequestInFlight = false;

/**
 * Fetch wrapper with automatic retry + exponential backoff.
 * Retries on 502/503/504 (typical Render cold-start errors) up to
 * `maxRetries` times before giving up. All other status codes are
 * returned immediately so callers can handle them.
 */
async function fetchWithFallback(path, options = {}, maxRetries = 8) {
    const url = `${API_BASE}${path}`;
    let lastError = null;

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
        try {
            const res = await fetch(url, options);

            // Only retry on gateway errors (cold-start / transient)
            if ([502, 503, 504].includes(res.status) && attempt < maxRetries) {
                const wait = Math.min(2000 * 2 ** attempt, 10000);
                console.log(`[fetchWithFallback] Got ${res.status} for ${path}. Retrying in ${wait}ms... (Attempt ${attempt + 1}/${maxRetries})`);
                await new Promise(r => setTimeout(r, wait));
                continue;
            }

            return res; // success or non-retryable error
        } catch (err) {
            lastError = err;
            if (attempt < maxRetries) {
                const wait = Math.min(2000 * 2 ** attempt, 10000);
                console.log(`[fetchWithFallback] Network error for ${path}. Retrying in ${wait}ms... (Attempt ${attempt + 1}/${maxRetries})`);
                await new Promise(r => setTimeout(r, wait));
            }
        }
    }

    // All retries exhausted — throw so callers can show a toast
    throw lastError || new Error('Request failed after retries');
}

function getSessionToken() {
    return localStorage.getItem(AUTH_STORAGE_KEY) || '';
}

function setSessionToken(token) {
    if (token) {
        localStorage.setItem(AUTH_STORAGE_KEY, token);
    } else {
        localStorage.removeItem(AUTH_STORAGE_KEY);
    }
}

function authHeaders() {
    const token = getSessionToken();
    if (!token) return { 'Content-Type': 'application/json' };
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
    };
}

function updateAuthUi(isLoggedIn) {
    const loginBtn = document.querySelector('#loginDropdown .nav-btn');
    const signupBtn = document.querySelector('#signupDropdown .nav-btn');
    const accountBtn = document.getElementById('accountBtn');

    // Mobile buttons
    const mLoginBtn = document.getElementById('mobileLoginBtn');
    const mSignupBtn = document.getElementById('mobileSignupBtn');
    const mLogoutBtn = document.getElementById('mobileLogoutBtn');

    if (loginBtn) loginBtn.style.display = isLoggedIn ? 'none' : '';
    if (signupBtn) signupBtn.style.display = isLoggedIn ? 'none' : '';
    if (accountBtn) accountBtn.style.display = isLoggedIn ? '' : 'none';
    
    if (mLoginBtn) mLoginBtn.style.display = isLoggedIn ? 'none' : '';
    if (mSignupBtn) mSignupBtn.style.display = isLoggedIn ? 'none' : '';
    if (mLogoutBtn) mLogoutBtn.style.display = isLoggedIn ? '' : 'none';
}

async function hydrateSession() {
    const token = getSessionToken();
    if (!token) {
        updateAuthUi(false);
        return;
    }

    try {
        const res = await fetchWithFallback('/auth/me', {
            method: 'GET',
            headers: authHeaders(),
        });
        if (res.status === 429) {
            showToast('⚠ Too many requests. Please wait and try again.');
            return;
        }
        if (!res.ok) {
            setSessionToken('');
            updateAuthUi(false);
            return;
        }
        updateAuthUi(true);
    } catch (_err) {
        setSessionToken('');
        updateAuthUi(false);
    }
}

function toggleDropdown(id) {
    const isOpen = document.getElementById(id).classList.contains('open');
    closeAllDropdowns();
    if (!isOpen) openDropdown(id);
}

function openDropdown(id) {
    document.getElementById(id).classList.add('open');
    document.getElementById('backdrop').classList.add('active');
    document.body.style.overflow = '';
}

function closeAllDropdowns() {
    DROPDOWN_IDS.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.classList.remove('open');
    });
    const backdrop = document.getElementById('backdrop');
    if (backdrop) backdrop.classList.remove('active');
}

/** Close dropdowns on Esc key */
document.addEventListener('keydown', e => {
    if (e.key === 'Escape') closeAllDropdowns();
});

/** Switch from one dropdown to another (e.g. "Sign Up" link inside Login panel) */
function switchDropdown(fromId, toId) {
    closeAllDropdowns();
    setTimeout(() => openDropdown(toId), 80);
}


// ── Mobile nav ───────────────────────────────────────────────
function toggleMobileMenu() {
    const menu = document.getElementById('mobileMenu');
    const ham  = document.getElementById('hamburger');
    menu.classList.toggle('open');
    ham.classList.toggle('open');
}

// Close mobile menu on outside click
document.addEventListener('click', e => {
    const menu = document.getElementById('mobileMenu');
    const ham  = document.getElementById('hamburger');
    if (menu && ham && !menu.contains(e.target) && !ham.contains(e.target)) {
        menu.classList.remove('open');
        ham.classList.remove('open');
    }
});


// ── Navbar scroll effect ─────────────────────────────────────
window.addEventListener('scroll', () => {
    const navbar = document.getElementById('navbar');
    if (navbar) {
        navbar.classList.toggle('scrolled', window.scrollY > 20);
    }
}, { passive: true });


// ── Hero fade-in on load ─────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    const heroContent = document.getElementById('heroContent');
    if (heroContent) {
        // Animation is driven purely by CSS animation-delay stagger,
        // but we ensure the section is visible first.
        heroContent.style.visibility = 'visible';
    }

    hydrateSession();
});


// ── Intersection Observer for feature cards ──────────────────
document.addEventListener('DOMContentLoaded', () => {
    const cards = document.querySelectorAll('.feature-card');
    if (!('IntersectionObserver' in window)) {
        cards.forEach(c => { c.style.opacity = '1'; c.style.transform = 'none'; });
        return;
    }
    cards.forEach((card, i) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(24px)';
        card.style.transition = `opacity 0.55s ease ${i * 0.09}s, transform 0.55s ease ${i * 0.09}s`;
    });

    const observer = new IntersectionObserver(entries => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.15 });

    cards.forEach(card => observer.observe(card));
});


// ── Toast helper ─────────────────────────────────────────────
function showToast(message, duration = 3000) {
    const toast = document.getElementById('toast');
    if (!toast) return;
    toast.textContent = message;
    toast.classList.add('show');
    clearTimeout(toast._timer);
    toast._timer = setTimeout(() => toast.classList.remove('show'), duration);
}


// ── Form handlers ─────────────────────────────────────────────
async function handleLogin(e) {
    e.preventDefault();

    if (loginRequestInFlight) {
        return;
    }

    const form = e.currentTarget || e.target;
    const submitBtn = form?.querySelector('button[type="submit"]');
    const originalBtnText = submitBtn?.textContent || 'Login';

    const identifier = document.getElementById('loginIdentifier')?.value.trim() || '';
    const password = document.getElementById('loginPassword')?.value || '';

    if (!identifier || !password) {
        showToast('⚠ Enter your username/gmail and password.');
        return;
    }

    loginRequestInFlight = true;
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = 'Logging in...';
    }

    try {
        const res = await fetchWithFallback('/auth/signin', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: identifier, gmail: identifier, password }),
        });

        if (res.status === 429) {
            showToast('⚠ Too many login attempts. Please wait and try again.');
            return;
        }

        const payload = await res.json();
        if (!res.ok || !payload.success) {
            showToast(`⚠ ${payload.error || 'Login failed'}`);
            return;
        }

        setSessionToken(payload.token || '');
        updateAuthUi(true);
        closeAllDropdowns();
        showToast('✓ Logged in successfully!');
        e.target.reset();
    } catch (_err) {
        showToast('⚠ Login failed. Please try again.');
    } finally {
        loginRequestInFlight = false;
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.textContent = originalBtnText;
        }
    }
}

async function handleSignup(e) {
    e.preventDefault();

    const username = document.getElementById('signupUsername')?.value.trim() || '';
    const gmail = document.getElementById('signupEmail')?.value.trim() || '';
    const password = document.getElementById('signupPassword')?.value || '';
    const confirmPassword = document.getElementById('signupConfirmPassword')?.value || '';
    const githubToken = document.getElementById('signupGithubToken')?.value.trim() || '';

    if (password !== confirmPassword) {
        showToast('⚠ Passwords do not match. Please try again.');
        return;
    }

    try {
        const res = await fetchWithFallback('/auth/signup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                username,
                gmail,
                password,
                github_token: githubToken,
            }),
        });

        if (res.status === 429) {
            showToast('⚠ Too many signup attempts. Please wait and try again.');
            return;
        }

        const raw = await res.text();
        let payload = {};
        try {
            payload = raw ? JSON.parse(raw) : {};
        } catch (_parseErr) {
            payload = { error: raw || 'Unexpected response from server' };
        }

        if (!res.ok || !payload.success) {
            showToast(`⚠ ${payload.error || 'Signup failed'}`);
            return;
        }

        setSessionToken(payload.token || '');
        updateAuthUi(true);
        closeAllDropdowns();
        showToast('🎉 Account created and logged in.');
        e.target.reset();
    } catch (err) {
        showToast(`⚠ Signup failed: ${err.message || 'Please try again.'}`);
    }
}

async function handleTokenUpdate(e) {
    e.preventDefault();

    const token = getSessionToken();
    if (!token) {
        showToast('⚠ Please login first.');
        return;
    }

    const githubToken = document.getElementById('updateGithubToken')?.value.trim() || '';
    if (!githubToken) {
        showToast('⚠ Enter a GitHub token first.');
        return;
    }

    try {
        const res = await fetchWithFallback('/auth/github-token', {
            method: 'PUT',
            headers: authHeaders(),
            body: JSON.stringify({ github_token: githubToken }),
        });

        if (res.status === 429) {
            showToast('⚠ Too many requests. Please wait and try again.');
            return;
        }

        const payload = await res.json();
        if (!res.ok || !payload.success) {
            showToast(`⚠ ${payload.error || 'Token update failed'}`);
            return;
        }

        closeAllDropdowns();
        showToast('✓ GitHub token updated securely.');
        e.target.reset();
    } catch (_err) {
        showToast('⚠ Token update failed. Please try again.');
    }
}

function handleLogout() {
    setSessionToken('');
    updateAuthUi(false);
    closeAllDropdowns();
    showToast('✓ Logged out successfully.');
}

async function handleContact(e) {
    e.preventDefault();
    const form = e.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn ? submitBtn.textContent : 'Send Message';
    
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = 'Sending...';
    }
    
    try {
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());
        
        const res = await fetchWithFallback('/contact', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (res.status === 429) {
            showToast('⚠ Too many contact requests. Please wait and try again.');
            return;
        }

        const payload = await res.json();
        if (res.ok && payload.success) {
            showToast('✉ Message sent! We\'ll be in touch soon.');
            form.reset();
        } else {
            showToast(`⚠ ${payload.error || 'Failed to send message'}`);
        }
    } catch (_err) {
        showToast('⚠ Error sending message. Please try again.');
    } finally {
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        }
    }
}

// ── Smooth scroll for anchor links ───────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                e.preventDefault();
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                // Close mobile menu if open
                document.getElementById('mobileMenu')?.classList.remove('open');
                document.getElementById('hamburger')?.classList.remove('open');
            }
        });
    });
});
