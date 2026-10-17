import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../api/api_client.dart';
import '../api/google_tasks_direct_client.dart';
import '../models/task_item.dart';
import '../models/account.dart';
import '../models/task_tab.dart';
import '../services/widget_service.dart';
import '../services/notification_service.dart';
import '../services/subscriber_service.dart';
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
  Set<String> _selectedAccounts = {};
  String _statusFilter = 'pending'; // 'pending', 'completed', 'all'
  String _searchQuery = '';
  Set<String> _selectedLists = {};
  Set<String> _selectedTags = {};
  String? _selectedSpace;
  String? _selectedSubspace;
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
  Map<String, int> _spacesWithCountsCache = {};
  Map<String, Map<String, int>> _subspacesWithCountsCache = {};
  int _pendingTasksCountCache = 0;

  List<TaskItem> get tasks => _filteredTasksCache;
  List<TaskItem> get allTasksUnfiltered => _tasks;
  List<GTasksAccount> get accounts => _accounts;
  String get selectedAccount => _selectedAccount;
  Set<String> get selectedAccounts => _selectedAccounts;
  String get statusFilter => _statusFilter;
  String get searchQuery => _searchQuery;
  Set<String> get selectedLists => _selectedLists;
  Set<String> get selectedTags => _selectedTags;
  String? get selectedSpace => _selectedSpace;
  String? get selectedSubspace => _selectedSubspace;
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

  bool _isSyncing = false;
  bool get isSyncing => _isSyncing;

  static const String _keyBrowserTabs = 'gtasks_browser_tabs_v2';
  static const String _keyActiveTabIndex = 'gtasks_browser_active_tab_index_v2';

  List<TaskTab> _tabs = [];
  int _activeTabIndex = 0;
  bool _isApplyingTab = false;

  List<TaskTab> get tabs => List.unmodifiable(_tabs);
  int get activeTabIndex => _activeTabIndex;
  TaskTab? get activeTab => _tabs.isNotEmpty && _activeTabIndex < _tabs.length ? _tabs[_activeTabIndex] : null;

  Future<void> _initTabs() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final tabsRaw = prefs.getString(_keyBrowserTabs);
      final activeIdx = prefs.getInt(_keyActiveTabIndex) ?? 0;

      if (tabsRaw != null && tabsRaw.isNotEmpty) {
        final List decoded = jsonDecode(tabsRaw);
        _tabs = decoded.map((item) => TaskTab.fromJson(item as Map<String, dynamic>)).toList();
      }

      if (_tabs.isEmpty) {
        _tabs = _generateDefaultTabs();
      }

      _activeTabIndex = (activeIdx >= 0 && activeIdx < _tabs.length) ? activeIdx : 0;
      _applyTabFilters(_tabs[_activeTabIndex], shouldNotify: false);
    } catch (e) {
      debugPrint('[TaskProvider] Error initializing tabs: $e');
      if (_tabs.isEmpty) {
        _tabs = _generateDefaultTabs();
        _activeTabIndex = 0;
      }
    }
  }

  List<TaskTab> _generateDefaultTabs() {
    return [
      TaskTab(
        id: 'tab_all_tasks',
        title: 'All Tasks',
        iconCodePoint: Icons.inbox_rounded.codePoint,
        statusFilter: 'pending',
      ),
      TaskTab(
        id: 'tab_today',
        title: 'Today & Due',
        iconCodePoint: Icons.today_rounded.codePoint,
        statusFilter: 'pending',
        dateField: 'due',
        dateRange: DateTimeRange(
          start: DateTime(2000, 1, 1),
          end: DateTime(DateTime.now().year, DateTime.now().month, DateTime.now().day, 23, 59, 59),
        ),
      ),
      TaskTab(
        id: 'tab_priority',
        title: 'High Priority',
        iconCodePoint: Icons.local_fire_department_rounded.codePoint,
        statusFilter: 'pending',
        selectedPriority: 'high',
      ),
    ];
  }

  Future<void> _saveTabs() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final raw = jsonEncode(_tabs.map((t) => t.toJson()).toList());
      await prefs.setString(_keyBrowserTabs, raw);
      await prefs.setInt(_keyActiveTabIndex, _activeTabIndex);
      WidgetService.updateWidget(tabsJson: _tabsToJsonString());
    } catch (e) {
      debugPrint('[TaskProvider] Error saving tabs: $e');
    }
  }

  String _tabsToJsonString() {
    return jsonEncode(_tabs.map((t) => t.toWidgetJson()).toList());
  }

  void _applyTabFilters(TaskTab tab, {bool shouldNotify = true}) {
    _isApplyingTab = true;
    _selectedAccounts = Set.from(tab.effectiveAccounts);
    if (_selectedAccounts.length == 1 && !_selectedAccounts.contains('all')) {
      _selectedAccount = _selectedAccounts.first;
    } else {
      _selectedAccount = 'all';
    }
    _statusFilter = tab.statusFilter;
    _selectedSpace = tab.selectedSpace;
    _selectedSubspace = tab.selectedSubspace;
    _selectedPriority = tab.selectedPriority;
    _selectedLists = Set.from(tab.selectedLists);
    _selectedTags = Set.from(tab.selectedTags);
    _searchQuery = tab.searchQuery;
    _dateField = tab.dateField ?? 'modified_at';
    _dateRange = tab.dateRange;
    _hideRecurring = tab.hideRecurring;
    _hiddenLists = Set.from(tab.hiddenLists);
    _hiddenTags = Set.from(tab.hiddenTags);
    _sortField = tab.sortField;
    _sortAscending = tab.sortAscending;
    _isApplyingTab = false;

    _recomputeFilteredTasks();
    if (shouldNotify) {
      notifyListeners();
    }
  }

  void _syncActiveTabFromCurrentFilters() {
    if (_isApplyingTab || _tabs.isEmpty || _activeTabIndex >= _tabs.length) return;
    final current = _tabs[_activeTabIndex];
    _tabs[_activeTabIndex] = current.copyWith(
      selectedAccount: _selectedAccount,
      selectedAccounts: _selectedAccounts,
      statusFilter: _statusFilter,
      selectedSpace: _selectedSpace,
      clearSpace: _selectedSpace == null,
      selectedSubspace: _selectedSubspace,
      clearSubspace: _selectedSubspace == null,
      selectedPriority: _selectedPriority,
      clearPriority: _selectedPriority == null,
      selectedLists: _selectedLists,
      selectedTags: _selectedTags,
      searchQuery: _searchQuery,
      dateField: _dateField,
      dateRange: _dateRange,
      clearDateRange: _dateRange == null,
      hideRecurring: _hideRecurring,
      hiddenLists: _hiddenLists,
      hiddenTags: _hiddenTags,
      sortField: _sortField,
      sortAscending: _sortAscending,
    );
    _saveTabs();
  }

  Future<void> switchToTab(int index) async {
    if (index < 0 || index >= _tabs.length || index == _activeTabIndex) return;
    _activeTabIndex = index;
    final tab = _tabs[index];
    final targetAccount = (tab.effectiveAccounts.length == 1 && !tab.effectiveAccounts.contains('all'))
        ? tab.effectiveAccounts.first
        : 'all';
    if (targetAccount != _selectedAccount) {
      await setAccount(targetAccount);
    }
    _applyTabFilters(tab);
    _saveTabs();
  }

  void switchToTabById(String tabId) {
    final idx = _tabs.indexWhere((t) => t.id == tabId);
    if (idx != -1) {
      switchToTab(idx);
    }
  }

  void addNewTab({
    String? title,
    String? account,
    Set<String>? accounts,
    int? iconCodePoint,
    String? space,
    String? subspace,
    String? priority,
    String? list,
    String? tag,
    DateTimeRange? dateRange,
    String? dateField,
    String? statusFilter,
  }) {
    final newId = 'tab_${DateTime.now().millisecondsSinceEpoch}';
    final tabAccounts = accounts ?? (account != null ? (account == 'all' ? <String>{} : {account}) : _selectedAccounts);
    String defaultTitle;
    if (title != null && title.isNotEmpty) {
      defaultTitle = title;
    } else if (tabAccounts.length == 1) {
      final accName = _accounts.firstWhere((a) => a.id == tabAccounts.first, orElse: () => GTasksAccount(id: tabAccounts.first, name: tabAccounts.first)).name;
      defaultTitle = space != null ? '$accName - $space' : (priority != null ? '$accName - $priority' : accName);
    } else if (tabAccounts.length > 1) {
      final accNames = tabAccounts.map((id) => _accounts.firstWhere((a) => a.id == id, orElse: () => GTasksAccount(id: id, name: id)).name).join(', ');
      defaultTitle = space != null ? '$accNames - $space' : (priority != null ? '$accNames - $priority' : '$accNames Tasks');
    } else {
      defaultTitle = space ?? (priority != null ? '$priority Priority' : 'New Tab ${_tabs.length + 1}');
    }

    final newTab = TaskTab(
      id: newId,
      title: defaultTitle,
      selectedAccount: tabAccounts.length == 1 ? tabAccounts.first : null,
      selectedAccounts: tabAccounts,
      iconCodePoint: iconCodePoint,
      selectedSpace: space,
      selectedSubspace: subspace,
      selectedPriority: priority,
      selectedLists: list != null ? {list} : {},
      selectedTags: tag != null ? {tag} : {},
      dateRange: dateRange,
      dateField: dateField,
      statusFilter: statusFilter ?? 'pending',
    );
    _tabs.add(newTab);
    _activeTabIndex = _tabs.length - 1;
    _applyTabFilters(newTab);
    _saveTabs();
  }

  Future<void> updateTabAccount(int index, String? account) async {
    if (index < 0 || index >= _tabs.length) return;
    final isAll = account == null || account == 'all';
    _tabs[index] = _tabs[index].copyWith(
      selectedAccount: isAll ? null : account,
      clearAccount: isAll,
    );
    if (_activeTabIndex == index) {
      final targetAccount = isAll ? 'all' : account;
      if (targetAccount != _selectedAccount) {
        await setAccount(targetAccount);
      }
      _applyTabFilters(_tabs[index]);
    }
    _saveTabs();
    notifyListeners();
  }

  Future<void> updateTabAccounts(int index, Set<String> accounts) async {
    if (index < 0 || index >= _tabs.length) return;
    final isAll = accounts.isEmpty || accounts.contains('all');
    final singleAcc = (!isAll && accounts.length == 1) ? accounts.first : null;
    _tabs[index] = _tabs[index].copyWith(
      selectedAccount: singleAcc,
      selectedAccounts: isAll ? {} : accounts,
      clearAccount: isAll,
    );
    if (_activeTabIndex == index) {
      _applyTabFilters(_tabs[index]);
    }
    _saveTabs();
    notifyListeners();
  }

  void closeTab(int index) {
    if (_tabs.length <= 1) return; // Keep at least one tab
    _tabs.removeAt(index);
    if (_activeTabIndex >= _tabs.length) {
      _activeTabIndex = _tabs.length - 1;
    } else if (_activeTabIndex > index) {
      _activeTabIndex--;
    }
    _applyTabFilters(_tabs[_activeTabIndex]);
    _saveTabs();
  }

  void renameTab(int index, String newTitle) {
    if (index < 0 || index >= _tabs.length) return;
    _tabs[index].title = newTitle.trim().isEmpty ? 'Tab' : newTitle.trim();
    _saveTabs();
    notifyListeners();
  }

  void duplicateTab(int index) {
    if (index < 0 || index >= _tabs.length) return;
    final source = _tabs[index];
    final copy = source.copyWith(
      id: 'tab_${DateTime.now().millisecondsSinceEpoch}',
      title: '${source.title} (Copy)',
    );
    _tabs.insert(index + 1, copy);
    _activeTabIndex = index + 1;
    _applyTabFilters(copy);
    _saveTabs();
  }

  void reorderTabs(int oldIndex, int newIndex) {
    if (oldIndex < 0 || oldIndex >= _tabs.length || newIndex < 0 || newIndex > _tabs.length) return;
    if (oldIndex < newIndex) {
      newIndex -= 1;
    }
    final activeTabId = _tabs[_activeTabIndex].id;
    final item = _tabs.removeAt(oldIndex);
    _tabs.insert(newIndex, item);
    _activeTabIndex = _tabs.indexWhere((t) => t.id == activeTabId);
    if (_activeTabIndex == -1) _activeTabIndex = 0;
    _saveTabs();
    notifyListeners();
  }

  bool get hasActiveFilters {
    return _selectedLists.isNotEmpty ||
        _selectedTags.isNotEmpty ||
        _selectedSpace != null ||
        _selectedSubspace != null ||
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
    if (_selectedSpace != null) count++;
    if (_selectedSubspace != null) count++;
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
  Map<String, int> get spacesWithCounts => _spacesWithCountsCache;
  Map<String, Map<String, int>> get subspacesWithCounts => _subspacesWithCountsCache;

  void _recomputeAllCaches() {
    _recomputeAggregates();
    _recomputeFilteredTasks();
    WidgetService.updateWidget(tabsJson: _tabsToJsonString());
  }

  void _recomputeAggregates() {
    int pendingCount = 0;
    final Map<String, int> listMap = {};
    final Map<String, int> tagMap = {};
    final Map<String, int> spaceMap = {};
    final Map<String, Map<String, int>> subspaceMap = {};

    for (final task in _tasks) {
      if (_selectedAccounts.isNotEmpty && !_selectedAccounts.contains('all')) {
        if (!_selectedAccounts.contains(task.account)) continue;
      } else if (_selectedAccount != 'all' && task.account != _selectedAccount) {
        continue;
      }
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

      for (final entry in task.spaces.entries) {
        final spaceName = entry.key;
        spaceMap[spaceName] = (spaceMap[spaceName] ?? 0) + 1;
        if (!subspaceMap.containsKey(spaceName)) {
          subspaceMap[spaceName] = {};
        }
        for (final sub in entry.value) {
          subspaceMap[spaceName]![sub] = (subspaceMap[spaceName]![sub] ?? 0) + 1;
        }
      }
    }

    _pendingTasksCountCache = pendingCount;
    _listsWithCountsCache = listMap;
    _tagsWithCountsCache = tagMap;
    _spacesWithCountsCache = spaceMap;
    _subspacesWithCountsCache = subspaceMap;
  }

  void _recomputeFilteredTasks() {
    _filteredTasksCache = _filteredTasks();
    _syncActiveTabFromCurrentFilters();
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
      if (_selectedAccounts.isNotEmpty && !_selectedAccounts.contains('all')) {
        if (!_selectedAccounts.contains(task.account)) return false;
      } else if (_selectedAccount != 'all' && task.account != _selectedAccount) {
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
      if (_selectedSpace != null) {
        if (!task.spaces.containsKey(_selectedSpace)) return false;
        if (_selectedSubspace != null) {
          final subs = task.spaces[_selectedSpace] ?? [];
          if (!subs.contains(_selectedSubspace)) return false;
        }
      }
      if (_selectedPriority != null) {
        final prio = _selectedPriority!.toLowerCase();
        final taskPrio = task.calculatedPriority.toLowerCase();
        if (prio == 'high_or_critical' || prio == 'high') {
          if (taskPrio != 'high' && taskPrio != 'critical') return false;
        } else if (taskPrio != prio) {
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
        final matchSpaces = task.spaces.keys.any((s) => s.toLowerCase().contains(query)) ||
            task.spaces.values.any((subs) => subs.any((sub) => sub.toLowerCase().contains(query)));
        return matchTitle || matchNotes || matchTags || matchSpaces;
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
      await _initTabs();
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
      for (final acc in _accounts) {
        if (acc.email != null && acc.email!.isNotEmpty) {
          SubscriberService().syncSubscriber(email: acc.email!, name: acc.name, accountId: acc.id);
        }
      }
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
    NotificationService().syncAllTaskReminders(_tasks);
  }

  Future<bool> syncGoogleTasks({String? account, bool syncAll = false}) async {
    if (_isSyncing) {
      debugPrint('[TaskProvider] Sync already in progress, skipping duplicate request.');
      return true;
    }
    _isSyncing = true;
    _isLoading = true;
    notifyListeners();

    try {
      final targetAccount = account ?? _selectedAccount;

      if (!_isStandalone) {
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
      }

      // Standalone direct Google Tasks mode
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
      _errorMessage = 'Sync failed: $e';
      return false;
    } finally {
      _isLoading = false;
      _isSyncing = false;
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
    String? selectedSpace,
    String? selectedSubspace,
    bool clearSpace = false,
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
    if (clearSpace) {
      _selectedSpace = null;
      _selectedSubspace = null;
    } else if (selectedSpace != null) {
      _selectedSpace = selectedSpace;
      _selectedSubspace = selectedSubspace;
    }
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

  void setSelectedSpace(String? space, {String? subspace}) {
    if (_selectedSpace == space && _selectedSubspace == subspace) {
      _selectedSpace = null;
      _selectedSubspace = null;
    } else {
      _selectedSpace = space;
      _selectedSubspace = subspace;
    }
    _recomputeFilteredTasks();
    notifyListeners();
  }

  void setSpaceFilter(String? space, {String? subspace}) {
    _selectedSpace = space;
    _selectedSubspace = subspace;
    _recomputeFilteredTasks();
    notifyListeners();
  }

  void clearSpaceFilter() {
    _selectedSpace = null;
    _selectedSubspace = null;
    _recomputeFilteredTasks();
    notifyListeners();
  }

  void clearAllFilters() {
    _statusFilter = 'pending';
    _searchQuery = '';
    _selectedLists.clear();
    _selectedTags.clear();
    _selectedSpace = null;
    _selectedSubspace = null;
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
        spaces: targetTask.spaces,
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
      NotificationService().cancelReminder(taskId.hashCode);
      return true;
    }

    final defaultAcc = (_selectedAccounts.isNotEmpty && !_selectedAccounts.contains('all'))
        ? _selectedAccounts.first
        : (_accounts.isNotEmpty ? _accounts.first.id : 'default');
    final acc = targetTask?.account ?? (_selectedAccount == 'all' ? defaultAcc : _selectedAccount);
    final success = await apiClient.completeTask(taskId, account: acc);
    if (success) {
      NotificationService().cancelReminder(taskId.hashCode);
    }
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
    Map<String, List<String>>? spaces,
  }) async {
    final effectiveAccount = account ??
        ((_selectedAccount != 'all' && _selectedAccount.isNotEmpty)
            ? _selectedAccount
            : (_selectedAccounts.isNotEmpty && !_selectedAccounts.contains('all')
                ? _selectedAccounts.first
                : (_accounts.isNotEmpty ? _accounts.first.id : 'default')));
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
        spaces: spaces,
        account: effectiveAccount,
        createdAt: DateTime.now().toUtc().toIso8601String(),
      );
      await localDb.upsertTask(newTask, syncStatus: 'pending_insert');
      await refreshTasks();
      // Sync immediately to Google Tasks in background
      _syncStandaloneTaskToGoogle(newTask, isCreate: true);
      NotificationService().scheduleTaskReminder(newTask);
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
    Map<String, List<String>>? spaces,
  }) async {
    TaskItem? existingTask;
    try {
      existingTask = _tasks.firstWhere((t) => t.id == taskId);
    } catch (_) {}

    final defaultAcc = (existingTask?.account.isNotEmpty == true && existingTask!.account != 'default')
        ? existingTask.account
        : ((_selectedAccount != 'all' && _selectedAccount.isNotEmpty)
            ? _selectedAccount
            : (_selectedAccounts.isNotEmpty && !_selectedAccounts.contains('all')
                ? _selectedAccounts.first
                : (_accounts.isNotEmpty ? _accounts.first.id : 'default')));
    final effectiveAccount = account ?? defaultAcc;

    if (_isStandalone) {
      final existing = await localDb.getTaskById(taskId);
      if (existing != null) {
        final newTags = tags ?? existing.tags;
        final newSpaces = spaces ?? existing.spaces;
        final newPriority = priority ?? GoogleTasksDirectClient.calculatePriorityFromTags(newTags);
        final updated = TaskItem(
          id: taskId,
          title: title,
          description: description ?? existing.description,
          due: due ?? existing.due,
          status: existing.status,
          tags: newTags,
          spaces: newSpaces,
          listId: existing.listId,
          listTitle: listTitle ?? existing.listTitle,
          account: effectiveAccount,
          calculatedPriority: newPriority,
          createdAt: existing.createdAt,
        );
        await localDb.upsertTask(updated, syncStatus: 'pending_update');
        await refreshTasks();
        _syncStandaloneTaskToGoogle(updated, isUpdate: true);
        NotificationService().scheduleTaskReminder(updated);
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
    TaskItem? targetTask;
    try {
      targetTask = _tasks.firstWhere((t) => t.id == taskId);
    } catch (_) {}
    final defaultAcc = (_selectedAccounts.isNotEmpty && !_selectedAccounts.contains('all'))
        ? _selectedAccounts.first
        : (_accounts.isNotEmpty ? _accounts.first.id : 'default');
    final effectiveAccount = account ?? targetTask?.account ?? (_selectedAccount == 'all' ? defaultAcc : _selectedAccount);
    NotificationService().cancelReminder(taskId.hashCode);
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

  Future<int> removeTagGlobally(String tag, {String? account}) async {
    final effectiveAccount = account ?? _selectedAccount;
    final targetTag = tag.trim().toLowerCase().replaceAll(RegExp(r'^[\[#]+|[\]]+$'), '');
    int updatedCount = 0;

    if (_isStandalone) {
      final List<TaskItem> tasksToUpdate = [];
      for (int i = 0; i < _tasks.length; i++) {
        final task = _tasks[i];
        if (effectiveAccount != 'all' && effectiveAccount.isNotEmpty && task.account != effectiveAccount) {
          continue;
        }

        final rawNotes = task.description;
        final parsed = NotesParser.splitNotesAndMetadata(rawNotes);
        final hasTag = parsed.tags.any((t) => t.toLowerCase() == targetTag) ||
            task.tags.any((t) => t.toLowerCase() == targetTag);

        if (hasTag) {
          final newTags = parsed.tags.where((t) => t.toLowerCase() != targetTag).toList();
          final newNotes = NotesParser.combineNotesAndMetadata(parsed.cleanNotes, newTags, spaces: parsed.spaces);
          final updated = TaskItem(
            id: task.id,
            title: task.title,
            description: newNotes,
            due: task.due,
            status: task.status,
            tags: newTags,
            spaces: parsed.spaces,
            listId: task.listId,
            listTitle: task.listTitle,
            account: task.account,
            calculatedPriority: task.calculatedPriority,
            createdAt: task.createdAt,
          );
          _tasks[i] = updated;
          tasksToUpdate.add(updated);
          updatedCount++;
        }
      }

      if (tasksToUpdate.isNotEmpty) {
        await localDb.upsertTasks(tasksToUpdate, syncStatus: 'pending_update');
        for (final t in tasksToUpdate) {
          _syncStandaloneTaskToGoogle(t, isUpdate: true);
        }
      }
      _recomputeAllCaches();
      notifyListeners();
      return updatedCount;
    } else {
      final success = await apiClient.deleteTag(targetTag, account: effectiveAccount);
      if (success) {
        await refreshTasks();
        return 1;
      }
      return 0;
    }
  }

  Future<int> removeSpaceGlobally(String space, {String? account}) async {
    final effectiveAccount = account ?? _selectedAccount;
    final targetSpace = space.trim().toLowerCase();
    int updatedCount = 0;

    if (_isStandalone) {
      final List<TaskItem> tasksToUpdate = [];
      for (int i = 0; i < _tasks.length; i++) {
        final task = _tasks[i];
        if (effectiveAccount != 'all' && effectiveAccount.isNotEmpty && task.account != effectiveAccount) {
          continue;
        }

        final rawNotes = task.description;
        final parsed = NotesParser.splitNotesAndMetadata(rawNotes);
        final matchedKey = parsed.spaces.keys.firstWhere(
          (k) => k.toLowerCase() == targetSpace,
          orElse: () => '',
        );

        if (matchedKey.isNotEmpty) {
          final newSpaces = Map<String, List<String>>.from(parsed.spaces);
          newSpaces.remove(matchedKey);
          final newNotes = NotesParser.combineNotesAndMetadata(parsed.cleanNotes, parsed.tags, spaces: newSpaces);
          final updated = TaskItem(
            id: task.id,
            title: task.title,
            description: newNotes,
            due: task.due,
            status: task.status,
            tags: parsed.tags,
            spaces: newSpaces,
            listId: task.listId,
            listTitle: task.listTitle,
            account: task.account,
            calculatedPriority: task.calculatedPriority,
            createdAt: task.createdAt,
          );
          _tasks[i] = updated;
          tasksToUpdate.add(updated);
          updatedCount++;
        }
      }

      if (tasksToUpdate.isNotEmpty) {
        await localDb.upsertTasks(tasksToUpdate, syncStatus: 'pending_update');
        for (final t in tasksToUpdate) {
          _syncStandaloneTaskToGoogle(t, isUpdate: true);
        }
      }
      _recomputeAllCaches();
      notifyListeners();
      return updatedCount;
    } else {
      final success = await apiClient.deleteSpace(space, account: effectiveAccount);
      if (success) {
        await refreshTasks();
        return 1;
      }
      return 0;
    }
  }

  Future<int> removeSubspaceGlobally(String space, String subspace, {String? account}) async {
    final effectiveAccount = account ?? _selectedAccount;
    final targetSpace = space.trim().toLowerCase();
    final targetSubspace = subspace.trim().toLowerCase();
    int updatedCount = 0;

    if (_isStandalone) {
      final List<TaskItem> tasksToUpdate = [];
      for (int i = 0; i < _tasks.length; i++) {
        final task = _tasks[i];
        if (effectiveAccount != 'all' && effectiveAccount.isNotEmpty && task.account != effectiveAccount) {
          continue;
        }

        final rawNotes = task.description;
        final parsed = NotesParser.splitNotesAndMetadata(rawNotes);
        final matchedKey = parsed.spaces.keys.firstWhere(
          (k) => k.toLowerCase() == targetSpace,
          orElse: () => '',
        );

        if (matchedKey.isNotEmpty) {
          final currentSubs = parsed.spaces[matchedKey] ?? [];
          final hasSub = currentSubs.any((s) => s.toLowerCase() == targetSubspace);
          if (hasSub) {
            final newSpaces = Map<String, List<String>>.from(parsed.spaces);
            newSpaces[matchedKey] = currentSubs.where((s) => s.toLowerCase() != targetSubspace).toList();
            final newNotes = NotesParser.combineNotesAndMetadata(parsed.cleanNotes, parsed.tags, spaces: newSpaces);
            final updated = TaskItem(
              id: task.id,
              title: task.title,
              description: newNotes,
              due: task.due,
              status: task.status,
              tags: parsed.tags,
              spaces: newSpaces,
              listId: task.listId,
              listTitle: task.listTitle,
              account: task.account,
              calculatedPriority: task.calculatedPriority,
              createdAt: task.createdAt,
            );
            _tasks[i] = updated;
            tasksToUpdate.add(updated);
            updatedCount++;
          }
        }
      }

      if (tasksToUpdate.isNotEmpty) {
        await localDb.upsertTasks(tasksToUpdate, syncStatus: 'pending_update');
        for (final t in tasksToUpdate) {
          _syncStandaloneTaskToGoogle(t, isUpdate: true);
        }
      }
      _recomputeAllCaches();
      notifyListeners();
      return updatedCount;
    } else {
      final success = await apiClient.deleteSpace(space, subspace: subspace, account: effectiveAccount);
      if (success) {
        await refreshTasks();
        return 1;
      }
      return 0;
    }
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
      final combinedNotes = NotesParser.combineNotesAndMetadata(
        task.cleanNotes,
        task.tags,
        spaces: task.spaces,
      );

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
