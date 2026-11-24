import '../transport/transport_response.dart';

final class PageRequest {
  PageRequest.first([int limit = 10]) : this._(limit, null);

  PageRequest.next(String after, [int limit = 10]) : this._(limit, after);

  PageRequest._(this.limit, this.after) {
    RangeError.checkValueInInterval(limit, 1, 50, 'limit');
    if (after != null && after!.isEmpty) {
      throw ArgumentError.value(after, 'after');
    }
  }

  final int limit;
  final String? after;
  JsonMap toVariables() => {'first': limit, if (after != null) 'after': after};
}
