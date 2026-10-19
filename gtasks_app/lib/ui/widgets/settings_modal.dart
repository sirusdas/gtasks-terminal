import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../providers/settings_provider.dart';
import '../../providers/task_provider.dart';
import '../../services/notification_service.dart';
import '../../services/backup_service.dart';
import '../../services/subscriber_service.dart';
import 'add_account_modal.dart';
import 'sync_progress_dialog.dart';

class SettingsModal extends StatefulWidget {
  const SettingsModal({super.key});

  @override
  State<SettingsModal> createState() => _SettingsModalState();
}

class _SettingsModalState extends State<SettingsModal> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  late TextEditingController _urlController;
  late TextEditingController _backupNoteController;
  late TextEditingController _subscriberApiUrlController;
  bool _testingConnection = false;
  String? _testResult;

  List<BackupMetadata> _backups = [];
  bool _loadingBackups = false;
  bool _creatingBackup = false;
  bool _testingSubscriberApi = false;
  String? _subscriberApiResult;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 6, vsync: this);
    final settings = context.read<SettingsProvider>();
    _urlController = TextEditingController(text: settings.baseUrl);
    _backupNoteController = TextEditingController();
    _subscriberApiUrlController = TextEditingController();
    _loadBackupAndSubscriberData();
  }

  Future<void> _loadBackupAndSubscriberData() async {
    setState(() => _loadingBackups = true);
    try {
      final list = await BackupService().listBackups();
      final subUrl = await SubscriberService().getApiUrl();
      if (mounted) {
        setState(() {
          _backups = list;
          _subscriberApiUrlController.text = subUrl ?? '';
          _loadingBackups = false;
        });
      }
    } catch (_) {
      if (mounted) setState(() => _loadingBackups = false);
    }
  }

  @override
  void dispose() {
    _tabController.dispose();
    _urlController.dispose();
    _backupNoteController.dispose();
    _subscriberApiUrlController.dispose();
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
            const Icon(Icons.warning_amber_rounded, color: Colors.amber),
            const SizedBox(width: 8),
            Expanded(child: Text('Delete "$accountName"')),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Select how you want to delete this account:',
              style: TextStyle(fontSize: 13),
            ),
            const SizedBox(height: 16),
            Card(
              elevation: 0,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(10),
                side: BorderSide(color: Colors.blue.withValues(alpha: 0.3)),
              ),
              color: Colors.blue.withValues(alpha: 0.05),
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Row(
                      children: [
                        Icon(Icons.phonelink_erase, size: 18, color: Colors.blue),
                        SizedBox(width: 6),
                        Text('Soft Delete (Local Only)', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Colors.blue)),
                      ],
                    ),
                    const SizedBox(height: 4),
                    const Text(
                      'Clears cached data and credentials from this device only. Server tasks and Google account remain untouched. Can be restored anytime.',
                      style: TextStyle(fontSize: 11),
                    ),
                    const SizedBox(height: 8),
                    Align(
                      alignment: Alignment.centerRight,
                      child: ElevatedButton.icon(
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.blue,
                          foregroundColor: Colors.white,
                          visualDensity: VisualDensity.compact,
                        ),
                        icon: const Icon(Icons.phonelink_erase, size: 14),
                        label: const Text('Soft Delete'),
                        onPressed: () async {
                          Navigator.pop(ctx);
                          final settings = context.read<SettingsProvider>();
                          final taskProvider = context.read<TaskProvider>();
                          await settings.removeAccount(accountId, isHardDelete: false);
                          await taskProvider.removeAccount(accountId, isHardDelete: false);
                          await taskProvider.loadInitialData();
                          if (mounted) {
                            ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(content: Text('Account "$accountName" soft deleted from device.')),
                            );
                          }
                        },
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 12),
            Card(
              elevation: 0,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(10),
                side: BorderSide(color: Colors.red.withValues(alpha: 0.3)),
              ),
              color: Colors.red.withValues(alpha: 0.05),
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Row(
                      children: [
                        Icon(Icons.delete_forever, size: 18, color: Colors.red),
                        SizedBox(width: 6),
                        Text('Hard Delete (Permanent)', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Colors.red)),
                      ],
                    ),
                    const SizedBox(height: 4),
                    const Text(
                      'Removes account from device and permanently deletes tasks from server. An automatic server backup is saved.',
                      style: TextStyle(fontSize: 11),
                    ),
                    const SizedBox(height: 8),
                    Align(
                      alignment: Alignment.centerRight,
                      child: ElevatedButton.icon(
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.red,
                          foregroundColor: Colors.white,
                          visualDensity: VisualDensity.compact,
                        ),
                        icon: const Icon(Icons.delete_forever, size: 14),
                        label: const Text('Hard Delete'),
                        onPressed: () async {
                          Navigator.pop(ctx);
                          final settings = context.read<SettingsProvider>();
                          final taskProvider = context.read<TaskProvider>();
                          await settings.removeAccount(accountId, isHardDelete: true);
                          await taskProvider.removeAccount(accountId, isHardDelete: true);
                          try {
                            await taskProvider.apiClient.deleteAccount(accountId, hard: true);
                          } catch (_) {}
                          await taskProvider.loadInitialData();
                          if (mounted) {
                            ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(content: Text('Account "$accountName" permanently deleted.')),
                            );
                          }
                        },
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancel'),
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
                Tab(icon: Icon(Icons.category_outlined, size: 18), text: 'Tags & Spaces'),
                Tab(icon: Icon(Icons.palette_outlined, size: 18), text: 'General & Theme'),
                Tab(icon: Icon(Icons.sync, size: 18), text: 'Sync & Network'),
                Tab(icon: Icon(Icons.backup_outlined, size: 18), text: 'Backup & Restore'),
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

                  // Tab 2: Tags & Spaces Management
                  _buildTagsSpacesTab(context, taskProvider, theme),

                  // Tab 3: General & Theme
                  _buildGeneralTab(context, settings, theme),

                  // Tab 4: Sync & Network
                  _buildSyncTab(context, settings, taskProvider, theme),

                  // Tab 5: Backup & Restore
                  _buildBackupTab(context, taskProvider, theme),

                  // Tab 6: Diagnostics
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
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Configured Accounts', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                  Text(
                    'Manage your connected Google accounts and workspaces.',
                    style: theme.textTheme.bodySmall?.copyWith(color: theme.hintColor),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 8),
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
                  backgroundColor: isCurrent
                      ? (acc.isMicrosoft ? const Color(0xFF0078D4) : theme.colorScheme.primary)
                      : (acc.isMicrosoft ? const Color(0xFF0078D4).withValues(alpha: 0.15) : theme.colorScheme.surfaceContainerHighest),
                  foregroundColor: isCurrent
                      ? Colors.white
                      : (acc.isMicrosoft ? const Color(0xFF0078D4) : theme.colorScheme.onSurface),
                  child: Icon(
                    acc.isMicrosoft ? Icons.task_alt : Icons.g_mobiledata,
                    size: 20,
                  ),
                ),
                title: Row(
                  children: [
                    Text(acc.name, style: const TextStyle(fontWeight: FontWeight.bold)),
                    const SizedBox(width: 6),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1.5),
                      decoration: BoxDecoration(
                        color: acc.isMicrosoft
                            ? const Color(0xFF0078D4).withValues(alpha: 0.15)
                            : Colors.teal.withValues(alpha: 0.15),
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: Text(
                        acc.isMicrosoft ? 'Microsoft To Do' : 'Google Tasks',
                        style: TextStyle(
                          fontSize: 9,
                          fontWeight: FontWeight.bold,
                          color: acc.isMicrosoft ? const Color(0xFF0078D4) : Colors.teal,
                        ),
                      ),
                    ),
                    if (isCurrent) ...[
                      const SizedBox(width: 6),
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
                subtitle: Text(
                  acc.email != null && acc.email!.isNotEmpty
                      ? '${acc.email} • ID: ${acc.id}'
                      : 'ID: ${acc.id}',
                  style: const TextStyle(fontSize: 11),
                ),
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
        if (settings.deletedAccounts.isNotEmpty) ...[
          const SizedBox(height: 16),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.green.withValues(alpha: 0.08),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: Colors.green.withValues(alpha: 0.3)),
            ),
            child: Row(
              children: [
                const Icon(Icons.restore, color: Colors.green),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('Restore Personal Account', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                      Text(
                        'You have deleted account(s) on file. Tap to restore.',
                        style: theme.textTheme.bodySmall?.copyWith(color: theme.hintColor),
                      ),
                    ],
                  ),
                ),
                ElevatedButton.icon(
                  icon: const Icon(Icons.restore, size: 14),
                  label: const Text('Restore'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.green,
                    foregroundColor: Colors.white,
                    visualDensity: VisualDensity.compact,
                  ),
                  onPressed: () async {
                    await settings.restoreAllAccounts();
                    await taskProvider.restoreAllAccounts();
                    if (mounted) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text('Personal account restored successfully!')),
                      );
                    }
                  },
                ),
              ],
            ),
          ),
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
        const SizedBox(height: 20),
        const Text('Google Tasks Synchronization', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
        const SizedBox(height: 8),
        Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: theme.colorScheme.surfaceContainerHighest.withValues(alpha: 0.4),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: theme.dividerColor.withValues(alpha: 0.3)),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  const Icon(Icons.cloud_sync, color: Colors.blueAccent),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'Full Sync (gtasks advanced-sync --all)',
                          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                        ),
                        Text(
                          'Synchronizes 100% of tasks across all tasklists without date range limits.',
                          style: theme.textTheme.bodySmall?.copyWith(color: theme.hintColor),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  ElevatedButton.icon(
                    icon: const Icon(Icons.cloud_sync, size: 16),
                    label: const Text('Run Full Sync (--all)'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.blueAccent,
                      foregroundColor: Colors.white,
                    ),
                    onPressed: () {
                      SyncProgressDialog.show(context, isFullSync: true);
                    },
                  ),
                  OutlinedButton.icon(
                    icon: const Icon(Icons.sync, size: 16),
                    label: const Text('Quick Sync'),
                    onPressed: () {
                      SyncProgressDialog.show(context, isFullSync: false);
                    },
                  ),
                ],
              ),
            ],
          ),
        ),
        const SizedBox(height: 20),
        const Text('User Onboarding & Subscriber Webhook', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
        const SizedBox(height: 8),
        Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: theme.colorScheme.surfaceContainerHighest.withValues(alpha: 0.4),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: theme.dividerColor.withValues(alpha: 0.3)),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Row(
                children: [
                  Icon(Icons.mark_email_read_outlined, color: Colors.indigoAccent),
                  SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      'External Subscriber API',
                      style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 4),
              Text(
                'Automatically pushes onboarded user emails and sign-ups to your external CRM/newsletter API endpoint.',
                style: theme.textTheme.bodySmall?.copyWith(color: theme.hintColor),
              ),
              const SizedBox(height: 10),
              TextField(
                controller: _subscriberApiUrlController,
                decoration: const InputDecoration(
                  hintText: 'https://api.yourdomain.com/v1/subscribers',
                  labelText: 'Webhook / Subscriber API Endpoint',
                  border: OutlineInputBorder(),
                  isDense: true,
                ),
              ),
              const SizedBox(height: 10),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  ElevatedButton(
                    onPressed: () async {
                      await SubscriberService().setApiUrl(_subscriberApiUrlController.text);
                      if (context.mounted) {
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(content: Text('Subscriber API URL saved and pending queue flushed!')),
                        );
                      }
                    },
                    child: const Text('Save Endpoint'),
                  ),
                  OutlinedButton(
                    onPressed: _testingSubscriberApi
                        ? null
                        : () async {
                            final url = _subscriberApiUrlController.text.trim();
                            if (url.isEmpty) return;
                            setState(() {
                              _testingSubscriberApi = true;
                              _subscriberApiResult = null;
                            });
                            final res = await SubscriberService().testEndpoint(url);
                            setState(() {
                              _testingSubscriberApi = false;
                              _subscriberApiResult = res.message;
                            });
                          },
                    child: _testingSubscriberApi
                        ? const SizedBox(width: 14, height: 14, child: CircularProgressIndicator(strokeWidth: 2))
                        : const Text('Test Connection'),
                  ),
                  OutlinedButton.icon(
                    icon: const Icon(Icons.send, size: 14),
                    label: const Text('Sync Active Accounts Now'),
                    onPressed: () async {
                      int count = 0;
                      for (final acc in taskProvider.accounts) {
                        if (acc.email != null && acc.email!.isNotEmpty) {
                          final res = await SubscriberService().syncSubscriber(
                            email: acc.email!,
                            name: acc.name,
                            accountId: acc.id,
                            force: true,
                          );
                          if (res.success) count++;
                        }
                      }
                      if (context.mounted) {
                        ScaffoldMessenger.of(context).showSnackBar(
                          SnackBar(content: Text('Synced $count account email(s) to subscriber API')),
                        );
                      }
                    },
                  ),
                ],
              ),
              if (_subscriberApiResult != null) ...[
                const SizedBox(height: 8),
                Text(
                  _subscriberApiResult!,
                  style: TextStyle(
                    fontSize: 12,
                    color: _subscriberApiResult!.contains('reachable') || _subscriberApiResult!.contains('Success')
                        ? Colors.green
                        : Colors.redAccent,
                  ),
                ),
              ],
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildBackupTab(
    BuildContext context,
    TaskProvider taskProvider,
    ThemeData theme,
  ) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        const Text('Database Backup & Recovery', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
        const SizedBox(height: 6),
        Text(
          'Export and restore complete snapshots of your tasks, tabs, spaces, and metadata.',
          style: TextStyle(fontSize: 12, color: theme.hintColor),
        ),
        const SizedBox(height: 16),

        // Create Backup Card
        Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: theme.colorScheme.surfaceContainerHighest.withValues(alpha: 0.4),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: theme.dividerColor.withValues(alpha: 0.3)),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  const Icon(Icons.archive_outlined, color: Colors.teal),
                  const SizedBox(width: 8),
                  const Text('Create Snapshot Backup', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                  const Spacer(),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                    decoration: BoxDecoration(
                      color: Colors.teal.withValues(alpha: 0.15),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Text(
                      '${taskProvider.allTasksUnfiltered.length} tasks',
                      style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Colors.teal),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 10),
              TextField(
                controller: _backupNoteController,
                decoration: const InputDecoration(
                  hintText: 'Backup note/label (optional)',
                  border: OutlineInputBorder(),
                  isDense: true,
                ),
              ),
              const SizedBox(height: 10),
              ElevatedButton.icon(
                icon: _creatingBackup
                    ? const SizedBox(width: 14, height: 14, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                    : const Icon(Icons.save_alt, size: 16),
                label: Text(_creatingBackup ? 'Creating...' : 'Create Backup Now'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.teal,
                  foregroundColor: Colors.white,
                ),
                onPressed: _creatingBackup
                    ? null
                    : () async {
                        setState(() => _creatingBackup = true);
                        try {
                          final note = _backupNoteController.text.trim().isEmpty ? 'Manual Snapshot' : _backupNoteController.text.trim();
                          final meta = await BackupService().createBackup(note: note);
                          _backupNoteController.clear();
                          await _loadBackupAndSubscriberData();
                          if (context.mounted) {
                            ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(content: Text('Backup created: ${meta.filename} (${meta.taskCount} tasks)')),
                            );
                          }
                        } catch (e) {
                          if (context.mounted) {
                            ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(content: Text('Failed to create backup: $e')),
                            );
                          }
                        } finally {
                          if (mounted) setState(() => _creatingBackup = false);
                        }
                      },
              ),
            ],
          ),
        ),

        const SizedBox(height: 20),

        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const Text('Available Backups', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
            IconButton(
              icon: const Icon(Icons.refresh, size: 18),
              tooltip: 'Refresh backups',
              onPressed: _loadBackupAndSubscriberData,
            ),
          ],
        ),
        const SizedBox(height: 8),

        if (_loadingBackups)
          const Center(child: Padding(padding: EdgeInsets.all(16), child: CircularProgressIndicator()))
        else if (_backups.isEmpty)
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: theme.colorScheme.surfaceContainerHighest.withValues(alpha: 0.2),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Center(
              child: Text('No backup files created yet.', style: TextStyle(color: theme.hintColor, fontStyle: FontStyle.italic)),
            ),
          )
        else
          ..._backups.map((b) => Container(
                margin: const EdgeInsets.only(bottom: 10),
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: theme.colorScheme.surfaceContainerHighest.withValues(alpha: 0.35),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: theme.dividerColor.withValues(alpha: 0.2)),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        const Icon(Icons.description_outlined, size: 18, color: Colors.blueAccent),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            b.filename,
                            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12.5),
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                          decoration: BoxDecoration(
                            color: Colors.blueAccent.withValues(alpha: 0.12),
                            borderRadius: BorderRadius.circular(6),
                          ),
                          child: Text(
                            '${b.taskCount} tasks • ${b.formattedSize}',
                            style: const TextStyle(fontSize: 10.5, fontWeight: FontWeight.bold, color: Colors.blueAccent),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 6),
                    Text(
                      'Note: ${b.note} | ${b.createdAt.toLocal().toString().split('.').first}',
                      style: TextStyle(fontSize: 11, color: theme.hintColor),
                    ),
                    const SizedBox(height: 8),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.end,
                      children: [
                        OutlinedButton.icon(
                          icon: const Icon(Icons.restore, size: 15, color: Colors.teal),
                          label: const Text('Restore', style: TextStyle(fontSize: 12, color: Colors.teal)),
                          style: OutlinedButton.styleFrom(
                            visualDensity: VisualDensity.compact,
                            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 0),
                          ),
                          onPressed: () => _confirmRestoreBackup(context, taskProvider, b),
                        ),
                        const SizedBox(width: 8),
                        IconButton(
                          icon: const Icon(Icons.delete_outline, size: 18, color: Colors.redAccent),
                          tooltip: 'Delete backup',
                          visualDensity: VisualDensity.compact,
                          onPressed: () async {
                            await BackupService().deleteBackup(b.filePath);
                            await _loadBackupAndSubscriberData();
                          },
                        ),
                      ],
                    ),
                  ],
                ),
              )),
      ],
    );
  }

  void _confirmRestoreBackup(BuildContext context, TaskProvider taskProvider, BackupMetadata backup) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Row(
          children: [
            Icon(Icons.warning_amber_rounded, color: Colors.amber),
            SizedBox(width: 8),
            Text('Confirm Restore'),
          ],
        ),
        content: Text(
          'Restoring "${backup.filename}" will load ${backup.taskCount} tasks into your local database.\n\n'
          'A safety backup of your current database will be saved automatically beforehand.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancel'),
          ),
          FilledButton(
            style: FilledButton.styleFrom(backgroundColor: Colors.teal),
            onPressed: () async {
              Navigator.pop(ctx);
              try {
                final count = await BackupService().restoreBackup(backup.filePath);
                await taskProvider.refreshTasks();
                await _loadBackupAndSubscriberData();
                if (context.mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('Successfully restored $count tasks from backup!')),
                  );
                }
              } catch (e) {
                if (context.mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('Restore failed: $e')),
                  );
                }
              }
            },
            child: const Text('Restore Now'),
          ),
        ],
      ),
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

  Widget _buildTagsSpacesTab(
    BuildContext context,
    TaskProvider taskProvider,
    ThemeData theme,
  ) {
    final spaces = taskProvider.spacesWithCounts;
    final subspaces = taskProvider.subspacesWithCounts;
    final tags = taskProvider.tagsWithCounts;

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Row(
              children: [
                Icon(Icons.rocket_launch, size: 18, color: theme.colorScheme.primary),
                const SizedBox(width: 8),
                const Text(
                  'Spaces & Sub-spaces',
                  style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
                ),
              ],
            ),
            Text(
              '${spaces.length} space(s)',
              style: TextStyle(fontSize: 12, color: theme.hintColor),
            ),
          ],
        ),
        const SizedBox(height: 6),
        Text(
          'Remove spaces or individual sub-spaces across all tasks.',
          style: TextStyle(fontSize: 12, color: theme.hintColor),
        ),
        const SizedBox(height: 12),
        if (spaces.isEmpty)
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 8),
            child: Text(
              'No spaces found in tasks.',
              style: TextStyle(fontStyle: FontStyle.italic, color: theme.hintColor, fontSize: 13),
            ),
          )
        else
          ...spaces.entries.map((entry) {
            final spaceName = entry.key;
            final count = entry.value;
            final spaceSubs = subspaces[spaceName] ?? {};

            return Container(
              margin: const EdgeInsets.only(bottom: 10),
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: theme.colorScheme.surfaceContainerHighest.withValues(alpha: 0.35),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                  color: theme.colorScheme.outlineVariant.withValues(alpha: 0.3),
                ),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      const Icon(Icons.rocket_launch, size: 16, color: Colors.deepPurpleAccent),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          spaceName,
                          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                        ),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(
                          color: Colors.deepPurpleAccent.withValues(alpha: 0.15),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Text(
                          '$count task${count != 1 ? 's' : ''}',
                          style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: Colors.deepPurpleAccent),
                        ),
                      ),
                      const SizedBox(width: 6),
                      IconButton(
                        icon: const Icon(Icons.delete_outline, color: Colors.redAccent, size: 20),
                        tooltip: 'Delete Space',
                        visualDensity: VisualDensity.compact,
                        padding: EdgeInsets.zero,
                        constraints: const BoxConstraints(minWidth: 28, minHeight: 28),
                        onPressed: () => _confirmDeleteSpace(context, taskProvider, spaceName, null, count),
                      ),
                    ],
                  ),
                  if (spaceSubs.isNotEmpty) ...[
                    const SizedBox(height: 8),
                    Wrap(
                      spacing: 6,
                      runSpacing: 4,
                      children: spaceSubs.entries.map((subEntry) {
                        final subName = subEntry.key;
                        final subCount = subEntry.value;
                        return Chip(
                          labelPadding: const EdgeInsets.symmetric(horizontal: 4),
                          visualDensity: VisualDensity.compact,
                          padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 0),
                          label: Text(
                            '$subName ($subCount)',
                            style: const TextStyle(fontSize: 11),
                          ),
                          deleteIcon: const Icon(Icons.close_rounded, size: 14, color: Colors.redAccent),
                          onDeleted: () => _confirmDeleteSpace(context, taskProvider, spaceName, subName, subCount),
                        );
                      }).toList(),
                    ),
                  ],
                ],
              ),
            );
          }),

        const Divider(height: 28),

        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const Row(
              children: [
                Icon(Icons.tag, size: 18, color: Colors.teal),
                SizedBox(width: 8),
                Text(
                  'Tags',
                  style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
                ),
              ],
            ),
            Text(
              '${tags.length} tag(s)',
              style: TextStyle(fontSize: 12, color: theme.hintColor),
            ),
          ],
        ),
        const SizedBox(height: 6),
        Text(
          'Remove tags globally from tasks.',
          style: TextStyle(fontSize: 12, color: theme.hintColor),
        ),
        const SizedBox(height: 12),
        if (tags.isEmpty)
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 8),
            child: Text(
              'No tags found in tasks.',
              style: TextStyle(fontStyle: FontStyle.italic, color: theme.hintColor, fontSize: 13),
            ),
          )
        else
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: tags.entries.map((entry) {
              final tagName = entry.key;
              final count = entry.value;
              return Container(
                padding: const EdgeInsets.only(left: 8, right: 4, top: 4, bottom: 4),
                decoration: BoxDecoration(
                  color: Colors.teal.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: Colors.teal.withValues(alpha: 0.3)),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      '#$tagName',
                      style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: Colors.teal),
                    ),
                    const SizedBox(width: 4),
                    Text(
                      '($count)',
                      style: TextStyle(fontSize: 11, color: theme.hintColor),
                    ),
                    const SizedBox(width: 4),
                    GestureDetector(
                      onTap: () => _confirmDeleteTag(context, taskProvider, tagName, count),
                      child: const Icon(Icons.close_rounded, size: 16, color: Colors.redAccent),
                    ),
                  ],
                ),
              );
            }).toList(),
          ),
      ],
    );
  }

  void _confirmDeleteSpace(
    BuildContext context,
    TaskProvider taskProvider,
    String space,
    String? subspace,
    int count,
  ) {
    final label = subspace != null ? "sub-space '$space › $subspace'" : "space '$space' and its sub-spaces";
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Row(
          children: [
            Icon(Icons.warning_amber_rounded, color: Colors.redAccent),
            SizedBox(width: 8),
            Text('Confirm Removal'),
          ],
        ),
        content: Text('Are you sure you want to remove $label from $count task(s)?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancel'),
          ),
          FilledButton(
            style: FilledButton.styleFrom(backgroundColor: Colors.redAccent),
            onPressed: () async {
              Navigator.pop(ctx);
              if (subspace != null) {
                await taskProvider.removeSubspaceGlobally(space, subspace);
              } else {
                await taskProvider.removeSpaceGlobally(space);
              }
              if (context.mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: Text('Removed $label')),
                );
              }
            },
            child: const Text('Delete'),
          ),
        ],
      ),
    );
  }

  void _confirmDeleteTag(
    BuildContext context,
    TaskProvider taskProvider,
    String tag,
    int count,
  ) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Row(
          children: [
            Icon(Icons.warning_amber_rounded, color: Colors.redAccent),
            SizedBox(width: 8),
            Text('Confirm Tag Removal'),
          ],
        ),
        content: Text('Are you sure you want to remove tag \'#$tag\' from $count task(s)?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancel'),
          ),
          FilledButton(
            style: FilledButton.styleFrom(backgroundColor: Colors.redAccent),
            onPressed: () async {
              Navigator.pop(ctx);
              await taskProvider.removeTagGlobally(tag);
              if (context.mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: Text('Removed tag \'#$tag\'')),
                );
              }
            },
            child: const Text('Delete'),
          ),
        ],
      ),
    );
  }
}
