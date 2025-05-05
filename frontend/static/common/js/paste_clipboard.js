function pasteFromClipboard(elementId) {
    const inputField = document.getElementById(elementId);

    if (navigator.clipboard) {
        navigator.clipboard.readText()
            .then(text => {
                inputField.value = text;
            })
            .catch(err => {
                console.error("Failed to paste from clipboard:", err);
                alert(`Unable to paste address from clipboard. Error: ${err}`);
            });
    } else {
        alert("Clipboard API not supported by your browser.");
    }
}