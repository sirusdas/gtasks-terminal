import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

class SettingsProvider with ChangeNotifier {
  static const String _keyBaseUrl = 'gtasks_base_url';
  static const String _keyDevMode = 'gtasks_dev_mode';
  static const String _keyThemeMode = 'gtasks_theme_mode';
  static const String _keyAppMode = 'gtasks_app_mode'; // 'standalone' or 'pc_server'
  static const String _keyOnboarded = 'gtasks_onboarded';
  static const String _keyGoogleAccessToken = 'gtasks_google_access_token';
  static const String _keyGoogleRefreshToken = 'gtasks_google_refresh_token';
  static const String _keyTaskViewMode = 'gtasks_task_view_mode'; // 'detailed', 'compact', 'two_column'
  static const String _keyGeminiApiKey = 'gtasks_gemini_api_key';
  static const String _keyAiProviderType = 'gtasks_ai_provider_type';
  static const String _keyAiModelName = 'gtasks_ai_model_name';
  static const String _keyAutoSyncEnabled = 'gtasks_auto_sync_enabled';
  static const String _keyAutoSyncIntervalMinutes = 'gtasks_auto_sync_interval_minutes';
  static const String _keySyncOnAppStart = 'gtasks_sync_on_app_start';
  static const String _keySyncOnAppResume = 'gtasks_sync_on_app_resume';
  static const String _keyAutoSyncFull = 'gtasks_auto_sync_full';
  static const String _keyLastSyncAt = 'gtasks_last_sync_at';
  static const String _keyLastSyncStatus = 'gtasks_last_sync_status';
  static const String _keyGoogleClientId = 'gtasks_google_client_id';
  static const String _keyGoogleClientSecret = 'gtasks_google_client_secret';

  // Common quick presets
  static const List<String> presetUrls = [
    'http://127.0.0.1:48275',     // Direct reverse port loopback (Android & PC)
    'http://localhost:48275',     // Local loopback
    'http://gtasks.com',          // Loopback DNS (if /etc/hosts exists)
    'http://10.0.2.2:48275',      // Android Emulator host loopback
    'http://192.168.1.100:48275', // Typical local Wi-Fi LAN
  ];

  String _baseUrl = 'http://127.0.0.1:48275';
  bool _isDevMode = true; // Enabled by default for easy configuration
  String _themeMode = 'system'; // 'system', 'light', 'dark'
  String _appMode = 'pc_server'; // 'pc_server' or 'standalone'
  bool _isOnboardingCompleted = false;
  String? _googleAccessToken;
  String? _googleRefreshToken;
  String _taskViewMode = 'detailed'; // 'detailed', 'compact', 'two_column'
  String? _geminiApiKey;
  String _aiProviderType = 'gemini';
  String _aiModelName = 'gemini-1.5-flash';
  String? _microsoftClientId;
  bool _autoSyncEnabled = true;
  int _autoSyncIntervalMinutes = 15;
  bool _syncOnAppStart = true;
  bool _syncOnAppResume = true;
  bool _autoSyncFull = false;
  DateTime? _lastSyncAt;
  String? _lastSyncStatus;
  String? _googleClientId;
  String? _googleClientSecret;

  String get baseUrl => _baseUrl;
  bool get isDevMode => _isDevMode;
  String get themeMode => _themeMode;
  String get appMode => _appMode;
  bool get isStandalone => _appMode == 'standalone';
  bool get isOnboardingCompleted => _isOnboardingCompleted;
  String? get googleAccessToken => _googleAccessToken;
  String? get googleRefreshToken => _googleRefreshToken;
  String? get microsoftClientId => _microsoftClientId;
  String get taskViewMode => _taskViewMode;
  String? get geminiApiKey => _geminiApiKey;
  String get aiProviderType => _aiProviderType;
  String get aiModelName => _aiModelName;
  bool get autoSyncEnabled => _autoSyncEnabled;
  int get autoSyncIntervalMinutes => _autoSyncIntervalMinutes;
  bool get syncOnAppStart => _syncOnAppStart;
  bool get syncOnAppResume => _syncOnAppResume;
  bool get autoSyncFull => _autoSyncFull;
  DateTime? get lastSyncAt => _lastSyncAt;
  String? get lastSyncStatus => _lastSyncStatus;
  String? get googleClientId => _googleClientId;
  String? get googleClientSecret => _googleClientSecret;

  SettingsProvider() {
    _loadSettings();
  }

