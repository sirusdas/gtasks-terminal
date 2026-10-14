import 'package:flutter/material.dart';
import '../api/api_client.dart';
import '../api/google_tasks_direct_client.dart';
import '../models/task_item.dart';
import '../models/account.dart';
import '../storage/local_database.dart';
import '../utils/notes_parser.dart';

class TaskProvider with ChangeNotifier {
  final ApiClient apiClient;
  final LocalDatabase localDb = LocalDatabase.instance;
  GoogleTasksDirectClient? _googleClient;
  bool _isStandalone = false;

  List<TaskItem> _tasks = [];
  List<GTasksAccount> _accounts = [];
  String _selectedAccount = 'all';
  String _statusFilter = 'pending'; // 'pending', 'completed', 'all'
  String _searchQuery = '';
  Set<String> _selectedLists = {};
  Set<String> _selectedTags = {};
  String? _selectedPriority; // 'critical', 'high', 'medium', 'low'
  Set<String> _hiddenLists = {};
  Set<String> _hiddenTags = {};
  bool _hideRecurring = false;
  String _sortField = 'modified_at'; // 'modified_at', 'due', 'created_at', 'priority', 'title'
  bool _sortAscending = false;
  DateTimeRange? _dateRange;
  String _dateField = 'modified_at'; // 'modified_at', 'created_at', 'due'
  bool _isLoading = false;
  String? _errorMessage;

  TaskProvider({
    required this.apiClient,
    bool isStandalone = false,
    String? googleAccessToken,
    String? googleRefreshToken,
    void Function(String)? onTokenRefreshed,
  }) {
    _isStandalone = isStandalone;
    _onTokenRefreshed = onTokenRefreshed;
    if (googleAccessToken != null && googleAccessToken.isNotEmpty) {
      _googleClient = GoogleTasksDirectClient(
        accessToken: googleAccessToken,
        refreshToken: googleRefreshToken,
        onTokenRefreshed: onTokenRefreshed,
      );
    }
  }

  Map<String, Map<String, dynamic>> _standaloneAccounts = {};
  Set<String> _deletedAccounts = {};
  void Function(String)? _onTokenRefreshed;

  void updateConfig({
    required String newUrl,
    required bool isStandalone,
    String? googleAccessToken,
    String? googleRefreshToken,
    void Function(String)? onTokenRefreshed,
    Map<String, Map<String, dynamic>>? standaloneAccounts,
    Set<String>? deletedAccounts,
  }) {
    if (onTokenRefreshed != null) {
      _onTokenRefreshed = onTokenRefreshed;
    }
    bool needsReload = false;
    if (apiClient.baseUrl != newUrl) {
      apiClient.baseUrl = newUrl;
      needsReload = true;
    }
    if (_isStandalone != isStandalone) {
      _isStandalone = isStandalone;
      needsReload = true;
    }
    if (standaloneAccounts != null) {
      if (_standaloneAccounts.toString() != standaloneAccounts.toString()) {
        _standaloneAccounts = standaloneAccounts;
        needsReload = true;
      }
    }
    if (deletedAccounts != null) {
      if (_deletedAccounts.toString() != deletedAccounts.toString()) {
        _deletedAccounts = deletedAccounts;
        needsReload = true;
      }
    }
    if (googleAccessToken != null && googleAccessToken.isNotEmpty) {
      _googleClient = GoogleTasksDirectClient(
        accessToken: googleAccessToken,
        refreshToken: googleRefreshToken,
        onTokenRefreshed: _onTokenRefreshed,
      );
    } else {
      _googleClient = null;
    }

    if (needsReload) {
      loadInitialData();
    }
  }

  Future<void> removeAccount(String accountId, {bool isHardDelete = false}) async {
    if (isHardDelete) {
      _deletedAccounts.add(accountId);
      if (accountId == 'default' || accountId == 'personal') {
        _deletedAccounts.add('default');
        _deletedAccounts.add('personal');
      }
    }
    _accounts.removeWhere((a) =>
        a.id == accountId ||
        ((accountId == 'default' || accountId == 'personal') &&
            (a.id == 'default' || a.id == 'personal')));

    await localDb.clearAllTasks(account: accountId);
    if (accountId == 'default' || accountId == 'personal') {
      await localDb.clearAllTasks(account: 'default');
      await localDb.clearAllTasks(account: 'personal');
    }

    if (_accounts.isEmpty) {
      await localDb.clearAllTasks();
      _tasks = [];
      _selectedAccount = 'all';
    } else if (_selectedAccount == accountId) {
      _selectedAccount = _accounts.first.id;
    }

    await refreshTasks();
    notifyListeners();
  }

