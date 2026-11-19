import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;

import '../session/session_store.dart';
import 'transport_response.dart';

enum AuthMode { required, optional, none }

final class GraphQLTransport {
  factory GraphQLTransport({
    required Uri endpoint,
    required http.Client client,
    required SessionStore session,
    Duration timeout = const Duration(seconds: 15),
  }) => GraphQLTransport._(endpoint, client, session, timeout);

  GraphQLTransport._(this.endpoint, this._client, this._session, this.timeout);

  final Uri endpoint;
  final http.Client _client;
  final SessionStore _session;
  final Duration timeout;

  Future<TransportResponse> query(
    String operation, {
    JsonMap variables = const <String, Object?>{},
    AuthMode auth = AuthMode.optional,
  }) => _send(operation, variables, auth);

  Future<TransportResponse> mutate(
    String operation, {
    JsonMap variables = const <String, Object?>{},
    AuthMode auth = AuthMode.required,
  }) => _send(operation, variables, auth);

  Future<TransportResponse> _send(
    String operation,
    JsonMap variables,
    AuthMode auth,
  ) async {
    final String? token;
    try {
      token = auth == AuthMode.none ? null : await _session.readToken();
    } on Exception {
      return const TransportResponse(issue: TransportIssue.invalidResponse);
    }
    if (auth == AuthMode.required && (token == null || token.isEmpty)) {
      return const TransportResponse(issue: TransportIssue.missingSession);
    }
    final String body;
    try {
      body = jsonEncode({'query': operation, 'variables': variables});
    } on JsonUnsupportedObjectError {
      return const TransportResponse(issue: TransportIssue.invalidResponse);
    }
    final http.Response response;
    try {
      response = await _client
          .post(
            endpoint,
            headers: {
              'Content-Type': 'application/json',
              if (token != null && token.isNotEmpty)
                'Authorization': 'Bearer $token',
            },
            body: body,
          )
          .timeout(timeout);
    } on TimeoutException {
      return const TransportResponse(issue: TransportIssue.timeout);
    } on http.ClientException {
      return const TransportResponse(issue: TransportIssue.network);
    }

    final String? requestId = response.headers['x-request-id'];
    final int status = response.statusCode;
    try {
      final Object? decoded = jsonDecode(utf8.decode(response.bodyBytes));
      if (decoded is JsonMap) {
        final Object? data = decoded['data'];
        final Object? errors = decoded['errors'];
        final bool validErrors =
            errors == null ||
            (errors is List<Object?> &&
                errors.every((Object? e) => e is JsonMap));
        if (validErrors &&
            (data is JsonMap || errors is List<Object?> && errors.isNotEmpty)) {
          return TransportResponse(
            data: data is JsonMap ? data : null,
            errors: errors is List<Object?>
                ? List<JsonMap>.unmodifiable(errors.whereType<JsonMap>())
                : const <JsonMap>[],
            status: status,
            requestId: requestId,
          );
        }
      }
    } on FormatException {
      // Preserve HTTP status even for an empty or non-JSON response.
    }
    return TransportResponse(
      status: status,
      requestId: requestId,
      issue: TransportIssue.invalidResponse,
    );
  }
}
