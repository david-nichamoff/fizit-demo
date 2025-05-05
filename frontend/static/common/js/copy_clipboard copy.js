// static/js/balances.js
function copyToClipboard(elementId) {
    const element = document.getElementById(elementId);
    if (!element) {
        console.error("Element not found:", elementId);
        return;
    }

    const textToCopy = element.innerText || element.textContent;

    if (navigator.clipboard) {
        navigator.clipboard.writeText(textToCopy)
            .then(() => {
            })
            .catch(err => {
                console.error("Failed to copy:", err);
            });
    } else {
        const textarea = document.createElement("textarea");
        textarea.value = textToCopy;
        document.body.appendChild(textarea);
        textarea.select();
        try {
            document.execCommand('copy');
        } catch (err) {
            console.error("Fallback: Oops, unable to copy", err);
        }
        document.body.removeChild(textarea);
    }
}