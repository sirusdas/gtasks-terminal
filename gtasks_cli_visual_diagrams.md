# GTasks-CLI System Architecture Visual Diagram

```mermaid
graph TB
    %% CLI Layer
    CLI["CLI Entry Point<br/>main.py"]
    
    %% Commands Layer
    subgraph Commands["Commands Layer"]
        ADD["add.py"]
        LIST["list.py"]
        SEARCH["search.py"]
        VIEW["view.py"]
        DONE["done.py"]
        DELETE["delete.py"]
        UPDATE["update.py"]
        INTERACTIVE["interactive.py"]
        ADVANCED_SYNC["advanced_sync.py"]
        DEDUPLICATE["deduplicate.py"]
        REPORT["generate_report.py"]
        CONFIG["config.py"]
        ACCOUNT["account.py"]
        AUTH["auth.py"]
    end
    
    %% Core Layer
    subgraph Core["Core Business Logic"]
        TASK_MGR["TaskManager"]
    end
    
    %% Storage Layer
    subgraph Storage["Storage Layer"]
        CONFIG_MGR["ConfigManager"]
        SQLITE["SQLiteStorage"]
        LOCAL["LocalStorage"]
    end
    
    %% Integration Layer
    subgraph Integration["Integration Layer"]
        GTC["GoogleTasksClient"]
        GOOGLE_AUTH["GoogleAuth"]
        SYNC_MGR["SyncManager"]
        ADV_SYNC_MGR["AdvancedSyncManager"]
    end
    
    %% Models Layer
    subgraph Models["Data Models"]
        TASK_MODEL["Task Model"]
        TASKLIST_MODEL["TaskList Model"]
    end
    
    %% Reports Layer
    subgraph Reports["Reports Layer"]
        BASE_REPORT["Base Report"]
        COMPLETION_REPORT["Completion Report"]
        CREATION_REPORT["Creation Report"]
        DISTRIBUTION_REPORT["Distribution Report"]
        TIMELINE_REPORT["Timeline Report"]
        OVERDUE_REPORT["Overdue Report"]
        PENDING_REPORT["Pending Report"]
        FUTURE_REPORT["Future Timeline"]
        ORGANIZED_REPORT["Organized Tasks"]
        CUSTOM_REPORT["Custom Filtered"]
        RATE_REPORT["Completion Rate"]
    end
    
    %% Utils Layer
    subgraph Utils["Utilities Layer"]
        DT_UTILS["DateTime Utils"]
        DISPLAY["Display Utils"]
        DEDUP_UTILS["Deduplication Utils"]
        TAG_UTILS["Tag Extractor"]
        EMAIL["Email Sender"]
        LOGGER["Logger"]
        EXCEPTIONS["Exceptions"]
    end
    
    %% External Systems
    subgraph External["External Systems"]
        GOOGLE_API["Google Tasks API"]
        SMTP["SMTP Server"]
        FS["File System"]
        DB["SQLite Database"]
    end
    
    %% Main Flow Connections
    CLI --> Commands
    CLI --> TASK_MGR
    
    %% Command to TaskManager
    ADD --> TASK_MGR
    LIST --> TASK_MGR
    SEARCH --> TASK_MGR
    VIEW --> TASK_MGR
    DONE --> TASK_MGR
    DELETE --> TASK_MGR
    UPDATE --> TASK_MGR
    INTERACTIVE --> TASK_MGR
    ADVANCED_SYNC --> TASK_MGR
    DEDUPLICATE --> TASK_MGR
    REPORT --> TASK_MGR
    CONFIG --> TASK_MGR
    ACCOUNT --> TASK_MGR
    AUTH --> TASK_MGR
    
    %% TaskManager to Storage
    TASK_MGR --> Storage
    TASK_MGR --> Integration
    
    %% Storage Connections
    TASK_MGR --> CONFIG_MGR
    TASK_MGR --> SQLITE
    TASK_MGR --> LOCAL
    
    %% Integration Connections
    TASK_MGR --> GTC
    TASK_MGR --> SYNC_MGR
    TASK_MGR --> ADV_SYNC_MGR
    
    GTC --> GOOGLE_AUTH
    SYNC_MGR --> GTC
    ADV_SYNC_MGR --> GTC
    
    %% Models Connections
    TASK_MGR --> TASK_MODEL
    TASK_MGR --> TASKLIST_MODEL
    
    %% Reports Connections
    REPORT --> Reports
    REPORT --> TASK_MODEL
    
    %% Utils Connections
    LIST --> DISPLAY
    INTERACTIVE --> DISPLAY
    DEDUPLICATE --> DEDUPLICATE_UTILS
    DEDUPLICATE --> TAG_UTILS
    SYNC_MGR --> DEDUPLICATE_UTILS
    SYNC_MGR --> DT_UTILS
    REPORT --> DT_UTILS
    REPORT --> EMAIL
    ALL[".*"] --> LOGGER
    ALL[".*"] --> EXCEPTIONS
    
    %% External Connections
    GTC --> GOOGLE_API
    EMAIL --> SMTP
    CONFIG_MGR --> FS
    SQLITE --> DB
    LOCAL --> FS
    
    %% Styling
    classDef cliLayer fill:#e1f5fe
    classDef commandLayer fill:#f3e5f5
    classDef coreLayer fill:#e8f5e8
    classDef storageLayer fill:#fff3e0
    classDef integrationLayer fill:#fce4ec
    classDef modelsLayer fill:#e0f2f1
    classDef reportsLayer fill:#f1f8e9
    classDef utilsLayer fill:#fff8e1
    classDef externalLayer fill:#ffebee
    
    class CLI cliLayer
    class Commands commandLayer
    class TASK_MGR coreLayer
    class Storage storageLayer
    class Integration integrationLayer
    class Models modelsLayer
    class Reports reportsLayer
    class Utils utilsLayer
    class External externalLayer
```

