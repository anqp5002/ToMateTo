import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:tomateto/core/failure/app_failure.dart';
import 'package:tomateto/core/navigation/app_router.dart';
import 'package:tomateto/core/navigation/navigation_context.dart';
import 'package:tomateto/core/result/page.dart';
import 'package:tomateto/core/result/page_request.dart';
import 'package:tomateto/core/result/result.dart';
import 'package:tomateto/core/session/session_store.dart';
import 'package:tomateto/core/state/list_state.dart';
import 'package:tomateto/core/state/mutation_state.dart';
import 'package:tomateto/core/transport/graphql_transport.dart';
import 'package:tomateto/core/transport/transport_response.dart';

TransportResponse graphqlError(String code, {JsonMap extra = const {}}) =>
    TransportResponse(
      status: 200,
      requestId: 'req-1',
      errors: [
        {
          'extensions': {'code': code, ...extra},
        },
      ],
    );

void main() {
  group('failure mapping', () {
    const cases = {
      'VALIDATION_FAILED': FailureKind.validation,
      'UNAUTHENTICATED': FailureKind.unauthenticated,
      'FORBIDDEN': FailureKind.forbidden,
      'NOT_FOUND': FailureKind.notFound,
      'NOT_AVAILABLE': FailureKind.notAvailable,
      'ALREADY_EXISTS': FailureKind.alreadyExists,
      'CONFLICT': FailureKind.conflict,
      'RATE_LIMITED': FailureKind.rateLimited,
      'INTEGRATION_UNAVAILABLE': FailureKind.serviceUnavailable,
      'INTERNAL_ERROR': FailureKind.internalError,
      'PAYLOAD_TOO_LARGE': FailureKind.validation,
      'UNSUPPORTED_MEDIA_TYPE': FailureKind.validation,
    };
    for (final entry in cases.entries) {
      test('preserves ${entry.key} from HTTP 200', () {
        final response = graphqlError(entry.key);
        expect(response.isSuccess, isFalse);
        final failure = AppFailure.fromTransport(response);
        expect(failure.kind, entry.value);
        expect(failure.apiCode, entry.key);
        expect(failure.requestId, 'req-1');
      });
    }
    test('retains field code and retry metadata without inventing a timer', () {
      final failure = AppFailure.fromTransport(
        graphqlError(
          'VALIDATION_FAILED',
          extra: {
            'fieldErrors': [
              {'field': 'dishName', 'code': 'REQUIRED'},
            ],
          },
        ),
      );
      expect(failure.fieldErrors, {'dishName': 'REQUIRED'});
      expect(failure.retryAfterSeconds, isNull);
      expect(
        AppFailure.fromTransport(
          graphqlError('RATE_LIMITED', extra: {'retryAfterSeconds': 20}),
        ).retryAfterSeconds,
        20,
      );
    });
    test('classifies a network failure by operation type', () {
      const response = TransportResponse(issue: TransportIssue.network);
      expect(
        AppFailure.fromTransport(response).kind,
        FailureKind.serviceUnavailable,
      );
      expect(
        AppFailure.fromTransport(response, mutation: true).kind,
        FailureKind.outcomeUnknown,
      );
    });
    test('maps HTTP 413, 415 and non-mutation 5xx status codes', () {
      expect(
        AppFailure.fromTransport(const TransportResponse(status: 413)).kind,
        FailureKind.validation,
      );
      expect(
        AppFailure.fromTransport(const TransportResponse(status: 415)).kind,
        FailureKind.validation,
      );
      expect(
        AppFailure.fromTransport(const TransportResponse(status: 502)).kind,
        FailureKind.serviceUnavailable,
      );
      expect(
        AppFailure.fromTransport(
          const TransportResponse(status: 502),
          mutation: true,
        ).kind,
        FailureKind.outcomeUnknown,
      );
    });
  });

  group('GraphQL transport', () {
    final endpoint = Uri.parse('http://localhost/graphql');
    test(
      'reads the current token per request and omits it for public auth mode',
      () async {
        final session = MemorySessionStore();
        final sent = <String?>[];
        final client = MockClient((request) async {
          sent.add(request.headers['authorization']);
          expect(jsonDecode(request.body), {
            'query': 'query { feed }',
            'variables': {},
          });
          return http.Response('{"data":{"feed":[]}}', 200);
        });
        final transport = GraphQLTransport(
          endpoint: endpoint,
          client: client,
          session: session,
        );
        session.setToken('test-A');
        await transport.query('query { feed }');
        session.setToken('test-B');
        await transport.query('query { feed }');
        await transport.query('query { feed }', auth: AuthMode.none);
        expect(sent, ['Bearer test-A', 'Bearer test-B', null]);
      },
    );

    test('required auth does not send a request without a session', () async {
      final transport = GraphQLTransport(
        endpoint: endpoint,
        client: MockClient((_) async => throw StateError('unexpected request')),
        session: MemorySessionStore(),
      );
      final response = await transport.mutate('mutation { logout }');
      expect(
        AppFailure.fromTransport(response).kind,
        FailureKind.unauthenticated,
      );
    });

    test(
      'preserves empty 401, partial GraphQL response and network errors',
      () async {
        int count = 0;
        final transport = GraphQLTransport(
          endpoint: endpoint,
          client: MockClient(
            (_) async => switch (++count) {
              1 => http.Response('', 401, headers: {'x-request-id': 'req'}),
              2 => http.Response(
                '{"data":{"feed":{}},"errors":[{"extensions":{"code":"FORBIDDEN"}}]}',
                200,
              ),
              _ => throw http.ClientException('DNS'),
            },
          ),
          session: MemorySessionStore(),
        );
        final unauthorized = await transport.query('query { feed }');
        expect(unauthorized.requestId, 'req');
        expect(
          AppFailure.fromTransport(unauthorized).kind,
          FailureKind.unauthenticated,
        );
        final partial = await transport.query('query { feed }');
        expect(partial.data, {'feed': {}});
        expect(partial.isSuccess, isFalse);
        expect(
          (await transport.query('query { feed }')).issue,
          TransportIssue.network,
        );
      },
    );
  });

  group('result and state', () {
    test('typed result exposes value or failure', () {
      expect(const Result<int>.success(1), isA<Success<int>>());
      expect(
        Result<int>.failed(AppFailure(FailureKind.validation)),
        isA<Failure<int>>(),
      );
    });
    test('decodes a connection and requires a cursor for the next page', () {
      final page = Page<int>.fromConnection({
        'edges': [
          {
            'node': {'id': 1},
          },
        ],
        'pageInfo': {'hasNextPage': true, 'endCursor': 'cursor'},
      }, (node) => node['id']! as int);
      expect(page.items, [1]);
      expect(page.nextCursor, 'cursor');
      expect(() => Page<int>(items: [1], hasMore: true), throwsFormatException);
    });
    test('checks PageRequest bounds and maps first/after', () {
      expect(PageRequest.first().toVariables(), {'first': 10});
      expect(PageRequest.next('opaque', 50).toVariables(), {
        'first': 50,
        'after': 'opaque',
      });
      expect(() => PageRequest.first(0), throwsRangeError);
      expect(() => PageRequest.first(51), throwsRangeError);
    });
    test('ListState copies state and keeps items when changing phase', () {
      final initial = ListState<int>(
        items: [1],
        nextCursor: 'c',
        hasMore: true,
      );
      final next = initial.copyWith(
        phase: ListPhase.loadingMore,
        generation: 1,
      );
      expect(next.items, [1]);
      expect(initial.generation, 0);
      expect(next.generation, 1);
      expect(() => next.items.add(2), throwsUnsupportedError);
      expect(() => ListState<int>(hasMore: true), throwsArgumentError);
      expect(next.copyWith(clearCursor: true).hasMore, isFalse);
    });
    test(
      'mutation can preserve unknown outcome and clear failure explicitly',
      () {
        final updated = const MutationState().copyWith(
          phase: MutationPhase.outcomeUnknown,
          generation: 2,
          failure: AppFailure(FailureKind.outcomeUnknown),
        );
        expect(updated.phase, MutationPhase.outcomeUnknown);
        expect(updated.generation, 2);
        expect(updated.copyWith(clearFailure: true).failure, isNull);
      },
    );
  });

  group('navigation', () {
    test('returning as a guest preserves context and pending intent', () {
      final navigation = NavigationContext();
      final target = navigation.openPost('p1');
      expect(
        requireAuth(
          authenticated: false,
          navigation: navigation,
          target: target,
          intent: UserIntent.save,
        ),
        '/login',
      );
      expect(navigation.resume(false).path, '/posts/p1');
      expect(navigation.pendingIntent, UserIntent.save);
    });
    test(
      'resuming after login returns the destination and clears the intent',
      () {
        final navigation = NavigationContext();
        navigation.remember(navigation.openProfile('u1'), UserIntent.follow);
        expect(navigation.resume(true).path, '/profiles/u1');
        expect(navigation.pendingIntent, isNull);
        expect(navigation.back().path, '/');
      },
    );
    test(
      'rejects foreign URLs, unsupported routes and sensitive query strings',
      () {
        for (final target in [
          '//other.example',
          'https://other.example',
          '/login',
          '/posts/a?token=x',
        ]) {
          expect(() => InternalTarget.parse(target), throwsFormatException);
        }
      },
    );
  });
}
