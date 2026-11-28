import 'dart:convert';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';

abstract interface class SessionStore {
  Future<String?> readToken();
}

final class MemorySessionStore implements AccountSessionStore {
  String? _token;
  SessionSnapshot? _session;

  @override
  Future<SessionSnapshot?> readSession() async {
    final session = _session;
    if (session != null && session.expiresAt.isAfter(DateTime.now())) {
      return session;
    }
    if (session != null) await clearSession();
    return null;
  }

  @override
  Future<void> setSession(SessionSnapshot session) async {
    _session = session;
    _token = session.token;
  }

  @override
  Future<void> clearSession() async {
    _session = null;
    _token = null;
  }

  void setToken(String? token) => _token = token;

  @override
  Future<String?> readToken() async {
    await readSession();
    return _token;
  }
}

final class SessionSnapshot {
  const SessionSnapshot(
    this.userId,
    this.token,
    this.displayName,
    this.expiresAt,
  );
  final String userId;
  final String token;
  final String displayName;
  final DateTime expiresAt;
}

abstract interface class AccountSessionStore implements SessionStore {
  Future<SessionSnapshot?> readSession();
  Future<void> setSession(SessionSnapshot session);
  Future<void> clearSession();
}

final class AndroidSessionStore implements AccountSessionStore {
  const AndroidSessionStore(this._storage);

  final FlutterSecureStorage _storage;
  static const _key = 'tomateto.session';

  @override
  Future<SessionSnapshot?> readSession() async {
    final raw = await _storage.read(key: _key);
    if (raw == null) return null;
    final Object? decoded = jsonDecode(raw);
    if (decoded is Map<String, Object?> &&
        decoded['id'] is String &&
        decoded['token'] is String &&
        decoded['name'] is String &&
        decoded['expiresAt'] is String) {
      final expiresAt = DateTime.tryParse(decoded['expiresAt']! as String);
      if (expiresAt != null && expiresAt.isAfter(DateTime.now())) {
        return SessionSnapshot(
          decoded['id']! as String,
          decoded['token']! as String,
          decoded['name']! as String,
          expiresAt,
        );
      }
    }
    await clearSession();
    return null;
  }

  @override
  Future<String?> readToken() async => (await readSession())?.token;

  @override
  Future<void> setSession(SessionSnapshot session) => _storage.write(
    key: _key,
    value: jsonEncode({
      'id': session.userId,
      'token': session.token,
      'name': session.displayName,
      'expiresAt': session.expiresAt.toIso8601String(),
    }),
  );

  @override
  Future<void> clearSession() => _storage.delete(key: _key);
}
