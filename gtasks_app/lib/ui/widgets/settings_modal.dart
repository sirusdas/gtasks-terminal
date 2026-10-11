import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../providers/settings_provider.dart';
import '../../providers/task_provider.dart';
import '../../services/notification_service.dart';
import 'add_account_modal.dart';

class SettingsModal extends StatefulWidget {
  const SettingsModal({super.key});

  @override
  State<SettingsModal> createState() => _SettingsModalState();
}

class _SettingsModalState extends State<SettingsModal> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  late TextEditingController _urlController;
  bool _testingConnection = false;
  String? _testResult;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
    final settings = context.read<SettingsProvider>();
    _urlController = TextEditingController(text: settings.baseUrl);
  }

  @override
  void dispose() {
    _tabController.dispose();
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

  void _confirmDeleteAccount(BuildContext context, String accountId, String accountName) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Row(
          children: [
            const Icon(Icons.warning_amber_rounded, color: Colors.red),
            const SizedBox(width: 8),
            const Text('Delete Account'),
          ],
        ),
        content: Text(
          'Are you sure you want to remove account "$accountName"?\n\n'
          'This will remove account credentials from the app and clear its cached tasks.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red, foregroundColor: Colors.white),
            onPressed: () async {
              Navigator.pop(ctx);
              final settings = context.read<SettingsProvider>();
              final taskProvider = context.read<TaskProvider>();
              await settings.removeAccount(accountId);
              await taskProvider.removeAccount(accountId);
              try {
                await taskProvider.apiClient.deleteAccount(accountId);
              } catch (_) {}
              await taskProvider.loadInitialData();
              if (mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: Text('Account "$accountName" removed.')),
                );
              }
            },
            child: const Text('Delete'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final settings = context.watch<SettingsProvider>();
    final taskProvider = context.watch<TaskProvider>();

    return Dialog(
      insetPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 24),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Container(
        constraints: const BoxConstraints(maxWidth: 550, maxHeight: 680),
        child: Column(
          children: [
            // Header
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 16, 12, 8),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: theme.colorScheme.primary.withValues(alpha: 0.12),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Icon(Icons.settings, color: theme.colorScheme.primary, size: 22),
                  ),
                  const SizedBox(width: 12),
                  Text(
                    'Settings & Accounts',
                    style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                  ),
                  const Spacer(),
                  IconButton(
                    icon: const Icon(Icons.close),
                    onPressed: () => Navigator.pop(context),
                  ),
                ],
              ),
            ),

            // Tab Bar matching Web Dashboard
            TabBar(
              controller: _tabController,
              isScrollable: true,
              tabAlignment: TabAlignment.start,
              labelColor: theme.colorScheme.primary,
              indicatorColor: theme.colorScheme.primary,
              tabs: const [
                Tab(icon: Icon(Icons.manage_accounts, size: 18), text: 'Accounts'),
                Tab(icon: Icon(Icons.palette_outlined, size: 18), text: 'General & Theme'),
                Tab(icon: Icon(Icons.sync, size: 18), text: 'Sync & Network'),
                Tab(icon: Icon(Icons.bug_report_outlined, size: 18), text: 'Diagnostics'),
              ],
            ),

            const Divider(height: 1),

            // Tab View
            Expanded(
              child: TabBarView(
                controller: _tabController,
                children: [
                  // Tab 1: Accounts Management
                  _buildAccountsTab(context, settings, taskProvider, theme),

                  // Tab 2: General & Theme
                  _buildGeneralTab(context, settings, theme),

                  // Tab 3: Sync & Network
                  _buildSyncTab(context, settings, taskProvider, theme),

                  // Tab 4: Diagnostics
                  _buildDiagnosticsTab(context, settings, taskProvider, theme),
                ],
              ),
            ),

            const Divider(height: 1),

            // Footer
            Padding(
              padding: const EdgeInsets.all(12),
              child: Row(
                children: [
                  TextButton(
                    onPressed: () async {
                      await settings.setOnboardingCompleted(false);
                      if (context.mounted) Navigator.pop(context);
                    },
                    child: const Text('Reset Onboarding', style: TextStyle(color: Colors.orange)),
                  ),
                  const Spacer(),
                  ElevatedButton(
                    onPressed: () => Navigator.pop(context),
                    child: const Text('Done'),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildAccountsTab(
    BuildContext context,
    SettingsProvider settings,
    TaskProvider taskProvider,
    ThemeData theme,
  ) {
    final accounts = taskProvider.accounts;

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Row(
          children: [
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Configured Accounts', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                Text(
                  'Manage your connected Google accounts and workspaces.',
                  style: theme.textTheme.bodySmall?.copyWith(color: theme.hintColor),
                ),
              ],
            ),
            const Spacer(),
            ElevatedButton.icon(
              icon: const Icon(Icons.add, size: 16),
              label: const Text('Add Account'),
              style: ElevatedButton.styleFrom(visualDensity: VisualDensity.compact),
              onPressed: () {
                showDialog(
                  context: context,
                  builder: (_) => const AddGoogleAccountModal(),
                );
              },
            ),
          ],
        ),
        const SizedBox(height: 12),

        if (accounts.isEmpty) ...[
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.amber.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: Colors.amber.withValues(alpha: 0.4)),
            ),
            child: Column(
              children: [
                const Icon(Icons.account_circle_outlined, size: 40, color: Colors.amber),
                const SizedBox(height: 8),
                const Text(
                  'No Google Account Linked',
                  style: TextStyle(fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 4),
                const Text(
                  'Link an account to sync tasks with Google Tasks or manage multiple profiles.',
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 12),
                ),
                const SizedBox(height: 12),
                ElevatedButton.icon(
                  icon: const Icon(Icons.login, size: 16),
                  label: const Text('Connect Google Account'),
                  onPressed: () {
                    showDialog(
                      context: context,
                      builder: (_) => const AddGoogleAccountModal(),
                    );
                  },
                ),
              ],
            ),
          ),
        ] else ...[
          ...accounts.map((acc) {
            final isCurrent = taskProvider.selectedAccount == acc.id;
            return Card(
              margin: const EdgeInsets.only(bottom: 8),
              elevation: 0,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
                side: BorderSide(
                  color: isCurrent
                      ? theme.colorScheme.primary
                      : theme.colorScheme.outlineVariant.withValues(alpha: 0.5),
                  width: isCurrent ? 1.5 : 1,
                ),
              ),
              child: ListTile(
                leading: CircleAvatar(
                  backgroundColor: isCurrent ? theme.colorScheme.primary : theme.colorScheme.surfaceContainerHighest,
                  foregroundColor: isCurrent ? theme.colorScheme.onPrimary : theme.colorScheme.onSurface,
                  child: Text(acc.name.isNotEmpty ? acc.name[0].toUpperCase() : 'G'),
                ),
                title: Row(
                  children: [
                    Text(acc.name, style: const TextStyle(fontWeight: FontWeight.bold)),
                    if (isCurrent) ...[
                      const SizedBox(width: 8),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(
                          color: theme.colorScheme.primary.withValues(alpha: 0.15),
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: Text(
                          'Active',
                          style: TextStyle(fontSize: 10, color: theme.colorScheme.primary, fontWeight: FontWeight.bold),
                        ),
                      ),
                    ],
                  ],
                ),
                subtitle: Text('ID: ${acc.id}', style: const TextStyle(fontSize: 11)),
                trailing: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    if (!isCurrent)
                      IconButton(
                        icon: const Icon(Icons.check_circle_outline, size: 20),
                        tooltip: 'Switch to this account',
                        onPressed: () => taskProvider.setAccount(acc.id),
                      ),
                    IconButton(
                      icon: const Icon(Icons.delete_outline, size: 20, color: Colors.redAccent),
                      tooltip: 'Delete Account',
                      onPressed: () => _confirmDeleteAccount(context, acc.id, acc.name),
                    ),
                  ],
                ),
              ),
            );
          }),
        ],
      ],
    );
  }

  Widget _buildGeneralTab(BuildContext context, SettingsProvider settings, ThemeData theme) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        const Text('Appearance & Theme', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
        const SizedBox(height: 8),
        SegmentedButton<String>(
          segments: const [
            ButtonSegment(value: 'system', icon: Icon(Icons.brightness_auto, size: 16), label: Text('System')),
            ButtonSegment(value: 'light', icon: Icon(Icons.light_mode, size: 16), label: Text('Light')),
            ButtonSegment(value: 'dark', icon: Icon(Icons.dark_mode, size: 16), label: Text('Dark')),
          ],
          selected: {settings.themeMode},
          onSelectionChanged: (newSelection) {
            settings.setThemeMode(newSelection.first);
          },
        ),
        const SizedBox(height: 20),
        const Text('Reminders & Alerts', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
        const SizedBox(height: 8),
        OutlinedButton.icon(
          icon: const Icon(Icons.notifications_active_outlined),
          label: const Text('Test Notification Alert'),
          onPressed: () async {
            final scaffold = ScaffoldMessenger.of(context);
            try {
              final notif = NotificationService();
              await notif.showInstantNotification(
                id: 999,
                title: 'GTasks Notification',
                body: 'Instant alerts are verified and working on this device!',
              );
              scaffold.showSnackBar(const SnackBar(content: Text('Test notification dispatched!')));
            } catch (e) {
              scaffold.showSnackBar(SnackBar(content: Text('Error: $e')));
            }
          },
        ),
      ],
    );
  }

  Widget _buildSyncTab(
    BuildContext context,
    SettingsProvider settings,
    TaskProvider taskProvider,
    ThemeData theme,
  ) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        const Text('Architecture & Mode', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
        const SizedBox(height: 8),
        SegmentedButton<String>(
          segments: const [
            ButtonSegment(
              value: 'standalone',
              icon: Icon(Icons.phone_android, size: 16),
              label: Text('Standalone (No PC)'),
            ),
            ButtonSegment(
              value: 'pc_server',
              icon: Icon(Icons.computer, size: 16),
              label: Text('PC Server'),
            ),
          ],
          selected: {settings.appMode},
          onSelectionChanged: (newSelection) async {
            final newMode = newSelection.first;
            await settings.setAppMode(newMode);
            taskProvider.updateConfig(
              newUrl: settings.baseUrl,
              isStandalone: newMode == 'standalone',
              googleAccessToken: settings.googleAccessToken,
              standaloneAccounts: settings.storedAccounts,
            );
          },
        ),
        const SizedBox(height: 16),

        if (!settings.isStandalone) ...[
          const Text('PC Server URL', style: TextStyle(fontWeight: FontWeight.bold)),
          const SizedBox(height: 4),
          TextField(
            controller: _urlController,
            decoration: const InputDecoration(
              hintText: 'http://gtasks.com or http://192.168.1.x:48275',
              border: OutlineInputBorder(),
              isDense: true,
            ),
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              OutlinedButton(
                onPressed: () => _testConnection(_urlController.text.trim()),
                child: const Text('Test Connection'),
              ),
              const SizedBox(width: 8),
              ElevatedButton(
                onPressed: () {
                  settings.setBaseUrl(_urlController.text);
                  taskProvider.updateBaseUrl(_urlController.text);
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Server URL saved!')),
                  );
                },
                child: const Text('Save URL'),
              ),
            ],
          ),
          if (_testingConnection)
            const Padding(
              padding: EdgeInsets.only(top: 8),
              child: Row(
                children: [
                  SizedBox(width: 14, height: 14, child: CircularProgressIndicator(strokeWidth: 2)),
                  SizedBox(width: 8),
                  Text('Testing...', style: TextStyle(fontSize: 12)),
                ],
              ),
            )
          else if (_testResult != null)
            Padding(
              padding: EdgeInsets.only(top: 8),
              child: Text(
                _testResult!,
                style: TextStyle(
                  fontSize: 12,
                  color: _testResult!.startsWith('Success') ? Colors.green : Colors.red,
                ),
              ),
            ),
        ] else ...[
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.blue.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(10),
            ),
            child: const Text(
              'ℹ️ Running in Standalone Mode: Tasks are stored locally on device SQLite and synced directly with Google Tasks APIs without requiring a desktop server.',
              style: TextStyle(fontSize: 12),
            ),
          ),
        ],
      ],
    );
  }

  Widget _buildDiagnosticsTab(
    BuildContext context,
    SettingsProvider settings,
    TaskProvider taskProvider,
    ThemeData theme,
  ) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        const Text('System Diagnostics', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
        const SizedBox(height: 12),
        _diagRow('Architecture Mode', settings.isStandalone ? 'Standalone (Local SQLite)' : 'PC Backend Server'),
        _diagRow('Backend URL', settings.baseUrl),
        _diagRow('Cached Tasks', '${taskProvider.allTasksUnfiltered.length}'),
        _diagRow('Pending Tasks', '${taskProvider.pendingTasksCount}'),
        _diagRow('Active Accounts', '${taskProvider.accounts.length}'),
        _diagRow('Active Account ID', taskProvider.selectedAccount),
        _diagRow('Google Token Active', settings.googleAccessToken != null ? 'Yes' : 'No'),
        const SizedBox(height: 16),
        OutlinedButton.icon(
          icon: const Icon(Icons.refresh),
          label: const Text('Force Reload Local Cache'),
          onPressed: () async {
            await taskProvider.loadInitialData();
            if (context.mounted) {
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Cache reloaded.')),
              );
            }
          },
        ),
      ],
    );
  }

  Widget _diagRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(fontSize: 13)),
          Text(value, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }
}
