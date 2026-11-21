import 'dart:async';

import 'package:flutter_test/flutter_test.dart';
import 'package:tomateto/features/feed/feed_controller.dart';
import 'package:tomateto/repositories/content_repository.dart';

import 'content_test.dart' show FakeGateway, fixture;

final class PlannedFeed implements ContentGateway {
  final pending = <Completer<ContentPage>>[];
  final requests = <({String? after, String mode})>[];
  @override
  Future<ContentPage> feed({String? after, String mode = 'LATEST'}) {
    requests.add((after: after, mode: mode));
    final result = Completer<ContentPage>();
    pending.add(result);
    return result.future;
  }

  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

void main() {
  test('failed refresh preserves cursor, posts and next-page state', () async {
    final gateway = FakeGateway();
    final controller = FeedController(gateway);
    addTearDown(controller.dispose);
    await controller.refresh();
    final oldCursor = controller.cursor;
    gateway.fail = true;
    await controller.refresh();
    expect(controller.cursor, oldCursor);
    expect(controller.posts.map((p) => p.id), ['1']);
    expect(controller.hasNext, true);
    expect(controller.failed, true);
  });

  test(
    'refresh after last page preserves completed state on failure and retries',
    () async {
      final gateway = FakeGateway();
      final controller = FeedController(gateway);
      addTearDown(controller.dispose);
      await controller.refresh();
      await controller.loadMore();
      expect(controller.hasNext, false);
      gateway.fail = true;
      await controller.refresh();
      expect(controller.hasNext, false);
      expect(controller.posts.length, 2);
      gateway.fail = false;
      await controller.loadMore();
      expect(controller.posts.map((p) => p.id), ['1']);
      expect(controller.cursor, 'cursor');
    },
  );

  test('failed mode change retains old page; retry replaces from the requested mode', () async {
    final gateway = PlannedFeed();
    final controller = FeedController(gateway);
    addTearDown(controller.dispose);
    var operation = controller.refresh();
    gateway.pending.last.complete(
      ContentPage([fixture('1')], 'latest-cursor', true),
    );
    await operation;
    operation = controller.refresh(feedMode: 'TRENDING');
    gateway.pending.last.completeError(const FormatException());
    await operation;
    expect(controller.mode, 'LATEST');
    expect(controller.cursor, 'latest-cursor');
    operation = controller.loadMore();
    expect(gateway.requests.last, (after: null, mode: 'TRENDING'));
    gateway.pending.last.complete(
      ContentPage([fixture('9')], 'snapshot-cursor', true),
    );
    await operation;
    expect(controller.posts.map((p) => p.id), ['9']);
    expect(controller.mode, 'TRENDING');
  });

  test(
    'late load-more result cannot overwrite a newer successful refresh',
    () async {
      final gateway = PlannedFeed();
      final controller = FeedController(gateway);
      addTearDown(controller.dispose);
      var operation = controller.refresh();
      gateway.pending.last.complete(ContentPage([fixture('1')], 'old', true));
      await operation;
      final oldRequest = controller.loadMore();
      final oldResult = gateway.pending.last;
      operation = controller.refresh();
      gateway.pending.last.complete(ContentPage([fixture('9')], 'new', false));
      await operation;
      oldResult.complete(ContentPage([fixture('2')], 'stale', true));
      await oldRequest;
      expect(controller.posts.map((p) => p.id), ['9']);
      expect(controller.cursor, 'new');
      expect(controller.hasNext, false);
    },
  );
}
