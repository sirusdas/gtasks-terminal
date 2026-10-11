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

  String get baseUrl => _baseUrl;
  bool get isDevMode => _isDevMode;
  String get themeMode => _themeMode;
  String get appMode => _appMode;
  bool get isStandalone => _appMode == 'standalone';
  bool get isOnboardingCompleted => _isOnboardingCompleted;
  String? get googleAccessToken => _googleAccessToken;
  String? get googleRefreshToken => _googleRefreshToken;

  SettingsProvider() {
    _loadSettings();
  }

  static const String _keyAccounts = 'gtasks_accounts_list'; // JSON map of accounts

  Map<String, Map<String, dynamic>> _storedAccounts = {};

  Map<String, Map<String, dynamic>> get storedAccounts => _storedAccounts;

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

    final rawAccounts = prefs.getString(_keyAccounts);
    if (rawAccounts != null) {
      try {
        final decoded = json.decode(rawAccounts) as Map<String, dynamic>;
        _storedAccounts = decoded.map((k, v) => MapEntry(k, Map<String, dynamic>.from(v as Map)));
      } catch (_) {}
    }

    // Default account if none exists
    if (_storedAccounts.isEmpty && _googleAccessToken != null) {
      _storedAccounts['default'] = {
        'id': 'default',
        'name': 'Personal (Google)',
        'access_token': _googleAccessToken,
        'refresh_token': _googleRefreshToken,
      };
    }
    notifyListeners();
  }

  Future<void> saveAccount({
    required String id,
    required String name,
    String? accessToken,
    String? refreshToken,
  }) async {
    _storedAccounts[id] = {
      'id': id,
      'name': name,
      if (accessToken != null) 'access_token': accessToken,
      if (refreshToken != null) 'refresh_token': refreshToken,
    };
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_keyAccounts, json.encode(_storedAccounts));
    // If it's the first or active, update current tokens
    if (accessToken != null && accessToken.isNotEmpty) {
      if (_googleAccessToken == null || id == 'default') {
        await setGoogleTokens(accessToken: accessToken, refreshToken: refreshToken);
      }
    }
    notifyListeners();
  }

  Future<void> removeAccount(String id) async {
    _storedAccounts.remove(id);
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_keyAccounts, json.encode(_storedAccounts));
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
}
