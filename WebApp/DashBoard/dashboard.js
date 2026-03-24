const API_BASE = window.location.hostname.endsWith('vercel.app')
    ? 'https://bob-ai-1.onrender.com'
    : '';
const AUTH_STORAGE_KEY = 'bobai_session_token';
const profileState = {
    authenticated: false,
    hasSavedGithubToken: false,
};

function getSessionToken() {
    return localStorage.getItem(AUTH_STORAGE_KEY) || '';
}

function authHeaders() {
    const token = getSessionToken();
    const base = { 'Content-Type': 'application/json' };
    if (!token) return base;
    return { ...base, Authorization: `Bearer ${token}` };
}

function setMetric(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
}

function setResult(content, statusClass = '') {
    const container = document.getElementById('resultContent');
    if (!container) return;
    container.className = `result-content ${statusClass}`.trim();
    container.textContent = content;
}

function truncateText(value, maxLen = 70) {
    if (!value) return 'Untitled website request';
    return value.length > maxLen ? `${value.slice(0, maxLen - 3)}...` : value;
}

function escapeHtml(value) {
    return String(value || '')
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#39;');
}

function renderHistory(history) {
    const list = document.getElementById('historyList');
    if (!list) return;

    if (!Array.isArray(history) || history.length === 0) {
        list.innerHTML = '<p class="history-empty">No history yet.</p>';
        return;
    }

    list.innerHTML = history.map((item) => {
        const title = escapeHtml(truncateText(item.description));
        const when = item.created_at ? new Date(item.created_at).toLocaleString() : 'Unknown date';
        const structure = escapeHtml(item.structure_type || 'unknown');
        const projectType = escapeHtml(item.project_type || 'unknown');
        const repoUrl = item.repo_url || '';
        const safeWhen = escapeHtml(when);
        const repoAnchor = repoUrl
            ? `<a class="history-link" href="${escapeHtml(repoUrl)}" target="_blank" rel="noopener noreferrer">Open repository</a>`
            : '';

        return `
            <article class="history-item">
                <p class="history-title">${title}</p>
                <p class="history-meta">${safeWhen}</p>
                <p class="history-meta">${projectType} | ${structure} | ${item.file_count || 0} files</p>
                ${repoAnchor}
            </article>
        `;
    }).join('');
}

function setProfileSummary(user, historyCount) {
    const summary = document.getElementById('profileSummary');
    if (!summary) return;

    if (!user) {
        summary.textContent = 'Login to view your profile and website history.';
        return;
    }

    const tokenLabel = user.has_github_token ? 'token saved' : 'token not saved';
    summary.textContent = `${user.username || 'User'} | ${historyCount} websites | ${tokenLabel}`;
}

function setTokenFieldHint() {
    const help = document.getElementById('githubTokenHelp');
    const tokenInput = document.getElementById('githubToken');
    if (!help || !tokenInput) return;

    if (profileState.authenticated && profileState.hasSavedGithubToken) {
        help.textContent = 'Token found in your account. You can leave this field empty.';
        tokenInput.placeholder = 'Using saved token from your account';
    } else {
        help.textContent = 'Required if no saved token exists in your account.';
        tokenInput.placeholder = 'ghp_xxxxxxxxx';
    }
}

async function hydrateProfile() {
    const token = getSessionToken();
    if (!token) {
        profileState.authenticated = false;
        profileState.hasSavedGithubToken = false;
        setProfileSummary(null, 0);
        renderHistory([]);
        setTokenFieldHint();
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/auth/profile`, {
            method: 'GET',
            headers: authHeaders(),
        });

        const payload = await res.json();
        if (!res.ok || !payload.success) {
            profileState.authenticated = false;
            profileState.hasSavedGithubToken = false;
            setProfileSummary(null, 0);
            renderHistory([]);
            setTokenFieldHint();
            return;
        }

        const history = Array.isArray(payload.history) ? payload.history : [];
        profileState.authenticated = true;
        profileState.hasSavedGithubToken = Boolean(payload.user?.has_github_token);
        setProfileSummary(payload.user || null, history.length);
        renderHistory(history);
        setMetric('authMetric', payload.user?.username || 'Logged In');
        setTokenFieldHint();
    } catch (_err) {
        profileState.authenticated = false;
        profileState.hasSavedGithubToken = false;
        setProfileSummary(null, 0);
        renderHistory([]);
        setTokenFieldHint();
    }
}

async function hydrateAuthState() {
    const token = getSessionToken();
    if (!token) {
        setMetric('authMetric', 'Guest');
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/auth/me`, {
            method: 'GET',
            headers: authHeaders(),
        });

        const payload = await res.json();
        if (!res.ok || !payload.success) {
            setMetric('authMetric', 'Guest');
            return;
        }

        setMetric('authMetric', payload.user?.username || 'Logged In');
    } catch (_err) {
        setMetric('authMetric', 'Guest');
    }
}

