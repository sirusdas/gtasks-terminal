/**
 * Mandala Sacred Geometry Visualization Module
 * High-performance D3.js interactive Sacred Mandala for GTasks.
 * Supports Padma (Lotus), Sri Yantra, and Chakra geometries,
 * multi-tier grouping, sacred color themes, drill-down, and saved views.
 */

console.log('[Mandala] Initializing Sacred Mandala module...');

// Theme Color Palettes
const MANDALA_THEMES = {
    CYBERPUNK: {
        id: 'CYBERPUNK',
        name: 'Cyberpunk Neon',
        background: '#070a14',
        coreFill: '#0b1329',
        coreStroke: '#00f0ff',
        glowColor: '#00f0ff',
        colors: ['#00f0ff', '#ff007f', '#39ff14', '#ffe600', '#bf00ff', '#00d2ff', '#ff3366', '#7000ff']
    },
    GOLDEN_LOTUS: {
        id: 'GOLDEN_LOTUS',
        name: 'Golden Lotus',
        background: '#120d04',
        coreFill: '#221504',
        coreStroke: '#fbbf24',
        glowColor: '#f59e0b',
        colors: ['#fbbf24', '#f59e0b', '#d97706', '#f43f5e', '#ec4899', '#eab308', '#ca8a04', '#b45309']
    },
    VEDIC_FIRE: {
        id: 'VEDIC_FIRE',
        name: 'Vedic Fire',
        background: '#140602',
        coreFill: '#240b04',
        coreStroke: '#f97316',
        glowColor: '#ef4444',
        colors: ['#f97316', '#ef4444', '#eab308', '#dc2626', '#f59e0b', '#b91c1c', '#ea580c', '#fb923c']
    },
    SACRED_GEOMETRY: {
        id: 'SACRED_GEOMETRY',
        name: 'Sacred Sapphire',
        background: '#050c1e',
        coreFill: '#0a1638',
        coreStroke: '#38bdf8',
        glowColor: '#38bdf8',
        colors: ['#38bdf8', '#6366f1', '#06b6d4', '#8b5cf6', '#2563eb', '#0284c7', '#4f46e5', '#a855f7']
    },
    EMERALD_FOREST: {
        id: 'EMERALD_FOREST',
        name: 'Emerald Forest',
        background: '#03140a',
        coreFill: '#072414',
        coreStroke: '#10b981',
        glowColor: '#10b981',
        colors: ['#10b981', '#059669', '#34d399', '#84cc16', '#14b8a6', '#047857', '#65a30d', '#2dd4bf']
    }
};

class MandalaControllerClass {
    constructor() {
        this.grouping = 'spaces'; // spaces | tags | priority | lists
        this.geometry = 'PADMA'; // PADMA | SRI_YANTRA | CHAKRA
        this.theme = 'CYBERPUNK';
        this.statusFilter = 'pending'; // pending | all | completed
        this.tasks = [];
        this.allTasks = [];
        this.drillPath = []; // stack of { name, filterFn }
        this.selectedSlice = null;
        this.savedViews = [];
        this.zoomBehavior = null;
        this.svg = null;
        this.mainG = null;
        this.initialized = false;
    }

    async init() {
        console.log('[Mandala] Initializing view and data...');
        this.bindEvents();
        await this.loadTasks();
        await this.loadSavedViews();
        this.render();
        this.initialized = true;
    }

    bindEvents() {
        window.addEventListener('resize', () => {
            const section = document.getElementById('mandala-section');
            if (section && section.style.display !== 'none') {
                this.render();
            }
        });
    }

    async loadTasks() {
        try {
            const basePath = window.GTASKS_BASE_PATH || '';
            const res = await fetch(`${basePath}/api/data`);
            if (res.ok) {
                const data = await res.json();
                this.allTasks = data.all_tasks && data.all_tasks.length > 0 ? data.all_tasks : (data.tasks || []);
                this.tasks = [...this.allTasks];
            } else {
                console.warn('[Mandala] Fallback to window.dashboardData');
                if (window.dashboardData) {
                    this.allTasks = window.dashboardData.all_tasks || window.dashboardData.tasks || [];
                    this.tasks = [...this.allTasks];
                }
            }
        } catch (e) {
            console.error('[Mandala] Error loading tasks:', e);
            if (window.dashboardData) {
                this.allTasks = window.dashboardData.all_tasks || window.dashboardData.tasks || [];
                this.tasks = [...this.allTasks];
            }
        }
    }

    async loadSavedViews() {
        try {
            const basePath = window.GTASKS_BASE_PATH || '';
            const res = await fetch(`${basePath}/api/saved-views`);
            if (res.ok) {
                this.savedViews = await res.json();
                this.renderSidebarSavedViews();
            }
        } catch (e) {
            console.error('[Mandala] Error loading saved views:', e);
        }
    }

