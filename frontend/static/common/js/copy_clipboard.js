function copyToClipboard(elementId) {
    const el = document.getElementById(elementId);
    if (!el) {
        console.warn(`Element with ID '${elementId}' not found.`);
        return;
    }

    // Temporarily remove readonly to allow selection
    const wasReadOnly = el.hasAttribute('readonly');
    if (wasReadOnly) el.removeAttribute('readonly');

    el.select();
    el.setSelectionRange(0, 99999); // For mobile devices

    try {
        const successful = document.execCommand('copy');
        if (successful) {
            console.log("Copied to clipboard");
            // Optionally, show feedback
            alert("Copied!");
        } else {
            console.error("Copy failed");
        }
    } catch (err) {
        console.error("Copy command failed", err);
    }

    // Restore readonly state
    if (wasReadOnly) el.setAttribute('readonly', 'readonly');

    // Deselect text
    window.getSelection().removeAllRanges();
}