## Data Flow Diagram

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant Commands
    participant TaskManager
    participant Storage
    participant GoogleAPI
    
    User->>CLI: Execute command
    CLI->>Commands: Route command
    Commands->>TaskManager: Process operation
    
    alt Local Operation
        TaskManager->>Storage: Save/Load tasks
        Storage-->>TaskManager: Return data
    else Google Tasks Operation
        TaskManager->>GoogleAPI: API calls
        GoogleAPI-->>TaskManager: Return data
        TaskManager->>Storage: Cache data
    end
    
    TaskManager-->>Commands: Return result
    Commands-->>CLI: Format output
    CLI-->>User: Display result
```

## Storage Architecture

```mermaid
graph LR
    subgraph Storage["Storage Architecture"]
        CONFIG["Configuration<br/>YAML Files"]
        TASKS_DB["SQLite Database<br/>tasks.db"]
        JSON_FILES["JSON Files<br/>tasks.json"]
        TOKENS["Auth Tokens<br/>token.pickle"]
        CREDENTIALS["Credentials<br/>credentials.json"]
    end
    
    subgraph Account["Multi-Account Structure"]
        DEFAULT["~/.gtasks/<br/>Default Account"]
        WORK["~/.gtasks/work/<br/>Work Account"]
        PERSONAL["~/.gtasks/personal/<br/>Personal Account"]
    end
    
    DEFAULT --> CONFIG
    DEFAULT --> TASKS_DB
    DEFAULT --> JSON_FILES
    DEFAULT --> TOKENS
    DEFAULT --> CREDENTIALS
    
    WORK --> CONFIG
    WORK --> TASKS_DB
    WORK --> JSON_FILES
    WORK --> TOKENS
    WORK --> CREDENTIALS
    
    PERSONAL --> CONFIG
    PERSONAL --> TASKS_DB
    PERSONAL --> JSON_FILES
    PERSONAL --> TOKENS
    PERSONAL --> CREDENTIALS
    
    classDef config fill:#e3f2fd
    classDef storage fill:#f1f8e9
    classDef auth fill:#fce4ec
    
    class CONFIG,TASKS_DB,JSON_FILES storage
    class TOKENS,CREDENTIALS auth
