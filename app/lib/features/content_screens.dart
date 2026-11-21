import 'dart:async';

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';

import '../core/session/session_store.dart';
import '../repositories/content_repository.dart';
import 'compose/post_editor_controller.dart';
import 'feed/feed_controller.dart';

class ContentHome extends StatefulWidget {
  const ContentHome({super.key, required this.gateway, required this.session});
  final ContentGateway gateway;
  final SessionStore session;
  @override
  State<ContentHome> createState() => _ContentHomeState();
}

class _ContentHomeState extends State<ContentHome> {
  late final FeedController controller = FeedController(widget.gateway)
    ..refresh();
  @override
  void dispose() {
    controller.dispose();
    super.dispose();
  }

  Future<void> compose() async {
    final token = await widget.session.readToken();
    if (!mounted) return;
    if (token == null || token.isEmpty) {
      await context.push<void>('/login');
      return;
    }
    final created = await Navigator.of(context).push<PostData>(
      MaterialPageRoute(builder: (_) => ComposeScreen(gateway: widget.gateway)),
    );
    if (created != null && mounted) await controller.refresh();
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(
      title: const Text('ToMateTo'),
      actions: [
        IconButton(
          onPressed: compose,
          tooltip: 'Tạo bài',
          icon: const Icon(Icons.add),
        ),
      ],
    ),
    body: ListenableBuilder(
      listenable: controller,
      builder: (context, _) {
        if (controller.posts.isEmpty && controller.busy) {
          return const Center(child: CircularProgressIndicator());
        }
        return RefreshIndicator(
          onRefresh: controller.refresh,
          child: NotificationListener<ScrollNotification>(
            onNotification: (notice) {
              if (notice.metrics.extentAfter < 300 && !controller.failed) {
                unawaited(controller.loadMore());
              }
              return false;
            },
            child: CustomScrollView(
              physics: const AlwaysScrollableScrollPhysics(),
              slivers: [
                if (controller.failed)
                  SliverToBoxAdapter(
                    child: TextButton(
                      onPressed: () => controller.loadMore(
                        replace: controller.posts.isEmpty,
                      ),
                      child: const Text('Chưa tải được bài viết. Thử lại'),
                    ),
                  ),
                if (!controller.busy &&
                    !controller.failed &&
                    controller.posts.isEmpty)
                  const SliverFillRemaining(
                    child: Center(child: Text('Chưa có bài viết.')),
                  ),
                SliverPadding(
                  padding: const EdgeInsets.all(16),
                  sliver: SliverLayoutBuilder(
                    builder: (context, constraints) => SliverGrid(
                      gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
                        crossAxisCount: constraints.crossAxisExtent < 600
                            ? 1
                            : 2,
                        mainAxisSpacing: 12,
                        crossAxisSpacing: 12,
                        mainAxisExtent: 310,
                      ),
                      delegate: SliverChildBuilderDelegate((context, index) {
                        final post = controller.posts[index];
                        return Card(
                          clipBehavior: Clip.antiAlias,
                          child: InkWell(
                            onTap: () => Navigator.of(context).push(
                              MaterialPageRoute<void>(
                                builder: (_) => PostDetailScreen(
                                  id: post.id,
                                  gateway: widget.gateway,
                                ),
                              ),
                            ),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                SizedBox(
                                  height: 180,
                                  width: double.infinity,
                                  child: post.images.isEmpty
                                      ? const Center(
                                          child: Icon(
                                            Icons.restaurant,
                                            size: 48,
                                          ),
                                        )
                                      : Image.network(
                                          widget.gateway
                                              .imageUri(
                                                post.images.first['url']!
                                                    as String,
                                              )
                                              .toString(),
                                          fit: BoxFit.cover,
                                          errorBuilder: (_, error, trace) =>
                                              const Icon(Icons.broken_image),
                                        ),
                                ),
                                Padding(
                                  padding: const EdgeInsets.all(12),
                                  child: Column(
                                    crossAxisAlignment:
                                        CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        post.dishName,
                                        maxLines: 1,
                                        overflow: TextOverflow.ellipsis,
                                        style: Theme.of(context)
                                            .textTheme
                                            .titleLarge,
                                      ),
                                      Text(
                                        post.author['displayName'] as String? ??
                                            'Người dùng',
                                        maxLines: 1,
                                      ),
                                      Text(
                                        '${post.json['likeCount']} lượt thích · ${post.address}',
                                        maxLines: 1,
                                        overflow: TextOverflow.ellipsis,
                                      ),
                                    ],
                                  ),
                                ),
                              ],
                            ),
                          ),
                        );
                      }, childCount: controller.posts.length),
                    ),
                  ),
                ),
                if (controller.busy)
                  const SliverToBoxAdapter(
                    child: Padding(
                      padding: EdgeInsets.all(16),
                      child: Center(child: CircularProgressIndicator()),
                    ),
                  ),
              ],
            ),
          ),
        );
      },
    ),
    floatingActionButton: FloatingActionButton(
      onPressed: compose,
      tooltip: 'Tạo bài',
      child: const Icon(Icons.edit),
    ),
  );
}

