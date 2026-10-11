import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../providers/settings_provider.dart';
import '../../providers/task_provider.dart';
import '../../services/notification_service.dart';

class DeveloperSettingsModal extends StatefulWidget {
  const DeveloperSettingsModal({super.key});

  @override
  State<DeveloperSettingsModal> createState() => _DeveloperSettingsModalState();
}

class _DeveloperSettingsModalState extends State<DeveloperSettingsModal> {
  late TextEditingController _urlController;
  bool _testingConnection = false;
  String? _testResult;

  @override
  void initState() {
    super.initState();
    final settings = context.read<SettingsProvider>();
    _urlController = TextEditingController(text: settings.baseUrl);
  }

  @override
  void dispose() {
    _urlController.dispose();
    super.dispose();
  }

  Future<void> _testConnection(String url) async {
    setState(() {
      _testingConnection = true;
      _testResult = null;
    });

    try {
      final taskProvider = context.read<TaskProvider>();
      // Temporary test with api client
      final client = taskProvider.apiClient;
      final oldUrl = client.baseUrl;
      client.baseUrl = url;
      final accounts = await client.fetchAccounts();
      client.baseUrl = oldUrl;

      setState(() {
        _testResult = 'Success! Connected & found ${accounts.length} account(s).';
      });
    } catch (e) {
      setState(() {
        _testResult = 'Connection Failed: ${e.toString()}';
      });
    } finally {
      setState(() {
        _testingConnection = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final settings = context.watch<SettingsProvider>();
    final taskProvider = context.read<TaskProvider>();
    final theme = Theme.of(context);

    return AlertDialog(
      title: const Row(
        children: [
          Icon(Icons.developer_mode, color: Colors.amber),
          SizedBox(width: 8),
          Text('Developer Settings'),
        ],
      ),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Configure Backend Endpoint',
              style: TextStyle(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 4),
            Text(
              'Switch between local, loopback, or custom remote server URL.',
              style: theme.textTheme.bodySmall,
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _urlController,
              decoration: InputDecoration(
                labelText: 'Server Base URL',
                hintText: 'e.g. http://192.168.1.100:48275',
                border: const OutlineInputBorder(),
                isDense: true,
                suffixIcon: IconButton(
                  icon: const Icon(Icons.check),
                  onPressed: () {
                    settings.setBaseUrl(_urlController.text);
                    taskProvider.updateBaseUrl(_urlController.text);
                  },
                ),
              ),
            ),
            const SizedBox(height: 12),
            const Text('Appearance & Theme:', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
            const SizedBox(height: 6),
            SegmentedButton<String>(
              segments: const [
                ButtonSegment(value: 'system', icon: Icon(Icons.brightness_auto, size: 16), label: Text('Auto')),
                ButtonSegment(value: 'light', icon: Icon(Icons.light_mode, size: 16), label: Text('Light')),
                ButtonSegment(value: 'dark', icon: Icon(Icons.dark_mode, size: 16), label: Text('Dark')),
              ],
              selected: {settings.themeMode},
              onSelectionChanged: (newSelection) {
                settings.setThemeMode(newSelection.first);
              },
            ),
            const SizedBox(height: 14),
            const Text('Reminders & Notifications:', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
            const SizedBox(height: 6),
            OutlinedButton.icon(
              icon: const Icon(Icons.notifications_active, size: 16),
              label: const Text('Send Test Reminder Notification'),
              onPressed: () async {
                final scaffold = ScaffoldMessenger.of(context);
                try {
                  final notif = NotificationService();
                  await notif.showInstantNotification(
                    id: 999,
                    title: 'GTasks Reminder Alert',
                    body: 'Test notification triggered successfully! Due reminders are active.',
                  );
                  scaffold.showSnackBar(
                    const SnackBar(content: Text('Test reminder notification sent!')),
                  );
                } catch (e) {
                  scaffold.showSnackBar(
                    SnackBar(content: Text('Notification error: $e')),
                  );
                }
              },
            ),
            const SizedBox(height: 16),
            if (_testingConnection)
              const Row(
                children: [
                  SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2)),
                  SizedBox(width: 8),
                  Text('Testing connection...', style: TextStyle(fontSize: 12)),
                ],
              )
            else if (_testResult != null)
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: _testResult!.startsWith('Success')
                      ? Colors.green.withValues(alpha: 0.1)
                      : Colors.red.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  _testResult!,
                  style: TextStyle(
                    fontSize: 12,
                    color: _testResult!.startsWith('Success') ? Colors.green : Colors.red,
                  ),
                ),
              ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => _testConnection(_urlController.text.trim()),
          child: const Text('Test Connection'),
        ),
        ElevatedButton(
          onPressed: () {
            settings.setBaseUrl(_urlController.text);
            taskProvider.updateBaseUrl(_urlController.text);
            Navigator.pop(context);
          },
          child: const Text('Save & Apply'),
        ),
      ],
    );
  }
}