    renderSidebarSavedViews() {
        const container = document.getElementById('sidebar-saved-views-list');
        if (!container) return;

        if (!this.savedViews || this.savedViews.length === 0) {
            container.innerHTML = `<div style="font-size: 0.75rem; color: #64748b; padding: 4px 8px; font-style: italic;">No saved views</div>`;
            return;
        }

        container.innerHTML = this.savedViews.map(view => {
            const isMandala = view.viewMode === 'mandala' || view.mandalaGeometry;
            const icon = isMandala ? 'fa-dharmachakra' : 'fa-columns';
            const iconColor = isMandala ? '#06b6d4' : '#a855f7';
            return `
                <div class="sidebar-saved-view-item" style="display: flex; align-items: center; justify-content: space-between; padding: 5px 8px; border-radius: 6px; cursor: pointer; transition: background 0.15s; font-size: 0.8rem; color: #cbd5e1;"
                     onmouseover="this.style.background='rgba(255,255,255,0.06)'"
                     onmouseout="this.style.background='transparent'"
                     onclick="window.MandalaController.applySavedView('${view.id}')">
                    <div style="display: flex; align-items: center; gap: 6px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                        <i class="fas ${icon}" style="color: ${iconColor}; font-size: 0.75rem;"></i>
                        <span style="font-weight: 500;">${this.escapeHtml(view.title || 'Untitled View')}</span>
                    </div>
                    <button onclick="event.stopPropagation(); window.MandalaController.deleteSavedView('${view.id}')"
                            style="background: none; border: none; color: #64748b; cursor: pointer; padding: 2px 4px; font-size: 0.75rem;"
                            title="Delete view"
                            onmouseover="this.style.color='#ef4444'"
                            onmouseout="this.style.color='#64748b'">
                        <i class="fas fa-trash-alt"></i>
                    </button>
                </div>
            `;
        }).join('');
    }

    applySavedView(viewId) {
        const view = this.savedViews.find(v => v.id === viewId);
        if (!view) return;

        console.log('[Mandala] Applying saved view:', view);
        if (typeof window.showSection === 'function') {
            window.showSection('mandala');
        }

        if (view.mandalaGrouping) {
            this.grouping = view.mandalaGrouping;
            const select = document.getElementById('mandala-grouping-select');
            if (select) select.value = this.grouping;
        }

        if (view.mandalaGeometry) {
            this.geometry = view.mandalaGeometry;
            const select = document.getElementById('mandala-geometry-select');
            if (select) select.value = this.geometry;
        }

        if (view.mandalaTheme) {
            this.theme = view.mandalaTheme;
            const select = document.getElementById('mandala-theme-select');
            if (select) select.value = this.theme;
        }

        if (view.statusFilter) {
            this.statusFilter = view.statusFilter;
            const select = document.getElementById('mandala-status-select');
            if (select) select.value = this.statusFilter;
        }

        this.drillPath = [];
        this.selectedSlice = null;
        this.render();

        if (window.showNotification) {
            window.showNotification(`Loaded view: ${view.title} 🔖`, 'success');
        }
    }

