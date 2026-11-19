enum UserIntent { like, save, follow, createPost }

final class InternalTarget {
  factory InternalTarget.parse(String path) {
    final Uri? uri = Uri.tryParse(path);
    final List<String>? parts = uri?.pathSegments;
    if (uri == null ||
        uri.hasScheme ||
        uri.hasAuthority ||
        uri.hasQuery ||
        uri.hasFragment ||
        !path.startsWith('/') ||
        !(path == '/' ||
            parts != null &&
                parts.length == 2 &&
                const {
                  'posts',
                  'collections',
                  'profiles',
                }.contains(parts.first) &&
                RegExp(r'^[A-Za-z0-9_-]+$').hasMatch(parts.last))) {
      throw FormatException('Invalid internal destination', path);
    }
    return InternalTarget._(path);
  }

  const InternalTarget._(this.path);
  final String path;
}

final class NavigationContext {
  static const InternalTarget feed = InternalTarget._('/');
  InternalTarget? _target;
  UserIntent? _pendingIntent;

  UserIntent? get pendingIntent => _pendingIntent;

  void remember(InternalTarget target, UserIntent intent) {
    _target = target;
    _pendingIntent = intent;
  }

  InternalTarget resume(bool authenticated) {
    final InternalTarget destination = _target ?? feed;
    if (authenticated) clear();
    return destination;
  }

  InternalTarget openPost(String id) => InternalTarget.parse('/posts/$id');
  InternalTarget openCollection(String id) =>
      InternalTarget.parse('/collections/$id');
  InternalTarget openProfile(String id) =>
      InternalTarget.parse('/profiles/$id');
  InternalTarget back() => _target ?? feed;

  void clear() {
    _target = null;
    _pendingIntent = null;
  }
}