class PostDetailScreen extends StatefulWidget {
  const PostDetailScreen({super.key, required this.id, required this.gateway});
  final String id;
  final ContentGateway gateway;
  @override
  State<PostDetailScreen> createState() => _PostDetailScreenState();
}

class _PostDetailScreenState extends State<PostDetailScreen> {
  late Future<PostData> pending = widget.gateway.post(widget.id);
  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Chi tiết bài')),
    body: FutureBuilder(
      future: pending,
      builder: (context, snapshot) {
        if (snapshot.hasError) {
          return Center(
            child: TextButton(
              onPressed: () =>
                  setState(() => pending = widget.gateway.post(widget.id)),
              child: const Text('Bài viết không khả dụng. Thử lại'),
            ),
          );
        }
        final post = snapshot.data;
        if (post == null) {
          return const Center(child: CircularProgressIndicator());
        }
        final recipe = post.json['recipe'] as Map<String, Object?>?;
        return ListView(
          padding: const EdgeInsets.all(16),
          children: [
            if (post.images.isNotEmpty)
              SizedBox(
                height: 260,
                child: PageView(
                  children: [
                    for (final image in post.images)
                      Image.network(
                        widget.gateway
                            .imageUri(image['url']! as String)
                            .toString(),
                        fit: BoxFit.contain,
                        errorBuilder: (_, error, trace) =>
                            const Center(child: Text('Không tải được ảnh.')),
                      ),
                  ],
                ),
              ),
            Text(
              post.dishName,
              style: Theme.of(context).textTheme.headlineMedium,
            ),
            Text(post.author['displayName'] as String? ?? 'Người dùng'),
            Text(post.caption),
            Text(post.address),
            if (post.priceRange != null)
              Text(priceLabels[post.priceRange] ?? post.priceRange!),
            if (post.json['latitude'] != null)
              Text(
                'Vị trí: ${post.json['latitude']}, ${post.json['longitude']}',
              ),
            if (recipe != null) ...[
              const SizedBox(height: 16),
              const Text('Công thức'),
              for (final line in recipe['ingredients'] as List<Object?>? ?? [])
                Text('• $line'),
              for (final line in recipe['instructions'] as List<Object?>? ?? [])
                Text('$line'),
            ],
          ],
        );
      },
    ),
  );
}

const priceLabels = <String, String>{
  'UNDER_50K': 'Dưới 50.000đ',
  'FROM_50K_TO_100K': '50.000–100.000đ',
  'FROM_100K_TO_200K': '100.000–200.000đ',
  'ABOVE_200K': 'Trên 200.000đ',
};

class ComposeScreen extends StatefulWidget {
  const ComposeScreen({super.key, required this.gateway});
  final ContentGateway gateway;
  @override
  State<ComposeScreen> createState() => _ComposeScreenState();
}

class _ComposeScreenState extends State<ComposeScreen> {
  late final PostEditorController controller = PostEditorController(
    widget.gateway,
  );
  final form = GlobalKey<FormState>();
  final name = TextEditingController(),
      caption = TextEditingController(),
      address = TextEditingController(),
      restaurant = TextEditingController(),
      ingredients = TextEditingController(),
      steps = TextEditingController();
  String? price;
  @override
  void dispose() {
    for (final field in [
      name,
      caption,
      address,
      restaurant,
      ingredients,
      steps,
    ]) {
      field.dispose();
    }
    controller.dispose();
    super.dispose();
  }

