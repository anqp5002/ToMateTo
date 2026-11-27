import 'package:flutter/foundation.dart';

import '../../core/failure/app_failure.dart';
import '../../core/transport/transport_response.dart';
import '../../repositories/content_repository.dart';

final class UploadDraft {
  UploadDraft(this.bytes, this.name);
  final Uint8List bytes;
  final String name;
  String? uploadId;
  bool busy = false;
  AppFailure? failure;
  bool get failed => failure != null;
}

class PostEditorController extends ChangeNotifier {
  PostEditorController(this.gateway);
  final ContentGateway gateway;
  final List<UploadDraft> images = [];
  bool busy = false, outcomeUnknown = false;
  AppFailure? failure;
  bool _disposed = false;

  void emit() {
    if (!_disposed) notifyListeners();
  }

  Future<void> add(Uint8List bytes, String name) async {
    if (images.length >= 5 || busy || outcomeUnknown) return;
    final image = UploadDraft(bytes, name);
    images.add(image);
    await upload(image);
  }

  Future<void> upload(UploadDraft image) async {
    if (image.busy || busy || outcomeUnknown) return;
    image.busy = true;
    image.failure = null;
    emit();
    try {
      final result = await gateway.upload(image.bytes, image.name);
      image.uploadId = result['uploadId']! as String;
    } on ContentFailure catch (error) {
      image.failure = error.failure;
    } on Exception {
      image.failure = AppFailure(FailureKind.serviceUnavailable);
    } finally {
      image.busy = false;
      emit();
    }
  }

  void remove(UploadDraft image) {
    if (!busy && !outcomeUnknown) {
      images.remove(image);
      emit();
    }
  }

  Future<PostData?> submit(JsonMap fields) async {
    if (busy || outcomeUnknown) return null;
    if (images.any((i) => i.busy || i.failed || i.uploadId == null)) {
      failure = AppFailure(FailureKind.validation);
      emit();
      return null;
    }
    busy = true;
    failure = null;
    emit();
    try {
      return await gateway.create({
        ...fields,
        'images': [
          for (var i = 0; i < images.length; i++)
            {'uploadId': images[i].uploadId, 'position': i},
        ],
      });
    } on ContentFailure catch (error) {
      failure = error.failure;
      outcomeUnknown = failure!.kind == FailureKind.outcomeUnknown;
      return null;
    } on Exception {
      // An invalid/missing write response can follow a successful commit.
      outcomeUnknown = true;
      return null;
    } finally {
      busy = false;
      emit();
    }
  }

  @override
  void dispose() {
    _disposed = true;
    super.dispose();
  }
}