  Future<void> restoreAccount(String accountId) async {
    _deletedAccounts.remove(accountId);
    if (accountId == 'default' || accountId == 'personal') {
      _deletedAccounts.remove('default');
      _deletedAccounts.remove('personal');
    }
    try {
      await apiClient.restoreAccount(accountId);
    } catch (_) {}
    await loadInitialData();
  }

  Future<void> restoreAllAccounts() async {
    _deletedAccounts.clear();
    try {
      await apiClient.restoreAccount('default');
    } catch (_) {}
    await loadInitialData();
  }

  void updateBaseUrl(String newUrl) {
    updateConfig(
      newUrl: newUrl,
      isStandalone: _isStandalone,
      googleAccessToken: _googleClient?.accessToken,
    );
  }

  bool get isStandalone => _isStandalone;

  List<TaskItem> _filteredTasksCache = [];
  Map<String, int> _listsWithCountsCache = {};
  Map<String, int> _tagsWithCountsCache = {};
  int _pendingTasksCountCache = 0;

  List<TaskItem> get tasks => _filteredTasksCache;
  List<TaskItem> get allTasksUnfiltered => _tasks;
  List<GTasksAccount> get accounts => _accounts;
  String get selectedAccount => _selectedAccount;
  String get statusFilter => _statusFilter;
  String get searchQuery => _searchQuery;
  Set<String> get selectedLists => _selectedLists;
  Set<String> get selectedTags => _selectedTags;
  String? get selectedList => _selectedLists.isNotEmpty ? _selectedLists.first : null;
  String? get selectedTag => _selectedTags.isNotEmpty ? _selectedTags.first : null;
  String? get selectedPriority => _selectedPriority;
  Set<String> get hiddenLists => _hiddenLists;
  Set<String> get hiddenTags => _hiddenTags;
  bool get hideRecurring => _hideRecurring;
  String get sortField => _sortField;
  bool get sortAscending => _sortAscending;
  DateTimeRange? get dateRange => _dateRange;
  String get dateField => _dateField;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;

  bool get hasActiveFilters {
    return _selectedLists.isNotEmpty ||
        _selectedTags.isNotEmpty ||
        _selectedPriority != null ||
        _hiddenLists.isNotEmpty ||
        _hiddenTags.isNotEmpty ||
        _hideRecurring ||
        _dateRange != null;
  }

  // Active filter count for badge
  int get activeFilterCount {
    int count = 0;
    if (_selectedLists.isNotEmpty) count += _selectedLists.length;
    if (_selectedTags.isNotEmpty) count += _selectedTags.length;
    if (_selectedPriority != null) count++;
    if (_hiddenLists.isNotEmpty) count += _hiddenLists.length;
    if (_hiddenTags.isNotEmpty) count += _hiddenTags.length;
    if (_hideRecurring) count++;
    if (_dateRange != null) count++;
    if (_statusFilter != 'pending') count++;
    return count;
  }

  int get pendingTasksCount => _pendingTasksCountCache;
  Map<String, int> get listsWithCounts => _listsWithCountsCache;
  Map<String, int> get tagsWithCounts => _tagsWithCountsCache;

  void _recomputeAllCaches() {
    _recomputeAggregates();
    _recomputeFilteredTasks();
  }

  void _recomputeAggregates() {
    int pendingCount = 0;
    final Map<String, int> listMap = {};
    final Map<String, int> tagMap = {};

    for (final task in _tasks) {
      if (_selectedAccount != 'all' && task.account != _selectedAccount) continue;
      if (task.isCompleted) continue; // Only count pending tasks
      pendingCount++;

      final list = (task.listTitle != null && task.listTitle!.isNotEmpty)
          ? task.listTitle!
          : 'Default List';
      listMap[list] = (listMap[list] ?? 0) + 1;

      for (final tag in task.allTags) {
        if (tag.trim().isNotEmpty) {
          tagMap[tag] = (tagMap[tag] ?? 0) + 1;
        }
      }
    }

    _pendingTasksCountCache = pendingCount;
    _listsWithCountsCache = listMap;
    _tagsWithCountsCache = tagMap;
  }