    async saveCurrentViewPrompt() {
        const title = prompt('Enter a name for this Sacred Mandala View:', `${this.geometry} - ${this.grouping.toUpperCase()}`);
        if (!title || !title.trim()) return;

        const payload = {
            title: title.trim(),
            viewMode: 'mandala',
            mandalaGrouping: this.grouping,
            mandalaGeometry: this.geometry,
            mandalaTheme: this.theme,
            statusFilter: this.statusFilter
        };

        try {
            const basePath = window.GTASKS_BASE_PATH || '';
            const res = await fetch(`${basePath}/api/saved-views`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (res.ok) {
                const data = await res.json();
                if (data.success) {
                    await this.loadSavedViews();
                    if (window.showNotification) {
                        window.showNotification(`Saved View "${payload.title}" created! 🔖`, 'success');
                    }
                }
            }
        } catch (e) {
            console.error('[Mandala] Error saving view:', e);
            alert('Failed to save view');
        }
    }

    async deleteSavedView(viewId) {
        if (!confirm('Are you sure you want to delete this saved view?')) return;
        try {
            const basePath = window.GTASKS_BASE_PATH || '';
            const res = await fetch(`${basePath}/api/saved-views/${viewId}`, {
                method: 'DELETE'
            });
            if (res.ok) {
                await this.loadSavedViews();
                if (window.showNotification) {
                    window.showNotification('Saved view deleted', 'info');
                }
            }
        } catch (e) {
            console.error('[Mandala] Error deleting view:', e);
        }
    }

    setGrouping(val) {
        this.grouping = val;
        this.drillPath = [];
        this.selectedSlice = null;
        this.render();
    }

    setGeometry(val) {
        this.geometry = val;
        this.render();
    }

    setTheme(val) {
        this.theme = val;
        this.render();
    }

    setStatusFilter(val) {
        this.statusFilter = val;
        this.render();
    }

    resetZoom() {
        if (this.svg && this.zoomBehavior) {
            this.svg.transition().duration(600).call(this.zoomBehavior.transform, d3.zoomIdentity);
        }
    }

    toggleFullscreen() {
        const elem = document.getElementById('mandala-section') || document.getElementById('mandala-canvas-container');
        if (!elem) return;
        if (!document.fullscreenElement) {
            if (elem.requestFullscreen) {
                elem.requestFullscreen();
            } else if (elem.webkitRequestFullscreen) {
                elem.webkitRequestFullscreen();
            }
        } else {
            if (document.exitFullscreen) {
                document.exitFullscreen();
            }
        }
    }

    drillDown(sliceName, sliceTasks) {
        console.log(`[Mandala] Drilling into: ${sliceName} (${sliceTasks.length} tasks)`);
        this.drillPath.push({
            name: sliceName,
            tasks: sliceTasks
        });
        this.selectedSlice = null;
        this.render();
    }

    drillUp() {
        if (this.drillPath.length > 0) {
            this.drillPath.pop();
            this.selectedSlice = null;
            this.render();
        }
    }

    drillToRoot() {
        this.drillPath = [];
        this.selectedSlice = null;
        this.render();
    }

    // Filter and group current active tasks
    getActiveTaskUniverse() {
        let baseTasks = this.allTasks || [];

        // Apply Status Filter
        if (this.statusFilter === 'pending') {
            baseTasks = baseTasks.filter(t => t.status !== 'completed' && t.status !== 'deleted');
        } else if (this.statusFilter === 'completed') {
            baseTasks = baseTasks.filter(t => t.status === 'completed');
        } else {
            baseTasks = baseTasks.filter(t => t.status !== 'deleted');
        }

        // Apply Drill-down hierarchy stack
        if (this.drillPath.length > 0) {
            const currentLevel = this.drillPath[this.drillPath.length - 1];
            baseTasks = currentLevel.tasks.filter(t => {
                if (this.statusFilter === 'pending') return t.status !== 'completed';
                if (this.statusFilter === 'completed') return t.status === 'completed';
                return true;
            });
        }

        return baseTasks;
    }

    extractSpace(task) {
        if (task.space) return task.space;
        const notes = task.notes || '';
        const spaceMatch = notes.match(/(?:^|\s)\[(?:Space|Workspace):\s*([^\]]+)\]/i) ||
                           notes.match(/(?:^|\s)@(\w+)/i) ||
                           notes.match(/(?:^|\s)space:([a-zA-Z0-9_\-]+)/i);
        if (spaceMatch) return spaceMatch[1];
        if (task.tasklist_name) return task.tasklist_name;
        if (task.list_name) return task.list_name;
        return 'General';
    }

