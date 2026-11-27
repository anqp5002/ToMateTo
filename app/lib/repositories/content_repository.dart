import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';

import 'package:http/http.dart' as http;

import '../core/failure/app_failure.dart';
import '../core/session/session_store.dart';
import '../core/transport/graphql_transport.dart';
import '../core/transport/transport_response.dart';

final class ContentFailure implements Exception {
  const ContentFailure(this.failure);
  final AppFailure failure;
}

final class PostData {
  const PostData(this.json);
  final JsonMap json;
  String get id => json['id']! as String;
  String get dishName => json['dishName']! as String;
  String get caption => json['caption'] as String? ?? '';
  String get address => json['address'] as String? ?? '';
  String? get priceRange => json['priceRange'] as String?;
  JsonMap get author => json['author']! as JsonMap;
  List<JsonMap> get images =>
      (json['images']! as List<Object?>).cast<JsonMap>();
}

final class ContentPage {
  const ContentPage(this.posts, this.cursor, this.hasNext);
  final List<PostData> posts;
  final String? cursor;
  final bool hasNext;
}

abstract interface class ContentGateway {
  Future<ContentPage> feed({String? after, String mode = 'LATEST'});
  Future<PostData> post(String id);
  Future<PostData> create(JsonMap input);
  Future<JsonMap> upload(Uint8List bytes, String name);
  Uri imageUri(String path);
}

const String postSelection = '''id dishName caption address priceRange feeling
 latitude longitude recipe{ingredients instructions}
 author{id displayName avatarUrl} images{id url position}
 restaurant{id name address} likeCount isLikedByViewer isSavedByViewer createdAt updatedAt''';

final class GraphQLContentRepository implements ContentGateway {
  GraphQLContentRepository({
    required this.transport,
    required this.client,
    required this.session,
    required this.baseUri,
  });
  final GraphQLTransport transport;
  final http.Client client;
  final SessionStore session;
  final Uri baseUri;

  Future<JsonMap> _response(
    Future<TransportResponse> pending, {
    bool mutation = false,
  }) async {
    final response = await pending;
    if (!response.isSuccess) {
      throw ContentFailure(
        AppFailure.fromTransport(response, mutation: mutation),
      );
    }
    return response.data!;
  }

  @override
  Future<ContentPage> feed({String? after, String mode = 'LATEST'}) async {
    final data = await _response(
      transport.query(
        'query(\$mode:FeedMode!,\$page:PageInput){feed(mode:\$mode,page:\$page){edges{node{$postSelection}}pageInfo{endCursor hasNextPage}}}',
        variables: {
          'mode': mode,
          'page': {'first': 10, 'after': ?after},
        },
      ),
    );
    final connection = data['feed']! as JsonMap;
    final page = connection['pageInfo']! as JsonMap;
    return ContentPage(
      (connection['edges']! as List<Object?>)
          .cast<JsonMap>()
          .map((e) => PostData(e['node']! as JsonMap))
          .toList(),
      page['endCursor'] as String?,
      page['hasNextPage']! as bool,
    );
  }

  @override
  Future<PostData> post(String id) async {
    final data = await _response(
      transport.query(
        'query(\$id:ID!){post(id:\$id){$postSelection}}',
        variables: {'id': id},
      ),
    );
    final rawPost = data['post'];
    if (rawPost is! JsonMap) {
      throw ContentFailure(AppFailure(FailureKind.notFound));
    }
    return PostData(rawPost);
  }

  @override
  Future<PostData> create(JsonMap input) async {
    final data = await _response(
      transport.mutate(
        'mutation(\$input:CreatePostInput!){createPost(input:\$input){$postSelection}}',
        variables: {'input': input},
      ),
      mutation: true,
    );
    return PostData(data['createPost']! as JsonMap);
  }

  @override
  Future<JsonMap> upload(Uint8List bytes, String name) async {
    if (bytes.length > 10 * 1024 * 1024) {
      throw ContentFailure(
        AppFailure(FailureKind.validation, apiCode: 'PAYLOAD_TOO_LARGE'),
      );
    }
    final token = await session.readToken();
    if (token == null || token.isEmpty) {
      throw ContentFailure(AppFailure(FailureKind.unauthenticated));
    }
    final request =
        http.MultipartRequest('POST', baseUri.resolve('/media/uploads'))
          ..headers['Authorization'] = 'Bearer $token'
          ..fields['purpose'] = 'POST'
          ..files.add(
            http.MultipartFile.fromBytes('file', bytes, filename: name),
          );
    try {
      final response = await http.Response.fromStream(
        await client.send(request).timeout(const Duration(seconds: 30)),
      ).timeout(const Duration(seconds: 30));
      JsonMap? data;
      final bodyText =
          utf8.decode(response.bodyBytes, allowMalformed: true).trim();
      if (bodyText.isNotEmpty) {
        try {
          final decoded = jsonDecode(bodyText);
          if (decoded is JsonMap) data = decoded;
        } on FormatException {
          // Non-JSON responses (e.g. proxy 413/415/502/401) still map by status.
        }
      }
      if (response.statusCode == 201) {
        if (data != null) return data;
        throw ContentFailure(AppFailure(FailureKind.serviceUnavailable));
      }
      final error = data?['error'];
      throw ContentFailure(
        AppFailure.fromTransport(
          TransportResponse(
            status: response.statusCode,
            errors: [
              if (error is JsonMap) {'extensions': error},
            ],
            requestId: response.headers['x-request-id'],
          ),
        ),
      );
    } on TimeoutException {
      throw ContentFailure(AppFailure(FailureKind.serviceUnavailable));
    } on http.ClientException {
      throw ContentFailure(AppFailure(FailureKind.serviceUnavailable));
    }
  }

  @override
  Uri imageUri(String path) => baseUri.resolve(path);
}
