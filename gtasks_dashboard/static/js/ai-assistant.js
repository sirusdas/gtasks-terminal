/**
 * GTasks AI Assistant Client Module
 * Provides floating sparkle button, slide-out chat drawer,
 * Gemini chat execution with tools, interactive task cards, and 1-command workflows.
 */

let currentSessionId = 'session_' + Date.now();
let isAiSending = false;

// Inject CSS styles for AI Assistant
function injectAiStyles() {
    if (document.getElementById('ai-assistant-styles')) return;
    const style = document.createElement('style');
    style.id = 'ai-assistant-styles';
    style.textContent = `
        /* Floating Action Button */
        .ai-fab-btn {
            position: fixed;
            bottom: 24px;
            right: 24px;
            width: 54px;
            height: 54px;
            border-radius: 50%;
            background: linear-gradient(135deg, #3b82f6, #8b5cf6, #ec4899);
            color: #ffffff;
            border: none;
            box-shadow: 0 4px 15px rgba(139, 92, 246, 0.4);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.4rem;
            z-index: 999;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .ai-fab-btn:hover {
            transform: scale(1.08) translateY(-2px);
            box-shadow: 0 8px 25px rgba(139, 92, 246, 0.6);
        }

        /* Slide-out Drawer */
        .ai-drawer-overlay {
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0, 0, 0, 0.5);
            backdrop-filter: blur(2px);
            z-index: 1040;
            display: none;
            transition: opacity 0.3s ease;
        }
        .ai-drawer {
            position: fixed;
            top: 0;
            right: -480px;
            width: 460px;
            max-width: 95vw;
            height: 100vh;
            background: #0f172a;
            border-left: 1px solid #1e293b;
            box-shadow: -10px 0 30px rgba(0, 0, 0, 0.6);
            z-index: 1050;
            display: flex;
            flex-direction: column;
            transition: right 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .ai-drawer.open {
            right: 0;
        }

        /* Drawer Header */
        .ai-header {
            padding: 1rem 1.25rem;
            background: #1e293b;
            border-bottom: 1px solid #334155;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .ai-title-wrap {
            display: flex;
            flex-direction: column;
            gap: 2px;
        }
        .ai-title {
            font-weight: 700;
            font-size: 1.1rem;
            color: #f8fafc;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .ai-meta-pills {
            display: flex;
            gap: 6px;
            font-size: 0.72rem;
            margin-top: 2px;
        }
        .ai-pill {
            padding: 1px 7px;
            border-radius: 10px;
            background: #334155;
            color: #94a3b8;
            border: 1px solid #475569;
        }
        .ai-header-actions {
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .ai-btn-icon {
            background: transparent;
            border: none;
            color: #94a3b8;
            font-size: 1rem;
            padding: 6px;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .ai-btn-icon:hover {
            color: #f8fafc;
            background: #334155;
        }

        /* Workflows Bar */
        .ai-workflows-bar {
            padding: 0.6rem 1rem;
            background: #141e33;
            border-bottom: 1px solid #1e293b;
            display: flex;
            gap: 6px;
            overflow-x: auto;
            white-space: nowrap;
            scrollbar-width: none;
        }
        .ai-wf-chip {
            background: #1e293b;
            color: #cbd5e1;
            border: 1px solid #334155;
            padding: 4px 10px;
            border-radius: 14px;
            font-size: 0.75rem;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 4px;
            transition: all 0.2s;
        }
        .ai-wf-chip:hover {
            background: #3b82f6;
            color: #ffffff;
            border-color: #60a5fa;
            transform: translateY(-1px);
        }

        /* Messages Container */
        .ai-messages-container {
            flex: 1;
            overflow-y: auto;
            padding: 1rem;
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }
        .ai-msg {
            max-width: 88%;
            padding: 0.8rem 1rem;
            border-radius: 14px;
            font-size: 0.88rem;
            line-height: 1.5;
            word-break: break-word;
        }
        .ai-msg-user {
            align-self: flex-end;
            background: linear-gradient(135deg, #2563eb, #1d4ed8);
            color: #ffffff;
            border-bottom-right-radius: 3px;
        }
        .ai-msg-assistant {
            align-self: flex-start;
            background: #1e293b;
            color: #e2e8f0;
            border: 1px solid #334155;
            border-bottom-left-radius: 3px;
        }

        /* Task Cards in Chat */
        .ai-task-card {
            background: #0f172a;
            border: 1px solid #334155;
            border-left: 3px solid #3b82f6;
            border-radius: 8px;
            padding: 0.6rem 0.8rem;
            margin-top: 0.5rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 8px;
        }
        .ai-task-info {
            display: flex;
            flex-direction: column;
            gap: 2px;
        }
        .ai-task-title {
            font-weight: 600;
            color: #f1f5f9;
            font-size: 0.84rem;
        }
        .ai-task-sub {
            font-size: 0.72rem;
            color: #94a3b8;
            display: flex;
            gap: 6px;
        }

        /* Input Area */
        .ai-input-wrap {
            padding: 0.8rem 1rem;
            background: #1e293b;
            border-top: 1px solid #334155;
            display: flex;
            align-items: flex-end;
            gap: 8px;
        }
        .ai-textarea {
            flex: 1;
            background: #0f172a;
            border: 1px solid #334155;
            color: #f8fafc;
            border-radius: 10px;
            padding: 0.6rem 0.8rem;
            font-size: 0.88rem;
            resize: none;
            max-height: 120px;
            outline: none;
            font-family: inherit;
        }
        .ai-textarea:focus {
            border-color: #3b82f6;
        }
        .ai-send-btn {
            background: #3b82f6;
            color: #ffffff;
            border: none;
            width: 38px;
            height: 38px;
            border-radius: 10px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
            flex-shrink: 0;
        }
        .ai-send-btn:hover:not(:disabled) {
            background: #2563eb;
            transform: scale(1.05);
        }
        .ai-send-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
    `;
    document.head.appendChild(style);
}