    extractTags(task) {
        const text = `${task.title || ''} ${task.notes || ''}`;
        const matches = text.match(/#([a-zA-Z0-9_-]+)/g);
        if (!matches || matches.length === 0) return ['No Tag'];
        return matches.map(m => m.toLowerCase());
    }

    groupTasks(tasks) {
        const groups = {};

        tasks.forEach(task => {
            if (this.grouping === 'spaces') {
                const space = this.extractSpace(task);
                if (!groups[space]) groups[space] = [];
                groups[space].push(task);
            } else if (this.grouping === 'tags') {
                const tags = this.extractTags(task);
                tags.forEach(tag => {
                    if (!groups[tag]) groups[tag] = [];
                    groups[tag].push(task);
                });
            } else if (this.grouping === 'priority') {
                let prio = (task.priority || 'None').toUpperCase();
                if (!['HIGH', 'MEDIUM', 'LOW', 'NONE'].includes(prio)) prio = 'NONE';
                if (!groups[prio]) groups[prio] = [];
                groups[prio].push(task);
            } else if (this.grouping === 'lists') {
                const listName = task.tasklist_name || task.list_name || 'Tasks';
                if (!groups[listName]) groups[listName] = [];
                groups[listName].push(task);
            }
        });

        // Convert to sorted array of buckets
        const buckets = Object.keys(groups).map(name => ({
            name: name,
            tasks: groups[name],
            count: groups[name].length,
            completedCount: groups[name].filter(t => t.status === 'completed').length
        }));

        buckets.sort((a, b) => b.count - a.count);
        return buckets;
    }

    render() {
        const container = document.getElementById('mandala-canvas-container');
        const svgEl = document.getElementById('mandala-svg');
        if (!container || !svgEl) return;

        const theme = MANDALA_THEMES[this.theme] || MANDALA_THEMES.CYBERPUNK;
        container.style.background = `radial-gradient(circle at center, ${theme.coreFill} 0%, ${theme.background} 100%)`;

        const width = container.clientWidth || 800;
        const height = container.clientHeight || 650;

        // Clear SVG
        d3.select(svgEl).selectAll('*').remove();

        const svg = d3.select(svgEl)
            .attr('width', width)
            .attr('height', height)
            .attr('viewBox', `0 0 ${width} ${height}`);

        this.svg = svg;

        // Add Defs (Glow filters & Gradients)
        const defs = svg.append('defs');
        const filter = defs.append('filter')
            .attr('id', 'mandala-glow')
            .attr('x', '-50%')
            .attr('y', '-50%')
            .attr('width', '200%')
            .attr('height', '200%');

        filter.append('feGaussianBlur')
            .attr('stdDeviation', '4')
            .attr('result', 'coloredBlur');

        const feMerge = filter.append('feMerge');
        feMerge.append('feMergeNode').attr('in', 'coloredBlur');
        feMerge.append('feMergeNode').attr('in', 'SourceGraphic');

        // Zoom Container Group
        const mainG = svg.append('g').attr('class', 'mandala-zoom-container');
        this.mainG = mainG;

        this.zoomBehavior = d3.zoom()
            .scaleExtent([0.4, 4])
            .on('zoom', (event) => {
                mainG.attr('transform', event.transform);
            });

        svg.call(this.zoomBehavior);

        const cx = width / 2;
        const cy = height / 2;
        const maxRadius = Math.min(width, height) * 0.42;

        const tasks = this.getActiveTaskUniverse();
        const buckets = this.groupTasks(tasks);

        this.updateBreadcrumbs(tasks.length);

        if (buckets.length === 0) {
            this.renderEmptyState(mainG, cx, cy, theme);
            this.renderDrawer([], 'No Slices');
            return;
        }

        // Draw Geometry based on selection
        if (this.geometry === 'SRI_YANTRA') {
            this.renderSriYantra(mainG, cx, cy, maxRadius, buckets, theme, tasks);
        } else if (this.geometry === 'CHAKRA') {
            this.renderChakra(mainG, cx, cy, maxRadius, buckets, theme, tasks);
        } else {
            this.renderPadma(mainG, cx, cy, maxRadius, buckets, theme, tasks);
        }

        // Auto select first bucket or previous selected
        if (!this.selectedSlice && buckets.length > 0) {
            this.selectSlice(buckets[0]);
        } else if (this.selectedSlice) {
            const current = buckets.find(b => b.name === this.selectedSlice.name);
            if (current) this.selectSlice(current);
            else if (buckets.length > 0) this.selectSlice(buckets[0]);
        }
    }

    renderEmptyState(g, cx, cy, theme) {
        g.append('circle')
            .attr('cx', cx)
            .attr('cy', cy)
            .attr('r', 80)
            .attr('fill', theme.coreFill)
            .attr('stroke', theme.coreStroke)
            .attr('stroke-width', 2)
            .attr('stroke-dasharray', '4,4');

        g.append('text')
            .attr('x', cx)
            .attr('y', cy - 10)
            .attr('text-anchor', 'middle')
            .attr('fill', '#94a3b8')
            .attr('font-size', '14px')
            .attr('font-weight', '600')
            .text('No Tasks in View');

        g.append('text')
            .attr('x', cx)
            .attr('y', cy + 15)
            .attr('text-anchor', 'middle')
            .attr('fill', '#64748b')
            .attr('font-size', '11px')
            .text('Change status or grouping filter');
    }

    /**
     * PADMA (Lotus Flower Geometry)
     * Curved radiating lotus petals with center glowing seed (bindu)
     */
    renderPadma(g, cx, cy, maxRadius, buckets, theme, allTasks) {
        const N = buckets.length;
        const innerRadius = maxRadius * 0.28;
        const outerRadius = maxRadius * 0.95;
        const angleStep = (2 * Math.PI) / N;

        // Background subtle concentric aura rings
        [0.4, 0.65, 0.95].forEach((ratio, idx) => {
            g.append('circle')
                .attr('cx', cx)
                .attr('cy', cy)
                .attr('r', maxRadius * ratio)
                .attr('fill', 'none')
                .attr('stroke', theme.glowColor)
                .attr('stroke-opacity', 0.12 - idx * 0.03)
                .attr('stroke-width', 1)
                .attr('stroke-dasharray', idx % 2 === 0 ? '6,4' : 'none');
        });

        // Petals Group
        const petalsG = g.append('g').attr('class', 'mandala-petals');

        buckets.forEach((bucket, i) => {
            const startAngle = i * angleStep;
            const midAngle = startAngle + angleStep / 2;
            const endAngle = startAngle + angleStep;

            const color = theme.colors[i % theme.colors.length];

            // Calculate lotus petal control points (quadratic bezier curve)
            const tipX = cx + outerRadius * Math.sin(midAngle);
            const tipY = cy - outerRadius * Math.cos(midAngle);

            const b1X = cx + innerRadius * Math.sin(startAngle + angleStep * 0.1);
            const b1Y = cy - innerRadius * Math.cos(startAngle + angleStep * 0.1);

            const b2X = cx + innerRadius * Math.sin(endAngle - angleStep * 0.1);
            const b2Y = cy - innerRadius * Math.cos(endAngle - angleStep * 0.1);

            // Wide belly control points for natural flower petal flare
            const bellyRadius = (innerRadius + outerRadius) * 0.62;
            const c1X = cx + bellyRadius * Math.sin(startAngle - angleStep * 0.15);
            const c1Y = cy - bellyRadius * Math.cos(startAngle - angleStep * 0.15);

            const c2X = cx + bellyRadius * Math.sin(endAngle + angleStep * 0.15);
            const c2Y = cy - bellyRadius * Math.cos(endAngle + angleStep * 0.15);

            const pathD = `M ${b1X} ${b1Y} Q ${c1X} ${c1Y} ${tipX} ${tipY} Q ${c2X} ${c2Y} ${b2X} ${b2Y} Z`;

            const petal = petalsG.append('path')
                .attr('d', pathD)
                .attr('fill', color)
                .attr('fill-opacity', 0.22)
                .attr('stroke', color)
                .attr('stroke-width', 2)
                .attr('class', 'mandala-petal-slice')
                .style('cursor', 'pointer')
                .style('transition', 'all 0.25s ease');

            // Interactive Events
            petal
                .on('mouseover', function () {
                    d3.select(this)
                        .attr('fill-opacity', 0.55)
                        .attr('stroke-width', 3.5)
                        .attr('filter', 'url(#mandala-glow)');
                })
                .on('mouseout', (event, d) => {
                    const isSelected = this.selectedSlice && this.selectedSlice.name === bucket.name;
                    petal
                        .attr('fill-opacity', isSelected ? 0.45 : 0.22)
                        .attr('stroke-width', isSelected ? 3 : 2)
                        .attr('filter', isSelected ? 'url(#mandala-glow)' : 'none');
                })
                .on('click', () => {
                    this.selectSlice(bucket);
                })
                .on('dblclick', () => {
                    this.drillDown(bucket.name, bucket.tasks);
                });

            // Label & Badge placed along radial petal centerline
            const labelRadius = (innerRadius + outerRadius) * 0.62;
            const lx = cx + labelRadius * Math.sin(midAngle);
            const ly = cy - labelRadius * Math.cos(midAngle);

            const labelG = petalsG.append('g')
                .attr('transform', `translate(${lx}, ${ly})`)
                .style('pointer-events', 'none');

            // Truncate title
            const shortName = bucket.name.length > 12 ? bucket.name.substring(0, 11) + '…' : bucket.name;

            labelG.append('text')
                .attr('text-anchor', 'middle')
                .attr('y', -4)
                .attr('fill', '#ffffff')
                .attr('font-size', '11px')
                .attr('font-weight', '700')
                .attr('text-shadow', '0 2px 4px rgba(0,0,0,0.9)')
                .text(shortName);

            labelG.append('text')
                .attr('text-anchor', 'middle')
                .attr('y', 12)
                .attr('fill', color)
                .attr('font-size', '10px')
                .attr('font-weight', '800')
                .attr('text-shadow', '0 1px 3px rgba(0,0,0,0.9)')
                .text(`${bucket.count} tasks`);
        });

        // Center Sacred Core Lotus Seed
        this.renderCoreHub(g, cx, cy, innerRadius, theme, allTasks);
    }

    /**
     * SRI YANTRA (Concentric Triangles & Sacred Rings Geometry)
     */
    renderSriYantra(g, cx, cy, maxRadius, buckets, theme, allTasks) {
        const N = buckets.length;
        const innerRadius = maxRadius * 0.35;
        const angleStep = (2 * Math.PI) / N;

        // Concentric Lotus Ring Sectors (Outer Mandala)
        const outerG = g.append('g').attr('class', 'mandala-sriyantra-outer');

        buckets.forEach((bucket, i) => {
            const startAngle = i * angleStep;
            const endAngle = startAngle + angleStep;
            const color = theme.colors[i % theme.colors.length];

            const arcGenerator = d3.arc()
                .innerRadius(innerRadius)
                .outerRadius(maxRadius * 0.92)
                .startAngle(startAngle)
                .endAngle(endAngle)
                .padAngle(0.02)
                .cornerRadius(4);

            const sector = outerG.append('path')
                .attr('d', arcGenerator)
                .attr('transform', `translate(${cx}, ${cy})`)
                .attr('fill', color)
                .attr('fill-opacity', 0.25)
                .attr('stroke', color)
                .attr('stroke-width', 2)
                .style('cursor', 'pointer')
                .style('transition', 'all 0.25s');

            sector
                .on('mouseover', function () {
                    d3.select(this)
                        .attr('fill-opacity', 0.55)
                        .attr('stroke-width', 3)
                        .attr('filter', 'url(#mandala-glow)');
                })
                .on('mouseout', () => {
                    const isSelected = this.selectedSlice && this.selectedSlice.name === bucket.name;
                    sector
                        .attr('fill-opacity', isSelected ? 0.45 : 0.25)
                        .attr('stroke-width', isSelected ? 3 : 2)
                        .attr('filter', isSelected ? 'url(#mandala-glow)' : 'none');
                })
                .on('click', () => {
                    this.selectSlice(bucket);
                })
                .on('dblclick', () => {
                    this.drillDown(bucket.name, bucket.tasks);
                });

            // Centroid for label
            const centroid = arcGenerator.centroid();
            const shortName = bucket.name.length > 10 ? bucket.name.substring(0, 9) + '…' : bucket.name;

            outerG.append('text')
                .attr('transform', `translate(${cx + centroid[0]}, ${cy + centroid[1] - 4})`)
                .attr('text-anchor', 'middle')
                .attr('fill', '#ffffff')
                .attr('font-size', '10px')
                .attr('font-weight', '700')
                .style('pointer-events', 'none')
                .text(shortName);

            outerG.append('text')
                .attr('transform', `translate(${cx + centroid[0]}, ${cy + centroid[1] + 11})`)
                .attr('text-anchor', 'middle')
                .attr('fill', color)
                .attr('font-size', '9px')
                .attr('font-weight', '800')
                .style('pointer-events', 'none')
                .text(`${bucket.count}`);
        });

        // Inner Sacred Interlocking Triangles (Shiva & Shakti)
        const innerG = g.append('g').attr('class', 'mandala-sriyantra-inner');

        const triangleSizes = [innerRadius * 0.85, innerRadius * 0.65, innerRadius * 0.45];
        triangleSizes.forEach((r, idx) => {
            const isUpward = idx % 2 === 0;
            const points = [];
            for (let k = 0; k < 3; k++) {
                const angle = (k * 2 * Math.PI) / 3 + (isUpward ? -Math.PI / 2 : Math.PI / 2);
                points.push(`${cx + r * Math.cos(angle)},${cy + r * Math.sin(angle)}`);
            }

            innerG.append('polygon')
                .attr('points', points.join(' '))
                .attr('fill', isUpward ? 'rgba(56, 189, 248, 0.08)' : 'rgba(244, 63, 94, 0.08)')
                .attr('stroke', isUpward ? theme.coreStroke : theme.glowColor)
                .attr('stroke-width', 1.5)
                .attr('stroke-dasharray', idx === 1 ? '3,3' : 'none');
        });

        this.renderCoreHub(g, cx, cy, innerRadius * 0.32, theme, allTasks);
    }

    /**
     * CHAKRA (Radial Energy Dharma Wheel Geometry)
     */
    renderChakra(g, cx, cy, maxRadius, buckets, theme, allTasks) {
        const N = buckets.length;
        const innerRadius = maxRadius * 0.3;
        const angleStep = (2 * Math.PI) / N;

        // Dharma Spokes
        const spokesG = g.append('g').attr('class', 'mandala-chakra-spokes');

        // Concentric Ripple rings
        [0.45, 0.7, 0.95].forEach((rRatio) => {
            spokesG.append('circle')
                .attr('cx', cx)
                .attr('cy', cy)
                .attr('r', maxRadius * rRatio)
                .attr('fill', 'none')
                .attr('stroke', theme.glowColor)
                .attr('stroke-opacity', 0.2)
                .attr('stroke-width', 1);
        });

        buckets.forEach((bucket, i) => {
            const angle = i * angleStep;
            const color = theme.colors[i % theme.colors.length];

            const x1 = cx + innerRadius * Math.sin(angle);
            const y1 = cy - innerRadius * Math.cos(angle);
            const x2 = cx + maxRadius * 0.92 * Math.sin(angle);
            const y2 = cy - maxRadius * 0.92 * Math.cos(angle);

            // Spoke ray
            spokesG.append('line')
                .attr('x1', x1)
                .attr('y1', y1)
                .attr('x2', x2)
                .attr('y2', y2)
                .attr('stroke', color)
                .attr('stroke-width', 2)
                .attr('stroke-opacity', 0.6);

            // Energy node sphere at outer rim
            const node = spokesG.append('circle')
                .attr('cx', x2)
                .attr('cy', y2)
                .attr('r', Math.min(22, Math.max(14, bucket.count * 2.5)))
                .attr('fill', color)
                .attr('fill-opacity', 0.35)
                .attr('stroke', color)
                .attr('stroke-width', 2.5)
                .style('cursor', 'pointer')
                .style('transition', 'all 0.2s');

            node
                .on('mouseover', function () {
                    d3.select(this)
                        .attr('fill-opacity', 0.75)
                        .attr('r', Math.min(26, Math.max(18, bucket.count * 2.5) + 4))
                        .attr('filter', 'url(#mandala-glow)');
                })
                .on('mouseout', () => {
                    const isSelected = this.selectedSlice && this.selectedSlice.name === bucket.name;
                    node
                        .attr('fill-opacity', isSelected ? 0.6 : 0.35)
                        .attr('r', Math.min(22, Math.max(14, bucket.count * 2.5)))
                        .attr('filter', isSelected ? 'url(#mandala-glow)' : 'none');
                })
                .on('click', () => {
                    this.selectSlice(bucket);
                })
                .on('dblclick', () => {
                    this.drillDown(bucket.name, bucket.tasks);
                });

            // Node count text
            spokesG.append('text')
                .attr('x', x2)
                .attr('y', y2 + 4)
                .attr('text-anchor', 'middle')
                .attr('fill', '#ffffff')
                .attr('font-size', '10px')
                .attr('font-weight', '800')
                .style('pointer-events', 'none')
                .text(bucket.count);

            // Label outside
            const labelX = cx + (maxRadius * 0.92 + 22) * Math.sin(angle);
            const labelY = cy - (maxRadius * 0.92 + 22) * Math.cos(angle);
            const shortName = bucket.name.length > 11 ? bucket.name.substring(0, 10) + '…' : bucket.name;

            spokesG.append('text')
                .attr('x', labelX)
                .attr('y', labelY + 3)
                .attr('text-anchor', Math.sin(angle) > 0.1 ? 'start' : (Math.sin(angle) < -0.1 ? 'end' : 'middle'))
                .attr('fill', '#e2e8f0')
                .attr('font-size', '10px')
                .attr('font-weight', '600')
                .text(shortName);
        });

        this.renderCoreHub(g, cx, cy, innerRadius, theme, allTasks);
    }

    /**
     * Central Sacred Bindu Hub (Core Total & Stats)
     */
    renderCoreHub(g, cx, cy, radius, theme, allTasks) {
        const completedTotal = allTasks.filter(t => t.status === 'completed').length;
        const total = allTasks.length;
        const percent = total > 0 ? Math.round((completedTotal / total) * 100) : 0;

        const hubG = g.append('g')
            .attr('class', 'mandala-core-hub')
            .style('cursor', 'pointer')
            .on('click', () => {
                this.selectedSlice = null;
                this.renderDrawer(allTasks, 'All Universe Tasks');
            });

        // Glowing outer core ring
        hubG.append('circle')
            .attr('cx', cx)
            .attr('cy', cy)
            .attr('r', radius)
            .attr('fill', theme.coreFill)
            .attr('stroke', theme.coreStroke)
            .attr('stroke-width', 2.5)
            .attr('filter', 'url(#mandala-glow)');

        // Inner decorative circle
        hubG.append('circle')
            .attr('cx', cx)
            .attr('cy', cy)
            .attr('r', radius * 0.78)
            .attr('fill', 'none')
            .attr('stroke', theme.glowColor)
            .attr('stroke-dasharray', '3,3')
            .attr('stroke-width', 1.5);

        // Core Text
        hubG.append('text')
            .attr('x', cx)
            .attr('y', cy - 8)
            .attr('text-anchor', 'middle')
            .attr('fill', theme.coreStroke)
            .attr('font-size', radius > 50 ? '18px' : '13px')
            .attr('font-weight', '800')
            .text(`${total}`);

        hubG.append('text')
            .attr('x', cx)
            .attr('y', cy + 8)
            .attr('text-anchor', 'middle')
            .attr('fill', '#94a3b8')
            .attr('font-size', radius > 50 ? '10px' : '8px')
            .attr('font-weight', '600')
            .text(`${percent}% DONE`);
    }

    selectSlice(bucket) {
        this.selectedSlice = bucket;
        this.renderDrawer(bucket.tasks, bucket.name);

        // Update visual highlight on petals
        d3.selectAll('.mandala-petal-slice').each(function () {
            // keep standard opacity
        });
    }

    renderDrawer(tasks, title) {
        const titleEl = document.getElementById('mandala-drawer-title');
        const subtitleEl = document.getElementById('mandala-drawer-subtitle');
        const badgeEl = document.getElementById('mandala-drawer-badge');
        const listEl = document.getElementById('mandala-drawer-list');

        if (titleEl) titleEl.textContent = title;
        if (subtitleEl) subtitleEl.textContent = `${tasks.length} task${tasks.length === 1 ? '' : 's'} in slice`;
        if (badgeEl) badgeEl.textContent = tasks.length;

        if (!listEl) return;

        if (tasks.length === 0) {
            listEl.innerHTML = `<div style="text-align: center; color: #64748b; padding: 2rem; font-size: 0.85rem;">No tasks in this slice</div>`;
            return;
        }

        listEl.innerHTML = tasks.map(task => {
            const isDone = task.status === 'completed';
            const prio = (task.priority || 'None').toUpperCase();
            let prioBg = '#334155';
            let prioColor = '#94a3b8';
            if (prio === 'HIGH') { prioBg = 'rgba(239, 68, 68, 0.2)'; prioColor = '#ef4444'; }
            else if (prio === 'MEDIUM') { prioBg = 'rgba(245, 158, 11, 0.2)'; prioColor = '#f59e0b'; }
            else if (prio === 'LOW') { prioBg = 'rgba(59, 130, 246, 0.2)'; prioColor = '#3b82f6'; }

            return `
                <div class="mandala-task-card" style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 0.6rem 0.75rem; display: flex; align-items: flex-start; gap: 0.6rem; transition: background 0.15s;"
                     onmouseover="this.style.background='rgba(255,255,255,0.06)'"
                     onmouseout="this.style.background='rgba(255,255,255,0.03)'">
                    <input type="checkbox" ${isDone ? 'checked' : ''}
                           style="margin-top: 3px; cursor: pointer; accent-color: #06b6d4;"
                           onchange="window.MandalaController.toggleTaskStatus('${task.id}', this.checked)">
                    <div style="flex: 1; min-width: 0;">
                        <div style="font-size: 0.85rem; font-weight: 600; color: ${isDone ? '#64748b' : '#f1f5f9'}; text-decoration: ${isDone ? 'line-through' : 'none'}; word-break: break-word;">
                            ${this.escapeHtml(task.title || 'Untitled Task')}
                        </div>
                        <div style="display: flex; align-items: center; gap: 6px; margin-top: 4px; flex-wrap: wrap;">
                            <span style="font-size: 0.68rem; font-weight: 700; padding: 1px 6px; border-radius: 4px; background: ${prioBg}; color: ${prioColor};">
                                ${prio}
                            </span>
                            ${task.tasklist_name ? `
                                <span style="font-size: 0.68rem; color: #94a3b8; background: rgba(0,0,0,0.3); padding: 1px 5px; border-radius: 4px;">
                                    <i class="fas fa-list-ul mr-1" style="font-size: 0.6rem;"></i>${this.escapeHtml(task.tasklist_name)}
                                </span>
                            ` : ''}
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }

    async toggleTaskStatus(taskId, completed) {
        console.log(`[Mandala] Toggle task ${taskId} to ${completed ? 'completed' : 'pending'}`);
        try {
            const basePath = window.GTASKS_BASE_PATH || '';
            let res;
            if (completed) {
                res = await fetch(`${basePath}/api/tasks/${taskId}/complete`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({})
                });
            } else {
                res = await fetch(`${basePath}/api/tasks/${taskId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ status: 'needs_action' })
                });
            }

