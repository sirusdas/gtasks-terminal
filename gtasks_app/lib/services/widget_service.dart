import 'package:flutter/services.dart';

class WidgetService {
  static const MethodChannel _channel = MethodChannel('com.gtasks.gtasks_app/widget');

  /// Requests the native Android AppWidget to refresh its RemoteViews and task count
  static Future<void> updateWidget() async {
    try {
      await _channel.invokeMethod('updateWidget');
    } catch (_) {
      // Gracefully ignore on non-Android platforms or when engine is detaching
    }
  }
}
