import 'package:flutter/foundation.dart';

import '../../repositories/content_repository.dart';

final class FeedController extends ChangeNotifier {
  FeedController(this.gateway);
  final ContentGateway gateway;
  List<PostData> posts = [];
  String? cursor;
  bool busy = false, hasNext = true, failed = false;
  String mode = 'LATEST';
  int _generation = 0;
  bool _disposed = false;
  String? _pendingRefreshMode;

  Future<void> refresh({String? feedMode}) async {
    _generation++;
    busy = false;
    _pendingRefreshMode = feedMode ?? mode;
    await loadMore(replace: true);
  }

  Future<void> loadMore({bool replace = false}) async {
    final refreshing = replace || _pendingRefreshMode != null;
    if (_disposed || busy || (!refreshing && !hasNext)) return;
    if (refreshing) _pendingRefreshMode ??= mode;
    final requestedMode = _pendingRefreshMode ?? mode;
    final generation = _generation;
    busy = true;
    failed = false;
    notifyListeners();
    try {
      final result = await gateway.feed(
        after: refreshing ? null : cursor,
        mode: requestedMode,
      );
      if (_disposed || generation != _generation) return;
      if (result.hasNext && result.cursor == null) {
        throw const FormatException('Next page requires a cursor');
      }
      final unique = <String, PostData>{
        if (!refreshing)
          for (final post in posts) post.id: post,
        for (final post in result.posts) post.id: post,
      };
      posts = unique.values.toList();
      cursor = result.cursor;
      hasNext = result.hasNext;
      mode = requestedMode;
      _pendingRefreshMode = null;
    } on Exception {
      if (generation == _generation) failed = true;
    } finally {
      if (!_disposed && generation == _generation) {
        busy = false;
        notifyListeners();
      }
    }
  }

  @override
  void dispose() {
    _disposed = true;
    super.dispose();
  }
}
