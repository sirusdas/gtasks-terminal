import 'package:flutter/material.dart';
import '../api/api_client.dart';
import '../api/google_tasks_direct_client.dart';
import '../models/task_item.dart';
import '../models/account.dart';
import '../storage/local_database.dart';

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
  }) {
    _isStandalone = isStandalone;
    if (googleAccessToken != null && googleAccessToken.isNotEmpty) {
      _googleClient = GoogleTasksDirectClient(accessToken: googleAccessToken);
    }
  }

  Map<String, Map<String, dynamic>> _standaloneAccounts = {};
  Set<String> _deletedAccounts = {};

  void updateConfig({
    required String newUrl,
    required bool isStandalone,
    String? googleAccessToken,
    Map<String, Map<String, dynamic>>? standaloneAccounts,
    Set<String>? deletedAccounts,
  }) {
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
      _googleClient = GoogleTasksDirectClient(accessToken: googleAccessToken);
    } else {
      _googleClient = null;
    }

    if (needsReload) {
      loadInitialData();
    }
  }

  Future<void> removeAccount(String accountId) async {
    _deletedAccounts.add(accountId);
    if (accountId == 'default' || accountId == 'personal') {
      _deletedAccounts.add('default');
      _deletedAccounts.add('personal');
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

  void updateBaseUrl(String newUrl) {
    updateConfig(
      newUrl: newUrl,
      isStandalone: _isStandalone,
      googleAccessToken: _googleClient?.accessToken,
    );
  }

  bool get isStandalone => _isStandalone;

  List<TaskItem> get tasks => _filteredTasks();
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

  int get pendingTasksCount {
    return _tasks.where((t) {
      if (_selectedAccount != 'all' && t.account != _selectedAccount) return false;
      return !t.isCompleted;
    }).length;
  }

  // Lists with pending task counts based on current account
  Map<String, int> get listsWithCounts {
    final Map<String, int> map = {};
    for (final task in _tasks) {
      if (_selectedAccount != 'all' && task.account != _selectedAccount) continue;
      if (task.isCompleted) continue; // Only count pending tasks
      final list = (task.listTitle != null && task.listTitle!.isNotEmpty)
          ? task.listTitle!
          : 'Default List';
      map[list] = (map[list] ?? 0) + 1;
    }
    return map;
  }

  // Tags with pending task counts based on current account
  Map<String, int> get tagsWithCounts {
    final Map<String, int> map = {};
    for (final task in _tasks) {
      if (_selectedAccount != 'all' && task.account != _selectedAccount) continue;
      if (task.isCompleted) continue; // Only count pending tasks
      for (final tag in task.allTags) {
        if (tag.trim().isNotEmpty) {
          map[tag] = (map[tag] ?? 0) + 1;
        }
      }
    }
    return map;
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
    notifyListeners();
  }

  Future<bool> syncGoogleTasks() async {
    if (!_isStandalone || _googleClient == null) {
      return await apiClient.triggerGoogleSync();
    }

    try {
      _isLoading = true;
      notifyListeners();

      final lists = await _googleClient!.fetchTaskLists();
      List<TaskItem> allFetched = [];

      for (final list in lists) {
        final listId = list['id'].toString();
        final listTitle = list['title']?.toString() ?? 'Default List';
        final tasks = await _googleClient!.fetchTasks(
          listId: listId,
          listTitle: listTitle,
          account: 'default',
        );
        allFetched.addAll(tasks);
      }

      // Upsert into local SQLite with Last-Write-Wins and zero duplicates
      await localDb.upsertTasks(allFetched);
      await refreshTasks();
      return true;
    } catch (e) {
      _errorMessage = 'Standalone Google Sync failed: $e';
      return false;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
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
    notifyListeners();
  }

  void setSearchQuery(String query) {
    _searchQuery = query;
    notifyListeners();
  }

  void selectList(String? list) {
    if (list == null) {
      _selectedLists.clear();
    } else {
      _selectedLists = {list};
    }
    notifyListeners();
  }

  void selectTag(String? tag) {
    if (tag == null) {
      _selectedTags.clear();
    } else {
      _selectedTags = {tag};
    }
    notifyListeners();
  }

  void setSelectedLists(Set<String> lists) {
    _selectedLists = Set.from(lists);
    notifyListeners();
  }

  void setSelectedTags(Set<String> tags) {
    _selectedTags = Set.from(tags);
    notifyListeners();
  }

  void toggleSelectedList(String list) {
    if (_selectedLists.contains(list)) {
      _selectedLists.remove(list);
    } else {
      _selectedLists.add(list);
    }
    notifyListeners();
  }

  void toggleSelectedTag(String tag) {
    if (_selectedTags.contains(tag)) {
      _selectedTags.remove(tag);
    } else {
      _selectedTags.add(tag);
    }
    notifyListeners();
  }

  void setPriorityFilter(String? priority) {
    _selectedPriority = priority;
    notifyListeners();
  }

  void toggleHiddenList(String list) {
    if (_hiddenLists.contains(list)) {
      _hiddenLists.remove(list);
    } else {
      _hiddenLists.add(list);
    }
    notifyListeners();
  }

  void toggleHiddenTag(String tag) {
    if (_hiddenTags.contains(tag)) {
      _hiddenTags.remove(tag);
    } else {
      _hiddenTags.add(tag);
    }
    notifyListeners();
  }

  void setHideRecurring(bool hide) {
    _hideRecurring = hide;
    notifyListeners();
  }

  void setHiddenLists(Set<String> lists) {
    _hiddenLists = Set.from(lists);
    notifyListeners();
  }

  void setHiddenTags(Set<String> tags) {
    _hiddenTags = Set.from(tags);
    notifyListeners();
  }

  void setSort(String field, bool ascending) {
    _sortField = field;
    _sortAscending = ascending;
    notifyListeners();
  }

  void setDateFilter(String field, DateTimeRange? range) {
    _dateField = field;
    _dateRange = range;
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
    notifyListeners();
  }

  Future<bool> completeTask(String taskId) async {
    if (_isStandalone) {
      await localDb.markTaskCompleted(taskId);
      final index = _tasks.indexWhere((t) => t.id == taskId);
      if (index != -1) {
        _tasks[index] = TaskItem(
          id: _tasks[index].id,
          title: _tasks[index].title,
          description: _tasks[index].description,
          status: 'completed',
          due: _tasks[index].due,
          listId: _tasks[index].listId,
          listTitle: _tasks[index].listTitle,
          account: _tasks[index].account,
          tags: _tasks[index].tags,
          calculatedPriority: _tasks[index].calculatedPriority,
          createdAt: _tasks[index].createdAt,
          completedAt: DateTime.now().toIso8601String(),
        );
        notifyListeners();
      }
      return true;
    }

    final success = await apiClient.completeTask(taskId, account: _selectedAccount);
    if (success) {
      final index = _tasks.indexWhere((t) => t.id == taskId);
      if (index != -1) {
        _tasks[index] = TaskItem(
          id: _tasks[index].id,
          title: _tasks[index].title,
          description: _tasks[index].description,
          status: 'completed',
          due: _tasks[index].due,
          listId: _tasks[index].listId,
          listTitle: _tasks[index].listTitle,
          account: _tasks[index].account,
          tags: _tasks[index].tags,
          calculatedPriority: _tasks[index].calculatedPriority,
          createdAt: _tasks[index].createdAt,
          completedAt: DateTime.now().toIso8601String(),
        );
        notifyListeners();
      }
    }
    return success;
  }

  Future<bool> addTask({
    required String title,
    String? description,
    String? due,
    List<String>? tags,
  }) async {
    if (_isStandalone) {
      final newTask = TaskItem(
        id: 'local_${DateTime.now().millisecondsSinceEpoch}',
        title: title,
        description: description ?? '',
        status: 'pending',
        due: due,
        tags: tags ?? [],
        createdAt: DateTime.now().toUtc().toIso8601String(),
      );
      await localDb.upsertTask(newTask, syncStatus: 'pending_insert');
      await refreshTasks();
      return true;
    }

    final success = await apiClient.createTask(
      title: title,
      description: description,
      due: due,
      account: _selectedAccount == 'all' ? 'default' : _selectedAccount,
      tags: tags,
    );
    if (success) {
      await refreshTasks();
    }
    return success;
  }

  Future<bool> updateTask({
    required String taskId,
    required String title,
    String? description,
    String? due,
    List<String>? tags,
  }) async {
    if (_isStandalone) {
      final existing = await localDb.getTaskById(taskId);
      if (existing != null) {
        final updated = TaskItem(
          id: taskId,
          title: title,
          description: description ?? existing.description,
          due: due ?? existing.due,
          status: existing.status,
          tags: tags ?? existing.tags,
          listId: existing.listId,
          listTitle: existing.listTitle,
          account: existing.account,
          createdAt: existing.createdAt,
        );
        await localDb.upsertTask(updated, syncStatus: 'pending_update');
        await refreshTasks();
        return true;
      }
      return false;
    }

    final success = await apiClient.updateTask(
      taskId: taskId,
      title: title,
      description: description,
      due: due,
      account: _selectedAccount == 'all' ? 'default' : _selectedAccount,
      tags: tags,
    );
    if (success) {
      await refreshTasks();
    }
    return success;
  }

  Future<bool> deleteTask(String taskId) async {
    if (_isStandalone) {
      await localDb.deleteTask(taskId);
      _tasks.removeWhere((t) => t.id == taskId);
      notifyListeners();
      return true;
    }

    final success = await apiClient.deleteTask(taskId, account: _selectedAccount);
    if (success) {
      _tasks.removeWhere((t) => t.id == taskId);
      notifyListeners();
    }
    return success;
  }
}
