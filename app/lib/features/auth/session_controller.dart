import 'dart:async';

import 'package:flutter/foundation.dart';

import '../../core/failure/app_failure.dart';
import '../../core/session/session_store.dart';
import '../../core/transport/graphql_transport.dart';
import '../../core/transport/transport_response.dart';

final class SessionController extends ChangeNotifier {
  SessionController(this._transport, this._store);

  final GraphQLTransport? _transport;
  final AccountSessionStore _store;
  String? displayName;
  bool busy = false;
  bool restored = false;
  AppFailure? failure;
  Timer? _expiry;
  bool _disposed = false;
  VoidCallback? onExpired;

  @override
  void notifyListeners() {
    if (!_disposed) super.notifyListeners();
  }

  @override
  void dispose() {
    _disposed = true;
    _expiry?.cancel();
    super.dispose();
  }

  void _watchExpiry(SessionSnapshot session) {
    if (_disposed) return;
    _expiry?.cancel();
    _expiry = Timer(session.expiresAt.difference(DateTime.now()), () async {
      if (await endLocalSession()) onExpired?.call();
    });
  }

  Future<void> restore() async {
    try {
      final session = await _store.readSession();
      displayName = session?.displayName;
      if (session != null) _watchExpiry(session);
    } on Exception {
      failure = AppFailure(FailureKind.internalError);
    }
    restored = true;
    notifyListeners();
  }

  Future<bool> authenticate(String email, String password, String? name) async {
    if (busy) return false;
    final operation = name == null ? 'login' : 'register';
    final inputType = name == null ? 'LoginInput' : 'RegisterInput';
    return _run(() async {
      final response = await _send(
        'mutation Auth(\$input: $inputType!) { $operation(input: \$input) '
        '{ accessToken expiresInSeconds user { id displayName } } }',
        variables: {
          'input': {'email': email, 'password': password, 'displayName': ?name},
        },
        auth: AuthMode.none,
      );
      if (!response.isSuccess) {
        failure = AppFailure.fromTransport(response, mutation: name != null);
        return false;
      }
      final data = response.data?[operation];
      final user = data is JsonMap ? data['user'] : null;
      final token = data is JsonMap ? data['accessToken'] : null;
      final ttl = data is JsonMap ? data['expiresInSeconds'] : null;
      final id = user is JsonMap ? user['id'] : null;
      final label = user is JsonMap ? user['displayName'] : null;
      if (token is! String ||
          token.isEmpty ||
          ttl is! int ||
          ttl <= 0 ||
          id is! String ||
          id.isEmpty ||
          label is! String) {
        failure = AppFailure(FailureKind.internalError);
        return false;
      }
      final session = SessionSnapshot(
        id,
        token,
        label,
        DateTime.now().toUtc().add(Duration(seconds: ttl)),
      );
      await _store.setSession(session);
      _watchExpiry(session);
      displayName = label;
      return true;
    });
  }

  Future<bool> logout() => _run(() async {
    final response = await _send('mutation { logout { success } }');
    final payload = response.data?['logout'];
    if (!response.isSuccess) {
      final error = AppFailure.fromTransport(response, mutation: true);
      if (error.kind != FailureKind.unauthenticated) {
        failure = error;
        return false;
      }
    } else if (payload is! JsonMap || payload['success'] != true) {
      failure = AppFailure(FailureKind.outcomeUnknown);
      return false;
    }
    await _clear();
    return true;
  });

  Future<bool> endLocalSession() => _run(() async {
    await _clear();
    return true;
  });

  Future<void> _clear() async {
    await _store.clearSession();
    _expiry?.cancel();
    displayName = null;
  }

  Future<bool> _run(Future<bool> Function() action) async {
    if (busy) return false;
    busy = true;
    failure = null;
    notifyListeners();
    try {
      return await action();
    } on Exception {
      failure = AppFailure(FailureKind.internalError);
      return false;
    } finally {
      busy = false;
      notifyListeners();
    }
  }

  Future<TransportResponse> _send(
    String query, {
    JsonMap variables = const {},
    AuthMode auth = AuthMode.required,
  }) async {
    return await _transport?.mutate(query, variables: variables, auth: auth) ??
        const TransportResponse(issue: TransportIssue.network);
  }
}