  Future<void> pick() async {
    final files = await ImagePicker().pickMultiImage(limit: 5);
    for (final file in files) {
      if (!mounted || controller.images.length >= 5) return;
      if (await file.length() > 10 * 1024 * 1024) {
        if (mounted) {
          ScaffoldMessenger.of(context)
              .showSnackBar(const SnackBar(content: Text('Ảnh vượt 10 MB.')));
        }
        continue;
      }
      await controller.add(await file.readAsBytes(), file.name);
    }
  }

  Future<void> submit() async {
    if (!form.currentState!.validate()) return;
    final post = await controller.submit({
      'dishName': name.text.trim(),
      'caption': caption.text,
      'address': address.text,
      'restaurantName': restaurant.text,
      'priceRange': price,
      'recipe': {
        'ingredients': ingredients.text
            .split('\n')
            .where((s) => s.trim().isNotEmpty)
            .toList(),
        'instructions': steps.text
            .split('\n')
            .where((s) => s.trim().isNotEmpty)
            .toList(),
      },
    });
    if (mounted && post != null) Navigator.of(context).pop(post);
  }

  @override
  Widget build(BuildContext context) => ListenableBuilder(
    listenable: controller,
    builder: (context, _) => Scaffold(
      appBar: AppBar(title: const Text('Tạo bài')),
      body: Form(
        key: form,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            TextFormField(
              controller: name,
              decoration: const InputDecoration(labelText: 'Tên món *'),
              validator: (value) => value == null || value.trim().isEmpty
                  ? 'Vui lòng nhập tên món.'
                  : null,
            ),
            TextFormField(
              controller: caption,
              decoration: const InputDecoration(labelText: 'Nội dung'),
              maxLines: 3,
            ),
            TextFormField(
              controller: restaurant,
              decoration: const InputDecoration(labelText: 'Tên quán'),
            ),
            TextFormField(
              controller: address,
              decoration: const InputDecoration(labelText: 'Địa chỉ'),
            ),
            DropdownButtonFormField<String>(
              initialValue: price,
              decoration: const InputDecoration(labelText: 'Khoảng giá'),
              items: [
                for (final entry in priceLabels.entries)
                  DropdownMenuItem(value: entry.key, child: Text(entry.value)),
              ],
              onChanged: controller.busy
                  ? null
                  : (value) => setState(() => price = value),
            ),
            TextFormField(
              controller: ingredients,
              decoration: const InputDecoration(
                labelText: 'Nguyên liệu (mỗi dòng một mục)',
              ),
              maxLines: 2,
            ),
            TextFormField(
              controller: steps,
              decoration: const InputDecoration(
                labelText: 'Các bước nấu (mỗi dòng một bước)',
              ),
              maxLines: 2,
            ),
            for (final image in controller.images)
              Card(
                child: Column(
                  children: [
                    Image.memory(
                      image.bytes,
                      height: 120,
                      errorBuilder: (_, error, trace) =>
                          const Icon(Icons.broken_image),
                    ),
                    if (image.busy) const LinearProgressIndicator(),
                    if (image.failed)
                      TextButton(
                        onPressed: () => controller.upload(image),
                        child: const Text('Tải ảnh lại'),
                      ),
                    TextButton(
                      onPressed: controller.busy || controller.outcomeUnknown
                          ? null
                          : () => controller.remove(image),
                      child: const Text('Bỏ ảnh'),
                    ),
                  ],
                ),
              ),
            OutlinedButton(
              onPressed:
                  controller.busy ||
                      controller.outcomeUnknown ||
                      controller.images.length >= 5
                  ? null
                  : pick,
              child: const Text('Chọn ảnh (tối đa 5)'),
            ),
            if (controller.outcomeUnknown) ...[
              const Text(
                'Chưa nhận được kết quả đăng bài. Hãy kiểm tra bài của bạn trước khi đăng lại.',
              ),
              TextButton(
                onPressed: () => Navigator.of(context).pop(),
                child: const Text('Kiểm tra bài viết của bạn'),
              ),
            ] else if (controller.failure != null)
              const Text(
                'Chưa đăng được bài. Vui lòng kiểm tra dữ liệu và thử lại.',
              ),
            FilledButton(
              onPressed: controller.busy || controller.outcomeUnknown
                  ? null
                  : submit,
              child: Text(controller.busy ? 'Đang đăng…' : 'Đăng bài'),
            ),
          ],
        ),
      ),
    ),
  );
}
