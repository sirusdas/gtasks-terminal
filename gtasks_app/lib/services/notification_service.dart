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
      try {
        await androidImpl.requestExactAlarmsPermission();
      } catch (_) {}
    }

    _initialized = true;
  }

  Future<void> showInstantNotification({
    required int id,
    required String title,
    required String body,
  }) async {
    await init();
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
    if (task.due == null || task.due!.trim().isEmpty || task.isCompleted) return;
    await init();

    try {
      final dueDate = DateTime.parse(task.due!);
      final now = tz.TZDateTime.now(tz.local);

      // Default reminder time: 9:00 AM on due date
      int hour = 9;
      int minute = 0;
      if (!task.due!.contains('T00:00:00') && (dueDate.hour != 0 || dueDate.minute != 0)) {
        hour = dueDate.hour;
        minute = dueDate.minute;
      }

      var scheduledTime = tz.TZDateTime(tz.local, dueDate.year, dueDate.month, dueDate.day, hour, minute);

      // If scheduled morning time has passed but the task is due today,
      // schedule an alert 1 minute from now so user gets reminded today.
      if (scheduledTime.isBefore(now)) {
        final isToday = dueDate.year == now.year && dueDate.month == now.month && dueDate.day == now.day;
        if (isToday) {
          scheduledTime = now.add(const Duration(minutes: 1));
        } else {
          // Task was due on an earlier date (overdue) - don't schedule an alarm in the past
          return;
        }
      }

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
        body: task.description.isNotEmpty ? task.description : 'Task is due today!',
        scheduledDate: scheduledTime,
        notificationDetails: details,
        androidScheduleMode: AndroidScheduleMode.exactAllowWhileIdle,
      );
    } catch (_) {
      // Ignored if invalid date format
    }
  }

  Future<void> cancelReminder(int id) async {
    try {
      await _notificationsPlugin.cancel(id: id);
    } catch (_) {}
  }

  Future<void> syncAllTaskReminders(List<TaskItem> tasks) async {
    await init();
    for (final task in tasks) {
      if (task.isCompleted || task.due == null || task.due!.isEmpty) {
        await cancelReminder(task.id.hashCode);
      } else {
        await scheduleTaskReminder(task);
      }
    }
  }
}
