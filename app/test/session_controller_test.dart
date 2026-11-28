import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:tomateto/core/session/session_store.dart';
import 'package:tomateto/core/transport/graphql_transport.dart';
import 'package:tomateto/features/auth/session_controller.dart';

void main() {
  test('login stores session and confirmed logout clears it', () async {
    final store = MemorySessionStore();
    final client = MockClient((request) async {
      final query = (jsonDecode(request.body) as Map)['query'] as String;
      if (query.contains('logout')) {
        expect(request.headers['Authorization'], 'Bearer sample');
        return http.Response('{"data":{"logout":{"success":true}}}', 200);
      }
      expect(request.headers['Authorization'], isNull);
      return http.Response(
        '{"data":{"login":{"accessToken":"sample","expiresInSeconds":604800,'
        '"user":{"id":"1","displayName":"Minh"}}}}',
        200,
      );
    });
    final controller = SessionController(
      GraphQLTransport(
        endpoint: Uri.http('localhost', '/graphql'),
        client: client,
        session: store,
      ),
      store,
    );
    addTearDown(controller.dispose);
    expect(
      await controller.authenticate('minh@example.test', 'example', null),
      isTrue,
    );
    expect(await store.readToken(), 'sample');
    expect(controller.displayName, 'Minh');
    expect(await controller.logout(), isTrue);
    expect(await store.readToken(), isNull);
  });

  test(
    'lost logout response preserves local session until user clears it',
    () async {
      final store = MemorySessionStore();
      await store.setSession(
        SessionSnapshot(
          '1',
          'sample',
          'Minh',
          DateTime.now().add(const Duration(days: 1)),
        ),
      );
      final controller = SessionController(
        GraphQLTransport(
          endpoint: Uri.http('localhost', '/graphql'),
          client: MockClient(
            (_) async => throw http.ClientException('offline'),
          ),
          session: store,
        ),
        store,
      );
      addTearDown(controller.dispose);
      await controller.restore();
      expect(await controller.logout(), isFalse);
      expect(await store.readToken(), 'sample');
      expect(await controller.endLocalSession(), isTrue);
      expect(await store.readToken(), isNull);
    },
  );
}
