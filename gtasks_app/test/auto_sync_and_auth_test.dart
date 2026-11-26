import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:gtasks_app/providers/settings_provider.dart';
import 'package:gtasks_app/api/google_tasks_direct_client.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('SettingsProvider Auto Sync & Token Persistence', () {
    setUp(() {
      SharedPreferences.setMockInitialValues({});
    });

    test('Auto Sync defaults and setters persist correctly', () async {
      final settings = SettingsProvider();
      await Future.delayed(const Duration(milliseconds: 50));

      expect(settings.autoSyncEnabled, isTrue);
      expect(settings.autoSyncIntervalMinutes, 15);
      expect(settings.syncOnAppStart, isTrue);
      expect(settings.syncOnAppResume, isTrue);
      expect(settings.autoSyncFull, isFalse);

      await settings.setAutoSyncEnabled(false);
      await settings.setAutoSyncIntervalMinutes(30);
      await settings.setSyncOnAppStart(false);
      await settings.setSyncOnAppResume(false);
      await settings.setAutoSyncFull(true);
      await settings.recordSyncResult(success: true);

      expect(settings.autoSyncEnabled, isFalse);
      expect(settings.autoSyncIntervalMinutes, 30);
      expect(settings.syncOnAppStart, isFalse);
      expect(settings.syncOnAppResume, isFalse);
      expect(settings.autoSyncFull, isTrue);
      expect(settings.lastSyncStatus, 'Success');
      expect(settings.lastSyncAt, isNotNull);
    });

    test('saveAccount preserves existing refresh_token when new refreshToken is null', () async {
      final settings = SettingsProvider();
      await Future.delayed(const Duration(milliseconds: 50));

      final expiry = DateTime.now().toUtc().add(const Duration(hours: 1));
      await settings.saveAccount(
        id: 'work',
        name: 'Work',
        email: 'work@example.com',
        provider: 'google',
        accessToken: 'acc_1',
        refreshToken: 'ref_1',
        expiresAt: expiry,
      );

      expect(settings.storedAccounts['work']?['refresh_token'], 'ref_1');

      // Re-saving without a refreshToken must not wipe out ref_1
      await settings.saveAccount(
        id: 'work',
        name: 'Work',
        provider: 'google',
        accessToken: 'acc_2',
        refreshToken: null,
      );

      expect(settings.storedAccounts['work']?['access_token'], 'acc_2');
      expect(settings.storedAccounts['work']?['refresh_token'], 'ref_1');
      expect(settings.storedAccounts['work']?['email'], 'work@example.com');
    });

    test('Custom Google OAuth credentials can be saved and cleared', () async {
      final settings = SettingsProvider();
      await Future.delayed(const Duration(milliseconds: 50));

      await settings.setGoogleOAuthCredentials(
        clientId: '  custom-id.apps.googleusercontent.com  ',
        clientSecret: '  custom-secret  ',
      );
      expect(settings.googleClientId, 'custom-id.apps.googleusercontent.com');
      expect(settings.googleClientSecret, 'custom-secret');

      await settings.setGoogleOAuthCredentials(clientId: null, clientSecret: null);
      expect(settings.googleClientId, isNull);
      expect(settings.googleClientSecret, isNull);
    });
  });

  group('GoogleTasksDirectClient Auth Handling', () {
    test('Reports missing refresh token clearly without throwing', () async {
      final client = GoogleTasksDirectClient(
        accessToken: 'expired_tok',
        refreshToken: null,
      );

      final ok = await client.refreshAccessToken();
      expect(ok, isFalse);
      expect(client.lastAuthError, contains('No refresh token'));
    });
  });
}
