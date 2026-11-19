import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:http/http.dart' as http;

import 'core/navigation/app_router.dart';
import 'core/navigation/navigation_context.dart';
import 'core/session/session_store.dart';
import 'core/theme/app_theme.dart';
import 'core/transport/graphql_transport.dart';
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

  @override
  void initState() {
    super.initState();
    const String config = String.fromEnvironment('GRAPHQL_URL');
    final Uri? endpoint = Uri.tryParse(config);
    final GraphQLTransport? transport =
        endpoint != null &&
            endpoint.hasAuthority &&
            (endpoint.scheme == 'https' || endpoint.scheme == 'http') &&
            endpoint.userInfo.isEmpty
        ? GraphQLTransport(
            endpoint: endpoint,
            client: _client,
            session: MemorySessionStore(),
          )
        : null;
    _smoke = SmokeController(
      transport == null ? null : SmokeRepository(transport),
    );
    _router = buildAppRouter(
      navigation: NavigationContext(),
      home: (_) => SmokeScreen(controller: _smoke),
    );
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
    _client.close();
    super.dispose();
  }
}
