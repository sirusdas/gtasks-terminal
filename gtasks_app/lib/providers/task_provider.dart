import 'package:flutter/foundation.dart';
import '../api/api_client.dart';
import '../models/task_item.dart';
import '../models/account.dart';

class TaskProvider with ChangeNotifier {
  final ApiClient apiClient;

  List<TaskItem> _tasks = [];
  List<GTasksAccount> _accounts = [];
  String _selectedAccount = 'all';
  String _statusFilter = 'needsAction'; // 'needsAction', 'completed', 'all'
  String _searchQuery = '';
  bool _isLoading = false;
  String? _errorMessage;

  TaskProvider({required this.apiClient});

  void updateBaseUrl(String newUrl) {
    if (apiClient.baseUrl != newUrl) {
      apiClient.baseUrl = newUrl;
      loadInitialData();
    }
  }

  List<TaskItem> get tasks => _filteredTasks();
  List<GTasksAccount> get accounts => _accounts;
  String get selectedAccount => _selectedAccount;
  String get statusFilter => _statusFilter;
  String get searchQuery => _searchQuery;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;

  List<TaskItem> _filteredTasks() {
    return _tasks.where((task) {
      if (_selectedAccount != 'all' && task.account != _selectedAccount) {
        return false;
      }
      if (_statusFilter == 'needsAction' && task.isCompleted) {
        return false;
      }
      if (_statusFilter == 'completed' && !task.isCompleted) {
        return false;
      }
      if (_searchQuery.isNotEmpty) {
        final query = _searchQuery.toLowerCase();
        final matchTitle = task.title.toLowerCase().contains(query);
        final matchNotes = task.description.toLowerCase().contains(query);
        final matchTags = task.tags.any((t) => t.toLowerCase().contains(query));
        return matchTitle || matchNotes || matchTags;
      }
      return true;
    }).toList();
  }

  Future<void> loadInitialData() async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final accountsList = await apiClient.fetchAccounts();
      _accounts = accountsList;
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
      final taskList = await apiClient.fetchTasks(
        account: _selectedAccount == 'all' ? null : _selectedAccount,
        status: _statusFilter == 'all' ? null : _statusFilter,
      );
      _tasks = taskList;
      _errorMessage = null;
    } catch (e) {
      _errorMessage = e.toString();
    }
    notifyListeners();
  }

  Future<void> setAccount(String accountId) async {
    _selectedAccount = accountId;
    if (accountId != 'all') {
      try {
        await apiClient.switchAccount(accountId);
      } catch (_) {}
    }
    await refreshTasks();
  }

  void setStatusFilter(String status) {
    _statusFilter = status;
    refreshTasks();
  }

  void setSearchQuery(String query) {
    _searchQuery = query;
    notifyListeners();
  }

  Future<bool> completeTask(String taskId) async {
    final success = await apiClient.completeTask(taskId, account: _selectedAccount);
    if (success) {
      // Optimistic update
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
    final success = await apiClient.deleteTask(taskId, account: _selectedAccount);
    if (success) {
      _tasks.removeWhere((t) => t.id == taskId);
      notifyListeners();
    }
    return success;
  }
}
