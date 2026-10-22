import 'package:flutter/services.dart';

class WidgetService {
  static const MethodChannel _channel = MethodChannel('com.gtasks.gtasks_app/widget');
  static Function(String action)? _onActionListener;

  static void init() {
    _channel.setMethodCallHandler((call) async {
      if (call.method == 'onActionReceived') {
        final action = call.arguments as String?;
        if (action != null) {
          _onActionListener?.call(action);
        }
      }
    });
  }

  static void setActionListener(Function(String action)? listener) {
    _onActionListener = listener;
  }

  static Future<String?> getInitialAction() async {
    try {
      return await _channel.invokeMethod<String>('getInitialAction');
    } catch (_) {
      return null;
    }
  }

  /// Requests the native Android AppWidget to refresh its RemoteViews and task count
  static Future<void> updateWidget({String? tabsJson, int? activeTabIndex}) async {
    try {
      await _channel.invokeMethod('updateWidget', {
        if (tabsJson != null) 'tabsJson': tabsJson,
        if (activeTabIndex != null) 'activeTabIndex': activeTabIndex,
      });
    } catch (_) {
      // Gracefully ignore on non-Android platforms or when engine is detaching
    }
  }

  /// Requests the native Android Mandala AppWidget to refresh its canvas and metrics
  static Future<void> updateMandalaWidget() async {
    try {
      await _channel.invokeMethod('updateMandalaWidget');
    } catch (_) {
      // Gracefully ignore on non-Android platforms or when engine is detaching
    }
  }
}
