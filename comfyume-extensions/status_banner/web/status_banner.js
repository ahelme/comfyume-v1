/**
 * Status Banner — ComfyuME
 *
 * Reusable floating status banner component.
 * Exposes window.comfyumeStatus for other extensions:
 *
 *   window.comfyumeStatus.show("Processing...", "#ffb74d")
 *   window.comfyumeStatus.hide(4000)
 *
 * Colors: cyan #4fc3f7, orange #ffb74d, green #66bb6a, red #ef5350
 */
import { app } from "../../scripts/app.js";

app.registerExtension({
    name: "comfy.statusBanner",

    async setup() {
        const banner = document.createElement('div');
        banner.id = 'comfyume-status-banner';
        banner.style.cssText = `
            position: fixed; top: 12px; left: 50%; transform: translateX(-50%);
            z-index: 99999; padding: 10px 20px; border-radius: 8px;
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 14px; font-weight: 500; color: #fff;
            background: #1a1a2e; border: 1px solid #333;
            box-shadow: 0 4px 12px rgba(0,0,0,0.5);
            display: none; transition: opacity 0.3s;
        `;
        document.body.appendChild(banner);

        let hideTimeout = null;

        window.comfyumeStatus = {
            show(message, color = '#4fc3f7') {
                if (hideTimeout) { clearTimeout(hideTimeout); hideTimeout = null; }
                banner.textContent = message;
                banner.style.borderColor = color;
                banner.style.display = 'block';
                banner.style.opacity = '1';
            },

            hide(delay = 3000) {
                hideTimeout = setTimeout(() => {
                    banner.style.opacity = '0';
                    setTimeout(() => { banner.style.display = 'none'; }, 300);
                    hideTimeout = null;
                }, delay);
            }
        };

        console.log("[StatusBanner] Ready — window.comfyumeStatus available");
    }
});
