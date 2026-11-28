import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../shared/widgets/placeholder_screen.dart';
import 'navigation_context.dart';

String requireAuth({
  required bool authenticated,
  required NavigationContext navigation,
  required InternalTarget target,
  required UserIntent intent,
}) {
  if (authenticated) return target.path;
  navigation.remember(target, intent);
  return '/login';
}

GoRouter buildAppRouter({
  required NavigationContext navigation,
  required WidgetBuilder home,
  Widget Function(BuildContext, GoRouterState)? authPage,
  Widget Function(BuildContext, GoRouterState, String)? resourcePage,
}) {
  final Map<String, String> auth = {
    '/login': 'Đăng nhập',
    '/register': 'Đăng ký',
    '/forgot-password': 'Khôi phục mật khẩu',
    '/reset-password': 'Đặt mật khẩu mới',
  };
  return GoRouter(
    routes: <RouteBase>[
      GoRoute(path: '/', builder: (context, state) => home(context)),
      for (final MapEntry<String, String> entry in auth.entries)
        GoRoute(
          path: entry.key,
          builder: (context, state) {
            if (authPage != null &&
                (entry.key == '/login' || entry.key == '/register')) {
              return authPage(context, state);
            }
            if (entry.key == '/reset-password') {
              // S10 will inject a verified reset grant into a real flow.
              return PlaceholderScreen(
                title: entry.value,
                onBack: () => context.go('/forgot-password'),
              );
            }
            return PlaceholderScreen(
              title: entry.value,
              onBack: () => context.go(navigation.resume(false).path),
            );
          },
        ),
      for (final (String path, String title) in <(String, String)>[
        ('/posts/:id', 'Chi tiết bài'),
        ('/collections/:id', 'Bộ sưu tập'),
        ('/profiles/:id', 'Hồ sơ'),
      ])
        GoRoute(
          path: path,
          builder: (context, state) =>
              resourcePage?.call(context, state, title) ??
              PlaceholderScreen(title: title, onBack: () => context.go('/')),
        ),
    ],
  );
}
