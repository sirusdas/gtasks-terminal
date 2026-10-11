import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:timezone/data/latest_all.dart' as tz;
import 'package:timezone/timezone.dart' as tz;
import '../models/task_item.dart';

class NotificationService {
  static final NotificationService _instance = NotificationService._internal();
  factory NotificationService() => _instance;
  NotificationService._internal();

  final FlutterLocalNotificationsPlugin _notificationsPlugin =
      FlutterLocalNotificationsPlugin();

  bool _initialized = false;

  Future<void> init() async {
    if (_initialized) return;

    tz.initializeTimeZones();

    const androidSettings = AndroidInitializationSettings('@mipmap/ic_launcher');
    const linuxSettings = LinuxInitializationSettings(defaultActionName: 'Open GTasks');

    const initSettings = InitializationSettings(
      android: androidSettings,
      linux: linuxSettings,
    );

    await _notificationsPlugin.initialize(
      settings: initSettings,
      onDidReceiveNotificationResponse: (response) {
        // Handle notification response tap
      },
    );

    // Request permissions on Android 13+
    final androidImpl = _notificationsPlugin
        .resolvePlatformSpecificImplementation<AndroidFlutterLocalNotificationsPlugin>();
    if (androidImpl != null) {
      await androidImpl.requestNotificationsPermission();
    }

    _initialized = true;
  }

  Future<void> showInstantNotification({
    required int id,
    required String title,
    required String body,
  }) async {
    const androidDetails = AndroidNotificationDetails(
      'gtasks_reminders_channel',
      'Task Reminders',
      channelDescription: 'Notifications and reminders for due tasks',
      importance: Importance.high,
      priority: Priority.high,
    );

    const details = NotificationDetails(
      android: androidDetails,
      linux: LinuxNotificationDetails(),
    );

    await _notificationsPlugin.show(
      id: id,
      title: title,
      body: body,
      notificationDetails: details,
    );
  }

  Future<void> scheduleTaskReminder(TaskItem task) async {
    if (task.due == null) return;

    try {
      final dueDate = DateTime.parse(task.due!);
      final scheduledTime = tz.TZDateTime.from(dueDate, tz.local);

      // Only schedule if the date is in the future
      if (scheduledTime.isAfter(tz.TZDateTime.now(tz.local))) {
        const androidDetails = AndroidNotificationDetails(
          'gtasks_reminders_channel',
          'Task Reminders',
          channelDescription: 'Notifications and reminders for due tasks',
          importance: Importance.high,
          priority: Priority.high,
        );

        const details = NotificationDetails(
          android: androidDetails,
          linux: LinuxNotificationDetails(),
        );

        await _notificationsPlugin.zonedSchedule(
          id: task.id.hashCode,
          title: 'Task Due: ${task.title}',
          body: task.description.isNotEmpty ? task.description : 'Your task is due today!',
          scheduledDate: scheduledTime,
          notificationDetails: details,
          androidScheduleMode: AndroidScheduleMode.exactAllowWhileIdle,
        );
      }
    } catch (_) {
      // Ignored if invalid date format
    }
  }

  Future<void> cancelReminder(int id) async {
    await _notificationsPlugin.cancel(id: id);
  }
}
