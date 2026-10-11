import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:provider/provider.dart';
import '../../providers/task_provider.dart';
import '../../providers/settings_provider.dart';

class AddGoogleAccountModal extends StatefulWidget {
  const AddGoogleAccountModal({super.key});

  @override
  State<AddGoogleAccountModal> createState() => _AddGoogleAccountModalState();
}

class _AddGoogleAccountModalState extends State<AddGoogleAccountModal> {
  final TextEditingController _accountNameController =
      TextEditingController(text: 'Work');
  final TextEditingController _authCodeController = TextEditingController();

  bool _loading = false;
  String? _authUrl;
  String? _error;
  int _selectedMethod = 0; // 0: Direct Web Browser, 1: Copy-Paste Auth Code

  // Fallback direct Google OAuth Client ID when in standalone mode without PC server
  static const String _defaultGoogleClientId =
      '1083428062171-vdlvakfkt2kvo4ncchvkt4m1hefnpqmg.apps.googleusercontent.com';

  @override
  void dispose() {
    _accountNameController.dispose();
    _authCodeController.dispose();
    super.dispose();
  }

  Future<void> _launchGoogleOAuth(bool useOob) async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final taskProvider = context.read<TaskProvider>();
      final settings = context.read<SettingsProvider>();

      String targetAuthUrl;

      if (taskProvider.isStandalone) {
        // Direct Google OAuth URL for standalone client
        final scopes = [
          'https://www.googleapis.com/auth/tasks',
          'openid',
          'email',
          'profile',
        ].join(' ');

        final redirect = useOob ? 'urn:ietf:wg:oauth:2.0:oob' : 'http://localhost';
        final queryParams = {
          'client_id': _defaultGoogleClientId,
          'redirect_uri': redirect,
          'response_type': 'code',
          'scope': scopes,
          'access_type': 'offline',
          'prompt': 'consent',
          'state': _accountNameController.text.trim(),
        };

        final uri = Uri.https('accounts.google.com', '/o/oauth2/v2/auth', queryParams);
        targetAuthUrl = uri.toString();
      } else {
        // PC Server flow
        final baseUrl = settings.baseUrl.replaceAll(RegExp(r'/+$'), '');
        final redirect = useOob ? 'oob' : '$baseUrl/api/auth/google/callback';

        final res = await taskProvider.apiClient.startGoogleAuth(
          _accountNameController.text.trim(),
          redirectUri: redirect,
        );
        targetAuthUrl = res['auth_url'] as String;
      }

      setState(() {
        _authUrl = targetAuthUrl;
      });

      final parsedUri = Uri.parse(targetAuthUrl);
      final launched = await launchUrl(
        parsedUri,
        mode: LaunchMode.externalApplication,
      );

