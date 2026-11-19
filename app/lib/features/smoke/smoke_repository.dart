import '../../core/failure/app_failure.dart';
import '../../core/result/result.dart';
import '../../core/transport/graphql_transport.dart';
import '../../core/transport/transport_response.dart';

/// Temporary read-only repository for the S8 connectivity check.
final class SmokeRepository {
  const SmokeRepository(this._transport);

  final GraphQLTransport _transport;

  Future<Result<bool>> hasFeedItems() async {
    final TransportResponse response = await _transport.query(
      'query FoundationSmoke { feed(mode: LATEST, page: {first: 1}) '
      '{ edges { node { id } } } }',
    );
    if (!response.isSuccess) {
      return Result<bool>.failed(AppFailure.fromTransport(response));
    }
    final Object? feed = response.data?['feed'];
    final Object? edges = feed is JsonMap ? feed['edges'] : null;
    return edges is List<Object?>
        ? Result<bool>.success(edges.isNotEmpty)
        : Result<bool>.failed(AppFailure(FailureKind.internalError));
  }
}
