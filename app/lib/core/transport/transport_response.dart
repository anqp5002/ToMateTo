enum TransportIssue { network, timeout, invalidResponse, missingSession }

typedef JsonMap = Map<String, Object?>;

final class TransportResponse {
  const TransportResponse({
    this.data,
    this.errors = const <JsonMap>[],
    this.status,
    this.requestId,
    this.issue,
  });

  final JsonMap? data;
  final List<JsonMap> errors;
  final int? status;
  final String? requestId;
  final TransportIssue? issue;

  bool get isSuccess =>
      issue == null &&
      status != null &&
      status! >= 200 &&
      status! < 300 &&
      errors.isEmpty &&
      data != null;
}
