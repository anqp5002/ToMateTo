import '../transport/transport_response.dart';

final class Page<T> {
  Page({required Iterable<T> items, required this.hasMore, this.nextCursor})
    : items = List<T>.unmodifiable(items) {
    if (hasMore && (nextCursor == null || nextCursor!.isEmpty)) {
      throw const FormatException('A next page requires a cursor');
    }
  }

  factory Page.fromConnection(JsonMap data, T Function(JsonMap) decodeNode) {
    final Object? edges = data['edges'];
    final Object? info = data['pageInfo'];
    if (edges is! List<Object?> || info is! JsonMap) {
      throw const FormatException('Invalid connection');
    }
    final Object? more = info['hasNextPage'];
    final Object? cursor = info['endCursor'];
    if (more is! bool || (cursor != null && cursor is! String)) {
      throw const FormatException('Invalid page info');
    }
    return Page<T>(
      items: edges.map((Object? edge) {
        if (edge is! JsonMap || edge['node'] is! JsonMap) {
          throw const FormatException('Invalid connection edge');
        }
        return decodeNode(edge['node']! as JsonMap);
      }),
      hasMore: more,
      nextCursor: cursor as String?,
    );
  }

  final List<T> items;
  final bool hasMore;
  final String? nextCursor;
}
