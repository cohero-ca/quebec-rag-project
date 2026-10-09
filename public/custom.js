// 1. INJECT FLOATING LOGO
document.addEventListener("DOMContentLoaded", () => {
    const injectLogo = () => {
        if (!document.getElementById('floating-cohero-logo')) {
            const logo = document.createElement("img");
            logo.id = 'floating-cohero-logo';
            logo.src = "/logo"; 
            logo.alt = "Cohero";
            logo.classList.add("floating-logo");
            document.body.appendChild(logo);
        }
    };
    injectLogo();
    setTimeout(injectLogo, 1000); 
});

// 2. INJECT PROXY VAULT BUTTON
const injectVaultBtn = () => {
    if (!document.getElementById('custom-vault-btn')) {
        const vaultBtn = document.createElement('button');
        vaultBtn.id = 'custom-vault-btn';
        vaultBtn.innerText = '📂 Vault';
        
        vaultBtn.style.position = 'fixed';
        vaultBtn.style.top = '14px';
        vaultBtn.style.right = '120px'; 
        vaultBtn.style.zIndex = '99999';
        vaultBtn.style.backgroundColor = '#004daa';
        vaultBtn.style.color = '#ffffff';
        vaultBtn.style.border = 'none';
        vaultBtn.style.borderRadius = '8px';
        vaultBtn.style.padding = '8px 16px';
        vaultBtn.style.fontWeight = '600';
        vaultBtn.style.fontSize = '14px';
        vaultBtn.style.cursor = 'pointer';
        vaultBtn.style.boxShadow = '0 4px 12px rgba(0,0,0,0.2)';
        vaultBtn.style.transition = 'all 0.2s ease';
        
        vaultBtn.onmouseover = () => {
            vaultBtn.style.backgroundColor = '#e57200';
            vaultBtn.style.transform = 'translateY(-2px)';
        };
        vaultBtn.onmouseout = () => {
            vaultBtn.style.backgroundColor = '#004daa';
            vaultBtn.style.transform = 'translateY(0)';
        };

        // BULLETPROOF SEND LOGIC
        vaultBtn.onclick = () => {
            // Strategy 1: Attempt to click the native hidden action
            const hiddenAction = document.querySelector('button[id*="manage_vault"], button[id*="action-manage_vault"]');
            if (hiddenAction) {
                hiddenAction.click();
            } else {
                // Strategy 2: Force the React chat input to fire
                const input = document.getElementById('chat-input');
                if (input) {
                    input.focus();
                    const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value").set;
                    nativeSetter.call(input, '/vault');
                    input.dispatchEvent(new Event('input', { bubbles: true })); // Un-disables the send button
                    
                    setTimeout(() => {
                        const sendBtn = document.querySelector('#ask-button:not([disabled]), button[type="submit"]:not([disabled])');
                        if (sendBtn) sendBtn.click();
                    }, 50);
                }
            }
        };
        document.body.appendChild(vaultBtn);
    }
};

// 3. ENFORCE UI OVERRIDES & DOM CLEANER
setInterval(() => {
    injectVaultBtn();

    const textarea = document.getElementById('chat-input');
    const newText = "💡 Type a general question or drag & drop files 📂 (ex: contract, policy) to receive answers about your own policy.";
    if (textarea && textarea.placeholder !== newText) {
        textarea.placeholder = newText;
        textarea.style.setProperty('--placeholder-size', '14px');
    }

    const avatar = document.querySelector('header span[class*="AvatarFallback"]');
    if (avatar && avatar.innerText !== '👑') {
        avatar.innerText = '👑';
        avatar.style.fontSize = '20px';
    }

    // SCRUBBER: Make sure the raw /vault text bubble is never seen
    document.querySelectorAll('.cl-message-content').forEach(el => {
        if (el.innerText.trim() === '/vault') {
            const step = el.closest('.step');
            if (step) step.style.display = 'none';
        }
    });
}, 200); 
