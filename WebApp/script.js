/* ============================================================
   BobAI — Interactive UI Logic
   ============================================================ */

// ── Dropdown management ──────────────────────────────────────
const DROPDOWN_IDS = ['loginDropdown', 'signupDropdown', 'tokenDropdown'];
const API_BASE = window.location.hostname.endsWith('vercel.app')
    ? 'https://bob-ai-1.onrender.com'
    : '';
const AUTH_STORAGE_KEY = 'bobai_session_token';

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

    if (loginBtn) loginBtn.style.display = isLoggedIn ? 'none' : '';
    if (signupBtn) signupBtn.style.display = isLoggedIn ? 'none' : '';
    if (accountBtn) accountBtn.style.display = isLoggedIn ? '' : 'none';
}

async function hydrateSession() {
    const token = getSessionToken();
    if (!token) {
        updateAuthUi(false);
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/auth/me`, {
            method: 'GET',
            headers: authHeaders(),
        });
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

    const identifier = document.getElementById('loginIdentifier')?.value.trim() || '';
    const password = document.getElementById('loginPassword')?.value || '';

    if (!identifier || !password) {
        showToast('⚠ Enter your username/gmail and password.');
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: identifier, gmail: identifier, password }),
        });

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
        const res = await fetch(`${API_BASE}/auth/signup`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                username,
                gmail,
                password,
                github_token: githubToken,
            }),
        });

        const payload = await res.json();
        if (!res.ok || !payload.success) {
            showToast(`⚠ ${payload.error || 'Signup failed'}`);
            return;
        }

        setSessionToken(payload.token || '');
        updateAuthUi(true);
        closeAllDropdowns();
        showToast('🎉 Account created and logged in.');
        e.target.reset();
    } catch (_err) {
        showToast('⚠ Signup failed. Please try again.');
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
        const res = await fetch(`${API_BASE}/auth/github-token`, {
            method: 'PUT',
            headers: authHeaders(),
            body: JSON.stringify({ github_token: githubToken }),
        });

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

function handleContact(e) {
    e.preventDefault();
    e.target.reset();
    showToast('✉ Message sent! We\'ll be in touch soon.');
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
