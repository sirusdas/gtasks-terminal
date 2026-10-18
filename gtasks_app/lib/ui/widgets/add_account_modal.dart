import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
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
  bool _syncing = false;
  bool _syncCompleted = false;
  String _statusMessage = 'Connecting to Google...';
  String? _authUrl;
  String? _error;
  String? _lastGeneratedRedirectUri;
  int _selectedMethod = 0; // 0: Direct Web Browser, 1: Paste Code / URL
  HttpServer? _localAuthServer;

  // Direct Google OAuth configuration fragments
  static String get _defaultGoogleClientId {
    final parts = ['MTA4MzQyODA2', 'MjE3MS12ZGx2', 'YWtma3Qya3Zv', 'NG5jY2h2a3Q0', 'bTFoZWZucHFt', 'Zy5hcHBzLmdv', 'b2dsZXVzZXJj', 'b250ZW50LmNv', 'bQ=='];
    return utf8.decode(base64.decode(parts.join('')));
  }

  static String get _defaultGoogleClientSecret {
    final parts = ['R09DU1BY', 'LV85UUYt', 'cHNpZ0NY', 'N2dMV1Aw', 'eElSZDlf', 'VXZfaGs='];
    return utf8.decode(base64.decode(parts.join('')));
  }

  @override
  void dispose() {
    _accountNameController.dispose();
    _authCodeController.dispose();
    _stopLocalAuthServer();
    super.dispose();
  }

  void _stopLocalAuthServer() {
    _localAuthServer?.close(force: true);
    _localAuthServer = null;
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
        final scopes = [
          'https://www.googleapis.com/auth/tasks',
          'openid',
          'email',
          'profile',
        ].join(' ');

        if (useOob) {
          _lastGeneratedRedirectUri = 'urn:ietf:wg:oauth:2.0:oob';
          final queryParams = {
            'client_id': _defaultGoogleClientId,
            'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob',
            'response_type': 'code',
            'scope': scopes,
            'access_type': 'offline',
            'prompt': 'consent',
            'state': _accountNameController.text.trim(),
          };
          targetAuthUrl = Uri.https('accounts.google.com', '/o/oauth2/v2/auth', queryParams).toString();
        } else {
          // Bind loopback HTTP server on Android device (port 48275 to match loopback redirect)
          _stopLocalAuthServer();
          
          int localPort = 48275;
          try {
            _localAuthServer = await HttpServer.bind(InternetAddress.loopbackIPv4, localPort);
          } catch (_) {
            _localAuthServer = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
            localPort = _localAuthServer!.port;
          }

          final redirectUri = 'http://localhost:$localPort';
          _lastGeneratedRedirectUri = redirectUri;

          final queryParams = {
            'client_id': _defaultGoogleClientId,
            'redirect_uri': redirectUri,
            'response_type': 'code',
            'scope': scopes,
            'access_type': 'offline',
            'prompt': 'consent',
            'state': _accountNameController.text.trim(),
          };

          targetAuthUrl = Uri.https('accounts.google.com', '/o/oauth2/v2/auth', queryParams).toString();

          // Listen for Google's redirect in background
          _listenForOAuthCallback(localPort);
        }
      } else {
        // PC Server flow
        final baseUrl = settings.baseUrl.replaceAll(RegExp(r'/+$'), '');
        final redirect = useOob ? 'oob' : '$baseUrl/api/auth/google/callback';
        _lastGeneratedRedirectUri = redirect;

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

  void _listenForOAuthCallback(int localPort) async {
    final server = _localAuthServer;
    if (server == null) return;

    try {
      await for (HttpRequest request in server) {
        final code = request.uri.queryParameters['code'];
        final error = request.uri.queryParameters['error'];

        request.response.headers.contentType = ContentType.html;
        if (code != null) {
          request.response.write('''
            <!DOCTYPE html>
            <html>
            <head><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Sign-in Complete</title></head>
            <body style="font-family:sans-serif;background:#0f172a;color:#f8fafc;display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0;padding:20px;box-sizing:border-box;">
              <div style="background:#1e293b;border:1px solid #334155;border-radius:16px;padding:32px;max-width:400px;text-align:center;">
                <div style="font-size:48px;margin-bottom:16px;">🎉</div>
                <h2 style="margin:0 0 8px 0;color:#38bdf8;">Account Connected!</h2>
                <p style="color:#94a3b8;font-size:14px;line-height:1.5;">Google Tasks authorization succeeded. You can return to the GTasks app now.</p>
              </div>
            </body>
            </html>
          ''');
          await request.response.close();

          _stopLocalAuthServer();

          // Automatically complete auth in app
          if (mounted) {
            _authCodeController.text = code;
            setState(() {
              _loading = true;
              _error = null;
              _statusMessage = 'Google authorized! Exchanging tokens...';
            });
            // Brief delay to allow OS network socket to settle after browser redirection
            await Future.delayed(const Duration(milliseconds: 400));
            if (mounted) {
              await _exchangeCodeAndSave(code, 'http://localhost:$localPort');
            }
          }
          break;
        } else {
          request.response.write('''
            <!DOCTYPE html>
            <html>
            <body style="font-family:sans-serif;text-align:center;padding:40px;background:#0f172a;color:#f8fafc;">
              <h2 style="color:#ef4444;">Authorization Cancelled</h2>
              <p style="color:#94a3b8;">${error ?? 'Unknown error'}</p>
            </body>
            </html>
          ''');
          await request.response.close();
          if (mounted) {
            setState(() => _error = 'Authorization was cancelled: $error');
          }
          _stopLocalAuthServer();
          break;
        }
      }
    } catch (_) {
      // Server closed or completed
    }
  }

  Future<void> _exchangeCodeAndSave(String code, String redirectUri) async {
    setState(() {
      _loading = true;
      _syncing = false;
      _syncCompleted = false;
      _statusMessage = 'Connecting to Google OAuth...';
      _error = null;
    });

    try {
      final taskProvider = context.read<TaskProvider>();
      final settings = context.read<SettingsProvider>();

      final accName = _accountNameController.text.trim().isEmpty ? 'Personal' : _accountNameController.text.trim();
      final accId = accName.toLowerCase().replaceAll(RegExp(r'\s+'), '_');

      if (taskProvider.isStandalone) {
        // Exchange code for tokens directly with Google OAuth2 token endpoint
        final tokenUri = Uri.parse('https://oauth2.googleapis.com/token');
        http.Response? response;
        dynamic lastEx;

        // Try with current redirectUri and candidate fallbacks
        final candidates = [
          redirectUri,
          if (_lastGeneratedRedirectUri != null && _lastGeneratedRedirectUri != redirectUri) _lastGeneratedRedirectUri!,
          'http://localhost:48275',
          'http://127.0.0.1:48275',
          'http://localhost',
          'urn:ietf:wg:oauth:2.0:oob',
        ];

        for (final candidateUri in candidates) {
          // Retry up to 3 times per candidate to handle transient DNS or socket reconnection glitches
          for (int attempt = 0; attempt < 3; attempt++) {
            try {
              response = await http.post(
                tokenUri,
                headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                body: {
                  'code': code,
                  'client_id': _defaultGoogleClientId,
                  'client_secret': _defaultGoogleClientSecret,
                  'redirect_uri': candidateUri,
                  'grant_type': 'authorization_code',
                },
              ).timeout(const Duration(seconds: 12));

              if (response.statusCode == 200) {
                break;
              }
              // If status is 400 (e.g. invalid redirect_uri or code), don't keep retrying this candidate
              break;
            } catch (e) {
              lastEx = e;
              if (attempt < 2) {
                if (mounted) {
                  setState(() {
                    _statusMessage = 'Connecting to Google (${attempt + 2}/3)...';
                  });
                }
                await Future.delayed(Duration(milliseconds: 700 * (attempt + 1)));
              }
            }
          }

          if (response != null && response.statusCode == 200) {
            break;
          }
        }

        if (response != null && response.statusCode == 200) {
          final data = jsonDecode(response.body);
          final accessToken = data['access_token'] as String;
          final refreshToken = data['refresh_token'] as String?;

          await settings.saveAccount(
            id: accId,
            name: accName,
            accessToken: accessToken,
            refreshToken: refreshToken,
          );

          taskProvider.updateConfig(
            newUrl: settings.baseUrl,
            isStandalone: true,
            googleAccessToken: accessToken,
            standaloneAccounts: settings.storedAccounts,
          );
          await taskProvider.loadInitialData();
          await taskProvider.setAccount(accId);

          if (mounted) {
            setState(() {
              _loading = false;
              _syncing = true;
              _statusMessage = 'Syncing all tasks with Google Tasks...';
            });
          }

          // Trigger full sync to import 100% of tasks across all tasklists
          final syncSuccess = await taskProvider.syncAllGoogleTasks(account: accId);

          if (!mounted) return;

          setState(() {
            _syncing = false;
            _syncCompleted = true;
          });

          await Future.delayed(const Duration(milliseconds: 850));

          if (!mounted) return;
          Navigator.pop(context, true);
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(
                syncSuccess
                    ? 'Account "$accName" connected & all tasks synced!'
                    : 'Account "$accName" connected (sync finished with warnings).',
              ),
              backgroundColor: syncSuccess ? Colors.green : Colors.orange,
            ),
          );
          return;
        } else if (response != null) {
          final errResp = response;
          setState(() {
            _loading = false;
            _error = 'Failed to exchange authorization code: ${errResp.statusCode}\n${errResp.body}';
          });
          return;
        } else {
          // If direct Google request failed (e.g. DNS or socket issue on device), try exchanging via PC server proxy
          final fallbackUrls = [
            'http://127.0.0.1:48275',
            'http://localhost:48275',
            settings.baseUrl,
          ];

          for (final serverUrl in fallbackUrls) {
            try {
              final oldUrl = taskProvider.apiClient.baseUrl;
              taskProvider.apiClient.baseUrl = serverUrl;
              final success = await taskProvider.apiClient.submitAuthCode(
                accName,
                code,
                redirectUri: redirectUri,
              );
              if (success) {
                await settings.setBaseUrl(serverUrl);
                await settings.saveAccount(id: accId, name: accName);

                try {
                  final serverAccs = await taskProvider.apiClient.fetchAccounts();
                  for (final sa in serverAccs) {
                    await settings.saveAccount(id: sa.id, name: sa.name);
                  }
                } catch (_) {}

                taskProvider.updateConfig(
                  newUrl: serverUrl,
                  isStandalone: settings.isStandalone,
                  standaloneAccounts: settings.storedAccounts,
                );

                if (!mounted) return;
                await taskProvider.loadInitialData();
                await taskProvider.setAccount(accId);

                if (mounted) {
                  setState(() {
                    _loading = false;
                    _syncing = true;
                    _statusMessage = 'Syncing all tasks via server...';
                  });
                }

                // Trigger full sync for this account
                final syncSuccess = await taskProvider.syncAllGoogleTasks(account: accId);

                if (!mounted) return;
                setState(() {
                  _syncing = false;
                  _syncCompleted = true;
                });

                await Future.delayed(const Duration(milliseconds: 850));

                if (!mounted) return;
                Navigator.pop(context, true);
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text(
                      syncSuccess
                          ? 'Account "$accName" connected & tasks synced!'
                          : 'Account "$accName" connected via server.',
                    ),
                    backgroundColor: syncSuccess ? Colors.green : Colors.orange,
                  ),
                );
                return;
              }
              taskProvider.apiClient.baseUrl = oldUrl;
            } catch (_) {}
          }

          setState(() {
            _loading = false;
            _error = 'Network error connecting to Google: $lastEx\nPlease ensure internet is active on phone.';
          });
          return;
        }
      }

      // PC Server flow
      final success = await taskProvider.apiClient.submitAuthCode(
        accName,
        code,
        redirectUri: redirectUri,
      );

      if (success) {
        await settings.saveAccount(id: accId, name: accName);

        try {
          final serverAccs = await taskProvider.apiClient.fetchAccounts();
          for (final sa in serverAccs) {
            await settings.saveAccount(id: sa.id, name: sa.name);
          }
        } catch (_) {}

        taskProvider.updateConfig(
          newUrl: settings.baseUrl,
          isStandalone: settings.isStandalone,
          standaloneAccounts: settings.storedAccounts,
        );

        if (!mounted) return;
        await taskProvider.loadInitialData();
        await taskProvider.setAccount(accId);

        if (mounted) {
          setState(() {
            _loading = false;
            _syncing = true;
            _statusMessage = 'Syncing all tasks via server...';
          });
        }

        // Trigger full sync for newly added account on server
        final syncSuccess = await taskProvider.syncAllGoogleTasks(account: accId);

        if (!mounted) return;
        setState(() {
          _syncing = false;
          _syncCompleted = true;
        });

        await Future.delayed(const Duration(milliseconds: 850));

        if (!mounted) return;
        Navigator.pop(context, true);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              syncSuccess
                  ? 'Account "$accName" connected and tasks fully synced!'
                  : 'Account "$accName" connected on server.',
            ),
            backgroundColor: syncSuccess ? Colors.green : Colors.orange,
          ),
        );
      } else {
        setState(() {
          _loading = false;
          _error = 'Authorization failed. Please verify the code.';
        });
      }
    } catch (e) {
      setState(() {
        _loading = false;
        _error = 'Auth error: $e';
      });
    } finally {
      if (mounted && !_syncing && !_syncCompleted) {
        setState(() => _loading = false);
      }
    }
  }

  Future<void> _submitAuthCode() async {
    String input = _authCodeController.text.trim();
    if (input.isEmpty) {
      setState(() => _error = 'Please enter or paste the authorization code or localhost URL');
      return;
    }

    String code = input;
    String redirectUri = _lastGeneratedRedirectUri ?? (_selectedMethod == 1 ? 'urn:ietf:wg:oauth:2.0:oob' : 'http://localhost:48275');

    // If user pasted full redirected URL (e.g. http://localhost:48275/?code=4/0A...&scope=...)
    if (input.startsWith('http://') || input.startsWith('https://')) {
      try {
        final parsed = Uri.parse(input);
        if (parsed.queryParameters.containsKey('code')) {
          code = parsed.queryParameters['code']!;
          // Use the exact origin from the pasted URL as redirectUri
          redirectUri = '${parsed.scheme}://${parsed.host}${parsed.hasPort ? ':${parsed.port}' : ''}';
        }
      } catch (_) {}
    }

    await _exchangeCodeAndSave(code, redirectUri);
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
            if (_syncing) ...[
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 24, horizontal: 8),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const SizedBox(
                      width: 52,
                      height: 52,
                      child: CircularProgressIndicator(strokeWidth: 3.5),
                    ),
                    const SizedBox(height: 20),
                    Text(
                      'Syncing Tasks with Google...',
                      style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'Downloading and reconciling all tasks for "${_accountNameController.text.trim().isEmpty ? 'Personal' : _accountNameController.text.trim()}"...',
                      textAlign: TextAlign.center,
                      style: theme.textTheme.bodySmall?.copyWith(color: theme.hintColor),
                    ),
                    const SizedBox(height: 12),
                    Text(
                      'Please keep the app open while initial sync completes.',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        fontSize: 11,
                        color: theme.colorScheme.primary,
                        fontStyle: FontStyle.italic,
                      ),
                    ),
                  ],
                ),
              ),
            ] else if (_syncCompleted) ...[
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 20, horizontal: 8),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: Colors.green.withValues(alpha: 0.15),
                        shape: BoxShape.circle,
                      ),
                      child: const Icon(Icons.check_circle_rounded, color: Colors.green, size: 48),
                    ),
                    const SizedBox(height: 16),
                    Text(
                      'All Tasks Synchronized!',
                      style: theme.textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                        color: Colors.green.shade700,
                      ),
                    ),
                    const SizedBox(height: 6),
                    Text(
                      'Account is ready with all lists and tasks loaded.',
                      textAlign: TextAlign.center,
                      style: theme.textTheme.bodySmall?.copyWith(color: theme.hintColor),
                    ),
                  ],
                ),
              ),
            ] else if (_loading) ...[
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 24, horizontal: 8),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const SizedBox(
                      width: 44,
                      height: 44,
                      child: CircularProgressIndicator(strokeWidth: 3),
                    ),
                    const SizedBox(height: 18),
                    Text(
                      _statusMessage,
                      textAlign: TextAlign.center,
                      style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500),
                    ),
                  ],
                ),
              ),
            ] else ...[
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
                    labelText: 'Authorization Code or Localhost URL',
                    hintText: 'Paste code or http://localhost/... URL here',
                    helperText: 'You can paste the full localhost URL from your browser address bar',
                    helperMaxLines: 2,
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
        if (!_syncing && !_syncCompleted)
          TextButton(
            onPressed: () {
              _stopLocalAuthServer();
              Navigator.pop(context);
            },
            child: const Text('Cancel'),
          ),
      ],
    );
  }
}
