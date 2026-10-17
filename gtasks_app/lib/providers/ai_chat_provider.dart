import 'dart:convert';
import 'package:flutter/foundation.dart';
import '../services/ai/ai_provider.dart';
import '../services/ai/gemini_provider.dart';
import '../services/ai/dashboard_proxy_provider.dart';
import '../services/ai/ai_tools_registry.dart';
import '../services/ai/workflow_engine.dart';
import '../storage/local_database.dart';
import 'settings_provider.dart';

class AiChatMessage {
  final String id;
  final String sessionId;
  final String role; // 'user', 'assistant', 'system'
  final String content;
  final List<dynamic>? toolCalls;
  final List<dynamic>? toolResults;
  final DateTime createdAt;

  AiChatMessage({
    required this.id,
    required this.sessionId,
    required this.role,
    required this.content,
    this.toolCalls,
    this.toolResults,
    required this.createdAt,
  });

  factory AiChatMessage.fromMap(Map<String, dynamic> map) {
    List<dynamic>? calls;
    List<dynamic>? results;
    if (map['tool_calls'] != null && map['tool_calls'].toString().isNotEmpty) {
      try {
        calls = jsonDecode(map['tool_calls'] as String);
      } catch (_) {}
    }
    if (map['tool_results'] != null && map['tool_results'].toString().isNotEmpty) {
      try {
        results = jsonDecode(map['tool_results'] as String);
      } catch (_) {}
    }
    return AiChatMessage(
      id: map['id'] as String,
      sessionId: map['session_id'] as String,
      role: map['role'] as String,
      content: map['content'] as String,
      toolCalls: calls,
      toolResults: results,
      createdAt: DateTime.tryParse(map['created_at']?.toString() ?? '') ?? DateTime.now(),
    );
  }
}

class AiChatProvider with ChangeNotifier {
  final LocalDatabase _db = LocalDatabase.instance;
  final AiToolsRegistry _tools = AiToolsRegistry();
  late final WorkflowEngine _workflowEngine = WorkflowEngine(_tools);

  SettingsProvider? _settings;
  AiProvider? _activeProvider;

  List<Map<String, dynamic>> _sessions = [];
  String? _currentSessionId;
  List<AiChatMessage> _messages = [];

  bool _isLoading = false;
  String? _statusText;
  String? _errorMessage;

  List<Map<String, dynamic>> get sessions => _sessions;
  String? get currentSessionId => _currentSessionId;
  List<AiChatMessage> get messages => _messages;
  bool get isLoading => _isLoading;
  String? get statusText => _statusText;
  String? get errorMessage => _errorMessage;
  AiProvider? get activeProvider => _activeProvider;
  WorkflowEngine get workflowEngine => _workflowEngine;

  void updateSettings(SettingsProvider settings) {
    final oldKey = _settings?.geminiApiKey;
    final oldType = _settings?.aiProviderType;
    final oldUrl = _settings?.baseUrl;
    _settings = settings;

    if (oldKey != settings.geminiApiKey || oldType != settings.aiProviderType || oldUrl != settings.baseUrl || _activeProvider == null) {
      _initProvider();
    }
  }

  void _initProvider() {
    if (_settings == null) return;
    if (_settings!.aiProviderType == 'gemini') {
      if (_settings!.geminiApiKey != null && _settings!.geminiApiKey!.isNotEmpty) {
        _activeProvider = GeminiProvider(
          apiKey: _settings!.geminiApiKey!,
          modelName: _settings!.aiModelName,
          tools: _tools,
        );
      } else {
        _activeProvider = null;
      }
    } else {
      // proxy
      _activeProvider = DashboardProxyProvider(
        baseUrl: _settings!.baseUrl,
        modelName: _settings!.aiModelName,
      );
    }
    notifyListeners();
  }

  Future<void> initialize() async {
    await loadSessions();
    if (_sessions.isNotEmpty && _currentSessionId == null) {
      await switchSession(_sessions.first['id'] as String);
    } else if (_currentSessionId == null) {
      await startNewSession();
    }
  }

  Future<void> loadSessions() async {
    _sessions = await _db.getAiSessions();
    notifyListeners();
  }

