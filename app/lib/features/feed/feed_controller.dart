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

  Future<void> refresh({String? feedMode}) async {
    _generation++;
    busy = false;
    cursor = null;
    hasNext = true;
    if (feedMode != null) mode = feedMode;
    await loadMore(replace: true);
  }

  Future<void> loadMore({bool replace = false}) async {
    if (_disposed || busy || !hasNext) return;
    final generation = _generation;
    busy = true;
    failed = false;
    notifyListeners();
    try {
      final result = await gateway.feed(
        after: replace ? null : cursor,
        mode: mode,
      );
      if (_disposed || generation != _generation) return;
      final unique = <String, PostData>{
        if (!replace)
          for (final post in posts) post.id: post,
        for (final post in result.posts) post.id: post,
      };
      posts = unique.values.toList();
      cursor = result.cursor;
      hasNext = result.hasNext;
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
