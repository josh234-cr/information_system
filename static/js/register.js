// Function to get CSRF token from cookies
function getCSRFToken() {
    const cookieValue = document.cookie
        .split("; ")
        .find(row => row.startsWith("csrftoken="))
        ?.split("=")[1];
    return cookieValue || "";
}

// Convert Base64 to Uint8Array
function base64ToArrayBuffer(base64) {
    const binaryString = atob(base64.replace(/-/g, "+").replace(/_/g, "/"));
    const bytes = new Uint8Array(binaryString.length);
    for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i);
    }
    return bytes;
}

// Convert ArrayBuffer to Base64
function arrayBufferToBase64(buffer) {
    return btoa(String.fromCharCode(...new Uint8Array(buffer)))
        .replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

// Start WebAuthn Registration
async function registerBegin() {
    // Extract full name from form
    const fullName = document.getElementById("full-name").value.trim();

    if (!fullName) {
        alert("Please enter your full name before scanning.");
        return;
    }

    try {
        const response = await fetch("/register/begin/", {
            method: "POST",
            headers: { "Content-Type": "application/json", "X-CSRFToken": getCSRFToken() },
            body: JSON.stringify({ username: fullName }),
        });

        if (!response.ok) throw new Error(`HTTP Error: ${response.status}`);

        const options = await response.json();
        console.log("Registration Options:", options);

        // Convert challenge and user ID to ArrayBuffer
        options.publicKey.challenge = base64ToArrayBuffer(options.publicKey.challenge);
        options.publicKey.user.id = base64ToArrayBuffer(options.publicKey.user.id);

        // Ensure passkey compatibility
        options.publicKey.authenticatorSelection = {
            authenticatorAttachment: "platform",
            residentKey: "required",
            userVerification: "required"
        };

        // Call WebAuthn API
        const credential = await navigator.credentials.create({ publicKey: options.publicKey });
        console.log("WebAuthn Credential:", credential);

        // Store credential data in hidden input field
        const credentialData = {
            id: credential.id,
            rawId: arrayBufferToBase64(credential.rawId),
            type: credential.type,
            response: {
                clientDataJSON: arrayBufferToBase64(credential.response.clientDataJSON),
                attestationObject: arrayBufferToBase64(credential.response.attestationObject)
            }
        };

        document.getElementById("fingerprint_data").value = JSON.stringify(credentialData);

        alert("Fingerprint registered successfully! You can now submit the form.");
        document.getElementById("register-button").disabled = false; // Enable submit button

    } catch (error) {
        console.error("Error during fingerprint capture:", error);
        alert("Fingerprint capture failed. Check console for details.");
    }
}

// Start WebAuthn Authentication
async function authBegin() {
    const fullName = document.getElementById("full-name").value.trim();

    if (!fullName) {
        alert("Please enter your full name.");
        return;
    }

    try {
        const response = await fetch("/begin/", {
            method: "POST",
            headers: { "Content-Type": "application/json", "X-CSRFToken": getCSRFToken() },
            body: JSON.stringify({ username: fullName }),
        });

        if (!response.ok) throw new Error(`HTTP Error: ${response.status}`);

        const options = await response.json();
        console.log("Authentication Options:", options);

        // Convert challenge and credential IDs to ArrayBuffer
        options.publicKey.challenge = base64ToArrayBuffer(options.publicKey.challenge);
        options.publicKey.allowCredentials = options.publicKey.allowCredentials.map(cred => ({
            id: base64ToArrayBuffer(cred.id),
            type: cred.type
        }));

        // Call WebAuthn API
        const assertion = await navigator.credentials.get({ publicKey: options.publicKey });
        console.log("WebAuthn Assertion:", assertion);

        // Send authentication response to the server
        const authData = {
            id: assertion.id,
            rawId: arrayBufferToBase64(assertion.rawId),
            type: assertion.type,
            response: {
                authenticatorData: arrayBufferToBase64(assertion.response.authenticatorData),
                clientDataJSON: arrayBufferToBase64(assertion.response.clientDataJSON),
                signature: arrayBufferToBase64(assertion.response.signature),
                userHandle: assertion.response.userHandle ? arrayBufferToBase64(assertion.response.userHandle) : null
            }
        };

        const completePayload = {
            username: fullName,
            credential: authData
        };

        const completeResponse = await fetch("/complete/", {
            method: "POST",
            headers: { "Content-Type": "application/json", "X-CSRFToken": getCSRFToken() },
            body: JSON.stringify(completePayload),
        });

        if (completeResponse.ok) {
            alert("Authentication successful!");
        } else {
            throw new Error("Authentication failed.");
        }
    } catch (error) {
        console.error("Error during authentication:", error);
        alert("Authentication failed. Check console for details.");
    }
}

// Attach event listener to Scan Fingerprint button
document.getElementById("scan-fingerprint").addEventListener("click", registerBegin);
