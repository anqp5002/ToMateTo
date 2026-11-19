abstract interface class SessionStore {
  Future<String?> readToken();
}

final class MemorySessionStore implements SessionStore {
  String? _token;

  void setToken(String? token) => _token = token;

  @override
  Future<String?> readToken() async => _token;
}
