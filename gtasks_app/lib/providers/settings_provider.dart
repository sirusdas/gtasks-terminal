import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

class SettingsProvider with ChangeNotifier {
  static const String _keyBaseUrl = 'gtasks_base_url';
  static const String _keyDevMode = 'gtasks_dev_mode';
  static const String _keyThemeMode = 'gtasks_theme_mode';

  // Common quick presets
  static const List<String> presetUrls = [
    'http://gtasks.com',
    'http://10.0.2.2:48275',      // Android Emulator host loopback
    'http://localhost:48275',     // Local Linux / Desktop
    'http://192.168.1.100:48275', // Typical local Wi-Fi LAN
  ];

  String _baseUrl = 'http://gtasks.com';
  bool _isDevMode = true; // Enabled by default for easy configuration
  String _themeMode = 'system'; // 'system', 'light', 'dark'

  String get baseUrl => _baseUrl;
  bool get isDevMode => _isDevMode;
  String get themeMode => _themeMode;

  SettingsProvider() {
    _loadSettings();
  }

  Future<void> _loadSettings() async {
    final prefs = await SharedPreferences.getInstance();
    _baseUrl = prefs.getString(_keyBaseUrl) ?? 'http://gtasks.com';
    _isDevMode = prefs.getBool(_keyDevMode) ?? true;
    _themeMode = prefs.getString(_keyThemeMode) ?? 'system';
    notifyListeners();
  }

  Future<void> setThemeMode(String mode) async {
    _themeMode = mode;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_keyThemeMode, mode);
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
