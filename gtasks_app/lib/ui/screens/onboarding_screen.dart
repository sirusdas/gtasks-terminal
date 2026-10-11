import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../providers/settings_provider.dart';
import '../../providers/task_provider.dart';

class OnboardingScreen extends StatefulWidget {
  const OnboardingScreen({super.key});

  @override
  State<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends State<OnboardingScreen> {
  final PageController _pageController = PageController();
  int _currentPage = 0;

  // Mode Selection: 'standalone' vs 'pc_server'
  String _selectedMode = 'standalone';

  // Standalone Google Auth State
  final TextEditingController _accessTokenController = TextEditingController();
  bool _isAuthenticating = false;
  String? _authError;

  // PC Server Mode State
  late TextEditingController _serverUrlController;
  bool _isTestingConnection = false;
  bool? _connectionSuccess;
  String? _connectionError;

  @override
  void initState() {
    super.initState();
    final settings = context.read<SettingsProvider>();
    _serverUrlController = TextEditingController(text: settings.baseUrl);
  }

  @override
  void dispose() {
    _pageController.dispose();
    _accessTokenController.dispose();
    _serverUrlController.dispose();
    super.dispose();
  }

  Future<void> _testServerConnection() async {
    setState(() {
      _isTestingConnection = true;
      _connectionSuccess = null;
      _connectionError = null;
    });

    final url = _serverUrlController.text.trim();
    try {
      final taskProvider = context.read<TaskProvider>();
      taskProvider.apiClient.baseUrl = url;
      final accounts = await taskProvider.apiClient.fetchAccounts();
      setState(() {
        _connectionSuccess = true;
      });
    } catch (e) {
      setState(() {
        _connectionSuccess = false;
        _connectionError = e.toString();
      });
    } finally {
      setState(() {
        _isTestingConnection = false;
      });
    }
  }

  Future<void> _completeOnboarding() async {
    final settings = context.read<SettingsProvider>();
    final taskProvider = context.read<TaskProvider>();

    if (_selectedMode == 'standalone') {
      await settings.setAppMode('standalone');
      final token = _accessTokenController.text.trim();
      if (token.isNotEmpty) {
        await settings.setGoogleTokens(accessToken: token);
      }
    } else {
      await settings.setAppMode('pc_server');
      await settings.setBaseUrl(_serverUrlController.text.trim());
    }

    await settings.setOnboardingCompleted(true);
    taskProvider.updateConfig(
      newUrl: settings.baseUrl,
      isStandalone: settings.isStandalone,
      googleAccessToken: settings.googleAccessToken,
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            // Top App Logo & Skip/Indicator Bar
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(6),
                    decoration: BoxDecoration(
                      color: theme.colorScheme.primary.withValues(alpha: 0.15),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Icon(Icons.check_box_outlined, color: theme.colorScheme.primary, size: 22),
                  ),
                  const SizedBox(width: 8),
                  Text('GTasks', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
                  const Spacer(),
                  if (_currentPage < 2)
                    TextButton(
                      onPressed: () {
                        _pageController.animateToPage(2, duration: const Duration(milliseconds: 300), curve: Curves.easeInOut);
                      },
                      child: const Text('Skip'),
                    ),
                ],
              ),
            ),

            // Carousel Pages
            Expanded(
              child: PageView(
                controller: _pageController,
                onPageChanged: (page) => setState(() => _currentPage = page),
                children: [
                  _buildWelcomePage(theme),
                  _buildFeaturesPage(theme),
                  _buildModeSelectionPage(theme),
                ],
              ),
            ),

            // Navigation Controls & Dots
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  // Page Dots
                  Row(
                    children: List.generate(3, (index) {
                      return AnimatedContainer(
                        duration: const Duration(milliseconds: 200),
                        margin: const EdgeInsets.only(right: 6),
                        height: 8,
                        width: _currentPage == index ? 24 : 8,
                        decoration: BoxDecoration(
                          color: _currentPage == index ? theme.colorScheme.primary : theme.colorScheme.outlineVariant,
                          borderRadius: BorderRadius.circular(4),
                        ),
                      );
                    }),
                  ),

                  // Next / Get Started Action
                  ElevatedButton(
                    style: ElevatedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                    ),
                    onPressed: () {
                      if (_currentPage < 2) {
                        _pageController.nextPage(duration: const Duration(milliseconds: 300), curve: Curves.easeInOut);
                      } else {
                        _completeOnboarding();
                      }
                    },
                    child: Text(_currentPage == 2 ? 'Get Started' : 'Next'),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // Slide 1: Welcome
  // ---------------------------------------------------------------------------
  Widget _buildWelcomePage(ThemeData theme) {
    return Padding(
      padding: const EdgeInsets.all(28),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Container(
            padding: const EdgeInsets.all(24),
            decoration: BoxDecoration(
              color: Colors.blueAccent.withValues(alpha: 0.12),
              shape: BoxShape.circle,
            ),
            child: const Icon(Icons.task_alt, size: 72, color: Colors.blueAccent),
          ),
          const SizedBox(height: 32),
          Text(
            'Master Your Tasks',
            style: theme.textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.bold),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 14),
          Text(
            'GTasks gives you the speed of a terminal task manager with an elegant, offline-first mobile dashboard.',
            style: theme.textTheme.bodyMedium?.copyWith(color: theme.hintColor, height: 1.5),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // Slide 2: Features
  // ---------------------------------------------------------------------------
  Widget _buildFeaturesPage(ThemeData theme) {
    return Padding(
      padding: const EdgeInsets.all(28),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          _buildFeatureRow(
            icon: Icons.sync,
            color: Colors.greenAccent.shade700,
            title: 'Zero-Conflict Cloud Sync',
            desc: 'Sync directly with Google Tasks using immutable IDs and Last-Write-Wins.',
            theme: theme,
          ),
          const SizedBox(height: 24),
          _buildFeatureRow(
            icon: Icons.tag,
            color: Colors.teal,
            title: 'Multi-Tag Workflow',
            desc: 'Clean #tags and [tags] extracted from notes automatically with fast filters.',
            theme: theme,
          ),
          const SizedBox(height: 24),
          _buildFeatureRow(
            icon: Icons.offline_pin_outlined,
            color: Colors.orangeAccent,
            title: '100% Offline Capable',
            desc: 'Embedded on-device SQLite database. Add and complete tasks anywhere without network.',
            theme: theme,
          ),
        ],
      ),
    );
  }

  Widget _buildFeatureRow({
    required IconData icon,
    required Color color,
    required String title,
    required String desc,
    required ThemeData theme,
  }) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          padding: const EdgeInsets.all(10),
          decoration: BoxDecoration(
            color: color.withValues(alpha: 0.15),
            borderRadius: BorderRadius.circular(10),
          ),
          child: Icon(icon, color: color, size: 24),
        ),
        const SizedBox(width: 16),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
              const SizedBox(height: 4),
              Text(desc, style: TextStyle(color: theme.hintColor, fontSize: 13, height: 1.4)),
            ],
          ),
        ),
      ],
    );
  }

  // ---------------------------------------------------------------------------
  // Slide 3: Mode Selection
  // ---------------------------------------------------------------------------
  Widget _buildModeSelectionPage(ThemeData theme) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'How would you like to run?',
            style: theme.textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 6),
          Text(
            'Choose between running completely standalone or connecting to your desktop server.',
            style: TextStyle(color: theme.hintColor, fontSize: 13),
          ),
          const SizedBox(height: 20),

          // Option A: Standalone
          _buildModeCard(
            mode: 'standalone',
            title: 'Standalone (Recommended)',
            subtitle: 'Runs entirely on this phone. Stores tasks in on-device SQLite and syncs with Google Tasks.',
            icon: Icons.phone_android,
            badgeText: 'Serverless',
            theme: theme,
          ),

          const SizedBox(height: 14),

          // Option B: PC Server
          _buildModeCard(
            mode: 'pc_server',
            title: 'Connect to PC Server',
            subtitle: 'Connects to your local gtasks terminal server (http://gtasks.com:48275).',
            icon: Icons.computer,
            badgeText: 'Desktop Sync',
            theme: theme,
          ),

          const SizedBox(height: 20),

          // Configuration Details based on selection
          if (_selectedMode == 'standalone') ...[
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: theme.colorScheme.surfaceContainerHighest.withValues(alpha: 0.35),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: theme.colorScheme.outlineVariant),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Row(
                    children: [
                      Icon(Icons.check_circle_outline, color: Colors.green, size: 20),
                      SizedBox(width: 8),
                      Text('Ready to Start Offline', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                    ],
                  ),
                  const SizedBox(height: 6),
                  Text(
                    'Your local SQLite database is ready. You can start creating tasks right now, or link Google Tasks in Settings anytime.',
                    style: TextStyle(fontSize: 12, color: theme.hintColor, height: 1.4),
                  ),
                ],
              ),
            ),
          ] else ...[
            // PC Server URL input & test button
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: theme.colorScheme.surfaceContainerHighest.withValues(alpha: 0.35),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: theme.colorScheme.outlineVariant),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Server Address', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                  const SizedBox(height: 8),
                  TextField(
                    controller: _serverUrlController,
                    decoration: const InputDecoration(
                      hintText: 'http://gtasks.com:48275',
                      border: OutlineInputBorder(),
                      isDense: true,
                    ),
                  ),
                  const SizedBox(height: 10),
                  Row(
                    children: [
                      OutlinedButton.icon(
                        icon: _isTestingConnection
                            ? const SizedBox(width: 14, height: 14, child: CircularProgressIndicator(strokeWidth: 2))
                            : const Icon(Icons.network_check, size: 16),
                        label: const Text('Test Connection', style: TextStyle(fontSize: 12)),
                        onPressed: _isTestingConnection ? null : _testServerConnection,
                      ),
                      const SizedBox(width: 10),
                      if (_connectionSuccess == true)
                        const Row(
                          children: [
                            Icon(Icons.check_circle, color: Colors.green, size: 18),
                            SizedBox(width: 4),
                            Text('Connected!', style: TextStyle(color: Colors.green, fontWeight: FontWeight.bold, fontSize: 12)),
                          ],
                        )
                      else if (_connectionSuccess == false)
                        const Row(
                          children: [
                            Icon(Icons.cancel, color: Colors.red, size: 18),
                            SizedBox(width: 4),
                            Text('Unreachable', style: TextStyle(color: Colors.red, fontSize: 12)),
                          ],
                        ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildModeCard({
    required String mode,
    required String title,
    required String subtitle,
    required IconData icon,
    required String badgeText,
    required ThemeData theme,
  }) {
    final isSelected = _selectedMode == mode;
    return InkWell(
      onTap: () => setState(() => _selectedMode = mode),
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: isSelected ? theme.colorScheme.primary : theme.colorScheme.outlineVariant,
            width: isSelected ? 2 : 1,
          ),
          color: isSelected ? theme.colorScheme.primary.withValues(alpha: 0.05) : null,
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(
              isSelected ? Icons.radio_button_checked : Icons.radio_button_off,
              color: isSelected ? theme.colorScheme.primary : theme.disabledColor,
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Text(title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                      const Spacer(),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(
                          color: theme.colorScheme.primary.withValues(alpha: 0.12),
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: Text(
                          badgeText,
                          style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: theme.colorScheme.primary),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 6),
                  Text(subtitle, style: TextStyle(fontSize: 12, color: theme.hintColor, height: 1.3)),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
