/* ============================================================
   BobAI — Interactive UI Logic
   ============================================================ */

// ── Dropdown management ──────────────────────────────────────
const DROPDOWN_IDS = ['loginDropdown', 'signupDropdown'];

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
function handleLogin(e) {
    e.preventDefault();
    closeAllDropdowns();
    showToast('✓ Logged in successfully! Welcome back.');
}

function handleSignup(e) {
    e.preventDefault();
    const inputs = e.target.querySelectorAll('input[type="password"]');
    if (inputs.length >= 2 && inputs[0].value !== inputs[1].value) {
        showToast('⚠ Passwords do not match. Please try again.');
        return;
    }
    closeAllDropdowns();
    showToast('🎉 Account created! Welcome to BobAI.');
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
