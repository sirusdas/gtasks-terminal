import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'api/api_client.dart';
import 'providers/task_provider.dart';
import 'providers/settings_provider.dart';
import 'services/notification_service.dart';
import 'ui/screens/tasks_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await NotificationService().init();
  runApp(const GTasksApp());
}

class GTasksApp extends StatelessWidget {
  const GTasksApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => SettingsProvider()),
        ChangeNotifierProxyProvider<SettingsProvider, TaskProvider>(
          create: (ctx) => TaskProvider(
            apiClient: ApiClient(baseUrl: 'http://gtasks.com'),
          ),
          update: (ctx, settings, taskProvider) {
            final provider = taskProvider ?? TaskProvider(
              apiClient: ApiClient(baseUrl: settings.baseUrl),
            );
            if (provider.apiClient.baseUrl != settings.baseUrl) {
              provider.updateBaseUrl(settings.baseUrl);
            }
            return provider;
          },
        ),
      ],
      child: Consumer<SettingsProvider>(
        builder: (context, settings, _) {
          ThemeMode currentMode = ThemeMode.system;
          if (settings.themeMode == 'light') {
            currentMode = ThemeMode.light;
          } else if (settings.themeMode == 'dark') {
            currentMode = ThemeMode.dark;
          }

          return MaterialApp(
            title: 'GTasks App',
            debugShowCheckedModeBanner: false,
            themeMode: currentMode,
            theme: ThemeData(
              useMaterial3: true,
              colorScheme: ColorScheme.fromSeed(
                seedColor: Colors.blueAccent,
                brightness: Brightness.light,
              ),
            ),
            darkTheme: ThemeData(
              useMaterial3: true,
              colorScheme: ColorScheme.fromSeed(
                seedColor: Colors.blueAccent,
                brightness: Brightness.dark,
              ),
            ),
            home: const TasksScreen(),
          );
        },
      ),
    );
  }
}
