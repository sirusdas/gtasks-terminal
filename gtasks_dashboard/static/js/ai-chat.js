/**
 * GTasks Dashboard - AI Assistant & Chat Bot
 * Full feature parity with mobile app:
 * - Active view context scoping & dynamic toggle banner
 * - Claude CLI-style interactive step-by-step Q&A Task Wizard
 * - Interactive Command Palette modal with instant search
 * - Command chaining (| or && or +)
 * - Scoped summary, earliest due, most urgent, bulk complete
 * - Grounded backend AI integration with Markdown rendering
 * - Keyboard shortcuts (Ctrl+Space, Ctrl+/, Escape)
 */

class AiChatController {
    constructor() {
        this.isOpen = false;
        this.isScopedToView = true;
        this.isProcessing = false;
        this.messages = [];
        this.history = [];
        this.historyIndex = -1;
        this.confirmingBulkComplete = false;
        
        // Claude CLI-style Task Creation Wizard
        this.wizardState = {
            step: 'none', // 'none' | 'title' | 'due' | 'priority' | 'space' | 'confirm'
            draft: {
                title: '',
                due: null,
                priority: 'medium',
                space: ''
            }
        };

        this.viewContext = {
            tasks: [],
            allTasks: [],
            filters: {},
            totalCount: 0,
            filteredCount: 0
        };

        this.init();
    }

    getBasePath() {
        return window.GTASKS_BASE_PATH || '';
    }

    init() {
        this.ensureDomElements();
        this.bindEvents();
        this.resetConversation();
        this.updateContextFromWindow();
    }

    ensureDomElements() {
        // If drawer container doesn't exist, inject it
        if (!document.getElementById('ai-chat-drawer')) {
            const drawerHtml = `
                <div class="ai-chat-backdrop" id="ai-chat-backdrop"></div>
                <aside class="ai-chat-drawer" id="ai-chat-drawer" aria-label="AI Assistant Drawer">
                    <!-- Drawer Header -->
                    <div class="ai-drawer-header">
                        <div class="ai-drawer-title-group">
                            <div class="ai-drawer-icon-wrap">
                                <i class="fas fa-sparkles"></i>
                            </div>
                            <div>
                                <div class="ai-drawer-title">GTasks AI Assistant</div>
                                <div class="ai-drawer-subtitle">Claude CLI Wizard • View Context-Aware</div>
                            </div>
                        </div>
                        <div class="ai-drawer-actions">
                            <button class="ai-header-btn" id="ai-drawer-palette-btn" title="Command Palette (/help)">
                                <i class="fas fa-terminal"></i>
                            </button>
                            <button class="ai-header-btn" id="ai-drawer-clear-btn" title="Clear Chat (/clear)">
                                <i class="fas fa-trash-alt"></i>
                            </button>
                            <button class="ai-header-btn" id="ai-drawer-close-btn" title="Close (Esc)">
                                <i class="fas fa-times"></i>
                            </button>
                        </div>
                    </div>

                    <!-- Context Scope Banner -->
                    <div class="ai-scope-banner" id="ai-scope-banner">
                        <div class="ai-scope-info">
                            <i class="fas fa-bullseye ai-scope-icon" id="ai-scope-icon"></i>
                            <div class="ai-scope-text-wrap">
                                <div class="ai-scope-badge-label" id="ai-scope-badge-label">VIEW SCOPE</div>
                                <div class="ai-scope-desc" id="ai-scope-desc">All Tasks • 0 tasks</div>
                            </div>
                        </div>
                        <button class="ai-scope-toggle-btn" id="ai-scope-toggle-btn">
                            <i class="fas fa-exchange-alt"></i> Switch to Global
                        </button>
                    </div>

                    <!-- Messages Scroll Area -->
                    <div class="ai-chat-messages" id="ai-chat-messages"></div>

                    <!-- Quick Suggestion Pills -->
                    <div class="ai-quick-pills" id="ai-quick-pills"></div>

                    <!-- Input Bar -->
                    <form class="ai-input-form" id="ai-input-form">
                        <div class="ai-input-wrapper">
                            <button type="button" class="ai-palette-trigger-btn" id="ai-palette-trigger-btn" title="Command Palette">
                                /
                            </button>
                            <textarea
                                class="ai-chat-input"
                                id="ai-chat-input"
                                placeholder="Ask AI about this view or type /help..."
                                rows="1"
                                autocomplete="off"
                            ></textarea>
                            <button type="submit" class="ai-chat-send-btn" id="ai-chat-send-btn" title="Send message">
                                <i class="fas fa-paper-plane"></i>
                            </button>
                        </div>
                    </form>
                </aside>

                <!-- Command Palette Modal -->
                <div class="ai-palette-backdrop" id="ai-palette-backdrop">
                    <div class="ai-palette-modal" id="ai-palette-modal">
                        <div class="ai-palette-header">
                            <i class="fas fa-search ai-palette-search-icon"></i>
                            <input
                                type="text"
                                class="ai-palette-input"
                                id="ai-palette-search"
                                placeholder="Search commands, wizards, or shortcuts..."
                                autocomplete="off"
                            />
                            <span class="ai-palette-esc-badge">ESC</span>
                        </div>
                        <div class="ai-palette-body" id="ai-palette-body">
                            <!-- Injected dynamically -->
                        </div>
                        <div class="ai-palette-footer">
                            <span><kbd>↑</kbd><kbd>↓</kbd> navigate</span>
                            <span><kbd>Enter</kbd> execute</span>
                            <span><kbd>Esc</kbd> close</span>
                        </div>
                    </div>
                </div>

                <!-- Floating Action Button (FAB) -->
                <button class="ai-assistant-fab" id="ai-assistant-fab" title="AI Assistant (Ctrl+Space)">
                    <i class="fas fa-sparkles"></i>
                    <span class="ai-fab-badge" id="ai-fab-badge" style="display: none;">0</span>
                </button>
            `;
            const container = document.createElement('div');
            container.id = 'ai-assistant-root';
            container.innerHTML = drawerHtml;
            document.body.appendChild(container);
        }
    }

