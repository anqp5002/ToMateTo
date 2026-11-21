import '../failure/app_failure.dart';

enum ListPhase { idle, loading, ready, empty, loadingMore, error }

final class ListState<T> {
  ListState({
    Iterable<T>? items,
    this.nextCursor,
    this.hasMore = false,
    this.phase = ListPhase.idle,
    this.failure,
    this.generation = 0,
  }) : items = List<T>.unmodifiable(items ?? <T>[]) {
    if (hasMore && (nextCursor == null || nextCursor!.isEmpty)) {
      throw ArgumentError('A next page requires a cursor');
    }
  }

  final List<T> items;
  final String? nextCursor;
  final bool hasMore;
  final ListPhase phase;
  final AppFailure? failure;
  final int generation;

  ListState<T> copyWith({
    Iterable<T>? items,
    String? nextCursor,
    bool clearCursor = false,
    bool? hasMore,
    ListPhase? phase,
    AppFailure? failure,
    bool clearFailure = false,
    int? generation,
  }) => ListState<T>(
    items: items ?? this.items,
    nextCursor: clearCursor ? null : nextCursor ?? this.nextCursor,
    hasMore: hasMore ?? (clearCursor ? false : this.hasMore),
    phase: phase ?? this.phase,
    failure: clearFailure ? null : failure ?? this.failure,
    generation: generation ?? this.generation,
  );
}
