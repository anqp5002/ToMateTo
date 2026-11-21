import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:tomateto/core/session/session_store.dart';
import 'package:tomateto/core/theme/app_theme.dart';
import 'package:tomateto/core/transport/graphql_transport.dart';
import 'package:tomateto/features/smoke/smoke_controller.dart';
import 'package:tomateto/features/smoke/smoke_repository.dart';
import 'package:tomateto/features/smoke/smoke_screen.dart';
import 'package:tomateto/main.dart';
import 'package:tomateto/shared/widgets/async_feedback.dart';

void main() {
  testWidgets('Flutter app opens the Content feed', (tester) async {
    await tester.pumpWidget(const ToMateToApp());
    expect(find.text('ToMateTo'), findsOneWidget);
  });

  testWidgets('feedback displays loading, empty and retry', (tester) async {
    int retried = 0;
    for (final phase in FeedbackPhase.values) {
      await tester.pumpWidget(
        MaterialApp(
          theme: buildAppTheme(),
          home: Scaffold(
            body: AsyncFeedback(phase: phase, onRetry: () => retried++),
          ),
        ),
      );
      switch (phase) {
        case FeedbackPhase.loading:
          expect(find.byType(CircularProgressIndicator), findsOneWidget);
        case FeedbackPhase.empty:
          expect(find.text('Chưa có dữ liệu.'), findsOneWidget);
        case FeedbackPhase.error:
          await tester.tap(find.text('Thử lại'));
          expect(retried, 1);
      }
    }
  });

  testWidgets('smoke feed sends the read query and retries a GraphQL error', (
    tester,
  ) async {
    final responses = <Completer<http.Response>>[];
    final client = MockClient((request) {
      expect(request.method, 'POST');
      expect(request.url.path, '/graphql');
      expect(request.body, contains('FoundationSmoke'));
      final response = Completer<http.Response>();
      responses.add(response);
      return response.future;
    });
    final controller = SmokeController(
      SmokeRepository(
        GraphQLTransport(
          endpoint: Uri.parse('http://localhost/graphql'),
          client: client,
          session: MemorySessionStore(),
        ),
      ),
    );
    addTearDown(controller.dispose);
    await tester.pumpWidget(
      MaterialApp(theme: buildAppTheme(), home: SmokeScreen(controller: controller)),
    );
    await tester.tap(find.text('Đọc bảng tin thử'));
    await tester.pump();
    expect(find.text('Đang tải…'), findsOneWidget);
    responses.single.complete(
      http.Response(
        '{"errors":[{"extensions":{"code":"INTERNAL_ERROR"}}]}',
        200,
      ),
    );
    await tester.pumpAndSettle();
    expect(find.text('Chưa tải được dữ liệu.'), findsOneWidget);
    await tester.tap(find.text('Thử lại'));
    await tester.pump();
    responses.last.complete(
      http.Response('{"data":{"feed":{"edges":[]}}}', 200),
    );
    await tester.pumpAndSettle();
    expect(find.text('Chưa có dữ liệu.'), findsOneWidget);
  });
}