      if (!launched) {
        setState(() {
          _error = 'Could not open browser automatically. Please tap the button below to copy the link.';
        });
      }
    } catch (e) {
      setState(() => _error = 'Error launching Google Sign-in: $e');
    } finally {
      setState(() => _loading = false);
    }
  }

  Future<void> _submitAuthCode() async {
    final code = _authCodeController.text.trim();
    if (code.isEmpty) {
      setState(() => _error = 'Please enter or paste the authorization code');
      return;
    }

    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final taskProvider = context.read<TaskProvider>();
      final settings = context.read<SettingsProvider>();

      if (taskProvider.isStandalone) {
        // Standalone mode: save code and complete
        await settings.setGoogleTokens(accessToken: code);
        taskProvider.updateConfig(
          newUrl: settings.baseUrl,
          isStandalone: true,
          googleAccessToken: code,
        );
        if (!mounted) return;
        Navigator.pop(context, true);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Account "${_accountNameController.text.trim()}" linked in standalone mode!')),
        );
        return;
      }

      // PC Server mode: submit code to Flask backend
      final baseUrl = settings.baseUrl.replaceAll(RegExp(r'/+$'), '');
      final success = await taskProvider.apiClient.submitAuthCode(
        _accountNameController.text.trim(),
        code,
        redirectUri: _selectedMethod == 1 ? 'oob' : '$baseUrl/api/auth/google/callback',
      );

      if (success) {
        if (!mounted) return;
        await taskProvider.loadInitialData();
        if (!mounted) return;
        Navigator.pop(context, true);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Account "${_accountNameController.text.trim()}" connected successfully!')),
        );
      } else {
        setState(() => _error = 'Authorization failed. Please verify the code.');
      }
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return AlertDialog(
      title: const Row(
        children: [
          Icon(Icons.account_circle, color: Colors.blueAccent),
          SizedBox(width: 8),
          Text('Add Google Account'),
        ],
      ),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text(
              'Connect a Google Account without touching terminals or token files.',
              style: TextStyle(fontSize: 13),
            ),
            const SizedBox(height: 14),
            TextField(
              controller: _accountNameController,
              decoration: const InputDecoration(
                labelText: 'Account Nickname',
                hintText: 'e.g. Work, School, Personal',
                border: OutlineInputBorder(),
                isDense: true,
              ),
            ),
            const SizedBox(height: 14),
            const Text('Connection Method:', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
            const SizedBox(height: 6),
            SegmentedButton<int>(
              segments: const [
                ButtonSegment(
                  value: 0,
                  icon: Icon(Icons.open_in_browser, size: 16),
                  label: Text('Direct Web'),
                ),
                ButtonSegment(
                  value: 1,
                  icon: Icon(Icons.vpn_key, size: 16),
                  label: Text('Paste Code'),
                ),
              ],
              selected: {_selectedMethod},
              onSelectionChanged: (set) => setState(() => _selectedMethod = set.first),
            ),
            const SizedBox(height: 14),
            if (_error != null)
              Container(
                padding: const EdgeInsets.all(8),
                margin: const EdgeInsets.only(bottom: 12),
                decoration: BoxDecoration(
                  color: Colors.red.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.red.withValues(alpha: 0.3)),
                ),
                child: SelectableText(_error!, style: const TextStyle(color: Colors.red, fontSize: 12)),
              ),
            if (_loading)
              const Center(
                child: Padding(
                  padding: EdgeInsets.all(12),
                  child: CircularProgressIndicator(),
                ),
              )
            else ...[
              ElevatedButton.icon(
                icon: const Icon(Icons.login),
                label: Text('Sign in with Google (${_selectedMethod == 0 ? "Browser" : "Auth Code"})'),
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 12),
                  backgroundColor: theme.colorScheme.primary,
                  foregroundColor: theme.colorScheme.onPrimary,
                ),
                onPressed: () => _launchGoogleOAuth(_selectedMethod == 1),
              ),
              if (_authUrl != null) ...[
                const SizedBox(height: 10),
                OutlinedButton.icon(
                  icon: const Icon(Icons.copy, size: 16),
                  label: const Text('Copy Google Sign-in URL', style: TextStyle(fontSize: 12)),
                  onPressed: () {
                    Clipboard.setData(ClipboardData(text: _authUrl!));
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Auth URL copied to clipboard! Open in any browser.')),
                    );
                  },
                ),
              ],
              if (_selectedMethod == 1 || _authUrl != null) ...[
                const SizedBox(height: 14),
                TextField(
                  controller: _authCodeController,
                  decoration: const InputDecoration(
                    labelText: 'Authorization Code',
                    hintText: 'Paste Google token/code here',
                    border: OutlineInputBorder(),
                    isDense: true,
                  ),
                ),
                const SizedBox(height: 10),
                OutlinedButton.icon(
                  icon: const Icon(Icons.check_circle_outline),
                  label: const Text('Complete Connection'),
                  onPressed: _submitAuthCode,
                ),
              ],
            ],
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('Cancel'),
        ),
      ],
    );
  }
}