  void _recomputeFilteredTasks() {
    _filteredTasksCache = _filteredTasks();
  }

  List<TaskItem> _filteredTasks() {
    if (_accounts.isEmpty) {
      return [];
    }

    final validAccountIds = _accounts.map((a) => a.id).toSet();
    var result = _tasks.where((task) {
      if (!validAccountIds.contains(task.account)) {
        return false;
      }
      if (_selectedAccount != 'all' && task.account != _selectedAccount) {
        return false;
      }
      if (_statusFilter == 'pending' && task.isCompleted) {
        return false;
      }
      if (_statusFilter == 'completed' && !task.isCompleted) {
        return false;
      }
      final taskListTitle = (task.listTitle != null && task.listTitle!.isNotEmpty)
          ? task.listTitle!
          : 'Default List';

      // Hide lists exclusion
      if (_hiddenLists.contains(taskListTitle)) {
        return false;
      }

      // Hide tags exclusion
      if (_hiddenTags.isNotEmpty && task.allTags.any((t) => _hiddenTags.contains(t))) {
        return false;
      }

      // Hide recurring tasks exclusion
      if (_hideRecurring && task.isRecurring) {
        return false;
      }

      if (_selectedLists.isNotEmpty) {
        if (!_selectedLists.contains(taskListTitle)) return false;
      }
      if (_selectedTags.isNotEmpty) {
        if (!task.allTags.any((t) => _selectedTags.contains(t))) return false;
      }
      if (_selectedPriority != null) {
        if (task.calculatedPriority.toLowerCase() != _selectedPriority!.toLowerCase()) {
          return false;
        }
      }
      if (_dateRange != null) {
        String? targetDateStr;
        if (_dateField == 'due') {
          targetDateStr = task.due;
        } else if (_dateField == 'created_at') {
          targetDateStr = task.createdAt;
        } else {
          targetDateStr = task.createdAt; // fallback to created
        }

        if (targetDateStr == null) return false;
        try {
          final dt = DateTime.parse(targetDateStr);
          if (dt.isBefore(_dateRange!.start) || dt.isAfter(_dateRange!.end.add(const Duration(days: 1)))) {
            return false;
          }
        } catch (_) {}
      }
      if (_searchQuery.isNotEmpty) {
        final query = _searchQuery.toLowerCase();
        final matchTitle = task.title.toLowerCase().contains(query);
        final matchNotes = task.description.toLowerCase().contains(query);
        final matchTags = task.allTags.any((t) => t.toLowerCase().contains(query));
        return matchTitle || matchNotes || matchTags;
      }
      return true;
    }).toList();

    // Sorting
    result.sort((a, b) {
      int comparison = 0;
      switch (_sortField) {
        case 'title':
          comparison = a.title.toLowerCase().compareTo(b.title.toLowerCase());
          break;
        case 'due':
          if (a.due == null && b.due == null) {
            comparison = 0;
          } else if (a.due == null) {
            comparison = 1;
          } else if (b.due == null) {
            comparison = -1;
          } else {
            comparison = a.due!.compareTo(b.due!);
          }
          break;
        case 'created_at':
          final aDate = a.createdAt ?? '';
          final bDate = b.createdAt ?? '';
          comparison = aDate.compareTo(bDate);
          break;
        case 'priority':
          final pMap = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1};
          final ap = pMap[a.calculatedPriority.toLowerCase()] ?? 0;
          final bp = pMap[b.calculatedPriority.toLowerCase()] ?? 0;
          comparison = ap.compareTo(bp);
          break;
        case 'modified_at':
        default:
          final aDate = a.createdAt ?? '';
          final bDate = b.createdAt ?? '';
          comparison = aDate.compareTo(bDate);
          break;
      }
      return _sortAscending ? comparison : -comparison;
    });

