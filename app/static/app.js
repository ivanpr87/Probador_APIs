async function runTest() {
    const url = document.getElementById("url").value;
    const method = document.getElementById("method").value;
    const payloadText = document.getElementById("payload").value;

    let payload = {};

    try {
        payload = payloadText ? JSON.parse(payloadText) : {};
    } catch (e) {
        alert("JSON inválido");
        return;
    }

    const response = await fetch("/run-test", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            url,
            method,
            payload
        })
    });

    const data = await response.json();

    document.getElementById("result").textContent = JSON.stringify(data, null, 2);
}