/**
 * Core type definitions for the GTasks Dashboard
 */

// Task Status Types
export enum TaskStatus {
  PENDING = 'pending',
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed',
  WAITING = 'waiting',
  DELETED = 'deleted'
}

// Priority Types
export enum Priority {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical'
}

// User Settings Interface
export interface UserSettings {
  show_deleted_tasks: boolean
  theme: 'light' | 'dark' | 'system'
  notifications: boolean
  default_view: 'dashboard' | 'list' | 'calendar' | 'graph'
  auto_refresh: boolean
  compact_view: boolean
  // Menu visibility settings
  menu_visible: boolean  // true by default - whether the sidebar menu is visible
  menu_animation: boolean  // enable/disable animations for menu show/hide
  keyboard_shortcuts: boolean  // enable keyboard shortcuts
}

// Task Interface
export interface Task {
  id: string
  title: string
  description?: string
  due?: string
  priority: Priority
  status: TaskStatus
  project?: string
  tags: string[]
  notes?: string
  dependencies: string[]
  recurrence_rule?: string
  created_at: string
  modified_at: string
  completed_at?: string
  estimated_duration?: number
  actual_duration?: number
  is_recurring: boolean
  recurring_task_id?: string
  tasklist_id: string
  list_title?: string
  position: number
  // Deleted task management fields
  is_deleted: boolean
  deleted_at?: string
  deleted_by?: string
}

// Account Types
export interface Account {
  id: string
  name: string
  email?: string
  avatar?: string
  isActive: boolean
  config: AccountConfig
  stats?: AccountStats
}

export interface AccountConfig {
  defaultTaskList: string
  syncEnabled: boolean
  autoSave: boolean
  notifications: boolean
  theme: 'light' | 'dark' | 'system'
  language: string
  timezone: string
}

export interface AccountStats {
  totalTasks: number
  completedTasks: number
  pendingTasks: number
  overdueTasks: number
  completionRate: number
  lastSync?: string
}

// Dashboard Data Types
export interface DashboardData {
  accounts: Account[]
  activeAccount: string
  tasks: Task[]
  categories: Category[]
  tags: Tag[]
  stats: DashboardStats
  realtime: RealtimeData
  settings?: UserSettings
}

export interface Category {
  id: string
  name: string
  color: string
  icon?: string
  taskCount: number
  tags: string[]
}

export interface Tag {
  id: string
  name: string
  color: string
  category?: string
  taskCount: number
}

export interface DashboardStats {
  totalTasks: number
  completedTasks: number
  pendingTasks: number
  overdueTasks: number
  completionRate: number
  productivityScore: number
  weeklyProgress: WeeklyProgress[]
  categoryDistribution: CategoryDistribution[]
  tagDistribution: TagDistribution[]
  deletedTasks?: number
}

export interface WeeklyProgress {
  week: string
  completed: number
  created: number
  productivity: number
}

export interface CategoryDistribution {
  category: string
  count: number
  percentage: number
  color: string
}

export interface TagDistribution {
  tag: string
  count: number
  percentage: number
}

// Real-time Data
export interface RealtimeData {
  connected: boolean
  lastUpdate: string
  activeUsers: number
  syncStatus: 'idle' | 'syncing' | 'error' | 'success'
  pendingChanges: number
}

// Graph Data for D3.js Force Graph
export interface GraphNode {
  id: string
  name: string
  group: number
  val: number
  color?: string
  category?: string
  level: 'category' | 'tag' | 'task'
}

export interface GraphLink {
  source: string | GraphNode
  target: string | GraphNode
  value: number
}

export interface GraphData {
  nodes: GraphNode[]
  links: GraphLink[]
}

// Filter and Search Types
export interface TaskFilters {
  status?: TaskStatus[]
  priority?: Priority[]
  project?: string[]
  tags?: string[]
  list?: string[]
  dueDate?: {
    from?: string
    to?: string
    type?: 'overdue' | 'today' | 'thisWeek' | 'thisMonth' | 'custom'
  }
  search?: string
  sortBy?: 'due' | 'priority' | 'created' | 'modified' | 'title'
  sortOrder?: 'asc' | 'desc'
  includeDeleted?: boolean
}

// API Response Types
export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  error?: string
  message?: string
  timestamp: string
}

export interface PaginatedResponse<T = any> extends ApiResponse<T[]> {
  pagination: {
    page: number
    limit: number
    total: number
    totalPages: number
  }
}

// MCP (Model Context Protocol) Types
export interface MCPMessage {
  id: string
  type: 'request' | 'response' | 'notification'
  method?: string
  params?: any
  result?: any
  error?: string
  timestamp: string
}

export interface MCPTool {
  name: string
  description: string
  parameters: Record<string, any>
}

// WebSocket Event Types
export interface WebSocketEvent {
  type: 'task_updated' | 'task_created' | 'task_deleted' | 'sync_started' | 'sync_completed' | 'account_switched'
  data: any
  accountId?: string
  timestamp: string
}

// Configuration Types
export interface DashboardConfig {
  general: {
    refreshInterval: number
    autoRefresh: boolean
    showCompleted: boolean
    compactView: boolean
    defaultView: 'dashboard' | 'list' | 'calendar' | 'graph'
  }
  notifications: {
    enabled: boolean
    desktop: boolean
    sound: boolean
    overdue: boolean
    dueSoon: boolean
  }
  appearance: {
    theme: 'light' | 'dark' | 'system'
    accentColor: string
    fontSize: 'small' | 'medium' | 'large'
    density: 'compact' | 'comfortable' | 'spacious'
  }
  accounts: {
    autoSwitch: boolean
    showAllAccounts: boolean
    defaultAccount: string
  }
}

// Error Types
export interface DashboardError {
  code: string
  message: string
  details?: any
  timestamp: string
  recoverable: boolean
}

// Form Types
export interface CreateTaskForm {
  title: string
  description?: string
  due?: string
  priority: Priority
  project?: string
  tags: string[]
  notes?: string
  estimatedDuration?: number
  recurrenceRule?: string
}

export interface UpdateTaskForm extends Partial<CreateTaskForm> {
  id: string
  status?: TaskStatus
}

// Chart Data Types
export interface ChartData {
  labels: string[]
  datasets: ChartDataset[]
}

export interface ChartDataset {
  label: string
  data: number[]
  backgroundColor?: string | string[]
  borderColor?: string | string[]
  borderWidth?: number
}

// Calendar Types
export interface CalendarEvent {
  id: string
  title: string
  start: Date
  end?: Date
  allDay?: boolean
  color?: string
  task?: Task
}

// Export Utility Types
export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P]
}

export type Optional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>

export type RequiredKeys<T> = {
  [K in keyof T]-?: {} extends Pick<T, K> ? never : K
}[keyof T]

export type OptionalKeys<T> = {
  [K in keyof T]-?: {} extends Pick<T, K> ? K : never
}[keyof T]