    return result;
  }

  Future<void> loadInitialData() async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      if (_isStandalone) {
        if (_standaloneAccounts.isNotEmpty) {
          _accounts = _standaloneAccounts.values
              .map((acc) => GTasksAccount(
                    id: acc['id']?.toString() ?? 'default',
                    name: acc['name']?.toString() ?? 'Personal',
                  ))
              .toList();
        } else if (_googleClient != null) {
          _accounts = [GTasksAccount(id: 'default', name: 'Personal (Google)')];
        } else {
          // Check if server accounts can be discovered
          try {
            final serverAccs = await apiClient.fetchAccounts();
            if (serverAccs.isNotEmpty) {
              _accounts = serverAccs;
            } else {
              _accounts = [];
            }
          } catch (_) {
            _accounts = [];
          }
        }
      } else {
        final accountsList = await apiClient.fetchAccounts();
        _accounts = accountsList;
      }
      _accounts = _accounts.where((a) => !_deletedAccounts.contains(a.id)).toList();
      await refreshTasks();
    } catch (e) {
      _errorMessage = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> refreshTasks() async {
    try {
      if (_accounts.isEmpty) {
        _tasks = [];
        _errorMessage = null;
        _recomputeAllCaches();
        notifyListeners();
        return;
      }

      final validAccountIds = _accounts.map((a) => a.id).toSet();

      if (_isStandalone) {
        if (_selectedAccount != 'all' && validAccountIds.contains(_selectedAccount)) {
          final localTasks = await localDb.getAllTasks(account: _selectedAccount);
          _tasks = localTasks;
        } else {
          // 'all' configured accounts only
          List<TaskItem> allTasks = [];
          for (final acc in _accounts) {
            final accTasks = await localDb.getAllTasks(account: acc.id);
            allTasks.addAll(accTasks);
          }
          _tasks = allTasks;
        }
        _errorMessage = null;
      } else {
        if (_selectedAccount != 'all' && validAccountIds.contains(_selectedAccount)) {
          final taskList = await apiClient.fetchTasks(account: _selectedAccount);
          _tasks = taskList;
        } else {
          // 'all' configured accounts only
          List<TaskItem> allTasks = [];
          for (final acc in _accounts) {
            try {
              final accTasks = await apiClient.fetchTasks(account: acc.id);
              allTasks.addAll(accTasks);
            } catch (_) {}
          }
          _tasks = allTasks;
        }
        _errorMessage = null;
      }
    } catch (e) {
      _errorMessage = e.toString();
    }
    _recomputeAllCaches();
    notifyListeners();
  }

  Future<bool> syncGoogleTasks({String? account, bool syncAll = false}) async {
    final targetAccount = account ?? _selectedAccount;

    if (!_isStandalone) {
      _isLoading = true;
      notifyListeners();
      try {
        if (targetAccount == 'all') {
          // Sync all accounts
          bool allSuccess = true;
          for (final acc in _accounts) {
            final res = await apiClient.triggerGoogleSync(account: acc.id, syncAll: syncAll);
            final syncId = res['sync_id']?.toString();
            if (syncId != null) {
              await apiClient.waitForSyncCompletion(syncId);
            } else if (res['success'] != true) {
              allSuccess = false;
            }
          }
          await refreshTasks();
          return allSuccess;
        } else {
          final res = await apiClient.triggerGoogleSync(account: targetAccount, syncAll: syncAll);
          final syncId = res['sync_id']?.toString();
          if (syncId != null) {
            final ok = await apiClient.waitForSyncCompletion(syncId);
            await refreshTasks();
            return ok;
          }
          await refreshTasks();
          return res['success'] == true;
        }
      } catch (e) {
        _errorMessage = 'Sync failed: $e';
        return false;
      } finally {
        _isLoading = false;
        notifyListeners();
      }
    }

    // Standalone direct Google Tasks mode
    try {
      _isLoading = true;
      notifyListeners();

      List<GTasksAccount> accountsToSync = [];
      if (targetAccount == 'all') {
        accountsToSync = List.from(_accounts);
      } else {
        accountsToSync = _accounts.where((a) => a.id == targetAccount).toList();
        if (accountsToSync.isEmpty && targetAccount.isNotEmpty) {
          accountsToSync = [GTasksAccount(id: targetAccount, name: targetAccount)];
        }
      }

      bool anySynced = false;

      for (final acc in accountsToSync) {
        // Retrieve access and refresh token for this account
        String? token;
        String? refreshToken;
        if (_standaloneAccounts.containsKey(acc.id)) {
          token = _standaloneAccounts[acc.id]?['access_token']?.toString();
          refreshToken = _standaloneAccounts[acc.id]?['refresh_token']?.toString();
        }
        if ((token == null || token.isEmpty) && _googleClient != null) {
          token = _googleClient!.accessToken;
          refreshToken = _googleClient!.refreshToken;
        }

        if (token == null || token.isEmpty) {
          _errorMessage = 'No Google token found for account "${acc.name}". Please add or reconnect the account in Settings.';
          continue;
        }

        final client = GoogleTasksDirectClient(
          accessToken: token,
          refreshToken: refreshToken,
          onTokenRefreshed: (newTok) {
            if (_standaloneAccounts.containsKey(acc.id)) {
              _standaloneAccounts[acc.id]!['access_token'] = newTok;
            }
            _onTokenRefreshed?.call(newTok);
          },
        );

        // 1. Flush offline pending changes first
        try {
          final pendingRows = await localDb.getPendingSyncRows(account: acc.id);
          for (final row in pendingRows) {
            final syncStatus = row['sync_status']?.toString();
            final taskId = row['id']?.toString() ?? '';
            final taskListId = row['list_id']?.toString() ?? '@default';

            if (syncStatus == 'pending_delete') {
              try {
                await client.deleteTask(listId: taskListId, taskId: taskId);
                await localDb.deleteTask(taskId);
              } catch (_) {}
            } else if (syncStatus == 'pending_insert') {
              try {
                final t = localDb.fromDbRow(row);
                final combinedNotes = NotesParser.combineNotesAndTags(t.description, t.tags);
                final created = await client.createTask(
                  listId: taskListId,
                  title: t.title,
                  notes: combinedNotes,
                  due: t.due,
                  listTitle: t.listTitle,
                  account: acc.id,
                );
                await localDb.deleteTask(taskId);
                await localDb.upsertTask(created, syncStatus: 'synced');
              } catch (_) {}
            } else if (syncStatus == 'pending_update') {
              try {
                final t = localDb.fromDbRow(row);
                final combinedNotes = NotesParser.combineNotesAndTags(t.description, t.tags);
                await client.updateTask(
                  listId: taskListId,
                  taskId: taskId,
                  title: t.title,
                  notes: combinedNotes,
                  due: t.due,
                  status: t.status,
                );
                await localDb.markTaskSynced(taskId);
              } catch (_) {}
            }
          }
        } catch (e) {
          debugPrint('[TaskProvider] Pending sync flush notice: $e');
        }

        // 2. Fetch remote task lists
        final lists = await client.fetchTaskLists();
        List<TaskItem> accFetchedTasks = [];

        // In advanced-sync: quick sync uses 10-day incremental window; syncAll (--all) fetches all historical tasks
        final DateTime? updatedMin = syncAll
            ? null
            : DateTime.now().toUtc().subtract(const Duration(days: 10));

        for (final list in lists) {
          final listId = list['id'].toString();
          final listTitle = list['title']?.toString() ?? 'Default List';
          final tasks = await client.fetchTasks(
            listId: listId,
            listTitle: listTitle,
            account: acc.id,
            updatedMin: updatedMin,
          );
          accFetchedTasks.addAll(tasks);
        }

        // 3. Upsert into local SQLite with Last-Write-Wins
        await localDb.upsertTasks(accFetchedTasks);
        anySynced = true;
      }

      await refreshTasks();
      return anySynced;
    } catch (e) {
      _errorMessage = 'Standalone Google Sync failed: $e';
      return false;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<bool> syncAllGoogleTasks({String? account}) async {
    return syncGoogleTasks(account: account, syncAll: true);
  }

  Future<void> setAccount(String accountId) async {
    _selectedAccount = accountId;
    if (!_isStandalone && accountId != 'all') {
      try {
        await apiClient.switchAccount(accountId);
      } catch (_) {}
    }
    await refreshTasks();
  }

  void setStatusFilter(String status) {
    _statusFilter = status;
    _recomputeFilteredTasks();
    notifyListeners();
  }

  void setSearchQuery(String query) {
    _searchQuery = query;
    _recomputeFilteredTasks();
    notifyListeners();
  }

  void selectList(String? list) {
    if (list == null) {
      _selectedLists.clear();
    } else {
      _selectedLists = {list};
    }
    _recomputeFilteredTasks();
    notifyListeners();
  }

  void selectTag(String? tag) {
    if (tag == null) {
      _selectedTags.clear();
    } else {
      _selectedTags = {tag};
    }
    _recomputeFilteredTasks();
    notifyListeners();
  }

  void setSelectedLists(Set<String> lists) {
    _selectedLists = Set.from(lists);
    _recomputeFilteredTasks();
    notifyListeners();
  }

  void setSelectedTags(Set<String> tags) {
    _selectedTags = Set.from(tags);
    _recomputeFilteredTasks();
    notifyListeners();
  }

  void toggleSelectedList(String list) {
    if (_selectedLists.contains(list)) {
      _selectedLists.remove(list);
    } else {
      _selectedLists.add(list);
    }
    _recomputeFilteredTasks();
    notifyListeners();
  }

  void toggleSelectedTag(String tag) {
    if (_selectedTags.contains(tag)) {
      _selectedTags.remove(tag);
    } else {
      _selectedTags.add(tag);
    }
    _recomputeFilteredTasks();
    notifyListeners();
  }

  void setPriorityFilter(String? priority) {
    _selectedPriority = priority;
    _recomputeFilteredTasks();
    notifyListeners();
  }

  void toggleHiddenList(String list) {
    if (_hiddenLists.contains(list)) {
      _hiddenLists.remove(list);
    } else {
      _hiddenLists.add(list);
    }
    _recomputeFilteredTasks();
    notifyListeners();
  }

  void toggleHiddenTag(String tag) {
    if (_hiddenTags.contains(tag)) {
      _hiddenTags.remove(tag);
    } else {
      _hiddenTags.add(tag);
    }
    _recomputeFilteredTasks();
    notifyListeners();
  }

  void setHideRecurring(bool hide) {
    _hideRecurring = hide;
    _recomputeFilteredTasks();
    notifyListeners();
  }

  void setHiddenLists(Set<String> lists) {
    _hiddenLists = Set.from(lists);
    _recomputeFilteredTasks();
    notifyListeners();
  }

  void setHiddenTags(Set<String> tags) {
    _hiddenTags = Set.from(tags);
    _recomputeFilteredTasks();
    notifyListeners();
  }

  void setSort(String field, bool ascending) {
    _sortField = field;
    _sortAscending = ascending;
    _recomputeFilteredTasks();
    notifyListeners();
  }

  void setDateFilter(String field, DateTimeRange? range) {
    _dateField = field;
    _dateRange = range;
    _recomputeFilteredTasks();
    notifyListeners();
  }

  void applyFiltersBatch({
    String? statusFilter,
    Set<String>? selectedLists,
    Set<String>? selectedTags,
    String? selectedPriority,
    bool clearPriority = false,
    Set<String>? hiddenLists,
    Set<String>? hiddenTags,
    bool? hideRecurring,
    String? dateField,
    DateTimeRange? dateRange,
    bool clearDateRange = false,
    String? sortField,
    bool? sortAscending,
  }) {
    if (statusFilter != null) _statusFilter = statusFilter;
    if (selectedLists != null) _selectedLists = Set.from(selectedLists);
    if (selectedTags != null) _selectedTags = Set.from(selectedTags);
    if (clearPriority) {
      _selectedPriority = null;
    } else if (selectedPriority != null) {
      _selectedPriority = selectedPriority;
    }
    if (hiddenLists != null) _hiddenLists = Set.from(hiddenLists);
    if (hiddenTags != null) _hiddenTags = Set.from(hiddenTags);
    if (hideRecurring != null) _hideRecurring = hideRecurring;
    if (dateField != null) _dateField = dateField;
    if (clearDateRange) {
      _dateRange = null;
    } else if (dateRange != null) {
      _dateRange = dateRange;
    }
    if (sortField != null) _sortField = sortField;
    if (sortAscending != null) _sortAscending = sortAscending;

    _recomputeFilteredTasks();
    notifyListeners();
  }

  void clearAllFilters() {
    _statusFilter = 'pending';
    _searchQuery = '';
    _selectedLists.clear();
    _selectedTags.clear();
    _selectedPriority = null;
    _hiddenLists.clear();
    _hiddenTags.clear();
    _hideRecurring = false;
    _dateRange = null;
    _sortField = 'modified_at';
    _sortAscending = false;
    _recomputeFilteredTasks();
    notifyListeners();
  }

  Future<bool> completeTask(String taskId) async {
    TaskItem? targetTask;
    final index = _tasks.indexWhere((t) => t.id == taskId);
    if (index != -1) {
      targetTask = _tasks[index];
      _tasks[index] = TaskItem(
        id: targetTask.id,
        title: targetTask.title,
        description: targetTask.description,
        status: 'completed',
        due: targetTask.due,
        listId: targetTask.listId,
        listTitle: targetTask.listTitle,
        account: targetTask.account,
        tags: targetTask.tags,
        calculatedPriority: targetTask.calculatedPriority,
        createdAt: targetTask.createdAt,
        completedAt: DateTime.now().toIso8601String(),
      );
      _recomputeAllCaches();
      notifyListeners();
    }

    if (_isStandalone) {
      await localDb.markTaskCompleted(taskId);
      // Trigger background sync to Google
      if (targetTask != null) {
        _syncStandaloneTaskToGoogle(targetTask, isComplete: true);
      }
      return true;
    }

    final acc = targetTask?.account ?? (_selectedAccount == 'all' ? 'default' : _selectedAccount);
    final success = await apiClient.completeTask(taskId, account: acc);
    return success;
  }

  Future<bool> addTask({
    required String title,
    String? description,
    String? due,
    String? account,
    String? listTitle,
    String? priority,
    List<String>? tags,
  }) async {
    final effectiveAccount = account ??
        ((_selectedAccount != 'all' && _selectedAccount.isNotEmpty)
            ? _selectedAccount
            : (_accounts.isNotEmpty ? _accounts.first.id : 'default'));
    final effectiveList = (listTitle != null && listTitle.isNotEmpty) ? listTitle : 'My Tasks';

    if (_isStandalone) {
      final effectiveTags = tags ?? [];
      final calculatedPriority = priority ?? GoogleTasksDirectClient.calculatePriorityFromTags(effectiveTags);
      final newTask = TaskItem(
        id: 'local_${DateTime.now().millisecondsSinceEpoch}',
        title: title,
        description: description ?? '',
        status: 'pending',
        due: due,
        listTitle: effectiveList,
        calculatedPriority: calculatedPriority,
        tags: effectiveTags,
        account: effectiveAccount,
        createdAt: DateTime.now().toUtc().toIso8601String(),
      );
      await localDb.upsertTask(newTask, syncStatus: 'pending_insert');
      await refreshTasks();
      // Sync immediately to Google Tasks in background
      _syncStandaloneTaskToGoogle(newTask, isCreate: true);
      return true;
    }

    try {
      final success = await apiClient.createTask(
        title: title,
        description: description,
        due: due,
        account: effectiveAccount,
        listTitle: effectiveList,
        priority: priority,
        tags: tags,
      );
      if (success) {
        await refreshTasks();
        return true;
      }
    } catch (e) {
      _errorMessage = 'Failed to create task on server: $e';
      notifyListeners();
    }
    return false;
  }

  Future<bool> updateTask({
    required String taskId,
    required String title,
    String? description,
    String? due,
    String? account,
    String? listTitle,
    String? priority,
    List<String>? tags,
  }) async {
    final effectiveAccount = account ??
        ((_selectedAccount != 'all' && _selectedAccount.isNotEmpty)
            ? _selectedAccount
            : (_accounts.isNotEmpty ? _accounts.first.id : 'default'));

    if (_isStandalone) {
      final existing = await localDb.getTaskById(taskId);
      if (existing != null) {
        final newTags = tags ?? existing.tags;
        final newPriority = priority ?? GoogleTasksDirectClient.calculatePriorityFromTags(newTags);
        final updated = TaskItem(
          id: taskId,
          title: title,
          description: description ?? existing.description,
          due: due ?? existing.due,
          status: existing.status,
          tags: newTags,
          listId: existing.listId,
          listTitle: listTitle ?? existing.listTitle,
          account: effectiveAccount,
          calculatedPriority: newPriority,
          createdAt: existing.createdAt,
        );
        await localDb.upsertTask(updated, syncStatus: 'pending_update');
        await refreshTasks();
        _syncStandaloneTaskToGoogle(updated, isUpdate: true);
        return true;
      }
      return false;
    }

    final success = await apiClient.updateTask(
      taskId: taskId,
      title: title,
      description: description,
      due: due,
      account: effectiveAccount,
      listTitle: listTitle,
      priority: priority,
      tags: tags,
    );
    if (success) {
      await refreshTasks();
    }
    return success;
  }

  Future<bool> deleteTask(String taskId, {String? account}) async {
    final effectiveAccount = account ?? (_selectedAccount == 'all' ? 'default' : _selectedAccount);
    if (_isStandalone) {
      final existing = await localDb.getTaskById(taskId);
      await localDb.markTaskPendingDelete(taskId);
      _tasks.removeWhere((t) => t.id == taskId);
      _recomputeAllCaches();
      notifyListeners();
      if (existing != null) {
        _syncStandaloneTaskToGoogle(existing, isDelete: true);
      }
      return true;
    }

    final success = await apiClient.deleteTask(taskId, account: effectiveAccount);
    if (success) {
      _tasks.removeWhere((t) => t.id == taskId);
      _recomputeAllCaches();
      notifyListeners();
    }
    return success;
  }

  void _syncStandaloneTaskToGoogle(
    TaskItem task, {
    bool isCreate = false,
    bool isUpdate = false,
    bool isComplete = false,
    bool isDelete = false,
  }) async {
    try {
      final accId = task.account.isNotEmpty ? task.account : 'default';
      String? token;
      String? refreshToken;
      if (_standaloneAccounts.containsKey(accId)) {
        token = _standaloneAccounts[accId]?['access_token']?.toString();
        refreshToken = _standaloneAccounts[accId]?['refresh_token']?.toString();
      }
      if ((token == null || token.isEmpty) && _googleClient != null) {
        token = _googleClient!.accessToken;
        refreshToken = _googleClient!.refreshToken;
      }
      if (token == null || token.isEmpty) {
        _errorMessage = 'No Google token for account "$accId"';
        notifyListeners();
        return;
      }

      final client = GoogleTasksDirectClient(
        accessToken: token,
        refreshToken: refreshToken,
        onTokenRefreshed: (newTok) {
          if (_standaloneAccounts.containsKey(accId)) {
            _standaloneAccounts[accId]!['access_token'] = newTok;
          }
          _onTokenRefreshed?.call(newTok);
        },
      );
      final lists = await client.fetchTaskLists();

      Future<Map<String, dynamic>> findOrCreateList(String title) async {
        final match = lists.firstWhere(
          (l) => (l['title']?.toString().toLowerCase() == title.toLowerCase()),
          orElse: () => <String, dynamic>{},
        );
        if (match.isNotEmpty) return match;
        final createdList = await client.createTaskList(title);
        lists.add(createdList);
        return createdList;
      }

      final targetList = await findOrCreateList(task.listTitle ?? 'My Tasks');
      final listId = targetList['id']?.toString() ?? '@default';
      final combinedNotes = NotesParser.combineNotesAndTags(task.description, task.tags);

      if (isCreate) {
        final created = await client.createTask(
          listId: listId,
          title: task.title,
          notes: combinedNotes,
          due: task.due,
          listTitle: task.listTitle,
          account: accId,
        );
        // Replace temporary local ID with Google's ID
        await localDb.deleteTask(task.id);
        await localDb.upsertTask(created, syncStatus: 'synced');
        await refreshTasks();
      } else if (isComplete) {
        await client.updateTask(
          listId: task.listId ?? listId,
          taskId: task.id,
          status: 'completed',
        );
        await localDb.markTaskSynced(task.id);
      } else if (isUpdate) {
        final oldListId = task.listId;
        if (oldListId != null && oldListId != listId) {
          // Re-create in new list, delete from old list
          final created = await client.createTask(
            listId: listId,
            title: task.title,
            notes: combinedNotes,
            due: task.due,
            listTitle: task.listTitle,
            account: accId,
          );
          try {
            await client.deleteTask(listId: oldListId, taskId: task.id);
          } catch (_) {}
          await localDb.deleteTask(task.id);
          await localDb.upsertTask(created, syncStatus: 'synced');
          await refreshTasks();
        } else {
          await client.updateTask(
            listId: task.listId ?? listId,
            taskId: task.id,
            title: task.title,
            notes: combinedNotes,
            due: task.due,
            status: task.status,
          );
          await localDb.markTaskSynced(task.id);
        }
      } else if (isDelete) {
        final deleteListId = task.listId ?? listId;
        await client.deleteTask(listId: deleteListId, taskId: task.id);
        await localDb.deleteTask(task.id);
      }
    } catch (e) {
      debugPrint('[TaskProvider] Standalone immediate Google sync notice: $e');
    }
  }
}