```

## Sync Architecture

```mermaid
graph TB
    subgraph Local["Local Environment"]
        LOCAL_TASKS["Local Tasks"]
        SYNC_MGR["SyncManager"]
        CONFLICT_RES["Conflict Resolution"]
    end
    
    subgraph Google["Google Tasks"]
        GOOGLE_TASKS["Google Tasks"]
        TASK_LISTS["Task Lists"]
    end
    
    subgraph Process["Sync Process"]
        UPLOAD["Upload Local → Google"]
        DOWNLOAD["Download Google → Local"]
        MERGE["Merge Changes"]
        DEDUP["Remove Duplicates"]
        LOG["Log Changes"]
    end
    
    LOCAL_TASKS --> SYNC_MGR
    GOOGLE_TASKS --> SYNC_MGR
    
    SYNC_MGR --> UPLOAD
    SYNC_MGR --> DOWNLOAD
    SYNC_MGR --> MERGE
    SYNC_MGR --> DEDUP
    SYNC_MGR --> LOG
    
    UPLOAD --> GOOGLE_TASKS
    DOWNLOAD --> LOCAL_TASKS
    MERGE --> CONFLICT_RES
    
    classDef local fill:#e8f5e8
    classDef google fill:#e3f2fd
    classDef process fill:#fff3e0
    
    class LOCAL_TASKS local
    class GOOGLE_TASKS,TASK_LISTS google
    class SYNC_MGR,UPLOAD,DOWNLOAD,MERGE,DEDUP,LOG,CONFLICT_RES process
```

## Interactive Mode Architecture

```mermaid
stateDiagram-v2
    [*] --> StartInteractive
    
    StartInteractive --> DisplayTasks : Load initial tasks
    DisplayTasks --> WaitCommand : Show numbered list
    
    WaitCommand --> ProcessCommand : User input
    
    ProcessCommand --> ViewTask : view <number>
    ProcessCommand --> CompleteTask : done <number>
    ProcessCommand --> DeleteTask : delete <number>
    ProcessCommand --> UpdateTask : update <number>
    ProcessCommand --> AddTask : add
    ProcessCommand --> SearchTasks : search <query>
    ProcessCommand --> FilterTasks : list --filter
    ProcessCommand --> BackCommand : back
    ProcessCommand --> DefaultCommand : default
    ProcessCommand --> HelpCommand : help
    ProcessCommand --> QuitInteractive : quit/exit
    
    ViewTask --> WaitCommand : Back to list
    CompleteTask --> DisplayTasks : Update display
    DeleteTask --> DisplayTasks : Update display
    UpdateTask --> DisplayTasks : Update display
    AddTask --> DisplayTasks : Update display
    SearchTasks --> DisplayTasks : Show results
    FilterTasks --> DisplayTasks : Show filtered
    BackCommand --> DisplayTasks : Previous view
    DefaultCommand --> DisplayTasks : Default view
    HelpCommand --> WaitCommand : Show help
    QuitInteractive --> [*] : Exit
    
    DisplayTasks --> WaitCommand : Ready for next command
```

This visual representation complements the detailed mindmap and shows:

1. **System Architecture** - How all layers connect and interact
2. **Data Flow** - The sequence of operations from user input to storage
3. **Storage Structure** - Multi-account file organization
4. **Sync Process** - Bi-directional synchronization workflow  
5. **Interactive Mode** - State machine for interactive command processing

The diagrams illustrate the modular, layered architecture that makes GTasks-CLI flexible, maintainable, and feature-rich while supporting both local and cloud-based task management.