  static const String _keyAccounts = 'gtasks_accounts_list'; // JSON map of accounts
  static const String _keyDeletedAccounts = 'gtasks_deleted_accounts'; // List of account IDs deleted by user
  static const String _keyMicrosoftClientId = 'gtasks_microsoft_client_id';

  Map<String, Map<String, dynamic>> _storedAccounts = {};
  Set<String> _deletedAccounts = {};

  Map<String, Map<String, dynamic>> get storedAccounts => _storedAccounts;
  Set<String> get deletedAccounts => _deletedAccounts;

  Future<void> _loadSettings() async {
    final prefs = await SharedPreferences.getInstance();
    final savedUrl = prefs.getString(_keyBaseUrl);
    if (savedUrl == null || savedUrl.isEmpty || savedUrl == 'http://gtasks.com') {
      _baseUrl = 'http://127.0.0.1:48275';
    } else {
      _baseUrl = savedUrl;
    }
    _isDevMode = prefs.getBool(_keyDevMode) ?? true;
    _themeMode = prefs.getString(_keyThemeMode) ?? 'system';
    _appMode = prefs.getString(_keyAppMode) ?? 'pc_server';
    _isOnboardingCompleted = prefs.getBool(_keyOnboarded) ?? false;
    _googleAccessToken = prefs.getString(_keyGoogleAccessToken);
    _googleRefreshToken = prefs.getString(_keyGoogleRefreshToken);
    _taskViewMode = prefs.getString(_keyTaskViewMode) ?? 'detailed';
    _geminiApiKey = prefs.getString(_keyGeminiApiKey);
    _aiProviderType = prefs.getString(_keyAiProviderType) ?? 'gemini';
    _aiModelName = prefs.getString(_keyAiModelName) ?? 'gemini-1.5-flash';
    _microsoftClientId = prefs.getString(_keyMicrosoftClientId);
    _autoSyncEnabled = prefs.getBool(_keyAutoSyncEnabled) ?? true;
    _autoSyncIntervalMinutes = prefs.getInt(_keyAutoSyncIntervalMinutes) ?? 15;
    _syncOnAppStart = prefs.getBool(_keySyncOnAppStart) ?? true;
    _syncOnAppResume = prefs.getBool(_keySyncOnAppResume) ?? true;
    _autoSyncFull = prefs.getBool(_keyAutoSyncFull) ?? false;
    final rawLastSync = prefs.getString(_keyLastSyncAt);
    _lastSyncAt = rawLastSync != null ? DateTime.tryParse(rawLastSync) : null;
    _lastSyncStatus = prefs.getString(_keyLastSyncStatus);
    _googleClientId = prefs.getString(_keyGoogleClientId);
    _googleClientSecret = prefs.getString(_keyGoogleClientSecret);

    final rawDeleted = prefs.getStringList(_keyDeletedAccounts);
    if (rawDeleted != null) {
      _deletedAccounts = rawDeleted.toSet();
    }

    final rawAccounts = prefs.getString(_keyAccounts);
    if (rawAccounts != null) {
      try {
        final decoded = json.decode(rawAccounts) as Map<String, dynamic>;
        _storedAccounts = decoded.map((k, v) => MapEntry(k, Map<String, dynamic>.from(v as Map)));
      } catch (_) {}
    }

    // Default account if none exists and not deleted
    if (_storedAccounts.isEmpty && _googleAccessToken != null && !_deletedAccounts.contains('default')) {
      _storedAccounts['default'] = {
        'id': 'default',
        'name': 'Personal (Google)',
        'provider': 'google',
        'access_token': _googleAccessToken,
        'refresh_token': _googleRefreshToken,
      };
    }
    notifyListeners();
  }

