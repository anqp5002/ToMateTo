import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:http/http.dart' as http;

import 'core/navigation/app_router.dart';
import 'core/navigation/navigation_context.dart';
import 'core/session/session_store.dart';
import 'core/theme/app_theme.dart';
import 'core/transport/graphql_transport.dart';
import 'features/content_screens.dart';
import 'repositories/content_repository.dart';

void main() {
  runApp(const ToMateToApp());
}

final class ToMateToApp extends StatefulWidget {
  const ToMateToApp({super.key, this.session});

  final SessionStore? session;

  @override
  State<ToMateToApp> createState() => _ToMateToAppState();
}

final class _ToMateToAppState extends State<ToMateToApp> {
  final http.Client _client = http.Client();
  late final GoRouter _router;

  @override
  void initState() {
    super.initState();
    const String config = String.fromEnvironment(
      'GRAPHQL_URL',
      defaultValue: 'http://localhost:8000/graphql',
    );
    final endpoint = Uri.parse(config);
    final session = widget.session ?? MemorySessionStore();
    final gateway = GraphQLContentRepository(
      transport: GraphQLTransport(
        endpoint: endpoint,
        client: _client,
        session: session,
      ),
      client: _client,
      session: session,
      baseUri: endpoint,
    );
    _router = buildAppRouter(
      navigation: NavigationContext(),
      home: (_) => ContentHome(gateway: gateway, session: session),
      postDetail: (_, id) => PostDetailScreen(id: id, gateway: gateway),
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
    _client.close();
    super.dispose();
  }
}