  Future<void> startNewSession([String? title]) async {
    final id = 'session_${DateTime.now().millisecondsSinceEpoch}';
    final sessionTitle = title ?? 'New Chat';
    await _db.createAiSession(
      id: id,
      title: sessionTitle,
      provider: _settings?.aiProviderType ?? 'gemini',
    );
    _currentSessionId = id;
    _messages = [];
    await loadSessions();
    notifyListeners();
  }

  Future<void> switchSession(String sessionId) async {
    _currentSessionId = sessionId;
    final rawMessages = await _db.getAiMessages(sessionId);
    _messages = rawMessages.map((m) => AiChatMessage.fromMap(m)).toList();
    notifyListeners();
  }

  Future<void> deleteSession(String sessionId) async {
    await _db.deleteAiSession(sessionId);
    if (_currentSessionId == sessionId) {
      _currentSessionId = null;
      _messages = [];
      await loadSessions();
      if (_sessions.isNotEmpty) {
        await switchSession(_sessions.first['id'] as String);
      } else {
        await startNewSession();
      }
    } else {
      await loadSessions();
    }
    notifyListeners();
  }

  Future<void> sendMessage(String text, {Map<String, dynamic>? extraContext}) async {
    final prompt = text.trim();
    if (prompt.isEmpty) return;

    if (_currentSessionId == null) {
      await startNewSession(prompt.length > 25 ? '${prompt.substring(0, 25)}...' : prompt);
    }

    final sessionId = _currentSessionId!;
    final userMsgId = 'msg_${DateTime.now().millisecondsSinceEpoch}';

    // Save user message locally
    await _db.saveAiMessage(
      id: userMsgId,
      sessionId: sessionId,
      role: 'user',
      content: prompt,
    );
    _messages.add(AiChatMessage(
      id: userMsgId,
      sessionId: sessionId,
      role: 'user',
      content: prompt,
      createdAt: DateTime.now(),
    ));

    _isLoading = true;
    _errorMessage = null;
    _statusText = 'Thinking...';
    notifyListeners();

    try {
      // Check if it's a workflow slash command: /morning, /evening, /triage, /breakdown
      if (prompt.startsWith('/')) {
        final command = prompt.split(' ').first;
        _statusText = 'Executing workflow $command...';
        notifyListeners();

        final workflowResult = await _workflowEngine.execute(command);
        final assistantMsgId = 'msg_${DateTime.now().millisecondsSinceEpoch + 1}';

        await _db.saveAiMessage(
          id: assistantMsgId,
          sessionId: sessionId,
          role: 'assistant',
          content: workflowResult,
        );
        _messages.add(AiChatMessage(
          id: assistantMsgId,
          sessionId: sessionId,
          role: 'assistant',
          content: workflowResult,
          createdAt: DateTime.now(),
        ));

        _isLoading = false;
        _statusText = null;
        await loadSessions();
        notifyListeners();
        return;
      }

      // Check provider
      if (_activeProvider == null) {
        throw Exception(
          _settings?.aiProviderType == 'gemini'
              ? 'Please configure your Gemini API Key in AI Settings to chat.'
              : 'Unable to connect to GTasks Dashboard proxy. Check connection.'
        );
      }

      // Build history for context
      final history = _messages
          .where((m) => m.id != userMsgId)
          .map((m) => {'role': m.role, 'content': m.content})
          .toList();

      _statusText = 'Processing with ${_activeProvider!.name}...';
      notifyListeners();

      final response = await _activeProvider!.chat(
        prompt: prompt,
        history: history,
        context: extraContext,
      );

      final assistantMsgId = 'msg_${DateTime.now().millisecondsSinceEpoch + 2}';

      await _db.saveAiMessage(
        id: assistantMsgId,
        sessionId: sessionId,
        role: 'assistant',
        content: response.reply,
        toolCalls: response.toolCalls,
        toolResults: response.toolResults,
      );

      _messages.add(AiChatMessage(
        id: assistantMsgId,
        sessionId: sessionId,
        role: 'assistant',
        content: response.reply,
        toolCalls: response.toolCalls,
        toolResults: response.toolResults,
        createdAt: DateTime.now(),
      ));

      _isLoading = false;
      _statusText = null;
      await loadSessions();
      notifyListeners();
    } catch (e) {
      _isLoading = false;
      _statusText = null;
      _errorMessage = e.toString().replaceAll('Exception: ', '');
      notifyListeners();
    }
  }

  Future<void> runWorkflow(String command) async {
    await sendMessage(command.startsWith('/') ? command : '/$command');
  }
}