function normalizeValue(formData, key) {
    return (formData.get(key) || '').toString().trim();
}

function collectPayload(form) {
    const formData = new FormData(form);
    return {
        description: normalizeValue(formData, 'description'),
        type: normalizeValue(formData, 'type') || 'vanilla',
        website_type: normalizeValue(formData, 'website_type') || '',
        company_name: normalizeValue(formData, 'company_name'),
        tagline: normalizeValue(formData, 'tagline'),
        primary_color: normalizeValue(formData, 'primary_color') || '#ffffff',
        secondary_color: normalizeValue(formData, 'secondary_color') || '#a0a0a0',
        github_token: normalizeValue(formData, 'github_token'),
        instagram: normalizeValue(formData, 'instagram'),
        twitter: normalizeValue(formData, 'twitter'),
        linkedin: normalizeValue(formData, 'linkedin'),
        facebook: normalizeValue(formData, 'facebook'),
        youtube: normalizeValue(formData, 'youtube'),
        email: normalizeValue(formData, 'email'),
        phone: normalizeValue(formData, 'phone'),
        address: normalizeValue(formData, 'address'),
        city: normalizeValue(formData, 'city'),
        state: normalizeValue(formData, 'state'),
        save_token: formData.get('save_token') === 'on',
    };
}

function validatePayload(payload) {
    if (!payload.description) return 'Website description is required.';
    if (!payload.company_name) return 'Company name is required.';
    if (!payload.github_token && !profileState.hasSavedGithubToken) {
        return 'GitHub Access Token is required because no saved token was found.';
    }
    return '';
}

function formatSuccessResponse(payload) {
    const lines = [
        `Status: Success`,
        `Project Type: ${payload.project_type || 'n/a'}`,
        `Files Generated: ${payload.file_count ?? 'n/a'}`,
    ];

    if (payload.github?.repo_url) {
        lines.push(`Repository URL: ${payload.github.repo_url}`);
    }

    if (payload.structure?.type) {
        lines.push(`Detected Structure: ${payload.structure.type}`);
    }

    lines.push(`Message: ${payload.message || 'Website generated and pushed.'}`);
    return lines.join('\n');
}

async function onSubmitForm(event) {
    event.preventDefault();

    const form = event.target;
    const submitBtn = document.getElementById('submitBtn');
    const payload = collectPayload(form);
    const validationError = validatePayload(payload);

    if (validationError) {
        setResult(`Status: Failed\nReason: ${validationError}`, 'status-error');
        setMetric('resultMetric', 'Failed');
        return;
    }

    setMetric('modeMetric', payload.type === 'react' ? 'React' : 'Vanilla');
    setMetric('resultMetric', 'Running');
    setResult('Starting generation and GitHub push...', '');

    submitBtn.disabled = true;
    submitBtn.textContent = 'Running...';

    try {
        const res = await fetch(`${API_BASE}/generate-and-deploy`, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify(payload),
        });

        const data = await res.json();
        if (!res.ok || !data.success) {
            setMetric('resultMetric', 'Failed');
            setResult(`Status: Failed\nReason: ${data.error || 'Unknown error from API.'}`, 'status-error');
            return;
        }

        setMetric('resultMetric', 'Success');
        setResult(formatSuccessResponse(data), 'status-success');
        hydrateProfile();
    } catch (_err) {
        setMetric('resultMetric', 'Failed');
        setResult('Status: Failed\nReason: Unable to reach backend service.', 'status-error');
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Generate and Push to GitHub';
    }
}

function initTypeMetric() {
    const typeEl = document.getElementById('projectType');
    if (!typeEl) return;

    setMetric('modeMetric', typeEl.value === 'react' ? 'React' : 'Vanilla');
    typeEl.addEventListener('change', () => {
        setMetric('modeMetric', typeEl.value === 'react' ? 'React' : 'Vanilla');
    });
}

function initLogout() {
    const button = document.getElementById('logoutBtn');
    if (!button) return;

    button.addEventListener('click', () => {
        localStorage.removeItem(AUTH_STORAGE_KEY);
        profileState.authenticated = false;
        profileState.hasSavedGithubToken = false;
        setMetric('authMetric', 'Guest');
        setResult('Session cleared. You are logged out from this browser.', '');
        setProfileSummary(null, 0);
        renderHistory([]);
        setTokenFieldHint();
    });
}

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('dashboardForm');
    if (form) {
        form.addEventListener('submit', onSubmitForm);
    }

    initTypeMetric();
    initLogout();
    setTokenFieldHint();
    hydrateAuthState();
    hydrateProfile();
});
