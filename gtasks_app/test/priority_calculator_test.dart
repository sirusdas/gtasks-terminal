import 'package:flutter_test/flutter_test.dart';
import 'package:gtasks_app/api/google_tasks_direct_client.dart';

void main() {
  group('Priority Calculator Tests', () {
    test('Calculates critical priority from asterisks and tags', () {
      expect(GoogleTasksDirectClient.calculatePriorityFromTags(['[******]']), equals('critical'));
      expect(GoogleTasksDirectClient.calculatePriorityFromTags(['critical']), equals('critical'));
      expect(GoogleTasksDirectClient.calculatePriorityFromTags(['urgent']), equals('critical'));
      expect(GoogleTasksDirectClient.calculatePriorityFromTags(['p0']), equals('critical'));
    });

    test('Calculates high priority from 4-5 asterisks and tags', () {
      expect(GoogleTasksDirectClient.calculatePriorityFromTags(['[****]']), equals('high'));
      expect(GoogleTasksDirectClient.calculatePriorityFromTags(['[*****]']), equals('high'));
      expect(GoogleTasksDirectClient.calculatePriorityFromTags(['high']), equals('high'));
      expect(GoogleTasksDirectClient.calculatePriorityFromTags(['p1']), equals('high'));
    });

    test('Calculates medium priority from 3 asterisks and tags', () {
      expect(GoogleTasksDirectClient.calculatePriorityFromTags(['[***]']), equals('medium'));
      expect(GoogleTasksDirectClient.calculatePriorityFromTags(['med']), equals('medium'));
      expect(GoogleTasksDirectClient.calculatePriorityFromTags(['medium']), equals('medium'));
      expect(GoogleTasksDirectClient.calculatePriorityFromTags(['p2']), equals('medium'));
    });

    test('Calculates low priority from 1-2 asterisks and tags', () {
      expect(GoogleTasksDirectClient.calculatePriorityFromTags(['[*]']), equals('low'));
      expect(GoogleTasksDirectClient.calculatePriorityFromTags(['[**]']), equals('low'));
      expect(GoogleTasksDirectClient.calculatePriorityFromTags(['low']), equals('low'));
      expect(GoogleTasksDirectClient.calculatePriorityFromTags(['p3']), equals('low'));
      expect(GoogleTasksDirectClient.calculatePriorityFromTags(['someday']), equals('low'));
    });

    test('Defaults to medium when no priority tag exists', () {
      expect(GoogleTasksDirectClient.calculatePriorityFromTags(['work', 'project']), equals('medium'));
    });
  });
}
