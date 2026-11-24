import '../transport/transport_response.dart';

enum FailureKind {
  validation,
  unauthenticated,
  forbidden,
  notFound,
  notAvailable,
  alreadyExists,
  conflict,
  rateLimited,
  serviceUnavailable,
  internalError,
  outcomeUnknown,
}

final class AppFailure {
  AppFailure(
    this.kind, {
    this.apiCode,
    this.requestId,
    this.retryAfterSeconds,
    Map<String, String> fieldErrors = const <String, String>{},
  }) : fieldErrors = Map<String, String>.unmodifiable(fieldErrors);

  factory AppFailure.fromTransport(
    TransportResponse response, {
    bool mutation = false,
  }) {
    if (response.isSuccess) {
      throw ArgumentError('Expected a failed transport response');
    }
    final Object? raw = response.errors.firstOrNull?['extensions'];
    final JsonMap extensions = raw is JsonMap ? raw : const <String, Object?>{};
    final Object? code = extensions['code'];
    final Object? retry = extensions['retryAfterSeconds'];
    final Object? fields = extensions['fieldErrors'];
    final fieldErrors = <String, String>{};
    if (fields is List<Object?>) {
      for (final JsonMap field in fields.whereType<JsonMap>()) {
        final Object? name = field['field'];
        final Object? fieldCode = field['code'];
        if (name is String && fieldCode is String) {
          fieldErrors[name] = fieldCode;
        }
      }
    }
    final FailureKind kind = switch (code) {
      'VALIDATION_FAILED' => FailureKind.validation,
      'UNAUTHENTICATED' => FailureKind.unauthenticated,
      'FORBIDDEN' => FailureKind.forbidden,
      'NOT_FOUND' => FailureKind.notFound,
      'NOT_AVAILABLE' => FailureKind.notAvailable,
      'ALREADY_EXISTS' => FailureKind.alreadyExists,
      'CONFLICT' => FailureKind.conflict,
      'RATE_LIMITED' => FailureKind.rateLimited,
      'INTEGRATION_UNAVAILABLE' => FailureKind.serviceUnavailable,
      'INTERNAL_ERROR' => FailureKind.internalError,
      _ => switch (response.status) {
        401 => FailureKind.unauthenticated,
        403 => FailureKind.forbidden,
        429 => FailureKind.rateLimited,
        _ when response.issue == TransportIssue.missingSession =>
          FailureKind.unauthenticated,
        _
            when response.issue == TransportIssue.network ||
                response.issue == TransportIssue.timeout =>
          mutation
              ? FailureKind.outcomeUnknown
              : FailureKind.serviceUnavailable,
        _ when mutation && (response.status ?? 0) >= 500 =>
          FailureKind.outcomeUnknown,
        _
            when mutation &&
                (response.status ?? 0) >= 200 &&
                (response.status ?? 0) < 300 =>
          FailureKind.outcomeUnknown,
        _ => FailureKind.internalError,
      },
    };
    return AppFailure(
      kind,
      apiCode: code is String ? code : null,
      requestId: response.requestId,
      retryAfterSeconds: retry is int && retry >= 0 ? retry : null,
      fieldErrors: fieldErrors,
    );
  }

  final FailureKind kind;
  final String? apiCode;
  final String? requestId;
  final int? retryAfterSeconds;
  final Map<String, String> fieldErrors;
}
