export function getCsrfToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]').value;
}

export function apiRequest(url, method = "GET", body = null) {
    const headers = {
        "Content-Type": "application/json",
        "X-CSRFToken": getCsrfToken(),
        "Authorization": `Api-Key ${document.querySelector('meta[name="api-key"]').getAttribute("content")}`,
    };

    return fetch(url, {
        method,
        headers,
        body: body ? JSON.stringify(body) : null,
    }).then((response) => {
        if (!response.ok) {
            return response.text().then((text) => {
                throw new Error(`API request failed: ${text}`);
            });
        }

        // Handle 204 No Content explicitly
        if (response.status === 204) {
            return null; // Return null explicitly for 204 responses
        }

        // Return JSON for all other successful responses
        return response.json();
    });
}