import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:tomateto/core/failure/app_failure.dart';
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
}
