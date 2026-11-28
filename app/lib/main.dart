import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:http/http.dart' as http;

import 'core/navigation/app_router.dart';
import 'core/navigation/navigation_context.dart';
import 'core/session/session_store.dart';
import 'core/theme/app_theme.dart';
import 'core/transport/graphql_transport.dart';
import 'features/auth/auth_screen.dart';
import 'features/auth/session_controller.dart';
import 'features/smoke/smoke_controller.dart';
import 'features/smoke/smoke_repository.dart';
import 'features/smoke/smoke_screen.dart';

void main() {
  runApp(const ToMateToApp());
}

final class ToMateToApp extends StatefulWidget {
  const ToMateToApp({super.key});

  @override
  State<ToMateToApp> createState() => _ToMateToAppState();
}

final class _ToMateToAppState extends State<ToMateToApp> {
  final http.Client _client = http.Client();
  late final GoRouter _router;
  late final SmokeController _smoke;
  late final SessionController _session;
  final _navigation = NavigationContext();

  @override
  void initState() {
    super.initState();
    const String config = String.fromEnvironment('GRAPHQL_URL');
    final Uri? endpoint = Uri.tryParse(config);
    final AccountSessionStore store =
        !kIsWeb && defaultTargetPlatform == TargetPlatform.android
        ? const AndroidSessionStore(FlutterSecureStorage())
        : MemorySessionStore();
    final GraphQLTransport? transport =
        endpoint != null &&
            endpoint.hasAuthority &&
            (endpoint.scheme == 'https' || endpoint.scheme == 'http') &&
            endpoint.userInfo.isEmpty
        ? GraphQLTransport(endpoint: endpoint, client: _client, session: store)
        : null;
    _smoke = SmokeController(
      transport == null ? null : SmokeRepository(transport),
    );
    _session = SessionController(transport, store);
    unawaited(_session.restore());
    _router = buildAppRouter(
      navigation: _navigation,
      home: (context) => ListenableBuilder(
        listenable: _session,
        builder: (context, _) => Column(
          children: [
            Material(child: SafeArea(child: _accountActions(context))),
            Expanded(child: SmokeScreen(controller: _smoke)),
          ],
        ),
      ),
      authPage: (_, state) => AuthScreen(
        key: ValueKey(state.uri.path),
        session: _session,
        navigation: _navigation,
        register: state.uri.path == '/register',
        initialEmail: state.extra is String ? state.extra! as String : '',
        expired: state.extra == true,
      ),
      resourcePage: (context, state, title) => Scaffold(
        appBar: AppBar(
          title: Text(title),
          leading: BackButton(onPressed: () => context.go('/')),
        ),
        body: ListenableBuilder(
          listenable: _session,
          builder: (context, _) =>
              Center(child: _accountActions(context, target: state.uri.path)),
        ),
      ),
    );
    _session.onExpired = () {
      if (!mounted) return;
      final path = _router.routeInformationProvider.value.uri.path;
      try {
        _navigation.rememberTarget(InternalTarget.parse(path));
      } on FormatException {
        _navigation.clear();
      }
      _smoke.reset();
      _router.go('/login', extra: true);
    };
  }

  Widget _accountActions(BuildContext context, {String? target}) {
    if (!_session.restored) return const LinearProgressIndicator();
    final name = _session.displayName;
    if (name == null) {
      return TextButton(
        onPressed: () {
          if (target != null) {
            try {
              _navigation.rememberTarget(InternalTarget.parse(target));
            } on FormatException {
              _navigation.clear();
            }
          }
          context.go('/login');
        },
        child: const Text('Đăng nhập'),
      );
    }
    return Wrap(
      crossAxisAlignment: WrapCrossAlignment.center,
      children: [
        Text(name),
        TextButton(
          onPressed: _session.busy ? null : () => _logout(context),
          child: const Text('Đăng xuất'),
        ),
      ],
    );
  }

  Future<void> _logout(BuildContext context) async {
    while (context.mounted) {
      final done = await _session.logout();
      if (!context.mounted) return;
      if (done) {
        _navigation.clear();
        _smoke.reset();
        context.go('/');
        return;
      }
      final local = await showDialog<bool>(
        context: context,
        builder: (dialogContext) => AlertDialog(
          title: const Text('Chưa xác nhận đăng xuất trên máy chủ.'),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(dialogContext, false),
              child: const Text('Thử lại'),
            ),
            TextButton(
              onPressed: () => Navigator.pop(dialogContext, true),
              child: const Text('Kết thúc trên thiết bị'),
            ),
          ],
        ),
      );
      if (!context.mounted || local == null) return;
      if (!local) continue;
      final cleared = await _session.endLocalSession();
      if (!context.mounted) return;
      if (cleared) {
        _navigation.clear();
        _smoke.reset();
        context.go('/');
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Chưa thể xóa phiên trên thiết bị.')),
        );
      }
      return;
    }
  }

  @override
  Widget build(BuildContext context) => MaterialApp.router(
    title: 'ToMateTo',
    theme: buildAppTheme(),
    routerConfig: _router,
  );

  @override
  void dispose() {
    _router.dispose();
    _smoke.dispose();
    _session.dispose();
    _client.close();
    super.dispose();
  }
}