  Future<void> saveAccount({
    required String id,
    required String name,
    String? email,
    String provider = 'google',
    String? accessToken,
    String? refreshToken,
    DateTime? expiresAt,
  }) async {
    _deletedAccounts.remove(id);
    final existing = _storedAccounts[id];
    final effectiveRefreshToken = (refreshToken != null && refreshToken.isNotEmpty)
        ? refreshToken
        : existing?['refresh_token']?.toString();
    final effectiveExpiresAt = expiresAt?.toIso8601String() ?? existing?['expires_at']?.toString();
    final effectiveEmail = (email != null && email.isNotEmpty) ? email : existing?['email']?.toString();

    _storedAccounts[id] = {
      'id': id,
      'name': name,
      'provider': provider,
      if (effectiveEmail != null && effectiveEmail.isNotEmpty) 'email': effectiveEmail,
      if (accessToken != null && accessToken.isNotEmpty) 'access_token': accessToken,
      if (effectiveRefreshToken != null && effectiveRefreshToken.isNotEmpty) 'refresh_token': effectiveRefreshToken,
      if (effectiveExpiresAt != null && effectiveExpiresAt.isNotEmpty) 'expires_at': effectiveExpiresAt,
    };
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_keyAccounts, json.encode(_storedAccounts));
    await prefs.setStringList(_keyDeletedAccounts, _deletedAccounts.toList());
    // If it's a Google account and the first or active, update current tokens
    if (provider == 'google' && accessToken != null && accessToken.isNotEmpty) {
      if (_googleAccessToken == null || id == 'default' || id == 'personal') {
        await setGoogleTokens(accessToken: accessToken, refreshToken: effectiveRefreshToken);
      }
    }
    notifyListeners();
  }

  Future<void> updateAccountTokens({
    required String id,
    required String accessToken,
    String? refreshToken,
    DateTime? expiresAt,
  }) async {
    if (_storedAccounts.containsKey(id)) {
      _storedAccounts[id]!['access_token'] = accessToken;
      if (refreshToken != null && refreshToken.isNotEmpty) {
        _storedAccounts[id]!['refresh_token'] = refreshToken;
      }
      if (expiresAt != null) {
        _storedAccounts[id]!['expires_at'] = expiresAt.toIso8601String();
      }
    } else {
      _storedAccounts[id] = {
        'id': id,
        'name': id,
        'provider': 'google',
        'access_token': accessToken,
        if (refreshToken != null && refreshToken.isNotEmpty) 'refresh_token': refreshToken,
        if (expiresAt != null) 'expires_at': expiresAt.toIso8601String(),
      };
    }
    final isGoogle = (_storedAccounts[id]?['provider']?.toString() ?? 'google').toLowerCase() != 'microsoft';
    if (isGoogle && (id == 'default' || id == 'personal' || _googleAccessToken == null)) {
      _googleAccessToken = accessToken;
      if (refreshToken != null && refreshToken.isNotEmpty) {
        _googleRefreshToken = refreshToken;
      }
    }
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_keyAccounts, json.encode(_storedAccounts));
    if (_googleAccessToken != null) {
      await prefs.setString(_keyGoogleAccessToken, _googleAccessToken!);
    }
    if (_googleRefreshToken != null) {
      await prefs.setString(_keyGoogleRefreshToken, _googleRefreshToken!);
    }
    notifyListeners();
  }

  Future<void> setMicrosoftClientId(String? clientId) async {
    _microsoftClientId = clientId;
    final prefs = await SharedPreferences.getInstance();
    if (clientId != null && clientId.isNotEmpty) {
      await prefs.setString(_keyMicrosoftClientId, clientId);
    } else {
      await prefs.remove(_keyMicrosoftClientId);
    }
    notifyListeners();
  }

  Future<void> removeAccount(String id, {bool isHardDelete = false}) async {
    _storedAccounts.remove(id);
    if (isHardDelete) {
      _deletedAccounts.add(id);
      if (id == 'default' || id == 'personal') {
        _deletedAccounts.add('default');
        _deletedAccounts.add('personal');
      }
    }
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_keyAccounts, json.encode(_storedAccounts));
    await prefs.setStringList(_keyDeletedAccounts, _deletedAccounts.toList());
    if (_storedAccounts.isEmpty) {
      await clearGoogleTokens();
    } else {
      final next = _storedAccounts.values.first;
      await setGoogleTokens(
        accessToken: next['access_token'] ?? '',
        refreshToken: next['refresh_token'],
      );
    }
    notifyListeners();
  }

  Future<void> restoreAccount(String id) async {
    _deletedAccounts.remove(id);
    if (id == 'default' || id == 'personal') {
      _deletedAccounts.remove('default');
      _deletedAccounts.remove('personal');
    }
    final prefs = await SharedPreferences.getInstance();
    await prefs.setStringList(_keyDeletedAccounts, _deletedAccounts.toList());
    notifyListeners();
  }

  Future<void> restoreAllAccounts() async {
    _deletedAccounts.clear();
    final prefs = await SharedPreferences.getInstance();
    await prefs.setStringList(_keyDeletedAccounts, []);
    notifyListeners();
  }

  Future<void> setThemeMode(String mode) async {
    _themeMode = mode;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_keyThemeMode, mode);
    notifyListeners();
  }

  Future<void> setAppMode(String mode) async {
    _appMode = mode;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_keyAppMode, mode);
    notifyListeners();
  }

  Future<void> setOnboardingCompleted(bool completed) async {
    _isOnboardingCompleted = completed;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_keyOnboarded, completed);
    notifyListeners();
  }

  Future<void> setGoogleTokens({required String accessToken, String? refreshToken}) async {
    _googleAccessToken = accessToken;
    if (refreshToken != null) {
      _googleRefreshToken = refreshToken;
    }
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_keyGoogleAccessToken, accessToken);
    if (refreshToken != null) {
      await prefs.setString(_keyGoogleRefreshToken, refreshToken);
    }
    notifyListeners();
  }

  Future<void> clearGoogleTokens() async {
    _googleAccessToken = null;
    _googleRefreshToken = null;
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_keyGoogleAccessToken);
    await prefs.remove(_keyGoogleRefreshToken);
    notifyListeners();
  }

  Future<void> setBaseUrl(String url) async {
    String formattedUrl = url.trim();
    if (formattedUrl.endsWith('/')) {
      formattedUrl = formattedUrl.substring(0, formattedUrl.length - 1);
    }
    if (!formattedUrl.startsWith('http://') && !formattedUrl.startsWith('https://')) {
      formattedUrl = 'http://$formattedUrl';
    }

    _baseUrl = formattedUrl;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_keyBaseUrl, _baseUrl);
    notifyListeners();
  }

  Future<void> setDevMode(bool enabled) async {
    _isDevMode = enabled;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_keyDevMode, enabled);
    notifyListeners();
  }

  Future<void> setTaskViewMode(String mode) async {
    _taskViewMode = mode;
    notifyListeners();
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_keyTaskViewMode, mode);
  }

  Future<void> setGeminiApiKey(String? key) async {
    _geminiApiKey = key;
    notifyListeners();
    final prefs = await SharedPreferences.getInstance();
    if (key == null || key.isEmpty) {
      await prefs.remove(_keyGeminiApiKey);
    } else {
      await prefs.setString(_keyGeminiApiKey, key);
    }
  }

  Future<void> setAiProviderType(String type) async {
    _aiProviderType = type;
    notifyListeners();
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_keyAiProviderType, type);
  }

  Future<void> setAiModelName(String model) async {
    _aiModelName = model;
    notifyListeners();
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_keyAiModelName, model);
  }

  Future<void> setAutoSyncEnabled(bool enabled) async {
    _autoSyncEnabled = enabled;
    notifyListeners();
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_keyAutoSyncEnabled, enabled);
  }

  Future<void> setAutoSyncIntervalMinutes(int minutes) async {
    _autoSyncIntervalMinutes = minutes;
    notifyListeners();
    final prefs = await SharedPreferences.getInstance();
    await prefs.setInt(_keyAutoSyncIntervalMinutes, minutes);
  }

  Future<void> setSyncOnAppStart(bool enabled) async {
    _syncOnAppStart = enabled;
    notifyListeners();
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_keySyncOnAppStart, enabled);
  }

  Future<void> setSyncOnAppResume(bool enabled) async {
    _syncOnAppResume = enabled;
    notifyListeners();
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_keySyncOnAppResume, enabled);
  }

  Future<void> setAutoSyncFull(bool fullSync) async {
    _autoSyncFull = fullSync;
    notifyListeners();
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_keyAutoSyncFull, fullSync);
  }

  Future<void> recordSyncResult({required bool success, String? message}) async {
    _lastSyncAt = DateTime.now().toUtc();
    _lastSyncStatus = success ? 'Success' : (message ?? 'Sync failed');
    notifyListeners();
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_keyLastSyncAt, _lastSyncAt!.toIso8601String());
    await prefs.setString(_keyLastSyncStatus, _lastSyncStatus!);
  }

  Future<void> setGoogleOAuthCredentials({String? clientId, String? clientSecret}) async {
    final cleanId = clientId?.trim();
    final cleanSecret = clientSecret?.trim();
    _googleClientId = (cleanId != null && cleanId.isNotEmpty) ? cleanId : null;
    _googleClientSecret = (cleanSecret != null && cleanSecret.isNotEmpty) ? cleanSecret : null;
    notifyListeners();
    final prefs = await SharedPreferences.getInstance();
    if (_googleClientId != null) {
      await prefs.setString(_keyGoogleClientId, _googleClientId!);
    } else {
      await prefs.remove(_keyGoogleClientId);
    }
    if (_googleClientSecret != null) {
      await prefs.setString(_keyGoogleClientSecret, _googleClientSecret!);
    } else {
      await prefs.remove(_keyGoogleClientSecret);
    }
  }
}