            if (res.ok) {
                // Update local task
                const localTask = this.allTasks.find(t => t.id === taskId);
                if (localTask) {
                    localTask.status = completed ? 'completed' : 'pending';
                }
                if (window.showNotification) {
                    window.showNotification(completed ? 'Task completed ✅' : 'Task marked pending', 'success');
                }
                this.render();
            }
        } catch (e) {
            console.error('[Mandala] Error updating task status:', e);
        }
    }

    updateBreadcrumbs(totalCount) {
        const breadcrumbsEl = document.getElementById('mandala-breadcrumbs');
        const upBtn = document.getElementById('mandala-btn-up-level');
        const pillEl = document.getElementById('mandala-task-count-pill');

        if (pillEl) pillEl.textContent = `${totalCount} Task${totalCount === 1 ? '' : 's'}`;

        if (!breadcrumbsEl) return;

        let html = `<span style="cursor: pointer; color: #38bdf8;" onclick="window.MandalaController.drillToRoot()"><i class="fas fa-dharmachakra mr-1"></i> Mandala Core</span>`;

        this.drillPath.forEach((level, idx) => {
            html += ` <i class="fas fa-chevron-right" style="font-size: 0.7rem; color: #64748b;"></i> `;
            if (idx === this.drillPath.length - 1) {
                html += `<span style="color: #f8fafc;">${this.escapeHtml(level.name)}</span>`;
            } else {
                html += `<span style="cursor: pointer; color: #38bdf8;" onclick="window.MandalaController.drillToLevel(${idx})">${this.escapeHtml(level.name)}</span>`;
            }
        });

        breadcrumbsEl.innerHTML = html;
        if (upBtn) {
            upBtn.style.display = this.drillPath.length > 0 ? 'inline-flex' : 'none';
        }
    }

    drillToLevel(targetIdx) {
        this.drillPath = this.drillPath.slice(0, targetIdx + 1);
        this.selectedSlice = null;
        this.render();
    }

    escapeHtml(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }
}

// Instantiate global controller
const mandalaController = new MandalaControllerClass();
window.MandalaController = mandalaController;

export function initMandalaView() {
    if (!mandalaController.initialized) {
        mandalaController.init();
    } else {
        mandalaController.loadTasks().then(() => mandalaController.render());
    }
}
window.initMandalaView = initMandalaView;

// Hook up sidebar "+" button for saved views
window.saveCurrentWebViewDialog = () => {
    mandalaController.saveCurrentViewPrompt();
};

// Auto-load saved views on initial script load so sidebar gets populated
mandalaController.loadSavedViews();

console.log('[Mandala] Sacred Mandala module ready.');
