// core/static/core/api.js

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

async function apiFetch(url, options = {}) {
    const csrftoken = getCookie('csrftoken');
    options.headers = options.headers || {};
    if (!options.headers['Content-Type'] && !(options.body instanceof FormData)) {
        options.headers['Content-Type'] = 'application/json';
    }
    if (!options.headers['X-CSRFToken']) {
        options.headers['X-CSRFToken'] = csrftoken;
    }
    // Optionally add token auth if available
    const token = localStorage.getItem('apiToken');
    if (token) {
        options.headers['Authorization'] = 'Token ' + token;
    }
    const response = await fetch(url, options);
    if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw { status: response.status, ...error };
    }
    if (response.status !== 204) {
        return response.json();
    }
    return null;
}

export { apiFetch }; 