    bindEvents() {
        const fab = document.getElementById('ai-assistant-fab');
        const backdrop = document.getElementById('ai-chat-backdrop');
        const closeBtn = document.getElementById('ai-drawer-close-btn');
        const clearBtn = document.getElementById('ai-drawer-clear-btn');
        const paletteBtn = document.getElementById('ai-drawer-palette-btn');
        const paletteTrigger = document.getElementById('ai-palette-trigger-btn');
        const scopeToggleBtn = document.getElementById('ai-scope-toggle-btn');
        const form = document.getElementById('ai-input-form');
        const input = document.getElementById('ai-chat-input');
        const paletteBackdrop = document.getElementById('ai-palette-backdrop');
        const paletteSearch = document.getElementById('ai-palette-search');

        fab?.addEventListener('click', () => this.toggleDrawer());
        backdrop?.addEventListener('click', () => this.closeDrawer());
        closeBtn?.addEventListener('click', () => this.closeDrawer());
        clearBtn?.addEventListener('click', () => this.resetConversation());
        paletteBtn?.addEventListener('click', () => this.openCommandPalette());
        paletteTrigger?.addEventListener('click', () => this.openCommandPalette());
        scopeToggleBtn?.addEventListener('click', () => this.toggleScope());
        
        paletteBackdrop?.addEventListener('click', (e) => {
            if (e.target === paletteBackdrop) this.closeCommandPalette();
        });

        paletteSearch?.addEventListener('input', (e) => {
            this.renderCommandPaletteItems(e.target.value);
        });

        paletteSearch?.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeCommandPalette();
            } else if (e.key === 'Enter') {
                const firstItem = document.querySelector('.ai-palette-item');
                if (firstItem) {
                    firstItem.click();
                }
            }
        });

        // Form submit
        form?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleSubmit();
        });

        // Auto-expand textarea & keyboard shortcuts
        input?.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.handleSubmit();
            } else if (e.key === 'ArrowUp') {
                if (this.history.length > 0 && input.selectionStart === 0) {
                    e.preventDefault();
                    if (this.historyIndex === -1) {
                        this.historyIndex = this.history.length - 1;
                    } else if (this.historyIndex > 0) {
                        this.historyIndex--;
                    }
                    input.value = this.history[this.historyIndex] || '';
                }
            } else if (e.key === 'ArrowDown') {
                if (this.historyIndex !== -1) {
                    e.preventDefault();
                    if (this.historyIndex < this.history.length - 1) {
                        this.historyIndex++;
                        input.value = this.history[this.historyIndex];
                    } else {
                        this.historyIndex = -1;
                        input.value = '';
                    }
                }
            } else if (e.key === '/' && input.value.trim() === '') {
                setTimeout(() => this.openCommandPalette(), 50);
            }
        });

        // Global shortcuts: Ctrl+Space or Ctrl+/ to toggle AI, Escape to close
        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey && e.code === 'Space') || (e.ctrlKey && e.key === '/')) {
                e.preventDefault();
                this.toggleDrawer();
            } else if (e.key === 'Escape') {
                if (this.isPaletteOpen()) {
                    this.closeCommandPalette();
                } else if (this.isOpen) {
                    this.closeDrawer();
                }
            }
        });

        // Header buttons hook
        const headerAiBtn = document.getElementById('header-ai-btn');
        headerAiBtn?.addEventListener('click', () => this.toggleDrawer());

        const tasksHeaderAiBtn = document.getElementById('tasks-header-ai-btn');
        tasksHeaderAiBtn?.addEventListener('click', () => this.toggleDrawer());

        const mobileHeaderAiBtn = document.getElementById('mobile-header-ai-btn');
        mobileHeaderAiBtn?.addEventListener('click', () => this.toggleDrawer());

        const navAiBtn = document.getElementById('nav-ai-chat');
        navAiBtn?.addEventListener('click', (e) => {
            e.preventDefault();
            this.openDrawer();
            if (typeof window.closeSidebarOnMobile === 'function') {
                window.closeSidebarOnMobile();
            }
        });
    }

    toggleDrawer() {
        if (this.isOpen) {
            this.closeDrawer();
        } else {
            this.openDrawer();
        }
    }

    openDrawer() {
        this.isOpen = true;
        this.updateContextFromWindow();
        const drawer = document.getElementById('ai-chat-drawer');
        const backdrop = document.getElementById('ai-chat-backdrop');
        drawer?.classList.add('open');
        backdrop?.classList.add('active');
        
        setTimeout(() => {
            document.getElementById('ai-chat-input')?.focus();
            this.scrollToBottom();
        }, 150);
    }

    closeDrawer() {
        this.isOpen = false;
        const drawer = document.getElementById('ai-chat-drawer');
        const backdrop = document.getElementById('ai-chat-backdrop');
        drawer?.classList.remove('open');
        backdrop?.classList.remove('active');
    }

    isPaletteOpen() {
        return document.getElementById('ai-palette-backdrop')?.classList.contains('active');
    }

    openCommandPalette() {
        const backdrop = document.getElementById('ai-palette-backdrop');
        const search = document.getElementById('ai-palette-search');
        if (search) search.value = '';
        this.renderCommandPaletteItems('');
        backdrop?.classList.add('active');
        setTimeout(() => search?.focus(), 100);
    }

    closeCommandPalette() {
        const backdrop = document.getElementById('ai-palette-backdrop');
        backdrop?.classList.remove('active');
        if (this.isOpen) {
            document.getElementById('ai-chat-input')?.focus();
        }
    }

    toggleScope() {
        this.isScopedToView = !this.isScopedToView;
        this.updateScopeBanner();
        
        const count = this.isScopedToView ? this.viewContext.filteredCount : this.viewContext.totalCount;
        const scopeName = this.isScopedToView ? 'Current View Scope' : 'Global Scope';
        
        this.addAssistantMessage({
            text: `🔄 **Switched to ${scopeName}** (${count} tasks).\n\nCommands like \`/summary\`, \`/urgent\`, and \`/these\` will now apply to ${this.isScopedToView ? 'only your visible filtered tasks' : 'all your tasks'}.`,
            chips: this.getDefaultQuickPills()
        });
    }

    updateContextFromWindow() {
        const tasks = window.currentFilteredTasks || window.dashboardData?.tasks || [];
        const allTasks = window.dashboardData?.tasks || window.allTasks || [];
        const filters = window.currentActiveFilters || {};

        this.onViewContextUpdated({
            tasks: tasks,
            allTasks: allTasks,
            filters: filters,
            totalCount: allTasks.length,
            filteredCount: tasks.length
        });
    }

    onViewContextUpdated(context) {
        this.viewContext = context;
        this.updateBadgeCounts();
        this.updateScopeBanner();
    }

    getFilterDescription() {
        const f = this.viewContext.filters || {};
        const parts = [];

        if (f.space) {
            parts.push(`Space: ${f.space}${f.subspace ? '/' + f.subspace : ''}`);
        } else if (f.spaces && f.spaces.length > 0) {
            parts.push(`Spaces: ${f.spaces.join(', ')}`);
        }

        if (f.tags && f.tags.length > 0) {
            parts.push(`Tags: ${f.tags.map(t => '#' + t).join(' ')}`);
        }

        if (f.priority) {
            parts.push(`Priority: ${f.priority.toUpperCase()}`);
        }

        if (f.search) {
            parts.push(`Search: "${f.search}"`);
        }

        if (f.status && f.status.length > 0) {
            parts.push(`Status: ${Array.isArray(f.status) ? f.status.join(', ') : f.status}`);
        }

        if (parts.length === 0) {
            return 'All Tasks';
        }

        return parts.join(' • ');
    }

    hasActiveFilters() {
        const f = this.viewContext.filters || {};
        return !!(f.space || (f.spaces && f.spaces.length) || (f.tags && f.tags.length) || f.priority || f.search || (f.status && f.status.length));
    }

    updateBadgeCounts() {
        const count = this.viewContext.filteredCount;
        const hasFilters = this.hasActiveFilters();
        const displayCount = hasFilters ? count : 0;
        const show = hasFilters && count > 0;

        ['ai-fab-badge', 'header-ai-badge', 'tasks-ai-badge', 'mobile-ai-badge', 'sidebar-ai-badge'].forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                el.textContent = displayCount;
                el.style.display = show ? 'inline-flex' : 'none';
            }
        });
    }

    updateScopeBanner() {
        const banner = document.getElementById('ai-scope-banner');
        const icon = document.getElementById('ai-scope-icon');
        const badgeLabel = document.getElementById('ai-scope-badge-label');
        const desc = document.getElementById('ai-scope-desc');
        const toggleBtn = document.getElementById('ai-scope-toggle-btn');
        if (!banner || !desc) return;

        const count = this.isScopedToView ? this.viewContext.filteredCount : this.viewContext.totalCount;
        const filterDesc = this.getFilterDescription();

        if (this.isScopedToView) {
            banner.classList.remove('global');
            if (icon) icon.className = 'fas fa-bullseye ai-scope-icon';
            if (badgeLabel) badgeLabel.textContent = 'VIEW SCOPE';
            desc.textContent = `${filterDesc} • ${count} task${count === 1 ? '' : 's'}`;
            if (toggleBtn) {
                toggleBtn.innerHTML = '<i class="fas fa-globe"></i> Switch to Global';
                toggleBtn.style.display = 'inline-flex';
            }
        } else {
            banner.classList.add('global');
            if (icon) icon.className = 'fas fa-globe ai-scope-icon';
            if (badgeLabel) badgeLabel.textContent = 'GLOBAL SCOPE';
            desc.textContent = `All Tasks • ${count} tasks`;
            if (toggleBtn) {
                toggleBtn.innerHTML = '<i class="fas fa-filter"></i> Switch to View';
                toggleBtn.style.display = this.hasActiveFilters() ? 'inline-flex' : 'none';
            }
        }
    }

    resetConversation() {
        this.messages = [];
        this.wizardState = { step: 'none', draft: { title: '', due: null, priority: 'medium', space: '' } };
        this.confirmingBulkComplete = false;

        const hasFilters = this.hasActiveFilters();
        const filterDesc = this.getFilterDescription();
        const count = this.viewContext.filteredCount;

        let welcomeText = `👋 **Hello! I'm your GTasks AI Assistant.**\n\n`;
        if (hasFilters) {
            welcomeText += `🎯 **Active View Scope:** I am currently scoped to **${filterDesc}** (**${count}** tasks visible).\n\n`;
            welcomeText += `You can ask questions about this view, run Claude CLI-style wizards, chain commands, or tap the quick pills below:`;
        } else {
            welcomeText += `🌐 **Global Scope:** Ready to manage all your tasks, deadlines, priorities, and spaces.\n\n`;
            welcomeText += `Type \`/help\` for commands, \`/wizard\` to add a task interactively, or ask a question in natural language:`;
        }

        this.addAssistantMessage({
            text: welcomeText,
            chips: this.getDefaultQuickPills()
        });
    }

    getDefaultQuickPills() {
        if (this.isScopedToView && this.hasActiveFilters()) {
            return [
                '📊 Summarize View',
                '⚡ Most Urgent',
                '⏰ Earliest Due',
                '🪄 Add Task Wizard',
                '✅ Done All',
                '🌐 Switch to Global',
                '📖 /help'
            ];
        } else {
            return [
                '📊 Summary',
                '⚡ High Priority',
                '⏰ Due Today',
                '🪄 Add Task Wizard',
                '⏳ Pending Tasks',
                '📖 /help'
            ];
        }
    }

    addUserMessage(text) {
        this.messages.push({
            id: 'msg-' + Date.now(),
            sender: 'user',
            text: text,
            timestamp: new Date()
        });
        this.renderMessages();
    }

    addAssistantMessage({ text, taskItems = [], chips = [], isError = false, wizardCard = null }) {
        this.messages.push({
            id: 'msg-' + Date.now(),
            sender: 'assistant',
            text: text,
            taskItems: taskItems,
            chips: chips,
            isError: isError,
            wizardCard: wizardCard,
            timestamp: new Date()
        });
        this.renderMessages();
        this.renderQuickPills(chips);
    }

    renderMessages() {
        const container = document.getElementById('ai-chat-messages');
        if (!container) return;

        container.innerHTML = '';
        this.messages.forEach(msg => {
            const row = document.createElement('div');
            row.className = `ai-message-row ${msg.sender}`;

            const avatar = document.createElement('div');
            avatar.className = `ai-message-avatar ${msg.sender}`;
            avatar.innerHTML = msg.sender === 'user' ? '<i class="fas fa-user"></i>' : '<i class="fas fa-sparkles"></i>';

            const bubble = document.createElement('div');
            bubble.className = `ai-message-bubble ${msg.sender} ${msg.isError ? 'error' : ''}`;

            // Markdown rendering
            const textEl = document.createElement('div');
            textEl.className = 'ai-markdown-content';
            if (window.marked && typeof window.marked.parse === 'function') {
                textEl.innerHTML = window.marked.parse(msg.text);
            } else {
                textEl.textContent = msg.text;
            }
            bubble.appendChild(textEl);

            // Task Cards if any
            if (msg.taskItems && msg.taskItems.length > 0) {
                const tasksContainer = document.createElement('div');
                tasksContainer.className = 'ai-task-card-list';
                msg.taskItems.forEach(t => {
                    tasksContainer.appendChild(this.createAiTaskCard(t));
                });
                bubble.appendChild(tasksContainer);
            }

            // Wizard Card if any
            if (msg.wizardCard) {
                bubble.appendChild(this.createWizardCard(msg.wizardCard));
            }

            row.appendChild(avatar);
            row.appendChild(bubble);
            container.appendChild(row);
        });

        this.scrollToBottom();
    }

    createAiTaskCard(task) {
        const card = document.createElement('div');
        card.className = `ai-task-item ${task.status === 'completed' ? 'completed' : ''}`;

        const isCompleted = task.status === 'completed';
        const prio = (task.calculated_priority || task.priority || 'medium').toLowerCase();
        const due = task.due ? task.due.substring(0, 10) : null;
        const spaces = task.spaces ? Object.keys(task.spaces).join(', ') : (task.space || '');

        card.innerHTML = `
            <div class="ai-task-item-header">
                <button class="ai-task-check-btn ${isCompleted ? 'checked' : ''}" title="${isCompleted ? 'Completed' : 'Mark Complete'}">
                    <i class="fas ${isCompleted ? 'fa-check' : 'fa-circle'}"></i>
                </button>
                <div class="ai-task-item-title ${isCompleted ? 'done' : ''}">${this.escapeHtml(task.title || 'Untitled')}</div>
            </div>
            <div class="ai-task-item-meta">
                ${spaces ? `<span class="ai-task-tag space"><i class="fas fa-layer-group"></i> ${this.escapeHtml(spaces)}</span>` : ''}
                <span class="ai-task-tag priority ${prio}">${prio.toUpperCase()}</span>
                ${due ? `<span class="ai-task-tag due"><i class="far fa-calendar-alt"></i> ${due}</span>` : ''}
            </div>
        `;

        const checkBtn = card.querySelector('.ai-task-check-btn');
        checkBtn?.addEventListener('click', async () => {
            if (!isCompleted) {
                await this.completeTask(task.id);
                checkBtn.classList.add('checked');
                checkBtn.innerHTML = '<i class="fas fa-check"></i>';
                card.classList.add('completed');
                card.querySelector('.ai-task-item-title')?.classList.add('done');
            }
        });

        return card;
    }

    createWizardCard(data) {
        const card = document.createElement('div');
        card.className = 'ai-wizard-card';

        card.innerHTML = `
            <div class="ai-wizard-header">
                <i class="fas fa-magic"></i> Task Summary Draft
            </div>
            <div class="ai-wizard-row">
                <span class="ai-wizard-label">Title</span>
                <span class="ai-wizard-val bold">${this.escapeHtml(data.title || 'Untitled')}</span>
            </div>
            <div class="ai-wizard-row">
                <span class="ai-wizard-label">Due Date</span>
                <span class="ai-wizard-val">${data.due ? `<span class="ai-task-tag due">${data.due}</span>` : '<span class="text-muted">None</span>'}</span>
            </div>
            <div class="ai-wizard-row">
                <span class="ai-wizard-label">Priority</span>
                <span class="ai-wizard-val"><span class="ai-task-tag priority ${(data.priority || 'medium').toLowerCase()}">${(data.priority || 'medium').toUpperCase()}</span></span>
            </div>
            <div class="ai-wizard-row">
                <span class="ai-wizard-label">Space</span>
                <span class="ai-wizard-val">${data.space ? `<span class="ai-task-tag space">${this.escapeHtml(data.space)}</span>` : '<span class="text-muted">None</span>'}</span>
            </div>
            <div class="ai-wizard-actions">
                <button class="ai-btn-primary" id="wizard-confirm-btn"><i class="fas fa-check"></i> Create Task</button>
                <button class="ai-btn-secondary" id="wizard-cancel-btn"><i class="fas fa-times"></i> Cancel</button>
            </div>
        `;

        card.querySelector('#wizard-confirm-btn')?.addEventListener('click', () => {
            this.handleQuery('confirm');
        });

        card.querySelector('#wizard-cancel-btn')?.addEventListener('click', () => {
            this.handleQuery('cancel');
        });

        return card;
    }

    renderQuickPills(chips) {
        const container = document.getElementById('ai-quick-pills');
        if (!container) return;

        container.innerHTML = '';
        const list = chips && chips.length > 0 ? chips : this.getDefaultQuickPills();

        list.forEach(chip => {
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'ai-pill-btn';
            btn.textContent = chip;
            btn.addEventListener('click', () => {
                this.handleQuery(chip);
            });
            container.appendChild(btn);
        });
    }

    scrollToBottom() {
        const container = document.getElementById('ai-chat-messages');
        if (container) {
            container.scrollTop = container.scrollHeight;
        }
    }

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    handleSubmit() {
        const input = document.getElementById('ai-chat-input');
        if (!input) return;

        const val = input.value.trim();
        if (!val) return;

        this.history.push(val);
        this.historyIndex = -1;
        input.value = '';
        this.handleQuery(val);
    }

    async handleQuery(rawQuery) {
        const query = rawQuery.trim();
        if (!query) return;

        this.addUserMessage(query);
        const qLower = query.toLowerCase().replace(/^[📊⚡⏰🪄✅🌐📖]\s*/, '').trim();

        // 1. Bulk complete confirmation
        if (this.confirmingBulkComplete) {
            this.confirmingBulkComplete = false;
            if (qLower.includes('confirm') || qLower.includes('yes') || qLower.includes('complete all') || qLower.includes('done all')) {
                await this.executeBulkComplete();
            } else {
                this.addAssistantMessage({
                    text: '🚫 **Bulk completion cancelled.** No tasks were modified.',
                    chips: this.getDefaultQuickPills()
                });
            }
            return;
        }

        // 2. Claude CLI Task Wizard Active Step
        if (this.wizardState.step !== 'none') {
            await this.handleWizardStep(query);
            return;
        }

        // 3. Wizard Trigger
        if (qLower === '/wizard' || qLower === '/new' || qLower === 'add task' || qLower === 'add task wizard' || qLower === 'create task' || qLower === 'new task') {
            this.startWizard();
            return;
        }

        // 4. Scope Toggling
        if (qLower === '/scope' || qLower === 'toggle scope' || qLower === 'switch scope' || qLower === 'switch to global' || qLower === 'switch to view') {
            this.toggleScope();
            return;
        }

        // 5. Command Palette Trigger
        if (qLower === '/help' || qLower === '/h' || qLower === 'help' || qLower === 'commands') {
            this.openCommandPalette();
            this.addAssistantMessage({
                text: '📖 **Opened Command Palette.** You can search or select any command, or pick from the quick suggestions below:',
                chips: this.getDefaultQuickPills()
            });
            return;
        }

        // 6. Clear Conversation
        if (qLower === '/clear' || qLower === 'clear') {
            this.resetConversation();
            return;
        }

        // 7. Bulk Complete Trigger
        if (qLower === '/doneall' || qLower === '/completeall' || qLower === 'done all' || qLower === 'complete all' || qLower === 'mark all done') {
            const targetTasks = this.getTargetTaskList().filter(t => t.status !== 'completed');
            if (targetTasks.length === 0) {
                this.addAssistantMessage({
                    text: '✨ **No pending tasks to complete in this scope!**',
                    chips: this.getDefaultQuickPills()
                });
            } else {
                this.confirmingBulkComplete = true;
                this.addAssistantMessage({
                    text: `⚠️ **Confirm Bulk Complete**\n\nAre you sure you want to mark all **${targetTasks.length}** visible pending tasks as completed?`,
                    chips: [`✅ Yes, Complete All (${targetTasks.length})`, '❌ Cancel']
                });
            }
            return;
        }

        // 8. Command Chaining (| or && or +)
        if (this.isChainedCommand(query)) {
            await this.handleChainedCommand(query);
            return;
        }

        // 9. Scoped Queries (/these, /summary, /urgent, /earliest)
        if (this.isScopedSlashCommand(qLower)) {
            await this.handleScopedSlashCommand(qLower);
            return;
        }

        // 10. Natural Language Query / Backend AI
        await this.handleNaturalLanguage(query);
    }

    getTargetTaskList() {
        if (this.isScopedToView && this.hasActiveFilters()) {
            return this.viewContext.tasks || [];
        }
        return this.viewContext.allTasks || [];
    }

    isChainedCommand(q) {
        return q.includes('&&') || q.includes('|') || (q.includes('+') && !q.includes('➕'));
    }

    async handleChainedCommand(raw) {
        const parts = raw.split(/\s*(?:\||&&|\+)\s*/).map(s => s.trim().toLowerCase());
        let list = this.getTargetTaskList().filter(t => t.status !== 'completed');

        let filterToday = false;
        let filterOverdue = false;
        let filterHigh = false;
        let spaceFilter = null;

        parts.forEach(p => {
            const clean = p.replace(/^\//, '');
            if (clean === 'today' || clean === 'due today' || clean === 't') filterToday = true;
            if (clean === 'overdue' || clean === 'o') filterOverdue = true;
            if (clean === 'high' || clean === 'urgent' || clean === 'critical') filterHigh = true;
            if (clean.startsWith('space:') || clean.startsWith('space ')) {
                spaceFilter = clean.replace(/^space:?\s*/, '');
            }
        });

        const todayStr = new Date().toISOString().substring(0, 10);

        if (filterToday) {
            list = list.filter(t => t.due && t.due.substring(0, 10) === todayStr);
        }
        if (filterOverdue) {
            list = list.filter(t => t.due && t.due.substring(0, 10) < todayStr);
        }
        if (filterHigh) {
            list = list.filter(t => {
                const p = (t.calculated_priority || t.priority || '').toLowerCase();
                return p === 'high' || p === 'critical';
            });
        }
        if (spaceFilter) {
            list = list.filter(t => {
                const sp = t.spaces ? Object.keys(t.spaces) : (t.space ? [t.space] : []);
                return sp.some(s => s.toLowerCase() === spaceFilter.toLowerCase());
            });
        }

        const label = parts.join(' ⧉ ');
        if (list.length === 0) {
            this.addAssistantMessage({
                text: `🔍 **Chained Filter (${label}):** No matching tasks found.`,
                chips: this.getDefaultQuickPills()
            });
        } else {
            this.addAssistantMessage({
                text: `🔍 **Chained Filter Result (${label}):** Found **${list.length}** matching task${list.length === 1 ? '' : 's'}:`,
                taskItems: list.slice(0, 8),
                chips: ['📊 Summarize View', '⚡ Most Urgent', '✅ Done All']
            });
        }
    }

    isScopedSlashCommand(q) {
        return (
            q === '/these' || q === 'tasks in view' || q === 'show these' || q === 'show tasks' ||
            q === '/summary' || q === '/stats' || q === 'summary' || q === 'stats' || q === 'summarize view' ||
            q === '/urgent' || q === '/mosturgent' || q === 'most urgent' || q === 'urgent' ||
            q === '/earliest' || q === '/earliestdue' || q === 'earliest due' || q === 'earliest' ||
            q === '/today' || q === 'due today' || q === '/overdue' || q === 'overdue' ||
            q === '/pending' || q === 'pending' || q === '/high' || q === 'high priority'
        );
    }

    async handleScopedSlashCommand(cmd) {
        const targetTasks = this.getTargetTaskList();
        const pending = targetTasks.filter(t => t.status !== 'completed');
        const completed = targetTasks.filter(t => t.status === 'completed');
        const todayStr = new Date().toISOString().substring(0, 10);

        // /these
        if (cmd === '/these' || cmd === 'tasks in view' || cmd === 'show these' || cmd === 'show tasks') {
            if (targetTasks.length === 0) {
                this.addAssistantMessage({
                    text: '✨ **No tasks found in the current scope.**',
                    chips: this.getDefaultQuickPills()
                });
            } else {
                this.addAssistantMessage({
                    text: `📋 **Current Scope Tasks (${targetTasks.length} total, ${pending.length} pending):**`,
                    taskItems: targetTasks.slice(0, 10),
                    chips: ['📊 Summarize View', '⚡ Most Urgent', '⏰ Earliest Due', '✅ Done All']
                });
            }
            return;
        }

        // /summary
        if (cmd === '/summary' || cmd === '/stats' || cmd === 'summary' || cmd === 'stats' || cmd === 'summarize view') {
            const overdue = pending.filter(t => t.due && t.due.substring(0, 10) < todayStr).length;
            const dueToday = pending.filter(t => t.due && t.due.substring(0, 10) === todayStr).length;
            const highPrio = pending.filter(t => {
                const p = (t.calculated_priority || t.priority || '').toLowerCase();
                return p === 'high' || p === 'critical';
            }).length;

            const spaceMap = {};
            pending.forEach(t => {
                const sp = t.spaces ? Object.keys(t.spaces) : (t.space ? [t.space] : []);
                if (sp.length === 0) {
                    spaceMap['(General)'] = (spaceMap['(General)'] || 0) + 1;
                } else {
                    sp.forEach(s => { spaceMap[s] = (spaceMap[s] || 0) + 1; });
                }
            });

            const spaceLines = Object.entries(spaceMap)
                .slice(0, 5)
                .map(([s, c]) => `  • **${s}**: ${c}`)
                .join('\n');

            const scopeTitle = this.isScopedToView && this.hasActiveFilters() ? `Active View (${this.getFilterDescription()})` : 'All Tasks';

            const summaryMd = `📊 **Task Summary: ${scopeTitle}**\n\n` +
                `• **Total in Scope:** ${targetTasks.length}\n` +
                `• **Pending:** ${pending.length} | **Completed:** ${completed.length}\n` +
                `• **Due Today:** ${dueToday} | **Overdue:** ${overdue}\n` +
                `• **High / Critical Priority:** ${highPrio}\n\n` +
                (spaceLines ? `**Spaces Breakdown:**\n${spaceLines}\n` : '');

            this.addAssistantMessage({
                text: summaryMd,
                chips: ['⚡ Most Urgent', '⏰ Earliest Due', '🪄 Add Task Wizard', '✅ Done All']
            });
            return;
        }

        // /urgent
        if (cmd === '/urgent' || cmd === '/mosturgent' || cmd === 'most urgent' || cmd === 'urgent') {
            if (pending.length === 0) {
                this.addAssistantMessage({
                    text: '✨ **No pending tasks found in this view!**',
                    chips: this.getDefaultQuickPills()
                });
                return;
            }

            const prioWeight = { critical: 4, high: 3, medium: 2, low: 1 };
            const sorted = [...pending].sort((a, b) => {
                const pa = prioWeight[(a.calculated_priority || a.priority || 'medium').toLowerCase()] || 2;
                const pb = prioWeight[(b.calculated_priority || b.priority || 'medium').toLowerCase()] || 2;
                if (pb !== pa) return pb - pa;
                if (a.due && b.due) return a.due.localeCompare(b.due);
                if (a.due) return -1;
                if (b.due) return 1;
                return 0;
            });

            const top = sorted[0];
            this.addAssistantMessage({
                text: `⚡ **Most Urgent Task in Scope:**\n\n` +
                    `**${top.title}** is currently your highest priority task with imminent attention needed.`,
                taskItems: [top],
                chips: ['⏰ Earliest Due', '📊 Summarize View', '✅ Done All']
            });
            return;
        }

        // /earliest
        if (cmd === '/earliest' || cmd === '/earliestdue' || cmd === 'earliest due' || cmd === 'earliest') {
            const withDue = pending.filter(t => !!t.due);
            if (withDue.length === 0) {
                this.addAssistantMessage({
                    text: 'ℹ️ **No pending tasks with due dates in this scope.**',
                    chips: this.getDefaultQuickPills()
                });
                return;
            }

            withDue.sort((a, b) => a.due.localeCompare(b.due));
            const earliest = withDue[0];

            this.addAssistantMessage({
                text: `⏰ **Earliest Due Task in Scope:**\n\n` +
                    `**${earliest.title}** is due next on **${earliest.due.substring(0, 10)}**.`,
                taskItems: [earliest],
                chips: ['⚡ Most Urgent', '📊 Summarize View', '✅ Done All']
            });
            return;
        }

        // /today
        if (cmd === '/today' || cmd === 'due today') {
            const dueToday = pending.filter(t => t.due && t.due.substring(0, 10) === todayStr);
            if (dueToday.length === 0) {
                this.addAssistantMessage({
                    text: '📅 **No pending tasks due today in this scope!**',
                    chips: this.getDefaultQuickPills()
                });
            } else {
                this.addAssistantMessage({
                    text: `📅 **Tasks Due Today (${dueToday.length}):**`,
                    taskItems: dueToday,
                    chips: ['⚡ Most Urgent', '📊 Summarize View']
                });
            }
            return;
        }

        // /overdue
        if (cmd === '/overdue' || cmd === 'overdue') {
            const overdue = pending.filter(t => t.due && t.due.substring(0, 10) < todayStr);
            if (overdue.length === 0) {
                this.addAssistantMessage({
                    text: '🎉 **No overdue tasks in this scope! Everything is on schedule.**',
                    chips: this.getDefaultQuickPills()
                });
            } else {
                this.addAssistantMessage({
                    text: `⚠️ **Overdue Tasks (${overdue.length}):**`,
                    taskItems: overdue,
                    chips: ['⚡ Most Urgent', '✅ Done All']
                });
            }
            return;
        }

        // /pending
        if (cmd === '/pending' || cmd === 'pending') {
            this.addAssistantMessage({
                text: `⏳ **Pending Tasks (${pending.length}):**`,
                taskItems: pending.slice(0, 8),
                chips: ['⚡ Most Urgent', '⏰ Earliest Due', '✅ Done All']
            });
            return;
        }

        // /high
        if (cmd === '/high' || cmd === 'high priority') {
            const high = pending.filter(t => {
                const p = (t.calculated_priority || t.priority || '').toLowerCase();
                return p === 'high' || p === 'critical';
            });
            if (high.length === 0) {
                this.addAssistantMessage({
                    text: '✨ **No high or critical priority tasks in this scope.**',
                    chips: this.getDefaultQuickPills()
                });
            } else {
                this.addAssistantMessage({
                    text: `⚡ **High Priority Tasks (${high.length}):**`,
                    taskItems: high,
                    chips: ['📊 Summarize View', '⏰ Earliest Due']
                });
            }
            return;
        }
    }

    // Claude CLI-style interactive task creation wizard
    startWizard() {
        // Auto-inherit active scoped space if present
        let defaultSpace = '';
        if (this.viewContext.filters?.space) {
            defaultSpace = this.viewContext.filters.space;
        } else if (this.viewContext.filters?.spaces && this.viewContext.filters.spaces.length > 0) {
            defaultSpace = this.viewContext.filters.spaces[0];
        }

        this.wizardState = {
            step: 'title',
            draft: {
                title: '',
                due: null,
                priority: 'medium',
                space: defaultSpace
            }
        };

        this.addAssistantMessage({
            text: `🪄 **Task Creation Wizard (Step 1/4)**\n\nWhat is the **title** of the task? *(Type your title below or 'cancel' to exit)*`,
            chips: ['Cancel']
        });
    }

    async handleWizardStep(rawInput) {
        const val = rawInput.trim();
        const vLower = val.toLowerCase();

        if (vLower === 'cancel' || vLower === 'exit' || vLower === 'quit') {
            this.wizardState = { step: 'none', draft: {} };
            this.addAssistantMessage({
                text: '🚫 **Task creation cancelled.**',
                chips: this.getDefaultQuickPills()
            });
            return;
        }

        // Step 1: Title
        if (this.wizardState.step === 'title') {
            if (!val) {
                this.addAssistantMessage({
                    text: '⚠️ Title cannot be empty. Please enter a task title:',
                    chips: ['Cancel']
                });
                return;
            }
            this.wizardState.draft.title = val;
            this.wizardState.step = 'due';

            this.addAssistantMessage({
                text: `📅 **Task Creation Wizard (Step 2/4)**\n\nTitle set to: **${val}**.\nWhen is this task **due**? Tap an option or type a date (YYYY-MM-DD):`,
                chips: ['Today', 'Tomorrow', 'Next Week', 'Skip (No Due Date)', 'Cancel']
            });
            return;
        }

        // Step 2: Due Date
        if (this.wizardState.step === 'due') {
            const today = new Date();
            let dueVal = null;

            if (vLower === 'skip' || vLower === 'none' || vLower === 'skip (no due date)') {
                dueVal = null;
            } else if (vLower === 'today') {
                dueVal = today.toISOString().substring(0, 10);
            } else if (vLower === 'tomorrow') {
                const tmrw = new Date(today);
                tmrw.setDate(tmrw.getDate() + 1);
                dueVal = tmrw.toISOString().substring(0, 10);
            } else if (vLower === 'next week') {
                const nw = new Date(today);
                nw.setDate(nw.getDate() + 7);
                dueVal = nw.toISOString().substring(0, 10);
            } else {
                // Check if user entered a date
                const dateMatch = val.match(/\d{4}-\d{2}-\d{2}/);
                if (dateMatch) {
                    dueVal = dateMatch[0];
                } else {
                    dueVal = val;
                }
            }

            this.wizardState.draft.due = dueVal;
            this.wizardState.step = 'priority';

            this.addAssistantMessage({
                text: `⚡ **Task Creation Wizard (Step 3/4)**\n\nDue date set to: **${dueVal || 'None'}**.\nWhat is the **priority** level?`,
                chips: ['High', 'Medium', 'Low', 'None (Medium)', 'Cancel']
            });
            return;
        }

        // Step 3: Priority
        if (this.wizardState.step === 'priority') {
            let prio = 'medium';
            if (vLower.includes('high') || vLower.includes('critical')) prio = 'high';
            else if (vLower.includes('low')) prio = 'low';
            else prio = 'medium';

            this.wizardState.draft.priority = prio;
            this.wizardState.step = 'space';

            // Gather available spaces from viewContext or window
            const availableSpaces = this.getAvailableSpaces();
            const spaceChips = availableSpaces.slice(0, 4);
            if (this.wizardState.draft.space && !spaceChips.includes(this.wizardState.draft.space)) {
                spaceChips.unshift(this.wizardState.draft.space);
            }
            spaceChips.push('Skip (No Space)', 'Cancel');

            const currentDefault = this.wizardState.draft.space ? ` (Default: **${this.wizardState.draft.space}**)` : '';

            this.addAssistantMessage({
                text: `📁 **Task Creation Wizard (Step 4/4)**\n\nPriority set to: **${prio.toUpperCase()}**.\nWhich **Space** should this task belong to?${currentDefault}`,
                chips: spaceChips
            });
            return;
        }

        // Step 4: Space
        if (this.wizardState.step === 'space') {
            if (vLower !== 'skip' && vLower !== 'none' && vLower !== 'skip (no space)') {
                this.wizardState.draft.space = val;
            }
            this.wizardState.step = 'confirm';

            this.addAssistantMessage({
                text: `✨ **Review Your New Task Draft:**\nPlease confirm to save this task to your workspace:`,
                wizardCard: { ...this.wizardState.draft },
                chips: ['✅ Create Task', '❌ Cancel']
            });
            return;
        }

        // Step 5: Confirm / Cancel
        if (this.wizardState.step === 'confirm') {
            if (vLower.includes('create') || vLower.includes('confirm') || vLower.includes('yes') || vLower.includes('✅')) {
                await this.createTaskFromDraft();
            } else {
                this.wizardState = { step: 'none', draft: {} };
                this.addAssistantMessage({
                    text: '🚫 **Task creation cancelled.**',
                    chips: this.getDefaultQuickPills()
                });
            }
        }
    }

    getAvailableSpaces() {
        const spacesSet = new Set();
        (this.viewContext.allTasks || []).forEach(t => {
            if (t.spaces) Object.keys(t.spaces).forEach(s => spacesSet.add(s));
            if (t.space) spacesSet.add(t.space);
        });
        return Array.from(spacesSet);
    }

    async createTaskFromDraft() {
        const draft = this.wizardState.draft;
        this.wizardState = { step: 'none', draft: {} };

        try {
            const payload = {
                title: draft.title,
                due: draft.due,
                priority: draft.priority,
                space: draft.space,
                account_id: window.currentAccountId || 'default'
            };

            const response = await fetch(`${this.getBasePath()}/api/tasks`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await response.json();
            if (data.success || response.ok) {
                // Refresh dashboard data
                if (typeof window.refreshData === 'function') {
                    window.refreshData();
                }

                this.addAssistantMessage({
                    text: `🎉 **Task Created Successfully!**\n\n` +
                        `• **Title:** ${draft.title}\n` +
                        `• **Due:** ${draft.due || 'None'}\n` +
                        `• **Priority:** ${draft.priority.toUpperCase()}\n` +
                        `• **Space:** ${draft.space || 'None'}`,
                    chips: this.getDefaultQuickPills()
                });
            } else {
                throw new Error(data.error || 'Failed to create task');
            }
        } catch (e) {
            this.addAssistantMessage({
                text: `⚠️ **Error creating task:** ${e.message}`,
                isError: true,
                chips: this.getDefaultQuickPills()
            });
        }
    }

    async completeTask(taskId) {
        try {
            const res = await fetch(`${this.getBasePath()}/api/tasks/${taskId}/complete`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            if (res.ok) {
                if (typeof window.refreshData === 'function') {
                    window.refreshData();
                }
            }
        } catch (e) {
            console.error('Error completing task:', e);
        }
    }

    async executeBulkComplete() {
        const targetTasks = this.getTargetTaskList().filter(t => t.status !== 'completed');
        let completedCount = 0;

        for (const t of targetTasks) {
            try {
                const res = await fetch(`${this.getBasePath()}/api/tasks/${t.id}/complete`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });
                if (res.ok) completedCount++;
            } catch (err) {
                console.error(`Error completing task ${t.id}:`, err);
            }
        }

        if (typeof window.refreshData === 'function') {
            window.refreshData();
        }

        this.addAssistantMessage({
            text: `🎉 **Bulk Complete Done!** Successfully marked **${completedCount}** task${completedCount === 1 ? '' : 's'} as completed!`,
            chips: this.getDefaultQuickPills()
        });
    }

    async handleNaturalLanguage(query) {
        this.setProcessing(true);

        try {
            // Build view context for LLM grounding
            const sampleTasks = this.getTargetTaskList().slice(0, 10).map(t => ({
                id: t.id,
                display_id: t.display_id || t.id,
                title: t.title,
                due: t.due ? t.due.substring(0, 10) : null,
                priority: t.calculated_priority || t.priority || 'medium',
                status: t.status
            }));

            const payload = {
                message: query,
                account: window.currentAccountId || 'default',
                context: {
                    scopeType: this.isScopedToView && this.hasActiveFilters() ? 'VIEW' : 'GLOBAL',
                    filterDescription: this.getFilterDescription(),
                    taskCount: this.getTargetTaskList().length,
                    tasksSample: sampleTasks
                }
            };

            const response = await fetch(`${this.getBasePath()}/api/ai/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                throw new Error(`Server returned HTTP ${response.status}`);
            }

            const resData = await response.json();
            if (resData.success && resData.reply) {
                this.addAssistantMessage({
                    text: resData.reply,
                    chips: this.getDefaultQuickPills()
                });
            } else {
                throw new Error(resData.error || 'Empty response');
            }
        } catch (e) {
            console.warn('Backend AI failed or offline, falling back to local assistant:', e);
            this.handleLocalFallback(query);
        } finally {
            this.setProcessing(false);
        }
    }

    handleLocalFallback(query) {
        const qLower = query.toLowerCase();

        // Check for common commands
        if (qLower.includes('search') || qLower.includes('find')) {
            const term = qLower.replace(/^(?:search|find)\s*/, '').trim();
            const matches = this.getTargetTaskList().filter(t => (t.title || '').toLowerCase().includes(term));
            if (matches.length === 0) {
                this.addAssistantMessage({
                    text: `🔍 No tasks found matching **"${term}"** in this scope.`,
                    chips: this.getDefaultQuickPills()
                });
            } else {
                this.addAssistantMessage({
                    text: `🔍 Found **${matches.length}** task${matches.length === 1 ? '' : 's'} matching **"${term}"**:`,
                    taskItems: matches.slice(0, 8),
                    chips: this.getDefaultQuickPills()
                });
            }
            return;
        }

        // Default response
        this.addAssistantMessage({
            text: `🤖 I heard: **"${query}"**.\n\n` +
                `You can use:\n` +
                `• \`/wizard\` or \`/new\` to create tasks interactively\n` +
                `• \`/summary\` to see active view metrics\n` +
                `• \`/urgent\` or \`/earliest\` to find key tasks\n` +
                `• \`/these\` to list tasks in view\n` +
                `• \`/doneall\` to bulk complete\n` +
                `• \`/help\` to open the command palette`,
            chips: this.getDefaultQuickPills()
        });
    }

    setProcessing(isProc) {
        this.isProcessing = isProc;
        const btn = document.getElementById('ai-chat-send-btn');
        if (btn) {
            btn.disabled = isProc;
            btn.innerHTML = isProc ? '<i class="fas fa-spinner fa-spin"></i>' : '<i class="fas fa-paper-plane"></i>';
        }
    }

    // Command Palette Modal Methods
    renderCommandPaletteItems(filterText) {
        const body = document.getElementById('ai-palette-body');
        if (!body) return;

        const f = filterText.toLowerCase().trim();

        const commands = [
            // Context & View
            { category: '🎯 View & Context Commands', cmd: '/these', desc: 'Display all visible tasks in the current active scope', icon: 'fa-list-ul' },
            { category: '🎯 View & Context Commands', cmd: '/scope', desc: 'Toggle between View Scope and Global Scope', icon: 'fa-exchange-alt' },
            { category: '🎯 View & Context Commands', cmd: '/summary', desc: 'Summarize metrics, priorities, and deadlines in view', icon: 'fa-chart-pie' },
            { category: '🎯 View & Context Commands', cmd: '/urgent', desc: 'Find highest priority task needing immediate attention', icon: 'fa-bolt' },
            { category: '🎯 View & Context Commands', cmd: '/earliest', desc: 'Find task with nearest upcoming due date', icon: 'fa-clock' },
            { category: '🎯 View & Context Commands', cmd: '/doneall', desc: 'Bulk complete all pending tasks in this view', icon: 'fa-check-double' },

            // Interactive Wizards
            { category: '🪄 Interactive Wizards', cmd: '/wizard', desc: 'Launch Claude CLI step-by-step task creation wizard', icon: 'fa-magic' },
            { category: '🪄 Interactive Wizards', cmd: '/new', desc: 'Shortcut to create new task interactively', icon: 'fa-plus' },

            // Filter Shortcuts
            { category: '🔍 Filter Shortcuts', cmd: '/today', desc: 'Filter tasks due today', icon: 'fa-calendar-day' },
            { category: '🔍 Filter Shortcuts', cmd: '/overdue', desc: 'Filter overdue pending tasks', icon: 'fa-exclamation-circle' },
            { category: '🔍 Filter Shortcuts', cmd: '/pending', desc: 'Filter all pending tasks', icon: 'fa-hourglass-half' },
            { category: '🔍 Filter Shortcuts', cmd: '/high', desc: 'Filter high or critical priority tasks', icon: 'fa-fire' },
            { category: '🔍 Filter Shortcuts', cmd: '/today && /high', desc: 'Example of chained command execution', icon: 'fa-link' },

            // Assistant
            { category: '⚙️ Assistant Commands', cmd: '/help', desc: 'Show this interactive command palette and guide', icon: 'fa-question-circle' },
            { category: '⚙️ Assistant Commands', cmd: '/clear', desc: 'Clear chat history and reset conversation', icon: 'fa-trash' }
        ];

        const matched = commands.filter(c => 
            !f || c.cmd.toLowerCase().includes(f) || c.desc.toLowerCase().includes(f) || c.category.toLowerCase().includes(f)
        );

        if (matched.length === 0) {
            body.innerHTML = '<div class="ai-palette-empty">No commands match your search</div>';
            return;
        }

        // Group by category
        const groups = {};
        matched.forEach(c => {
            if (!groups[c.category]) groups[c.category] = [];
            groups[c.category].push(c);
        });

        body.innerHTML = '';
        Object.entries(groups).forEach(([catName, items]) => {
            const section = document.createElement('div');
            section.className = 'ai-palette-section';

            const header = document.createElement('div');
            header.className = 'ai-palette-section-title';
            header.textContent = catName;
            section.appendChild(header);

            items.forEach(item => {
                const row = document.createElement('div');
                row.className = 'ai-palette-item';
                row.innerHTML = `
                    <div class="ai-palette-item-icon"><i class="fas ${item.icon}"></i></div>
                    <div class="ai-palette-item-info">
                        <div class="ai-palette-item-cmd">${item.cmd}</div>
                        <div class="ai-palette-item-desc">${item.desc}</div>
                    </div>
                `;
                row.addEventListener('click', () => {
                    this.closeCommandPalette();
                    if (!this.isOpen) {
                        this.openDrawer();
                    }
                    this.handleQuery(item.cmd);
                });
                section.appendChild(row);
            });

            body.appendChild(section);
        });
    }
}

// Instantiate globally on DOM load
let aiChatInstance = null;

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        aiChatInstance = new AiChatController();
        window.AiChatController = aiChatInstance;
        window.toggleAiChatDrawer = () => aiChatInstance.toggleDrawer();
        window.openAiChatDrawer = () => aiChatInstance.openDrawer();
        window.closeAiChatDrawer = () => aiChatInstance.closeDrawer();
    });
} else {
    aiChatInstance = new AiChatController();
    window.AiChatController = aiChatInstance;
    window.toggleAiChatDrawer = () => aiChatInstance.toggleDrawer();
    window.openAiChatDrawer = () => aiChatInstance.openDrawer();
    window.closeAiChatDrawer = () => aiChatInstance.closeDrawer();
}

export default AiChatController;
