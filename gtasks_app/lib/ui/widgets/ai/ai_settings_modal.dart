import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../../providers/settings_provider.dart';
import '../../../services/ai/gemini_provider.dart';

class AiSettingsModal extends StatefulWidget {
  const AiSettingsModal({super.key});

  @override
  State<AiSettingsModal> createState() => _AiSettingsModalState();
}

class _AiSettingsModalState extends State<AiSettingsModal> {
  late TextEditingController _apiKeyController;
  late String _providerType;
  late String _modelName;
  bool _obscureKey = true;
  bool _isTesting = false;
  String? _testMessage;
  bool _testSuccess = false;

  @override
  void initState() {
    super.initState();
    final settings = context.read<SettingsProvider>();
    _apiKeyController = TextEditingController(text: settings.geminiApiKey ?? '');
    _providerType = settings.aiProviderType;
    _modelName = settings.aiModelName;
  }

  @override
  void dispose() {
    _apiKeyController.dispose();
    super.dispose();
  }

  Future<void> _openAiStudio() async {
    final uri = Uri.parse('https://aistudio.google.com/app/apikey');
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    }
  }

  Future<void> _pasteClipboard() async {
    final data = await Clipboard.getData(Clipboard.kTextPlain);
    if (data?.text != null && data!.text!.trim().isNotEmpty) {
      setState(() {
        _apiKeyController.text = data.text!.trim();
      });
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Pasted API key from clipboard!'), duration: Duration(seconds: 1)),
      );
    }
  }

  Future<void> _testConnection() async {
    final key = _apiKeyController.text.trim();
    if (_providerType == 'gemini' && key.isEmpty) {
      setState(() {
        _testMessage = 'Please enter a Gemini API Key first.';
        _testSuccess = false;
      });
      return;
    }

    setState(() {
      _isTesting = true;
      _testMessage = null;
    });

    try {
      if (_providerType == 'gemini') {
        final testProvider = GeminiProvider(apiKey: key, modelName: _modelName);
        final resp = await testProvider.chat(prompt: 'Hello! Respond with: Ready', history: []);
        setState(() {
          _testMessage = 'Success! Connected to Gemini (${resp.reply.trim()})';
          _testSuccess = true;
        });
      } else {
        // Proxy mode test
        setState(() {
          _testMessage = 'Dashboard proxy mode configured.';
          _testSuccess = true;
        });
      }
    } catch (e) {
      setState(() {
        _testMessage = 'Failed: ${e.toString().replaceAll('Exception: ', '')}';
        _testSuccess = false;
      });
    } finally {
      setState(() {
        _isTesting = false;
      });
    }
  }

  Future<void> _saveSettings() async {
    final settings = context.read<SettingsProvider>();
    await settings.setAiProviderType(_providerType);
    await settings.setAiModelName(_modelName);
    await settings.setGeminiApiKey(_apiKeyController.text.trim());

    if (mounted) {
      Navigator.of(context).pop();
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('AI settings updated successfully!'), duration: Duration(seconds: 2)),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    return Dialog(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      backgroundColor: isDark ? const Color(0xFF1E222B) : Colors.white,
      child: Container(
        constraints: const BoxConstraints(maxWidth: 480),
        padding: const EdgeInsets.all(22),
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: Colors.purple.withOpacity(0.15),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: const Icon(Icons.auto_awesome, color: Colors.purple, size: 24),
                  ),
                  const SizedBox(width: 14),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'AI Assistant Settings',
                          style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                        ),
                        Text(
                          'Configure Gemini or Dashboard proxy',
                          style: theme.textTheme.bodySmall?.copyWith(color: Colors.grey),
                        ),
                      ],
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.close),
                    onPressed: () => Navigator.of(context).pop(),
                  ),
                ],
              ),
              const SizedBox(height: 20),

              // Provider Selector
              Text('AI Engine Provider', style: theme.textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w600)),
              const SizedBox(height: 8),
              SegmentedButton<String>(
                segments: const [
                  ButtonSegment(
                    value: 'gemini',
                    label: Text('Google Gemini (Direct)'),
                    icon: Icon(Icons.flash_on, size: 16),
                  ),
                  ButtonSegment(
                    value: 'proxy',
                    label: Text('Dashboard Proxy'),
                    icon: Icon(Icons.dns, size: 16),
                  ),
                ],
                selected: {_providerType},
                onSelectionChanged: (val) {
                  setState(() {
                    _providerType = val.first;
                    _testMessage = null;
                  });
                },
              ),
              const SizedBox(height: 16),

              // Model Selector
              Text('Gemini Model', style: theme.textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w600)),
              const SizedBox(height: 6),
              DropdownButtonFormField<String>(
                value: _modelName,
                decoration: InputDecoration(
                  contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                ),
                items: const [
                  DropdownMenuItem(
                    value: 'gemini-1.5-flash',
                    child: Text('Gemini 1.5 Flash (Ultra-fast, Free)'),
                  ),
                  DropdownMenuItem(
                    value: 'gemini-1.5-pro',
                    child: Text('Gemini 1.5 Pro (Deep reasoning)'),
                  ),
                ],
                onChanged: (val) {
                  if (val != null) setState(() => _modelName = val);
                },
              ),
              const SizedBox(height: 16),

              if (_providerType == 'gemini') ...[
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text('Gemini API Key', style: theme.textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w600)),
                    TextButton.icon(
                      style: TextButton.styleFrom(visualDensity: VisualDensity.compact),
                      icon: const Icon(Icons.open_in_new, size: 14),
                      label: const Text('Get Free Key', style: TextStyle(fontSize: 12)),
                      onPressed: _openAiStudio,
                    ),
                  ],
                ),
                const SizedBox(height: 4),
                TextField(
                  controller: _apiKeyController,
                  obscureText: _obscureKey,
                  decoration: InputDecoration(
                    hintText: 'AIzaSy...',
                    prefixIcon: const Icon(Icons.key, size: 18),
                    suffixIcon: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        IconButton(
                          icon: Icon(_obscureKey ? Icons.visibility : Icons.visibility_off, size: 18),
                          onPressed: () => setState(() => _obscureKey = !_obscureKey),
                        ),
                        IconButton(
                          icon: const Icon(Icons.paste, size: 18),
                          tooltip: 'Paste from clipboard',
                          onPressed: _pasteClipboard,
                        ),
                      ],
                    ),
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  '100% Free: Google AI Studio gives 15 requests/min at no cost without credit card.',
                  style: theme.textTheme.bodySmall?.copyWith(color: Colors.grey, fontSize: 11),
                ),
              ] else ...[
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.blue.withOpacity(0.08),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: Colors.blue.withOpacity(0.2)),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.info_outline, color: Colors.blue, size: 20),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          'Routes AI prompts through your local GTasks Web Dashboard at ${context.watch<SettingsProvider>().baseUrl}.',
                          style: theme.textTheme.bodySmall?.copyWith(fontSize: 12),
                        ),
                      ),
                    ],
                  ),
                ),
              ],

              const SizedBox(height: 14),

              // Test Connection message
              if (_testMessage != null)
                Container(
                  padding: const EdgeInsets.all(10),
                  margin: const EdgeInsets.only(bottom: 12),
                  decoration: BoxDecoration(
                    color: _testSuccess ? Colors.green.withOpacity(0.12) : Colors.red.withOpacity(0.12),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: _testSuccess ? Colors.green : Colors.red),
                  ),
                  child: Row(
                    children: [
                      Icon(_testSuccess ? Icons.check_circle : Icons.error, color: _testSuccess ? Colors.green : Colors.red, size: 18),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          _testMessage!,
                          style: TextStyle(
                            color: _testSuccess ? Colors.green.shade800 : Colors.red.shade800,
                            fontSize: 12,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),

              // Action buttons
              Row(
                children: [
                  OutlinedButton.icon(
                    style: OutlinedButton.styleFrom(
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                    icon: _isTesting
                        ? const SizedBox(width: 14, height: 14, child: CircularProgressIndicator(strokeWidth: 2))
                        : const Icon(Icons.network_check, size: 16),
                    label: const Text('Test'),
                    onPressed: _isTesting ? null : _testConnection,
                  ),
                  const Spacer(),
                  TextButton(
                    onPressed: () => Navigator.of(context).pop(),
                    child: const Text('Cancel'),
                  ),
                  const SizedBox(width: 8),
                  FilledButton.icon(
                    style: FilledButton.styleFrom(
                      backgroundColor: Colors.purple,
                      foregroundColor: Colors.white,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                    icon: const Icon(Icons.save, size: 16),
                    label: const Text('Save'),
                    onPressed: _saveSettings,
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
