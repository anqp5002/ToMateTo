import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:tomateto/core/failure/app_failure.dart';
import 'package:tomateto/core/session/session_store.dart';
import 'package:tomateto/core/transport/graphql_transport.dart';
import 'package:tomateto/core/transport/transport_response.dart';
import 'package:tomateto/features/compose/post_editor_controller.dart';
import 'package:tomateto/features/content_screens.dart';
import 'package:tomateto/features/feed/feed_controller.dart';
import 'package:tomateto/repositories/content_repository.dart';

PostData fixture(String id) => PostData({
  'id': id,
  'dishName': 'Phở bò',
  'caption': '',
  'address': '',
  'priceRange': null,
  'author': <String, Object?>{'id': '1', 'displayName': null},
  'images': <Object?>[],
  'likeCount': 0,
});

final class FakeGateway implements ContentGateway {
  int creates = 0;
  bool fail = false;
  @override
  Future<ContentPage> feed({String? after, String mode = 'LATEST'}) async {
    if (fail) throw const FormatException();
    return ContentPage(
      after == null ? [fixture('1')] : [fixture('1'), fixture('2')],
      after == null ? 'cursor' : null,
      after == null,
    );
  }

  @override
  Future<PostData> post(String id) async => fixture(id);
  @override
  Future<PostData> create(JsonMap input) async {
    creates++;
    throw ContentFailure(AppFailure(FailureKind.outcomeUnknown));
  }

  @override
  Future<JsonMap> upload(Uint8List bytes, String name) async => {
    'uploadId': 'ticket',
  };
  @override
  Uri imageUri(String path) => Uri.parse('https://example.invalid$path');
}

void main() {
  test('feed deduplicates pages and retains data on load-more error', () async {
    final gateway = FakeGateway();
    final controller = FeedController(gateway);
    addTearDown(controller.dispose);
    await controller.refresh();
    gateway.fail = true;
    await controller.loadMore();
    expect(controller.posts.length, 1);
    expect(controller.failed, isTrue);
    gateway.fail = false;
    await controller.loadMore();
    expect(controller.posts.map((p) => p.id), ['1', '2']);
  });

  test(
    'unknown write result cannot be submitted again automatically or manually',
    () async {
      final gateway = FakeGateway();
      final controller = PostEditorController(gateway);
      addTearDown(controller.dispose);
      await controller.submit({'dishName': 'Phở'});
      expect(controller.outcomeUnknown, isTrue);
      await controller.submit({'dishName': 'Phở'});
      expect(gateway.creates, 1);
    },
  );

  testWidgets('compose and detail fit 360 by 800', (tester) async {
    tester.view.physicalSize = const Size(360, 800);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final gateway = FakeGateway();
    await tester.pumpWidget(MaterialApp(home: ComposeScreen(gateway: gateway)));
    await tester.pumpAndSettle();
    expect(find.text('Tên món *'), findsOneWidget);
    expect(tester.takeException(), isNull);
    await tester.pumpWidget(
      MaterialApp(
        home: PostDetailScreen(id: '1', gateway: gateway),
      ),
    );
    await tester.pumpAndSettle();
    expect(find.text('Phở bò'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  test('GraphQLContentRepository.upload handles 413/502 non-JSON and 201 JSON', () async {
    final session = MemorySessionStore()..setToken('tok');
    final endpoint = Uri.parse('http://localhost/graphql');
    int step = 0;
    final client = MockClient((_) async {
      step++;
      return switch (step) {
        1 => http.Response('<html>413 Too Large</html>', 413),
        2 => http.Response('Bad Gateway', 502, headers: {'x-request-id': 'r2'}),
        _ => http.Response('{"uploadId":"u-201"}', 201),
      };
    });
    final repo = GraphQLContentRepository(
      transport: GraphQLTransport(
        endpoint: endpoint,
        client: client,
        session: session,
      ),
      client: client,
      session: session,
      baseUri: Uri.parse('http://localhost'),
    );
    final bytes = Uint8List.fromList([1, 2, 3]);
    await expectLater(
      repo.upload(bytes, 'a.jpg'),
      throwsA(
        isA<ContentFailure>().having(
          (e) => e.failure.kind,
          'kind',
          FailureKind.validation,
        ),
      ),
    );
    await expectLater(
      repo.upload(bytes, 'a.jpg'),
      throwsA(
        isA<ContentFailure>()
            .having((e) => e.failure.kind, 'kind', FailureKind.serviceUnavailable)
            .having((e) => e.failure.requestId, 'requestId', 'r2'),
      ),
    );
    final ok = await repo.upload(bytes, 'a.jpg');
    expect(ok['uploadId'], 'u-201');
  });

  test('PostEditorController blocks submit on failed image and retries failed image only', () async {
    final gateway = _MultiImageGateway();
    final controller = PostEditorController(gateway);
    addTearDown(controller.dispose);
    await controller.add(Uint8List.fromList([1]), 'ok.jpg');
    gateway.failUpload = true;
    await controller.add(Uint8List.fromList([2]), 'bad.jpg');

    expect(controller.images.length, 2);
    expect(controller.images[0].uploadId, 'u-1');
    expect(controller.images[1].failed, isTrue);

    final blocked = await controller.submit({'dishName': 'Bún chả'});
    expect(blocked, isNull);
    expect(controller.failure?.kind, FailureKind.validation);
    expect(gateway.creates, 0);

    gateway.failUpload = false;
    await controller.upload(controller.images[1]);
    expect(controller.images[0].uploadId, 'u-1');
    expect(controller.images[1].failed, isFalse);
    expect(controller.images[1].uploadId, 'u-2');

    final created = await controller.submit({'dishName': 'Bún chả'});
    expect(created, isNotNull);
    expect(gateway.creates, 1);
  });

  testWidgets('PostDetailScreen hides empty recipe and shows restaurant', (tester) async {
    final gateway = _DetailGateway();
    await tester.pumpWidget(
      MaterialApp(
        home: PostDetailScreen(id: '1', gateway: gateway),
      ),
    );
    await tester.pumpAndSettle();
    expect(find.text('Công thức'), findsNothing);
    expect(find.text('Quán: Phở Thìn'), findsOneWidget);
    expect(find.text('Địa chỉ quán: 13 Lò Đúc'), findsOneWidget);
  });
}

final class _MultiImageGateway extends FakeGateway {
  bool failUpload = false;
  int _uploads = 0;

  @override
  Future<JsonMap> upload(Uint8List bytes, String name) async {
    if (failUpload) {
      throw ContentFailure(
        AppFailure(FailureKind.validation, apiCode: 'PAYLOAD_TOO_LARGE'),
      );
    }
    _uploads++;
    return {'uploadId': 'u-$_uploads'};
  }

  @override
  Future<PostData> create(JsonMap input) async {
    creates++;
    return fixture('created');
  }
}

final class _DetailGateway extends FakeGateway {
  @override
  Future<PostData> post(String id) async => PostData({
    'id': id,
    'dishName': 'Phở bò',
    'caption': 'Ngon',
    'address': '13 Lò Đúc',
    'priceRange': null,
    'author': <String, Object?>{'id': '1', 'displayName': 'An'},
    'images': <Object?>[],
    'likeCount': 3,
    'recipe': <String, Object?>{'ingredients': <Object?>[], 'instructions': <Object?>[]},
    'restaurant': <String, Object?>{
      'id': 'r1',
      'name': 'Phở Thìn',
      'address': '13 Lò Đúc',
    },
  });
}
