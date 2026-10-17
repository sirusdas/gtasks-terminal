import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../providers/task_provider.dart';
import 'settings_modal.dart';

class SyncProgressDialog extends StatefulWidget {
  final bool isFullSync;
  final String? account;

  const SyncProgressDialog({
    super.key,
    required this.isFullSync,
    this.account,
  });

  static bool _isShowing = false;

  static Future<void> show(BuildContext context, {bool isFullSync = true, String? account}) async {
    final provider = context.read<TaskProvider>();
    if (_isShowing || provider.isSyncing) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Sync is already in progress. Please wait...'),
          duration: Duration(seconds: 2),
        ),
      );
      return;
    }
    _isShowing = true;
    try {
      await showDialog<void>(
        context: context,
        barrierDismissible: false,
        builder: (_) => SyncProgressDialog(isFullSync: isFullSync, account: account),
      );
    } finally {
      _isShowing = false;
    }
  }

  @override
  State<SyncProgressDialog> createState() => _SyncProgressDialogState();
}

class _SyncProgressDialogState extends State<SyncProgressDialog> {
  bool _isRunning = true;
  bool _success = false;
  String? _errorDetail;
  int _taskCount = 0;
  int _listCount = 0;

  @override
  void initState() {
    super.initState();
    _startSync();
  }

  void _startSync() async {
    final provider = context.read<TaskProvider>();
    try {
      final ok = await provider.syncGoogleTasks(
        account: widget.account ?? provider.selectedAccount,
        syncAll: widget.isFullSync,
      );

      if (mounted) {
        setState(() {
          _isRunning = false;
          _success = ok;
          _errorDetail = ok ? null : (provider.errorMessage ?? 'Sync returned false. Check authentication or network.');
          _taskCount = provider.allTasksUnfiltered.length;
          _listCount = provider.listsWithCounts.length;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isRunning = false;
          _success = false;
          _errorDetail = e.toString();
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return AlertDialog(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      contentPadding: const EdgeInsets.fromLTRB(24, 24, 24, 16),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (_isRunning) ...[
            const SizedBox(
              width: 48,
              height: 48,
              child: CircularProgressIndicator(strokeWidth: 3),
            ),
            const SizedBox(height: 20),
            Text(
              widget.isFullSync
                  ? 'Running Full Sync (--all)...'
                  : 'Running Quick Sync...',
              style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            Text(
              widget.isFullSync
                  ? 'Reconciling 100% of tasks across all tasklists with Google Tasks (parity with gtasks advanced-sync --all).'
                  : 'Syncing recent task changes with Google Tasks.',
              style: theme.textTheme.bodySmall?.copyWith(color: theme.hintColor),
              textAlign: TextAlign.center,
            ),
          ] else if (_success) ...[
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.green.withValues(alpha: 0.12),
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.check_circle, color: Colors.green, size: 44),
            ),
            const SizedBox(height: 16),
            Text(
              widget.isFullSync ? 'Full Sync Complete!' : 'Sync Successful!',
              style: theme.textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold,
                color: Colors.green.shade700,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'Successfully synchronized $_taskCount tasks across $_listCount lists with Google Tasks.',
              style: theme.textTheme.bodyMedium,
              textAlign: TextAlign.center,
            ),
          ] else ...[
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.red.withValues(alpha: 0.12),
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.error_outline, color: Colors.red, size: 44),
            ),
            const SizedBox(height: 16),
            Text(
              'Sync Failed',
              style: theme.textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold,
                color: Colors.red.shade700,
              ),
            ),
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: theme.colorScheme.surfaceContainerHighest.withValues(alpha: 0.5),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(
                _errorDetail ?? 'Unknown synchronization error occurred.',
                style: const TextStyle(fontSize: 12, fontFamily: 'monospace'),
                textAlign: TextAlign.center,
              ),
            ),
          ],
        ],
      ),
      actions: [
        if (!_isRunning) ...[
          if (!_success) ...[
            TextButton.icon(
              icon: const Icon(Icons.settings, size: 16),
              label: const Text('Settings'),
              onPressed: () {
                Navigator.pop(context);
                showDialog(
                  context: context,
                  builder: (_) => const SettingsModal(),
                );
              },
            ),
            ElevatedButton(
              onPressed: () {
                setState(() {
                  _isRunning = true;
                  _errorDetail = null;
                });
                _startSync();
              },
              child: const Text('Retry'),
            ),
          ] else ...[
            ElevatedButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Done'),
            ),
          ],
        ],
      ],
    );
  }
}
