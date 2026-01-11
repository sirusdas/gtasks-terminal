import express from 'express'
import cors from 'cors'
import helmet from 'helmet'
import compression from 'compression'
import { createServer } from 'http'
import { Server as SocketIOServer } from 'socket.io'
import morgan from 'morgan'
import rateLimit from 'express-rate-limit'
import dotenv from 'dotenv'

// Import our custom modules
import { GTasksIntegration } from './integrations/gtasks'
import { MCPIntegration } from './integrations/mcp'
import { WebSocketManager } from './websocket'
import { TaskRoutes } from './routes/tasks'
import { AccountRoutes } from './routes/accounts'
import { DashboardRoutes } from './routes/dashboard'
import { MCPMessageRoutes } from './routes/mcp'
import { SyncRoutes } from './routes/sync'
import { ConfigRoutes } from './routes/config'
import { errorHandler } from './middleware/errorHandler'
import { authMiddleware } from './middleware/auth'
import { logger } from './utils/logger'

// Load environment variables
dotenv.config()

const app = express()
const httpServer = createServer(app)
const io = new SocketIOServer(httpServer, {
  cors: {
    origin: process.env.CLIENT_URL || 'http://localhost:3000',
    methods: ['GET', 'POST'],
    credentials: true
  }
})

const PORT = process.env.PORT || 8080
const GTASKS_CLI_PATH = process.env.GTASKS_CLI_PATH || '../gtasks_cli'

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // limit each IP to 100 requests per windowMs
  message: 'Too many requests from this IP, please try again later.',
  standardHeaders: true,
  legacyHeaders: false,
})

// Middleware
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      scriptSrc: ["'self'"],
      imgSrc: ["'self'", "data:", "https:"],
      connectSrc: ["'self'", "ws:", "wss:"],
    },
  },
}))

app.use(cors({
  origin: process.env.CLIENT_URL || 'http://localhost:3000',
  credentials: true
}))

app.use(compression())
app.use(express.json({ limit: '10mb' }))
app.use(express.urlencoded({ extended: true }))
app.use(morgan('combined'))
app.use(limiter)

// Initialize integrations
const gtasksIntegration = new GTasksIntegration(GTASKS_CLI_PATH)
const mcpIntegration = new MCPIntegration()
const wsManager = new WebSocketManager(io)

// Health check endpoint
app.get('/api/health', (req, res) => {
  res.json({
    success: true,
    data: {
      status: 'healthy',
      version: '2.0.0',
      timestamp: new Date().toISOString(),
      uptime: process.uptime(),
      memory: process.memoryUsage()
    }
  })
})

// Auth middleware (for now, just sets a default user)
app.use(authMiddleware)

// API Routes
app.use('/api/tasks', TaskRoutes(gtasksIntegration, wsManager))
app.use('/api/accounts', AccountRoutes(gtasksIntegration))
app.use('/api/dashboard', DashboardRoutes(gtasksIntegration))
app.use('/api/mcp', MCPMessageRoutes(mcpIntegration))
app.use('/api/sync', SyncRoutes(gtasksIntegration, wsManager))
app.use('/api/config', ConfigRoutes())

// MCP Integration endpoint
app.get('/api/mcp/tools', async (req, res) => {
  try {
    const tools = await mcpIntegration.getTools()
    res.json({
      success: true,
      data: tools
    })
  } catch (error) {
    logger.error('Failed to get MCP tools:', error)
    res.status(500).json({
      success: false,
      error: 'Failed to get MCP tools',
      timestamp: new Date().toISOString()
    })
  }
})

// MCP WebSocket endpoint for real-time communication
app.post('/api/mcp/websocket', async (req, res) => {
  try {
    const { message } = req.body
    const response = await mcpIntegration.processMessage(message)
    
    // Emit response to WebSocket clients
    wsManager.emitToAll('mcp_response', response)
    
    res.json({
      success: true,
      data: response
    })
  } catch (error) {
    logger.error('MCP WebSocket error:', error)
    res.status(500).json({
      success: false,
      error: 'MCP processing failed',
      timestamp: new Date().toISOString()
    })
  }
})

// Static file serving for production
if (process.env.NODE_ENV === 'production') {
  app.use(express.static('dist'))
  
  app.get('*', (req, res) => {
    res.sendFile('index.html', { root: 'dist' })
  })
}

// Error handling
app.use(errorHandler)

// WebSocket connection handling
io.on('connection', (socket) => {
  logger.info(`Client connected: ${socket.id}`)
  
  socket.on('join_account', (accountId: string) => {
    socket.join(`account:${accountId}`)
    logger.info(`Client ${socket.id} joined account: ${accountId}`)
  })
  
  socket.on('leave_account', (accountId: string) => {
    socket.leave(`account:${accountId}`)
    logger.info(`Client ${socket.id} left account: ${accountId}`)
  })
  
  socket.on('mcp_message', async (message: any) => {
    try {
      const response = await mcpIntegration.processMessage(message)
      socket.emit('mcp_response', response)
    } catch (error) {
      logger.error('MCP WebSocket processing error:', error)
      socket.emit('mcp_error', { error: 'MCP processing failed' })
    }
  })
  
  socket.on('disconnect', () => {
    logger.info(`Client disconnected: ${socket.id}`)
  })
})

// Graceful shutdown
process.on('SIGTERM', () => {
  logger.info('SIGTERM received, shutting down gracefully')
  httpServer.close(() => {
    logger.info('Process terminated')
    process.exit(0)
  })
})

process.on('SIGINT', () => {
  logger.info('SIGINT received, shutting down gracefully')
  httpServer.close(() => {
    logger.info('Process terminated')
    process.exit(0)
  })
})

// Start server
httpServer.listen(PORT, () => {
  logger.info(`🚀 GTasks Dashboard Server running on port ${PORT}`)
  logger.info(`📊 Dashboard API: http://localhost:${PORT}/api`)
  logger.info(`🔌 WebSocket: ws://localhost:${PORT}`)
  logger.info(`💬 MCP Integration: http://localhost:${PORT}/api/mcp`)
})

export { app, io, gtasksIntegration, mcpIntegration, wsManager }