// Build and inject HTML DOM
function initAiAssistantDom() {
    injectAiStyles();

    // 1. Floating Action Button
    if (!document.getElementById('ai-fab-btn')) {
        const fab = document.createElement('button');
        fab.id = 'ai-fab-btn';
        fab.className = 'ai-fab-btn';
        fab.title = 'Open AI Assistant';
        fab.innerHTML = '<i class="fas fa-magic"></i>';
        fab.onclick = toggleAiChat;
        document.body.appendChild(fab);
    }

    // 2. Slide-out Drawer
    if (!document.getElementById('ai-chat-drawer')) {
        const overlay = document.createElement('div');
        overlay.id = 'ai-drawer-overlay';
        overlay.className = 'ai-drawer-overlay';
        overlay.onclick = toggleAiChat;
        document.body.appendChild(overlay);

        const drawer = document.createElement('div');
        drawer.id = 'ai-chat-drawer';
        drawer.className = 'ai-drawer';
        drawer.innerHTML = `
            <div class="ai-header">
                <div class="ai-title-wrap">
                    <div class="ai-title">
                        <i class="fas fa-sparkles" style="color: #a855f7;"></i>
                        <span>GTasks AI</span>
                    </div>
                    <div class="ai-meta-pills">
                        <span id="ai-model-pill" class="ai-pill">Gemini 1.5 Flash</span>
                        <span id="ai-scope-pill" class="ai-pill">Account: Work</span>
                    </div>
                </div>
                <div class="ai-header-actions">
                    <button class="ai-btn-icon" onclick="openAiSettings()" title="AI Settings">
                        <i class="fas fa-cog"></i>
                    </button>
                    <button class="ai-btn-icon" onclick="clearAiChat()" title="New Chat">
                        <i class="fas fa-plus"></i>
                    </button>
                    <button class="ai-btn-icon" onclick="toggleAiChat()" title="Close Drawer">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>

            <!-- Workflow Quick Chips -->
            <div class="ai-workflows-bar">
                <button class="ai-wf-chip" onclick="triggerWorkflow('morning')">
                    <span>☀️</span> Morning Plan
                </button>
                <button class="ai-wf-chip" onclick="triggerWorkflow('evening')">
                    <span>🌙</span> Evening Review
                </button>
                <button class="ai-wf-chip" onclick="triggerWorkflow('triage')">
                    <span>⚡</span> Triage Inbox
                </button>
                <button class="ai-wf-chip" onclick="promptBreakdown()">
                    <span>🔨</span> Breakdown Goal
                </button>
            </div>

            <!-- Messages List -->
            <div class="ai-messages-container" id="ai-messages-container">
                <div class="ai-msg ai-msg-assistant">
                    👋 <b>Hello! I am your GTasks AI Assistant.</b><br/>
                    I can search across your lists, filter spaces and sub-spaces, create tasks, and execute morning/evening workflows. How can I help you today?
                </div>
            </div>

            <!-- Input Wrap -->
            <div class="ai-input-wrap">
                <textarea id="ai-input-text" class="ai-textarea" rows="1" placeholder="Ask AI or type /morning, /triage..."></textarea>
                <button id="ai-send-btn" class="ai-send-btn" onclick="sendAiMessage()">
                    <i class="fas fa-paper-plane"></i>
                </button>
            </div>
        `;
        document.body.appendChild(drawer);

        // Auto-expand textarea & Enter key
        const textarea = document.getElementById('ai-input-text');
        textarea.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendAiMessage();
            }
        });
    }

    // 3. Settings Modal
    if (!document.getElementById('ai-settings-modal')) {
        const modal = document.createElement('div');
        modal.id = 'ai-settings-modal';
        modal.className = 'modal';
        modal.style.display = 'none';
        modal.innerHTML = `
            <div class="modal-dialog" style="max-width: 480px; background: #0f172a; border: 1px solid #334155; border-radius: 12px; color: #f8fafc; padding: 1.5rem;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <h3 style="margin: 0; font-size: 1.2rem; font-weight: 700; display: flex; align-items: center; gap: 8px;">
                        <i class="fas fa-robot" style="color: #3b82f6;"></i> AI Configuration
                    </h3>
                    <button class="ai-btn-icon" onclick="closeAiSettings()"><i class="fas fa-times"></i></button>
                </div>
                
                <div style="display: flex; flex-direction: column; gap: 1rem;">
                    <div>
                        <label style="font-size: 0.85rem; color: #94a3b8; display: block; margin-bottom: 4px;">AI Provider</label>
                        <select id="ai-config-provider" onchange="onAiProviderChanged()" style="width: 100%; padding: 8px; background: #1e293b; border: 1px solid #334155; color: #f8fafc; border-radius: 8px;">
                            <option value="gemini">Google Gemini (Recommended - Free)</option>
                            <option value="openai">OpenAI (GPT-4o / GPT-4o-mini)</option>
                            <option value="claude">Anthropic Claude</option>
                            <option value="local">Local LLM (Ollama / LM Studio)</option>
                        </select>
                    </div>

                    <div id="ai-key-group">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                            <label style="font-size: 0.85rem; color: #94a3b8;">API Key</label>
                            <a href="https://aistudio.google.com/app/apikey" target="_blank" style="font-size: 0.75rem; color: #60a5fa; text-decoration: underline;">
                                👉 Get Free Gemini Key (1-Tap)
                            </a>
                        </div>
                        <input type="password" id="ai-config-key" placeholder="AIzaSy..." style="width: 100%; padding: 8px; background: #1e293b; border: 1px solid #334155; color: #f8fafc; border-radius: 8px; font-family: monospace;">
                    </div>

                    <div id="ai-endpoint-group" style="display: none;">
                        <label style="font-size: 0.85rem; color: #94a3b8; display: block; margin-bottom: 4px;">Local Endpoint</label>
                        <input type="text" id="ai-config-endpoint" value="http://localhost:11434/v1" style="width: 100%; padding: 8px; background: #1e293b; border: 1px solid #334155; color: #f8fafc; border-radius: 8px;">
                    </div>

                    <div>
                        <label style="font-size: 0.85rem; color: #94a3b8; display: block; margin-bottom: 4px;">Model Name</label>
                        <input type="text" id="ai-config-model" value="gemini-1.5-flash" style="width: 100%; padding: 8px; background: #1e293b; border: 1px solid #334155; color: #f8fafc; border-radius: 8px;">
                    </div>
                </div>

                <div style="margin-top: 1.5rem; display: flex; justify-content: flex-end; gap: 8px;">
                    <button onclick="closeAiSettings()" class="btn-secondary-modal" style="padding: 8px 16px; border-radius: 8px; background: #334155; color: #f8fafc; border: none; cursor: pointer;">Cancel</button>
                    <button onclick="saveAiSettings()" class="btn-primary-modal" style="padding: 8px 16px; border-radius: 8px; background: #3b82f6; color: #ffffff; border: none; cursor: pointer; font-weight: 600;">Save Configuration</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }

    loadAiConfigBadge();
}

// Toggle Chat Drawer
window.toggleAiChat = function() {
    const drawer = document.getElementById('ai-chat-drawer');
    const overlay = document.getElementById('ai-drawer-overlay');
    if (!drawer) return;

    if (drawer.classList.contains('open')) {
        drawer.classList.remove('open');
        overlay.style.display = 'none';
    } else {
        drawer.classList.add('open');
        overlay.style.display = 'block';
        updateScopePill();
        document.getElementById('ai-input-text')?.focus();
    }
};

function updateScopePill() {
    const scopePill = document.getElementById('ai-scope-pill');
    if (scopePill) {
        const acc = window.currentAccount || 'Work';
        const spa = window.currentSpace || 'All';
        scopePill.textContent = `${acc} • ${spa}`;
    }
}

// Send Message
window.sendAiMessage = async function() {
    const input = document.getElementById('ai-input-text');
    const text = input.value.trim();
    if (!text || isAiSending) return;

    input.value = '';
    isAiSending = true;
    document.getElementById('ai-send-btn').disabled = true;

    // Append user message
    appendMessage('user', text);

    // Append loading assistant bubble
    const loadingId = 'ai-loading-' + Date.now();
    appendMessage('assistant', '<i class="fas fa-circle-notch fa-spin"></i> Thinking...', loadingId);

    try {
        const response = await fetch('/api/ai/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: text,
                session_id: currentSessionId,
                context: {
                    active_account: window.currentAccount || 'Work',
                    active_space: window.currentSpace || 'All',
                }
            })
        });

        const data = await response.json();
        const loadingEl = document.getElementById(loadingId);
        if (loadingEl) loadingEl.remove();

        if (data.success) {
            appendMessage('assistant', formatMarkdown(data.reply));
            // If tools modified data, trigger dashboard reload
            if (data.tool_calls && data.tool_calls.length > 0) {
                if (typeof window.refreshData === 'function') {
                    window.refreshData();
                }
            }
        } else {
            appendMessage('assistant', '⚠️ ' + (data.message || 'Error communicating with AI.'));
        }
    } catch (e) {
        const loadingEl = document.getElementById(loadingId);
        if (loadingEl) loadingEl.remove();
        appendMessage('assistant', '⚠️ Network error: ' + e.message);
    } finally {
        isAiSending = false;
        document.getElementById('ai-send-btn').disabled = false;
    }
};

// Workflows triggers
window.triggerWorkflow = function(name) {
    const input = document.getElementById('ai-input-text');
    input.value = '/' + name;
    sendAiMessage();
};

window.promptBreakdown = function() {
    const goal = prompt('Enter project or goal to break down into subtasks:');
    if (goal) {
        const input = document.getElementById('ai-input-text');
        input.value = `/breakdown ${goal}`;
        sendAiMessage();
    }
};

window.clearAiChat = function() {
    currentSessionId = 'session_' + Date.now();
    const container = document.getElementById('ai-messages-container');
    if (container) {
        container.innerHTML = `
            <div class="ai-msg ai-msg-assistant">
                🧹 <b>Chat cleared.</b><br/>Ready for your next questions or workflow!
            </div>
        `;
    }
};

function appendMessage(role, htmlContent, customId) {
    const container = document.getElementById('ai-messages-container');
    if (!container) return;

    const div = document.createElement('div');
    if (customId) div.id = customId;
    div.className = `ai-msg ai-msg-${role}`;
    div.innerHTML = htmlContent;

    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

function formatMarkdown(text) {
    if (!text) return '';
    return text
        .replace(/\*\*(.*?)\*\*/g, '<b>$1</b>')
        .replace(/\*(.*?)\*/g, '<i>$1</i>')
        .replace(/`([^`]+)`/g, '<code style="background:#0f172a;padding:2px 6px;border-radius:4px;font-size:0.82rem;">$1</code>')
        .replace(/\n/g, '<br/>');
}

// Settings Modal
window.openAiSettings = async function() {
    const modal = document.getElementById('ai-settings-modal');
    if (!modal) return;
    modal.style.display = 'flex';

    try {
        const res = await fetch('/api/ai/config');
        const data = await res.json();
        if (data.success && data.config) {
            document.getElementById('ai-config-provider').value = data.config.provider || 'gemini';
            document.getElementById('ai-config-model').value = data.config.model || 'gemini-1.5-flash';
            if (data.config.masked_key) {
                document.getElementById('ai-config-key').placeholder = data.config.masked_key;
            }
            onAiProviderChanged();
        }
    } catch (_) {}
};

window.closeAiSettings = function() {
    const modal = document.getElementById('ai-settings-modal');
    if (modal) modal.style.display = 'none';
};

window.onAiProviderChanged = function() {
    const prov = document.getElementById('ai-config-provider').value;
    const keyGrp = document.getElementById('ai-key-group');
    const endpointGrp = document.getElementById('ai-endpoint-group');
    const modelInput = document.getElementById('ai-config-model');

    if (prov === 'local') {
        keyGrp.style.display = 'none';
        endpointGrp.style.display = 'block';
        modelInput.value = 'llama3';
    } else {
        keyGrp.style.display = 'block';
        endpointGrp.style.display = 'none';
        if (prov === 'gemini') modelInput.value = 'gemini-1.5-flash';
        else if (prov === 'openai') modelInput.value = 'gpt-4o-mini';
        else if (prov === 'claude') modelInput.value = 'claude-3-5-sonnet';
    }
};

window.saveAiSettings = async function() {
    const provider = document.getElementById('ai-config-provider').value;
    const key = document.getElementById('ai-config-key').value.trim();
    const model = document.getElementById('ai-config-model').value.trim();
    const endpoint = document.getElementById('ai-config-endpoint').value.trim();

    const payload = { provider, model, local_endpoint: endpoint };
    if (key) payload.api_key = key;

    try {
        const res = await fetch('/api/ai/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.success) {
            alert('AI Configuration saved successfully!');
            closeAiSettings();
            loadAiConfigBadge();
        }
    } catch (e) {
        alert('Failed to save settings: ' + e.message);
    }
};

async function loadAiConfigBadge() {
    try {
        const res = await fetch('/api/ai/config');
        const data = await res.json();
        if (data.success && data.config) {
            const pill = document.getElementById('ai-model-pill');
            if (pill) {
                pill.textContent = data.config.model || data.config.provider;
            }
        }
    } catch (_) {}
}

// Auto initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAiAssistantDom);
} else {
    initAiAssistantDom();
}
