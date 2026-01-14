        function filterNodeTasks(node) {
            const relatedTasks = getRelatedTasks(node);
            
            // Apply current filters
            const statusFilter = document.getElementById('node-task-status-filter').value;
            const priorityFilter = document.getElementById('node-task-priority-filter').value;
            const searchFilter = document.getElementById('node-task-search-filter').value.toLowerCase();
            const projectFilter = document.getElementById('node-task-project-filter').value.toLowerCase();
            const tagsFilter = document.getElementById('node-task-tags-filter').value.toLowerCase();
            const dueDateStart = document.getElementById('node-task-due-date-start').value;
            const dueDateEnd = document.getElementById('node-task-due-date-end').value;
            const createdDateStart = document.getElementById('node-task-created-date-start').value;
            const createdDateEnd = document.getElementById('node-task-created-date-end').value;
            
            let filteredTasks = relatedTasks;
            
            if (statusFilter) {
                filteredTasks = filteredTasks.filter(task => task.status === statusFilter);
            }
            
            if (priorityFilter) {
                filteredTasks = filteredTasks.filter(task =>
                    task.calculated_priority === priorityFilter || task.priority === priorityFilter
                );
            }
            
            if (searchFilter) {
                filteredTasks = filteredTasks.filter(task =>
                    task.title.toLowerCase().includes(searchFilter) ||
                    (task.description && task.description.toLowerCase().includes(searchFilter))
                );
            }
            
            if (projectFilter) {
                filteredTasks = filteredTasks.filter(task =>
                    task.project && task.project.toLowerCase().includes(projectFilter)
                );
            }
            
            if (tagsFilter) {
                const tagsArray = tagsFilter.split(',').map(tag => tag.trim()).filter(tag => tag);
                if (tagsArray.length > 0) {
                    filteredTasks = filteredTasks.filter(task => {
                        const taskTags = [
                            ...task.hybrid_tags?.bracket || [],
                            ...task.hybrid_tags?.hash || [],
                            ...task.hybrid_tags?.user || [],
                            ...(task.tags || [])
                        ];
                        return tagsArray.some(filterTag => 
                            taskTags.some(taskTag => taskTag.toLowerCase().includes(filterTag))
                        );
                    });
                }
            }
            
            if (dueDateStart) {
                filteredTasks = filteredTasks.filter(task => {
                    if (!task.due) return false;
                    return new Date(task.due) >= new Date(dueDateStart);
                });
            }
            
            if (dueDateEnd) {
                filteredTasks = filteredTasks.filter(task => {
                    if (!task.due) return false;
                    return new Date(task.due) <= new Date(dueDateEnd);
                });
            }
            
            if (createdDateStart) {
                filteredTasks = filteredTasks.filter(task => {
                    if (!task.created_at) return false;
                    return new Date(task.created_at) >= new Date(createdDateStart);
                });
            }
            
            if (createdDateEnd) {
                filteredTasks = filteredTasks.filter(task => {
                    if (!task.created_at) return false;
                    return new Date(task.created_at) <= new Date(createdDateEnd);
                });
            }
            
            displayNodeTasks(filteredTasks, node);
        }