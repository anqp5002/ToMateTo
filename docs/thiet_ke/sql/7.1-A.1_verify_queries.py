"""Verify S6 reference SQL on a disposable PostgreSQL 16 container.

Run from repo root: python docs/thiet_ke/sql/7.1-A.1_verify_queries.py
Requires Python 3 and a running Docker Engine. No third-party Python dependency.
Creates no host-mounted database and always removes its own container/volume.
"""
import csv
import io
import json
import math
import re
import statistics
import subprocess
import time
import uuid
from datetime import datetime
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
NAME = 'tomateto-s6-check-' + uuid.uuid4().hex[:10]
DB = 's6_reference_check'
END = '2026-11-05T12:00:00Z'
REFERENCE = Path(__file__).with_name('7.1-A.1_reference_queries.sql').read_text(encoding='utf-8')
DDL_DOC = (ROOT / 'docs/thiet_ke/6.4-B_ddl.md').read_text(encoding='utf-8')
DDL = re.search(r'<!-- BEGIN DDL -->\s*```sql\n(.*?)```', DDL_DOC, re.S).group(1)
passed = []


def docker(*args, input_text=None, check=True):
    return subprocess.run(['docker', *args], input=input_text, text=True,
                          encoding='utf-8', capture_output=True, check=check)


def sql(command, prepare=True, check=True):
    prefix = REFERENCE if prepare else ''
    return docker('exec', '-i', '-e', 'PGCLIENTENCODING=UTF8', NAME,
                  'psql', '-X', '-q', '--csv', '-v', 'ON_ERROR_STOP=1',
                  '-v', 'VERBOSITY=sqlstate', '-U', 'postgres', '-d', DB,
                  input_text=prefix + '\n' + command, check=check)


def rows(command):
    return list(csv.DictReader(io.StringIO(sql(command).stdout)))


def expect(condition, label):
    if not condition:
        raise AssertionError(label)
    passed.append(label)


def literal(value):
    return "'" + value.replace("'", "''") + "'"


def visible_ids(command):
    return [int(r['id']) for r in rows(command)]


def bounds(lat, lon, radius=5000):
    angular = radius / 6371000.0
    lat_delta = math.degrees(angular)
    lo, hi = max(-90.0, lat-lat_delta), min(90.0, lat+lat_delta)
    if lo <= -90 or hi >= 90:
        return lo, hi, -180.0, 180.0
    delta = math.degrees(math.asin(min(1.0, math.sin(angular)/math.cos(math.radians(lat)))))
    return lo, hi, (lon-delta+180) % 360-180, (lon+delta+180) % 360-180


def distance(lat, lon, rlat, rlon):
    a = (math.sin(math.radians(rlat-lat)/2)**2
         + math.cos(math.radians(lat))*math.cos(math.radians(rlat))
         * math.sin(math.radians(rlon-lon)/2)**2)
    a = min(1.0, max(0.0, a))
    return 2*6371000.0*math.atan2(math.sqrt(a), math.sqrt(1-a))


def nearby(lat, lon):
    box = bounds(lat, lon)
    candidates = rows('EXECUTE s6_nearby_candidates(' + ','.join(map(str, box)) + ');')
    exact = [(distance(lat,lon,float(r['latitude']),float(r['longitude'])),int(r['id']))
             for r in candidates]
    return sorted((d,i) for d,i in exact if d <= 5000)[:50]


FIXTURE = r"""
INSERT INTO users(id,email,email_normalized,password_hash,display_name)
SELECT i, 'u'||i||'@example.invalid', 'u'||i||'@example.invalid','fixture-hash','User '||i
FROM generate_series(1,6) i;
INSERT INTO dishes(id,name,name_normalized,is_seed)
VALUES (1,'Phở bò','pho bo',true),(2,'Bún bò','bun bo',true);
INSERT INTO dishes(id,name,name_normalized,is_seed)
SELECT i,'Món '||i,'mon '||i,true FROM generate_series(3,100) i;
INSERT INTO tags(id,name,name_normalized)
VALUES (1,'Ăn sáng','an sang'),(2,'Món nước','mon nuoc'),(3,'Ẩn','an'),(4,'Blocked only','blocked only');
INSERT INTO posts(id,user_id,dish_id,caption,created_at,updated_at,is_hidden) VALUES
(101,3,1,'public fixture','2026-11-04T12:00Z','2026-11-04T12:00Z',false),
(102,2,1,'blocked fixture','2026-11-04T12:00Z','2026-11-04T12:00Z',false),
(103,3,2,'hidden fixture','2026-11-04T12:00Z','2026-11-04T12:00Z',true),
(104,4,2,'old post recent like','2026-10-20T12:00Z','2026-10-20T12:00Z',false),
(105,3,1,'at window start','2026-10-29T12:00Z','2026-10-29T12:00Z',false),
(106,3,2,'at window end','2026-11-05T12:00Z','2026-11-05T12:00Z',false),
(107,3,1,'old inactive','2026-10-10T12:00Z','2026-10-10T12:00Z',false),
(108,3,2,'multiple collections','2026-11-03T12:00Z','2026-11-03T12:00Z',false),
(109,4,2,'image fixture','2026-11-03T12:00Z','2026-11-03T12:00Z',false);
INSERT INTO posts(id,user_id,dish_id,created_at,updated_at)
SELECT i,3,3+(i%98),'2026-11-01T00:00Z','2026-11-01T00:00Z'
FROM generate_series(200,439) i;
INSERT INTO user_blocks(blocker_id,blocked_id) VALUES (2,1);
INSERT INTO likes(user_id,post_id,created_at) VALUES
(5,101,'2026-11-04T00:00Z'),(6,101,'2026-10-29T12:00Z'),
(4,101,'2026-11-05T12:00Z'),(1,101,'2026-10-29T11:59:59.999999Z'),
(5,102,'2026-11-04T00:00Z'),(5,104,'2026-11-04T00:00Z'),
(5,105,'2026-10-29T11:59:59.999999Z');
INSERT INTO collections(id,user_id,name,name_normalized,is_default) VALUES
(10,6,'Đã lưu','da luu',true),(11,6,'Bộ riêng','bo rieng',false),
(12,5,'Đã lưu','da luu',true),(13,1,'Đã lưu','da luu',true);
INSERT INTO collection_items(collection_id,post_id,added_at) VALUES
(10,101,'2026-11-02T00:00Z'),(11,101,'2026-11-03T00:00Z'),
(12,101,'2026-11-03T00:00Z'),(10,108,'2026-10-20T00:00Z'),
(11,108,'2026-11-03T00:00Z'),(13,102,'2026-11-03T00:00Z');
INSERT INTO post_tags(post_id,tag_id)
VALUES (101,1),(101,2),(102,1),(102,4),(103,3),(104,2),(105,1),(108,2);
INSERT INTO media_assets(id,owner_id,purpose,state,provider,storage_key,url,
input_size_bytes,stored_size_bytes,mime_type,width,height,created_at,expires_at,consumed_at)
SELECT ('00000000-0000-0000-0000-'||lpad(i::text,12,'0'))::uuid,
4,'POST','ATTACHED','fixture',i::text,'https://example.invalid/'||i,
100,80,'image/jpeg',100,100,'2026-11-01T00:00Z','2026-11-10T00:00Z','2026-11-03T00:00Z'
FROM generate_series(1,2) i;
INSERT INTO post_images(post_id,media_id,position)
SELECT 109,('00000000-0000-0000-0000-'||lpad(i::text,12,'0'))::uuid,i-1
FROM generate_series(1,2) i;
INSERT INTO restaurants(id,name,name_normalized,latitude,longitude) VALUES
(1,'Origin','origin',0,0),(2,'Near','near',0,0.01),(3,'Outside','outside',0,0.1),
(4,'Box corner','box corner',0.04,0.04),(5,'Missing','missing',NULL,NULL),
(6,'Date line','date line',0,-179.99),(7,'Pole','pole',89.99,120),
(8,'Isolated corner','isolated corner',10.04,10.04);
INSERT INTO restaurants(id,name,name_normalized,latitude,longitude)
SELECT i,'Near '||i,'near '||i,0,0.001+(i-100)*0.0001 FROM generate_series(100,159) i;
INSERT INTO chat_sessions(id,user_id) VALUES (1,1),(2,2);
INSERT INTO chat_messages(id,session_id,role,content,status,created_at)
VALUES (1,1,'user','fixture','OK','2026-11-01T00:00Z'),
       (2,2,'user','private fixture','OK','2026-11-01T00:00Z');
ANALYZE;
"""


def verify():
    version = rows('SHOW server_version;')[0]['server_version']
    expect(version.startswith('16.'), 'PostgreSQL 16 runtime')
    expect(rows("EXECUTE s6_normalize('  PHỞ   BÒ  ');")[0]['normalized']=='pho bo',
           'Vietnamese normalization/case/whitespace')
    guest = visible_ids('EXECUTE s6_feed_latest(NULL,50,NULL,NULL);')
    viewer = visible_ids('EXECUTE s6_feed_latest(1,50,NULL,NULL);')
    expect(102 in guest and 103 not in guest, 'Guest public/hidden filtering')
    expect(102 not in viewer and 103 not in viewer, 'Reverse block before LIMIT')
    expect(not rows('EXECUTE s6_post_visible(1,102);'), 'Direct detail respects reverse block')
    expect(not rows('BEGIN; INSERT INTO user_blocks(blocker_id,blocked_id) VALUES (1,4); EXECUTE s6_post_visible(1,104); ROLLBACK;'),
           'Forward block is enforced as well')
    expect(not rows('EXECUTE s6_author_posts(1,2,10,NULL,NULL);'), 'Author posts respect block')
    expect(not rows('EXECUTE s6_saved_posts(1,13,10,NULL,NULL);'), 'Saved posts respect block')
    expect(not rows('EXECUTE s6_saved_posts(2,13,10,NULL,NULL);'), 'Foreign collection has no rows')
    image_row = next(r for r in rows('EXECUTE s6_feed_latest(NULL,50,NULL,NULL);') if r['id']=='109')
    expect(len(json.loads(image_row['images']))==2, 'Image hydration avoids duplicate posts')
    row101 = next(r for r in rows('EXECUTE s6_feed_latest(1,50,NULL,NULL);') if r['id']=='101')
    expect(row101['like_count']=='4' and row101['is_liked']=='t', 'Batch like count and viewer state')
    seen=[]
    after='NULL,NULL'
    pages=0
    while True:
        page=rows('EXECUTE s6_feed_latest(1,10,'+after+');')
        displayed=page[:10]
        seen.extend(int(r['id']) for r in displayed)
        pages+=1
        if len(page)<=10:
            break
        last=displayed[-1]
        after=literal(last['created_at'])+','+last['id']
    expect(pages>=10 and len(seen)==len(set(seen)) and len(seen)==247,
           'Deep keyset pages: no duplicate/missing rows with tied timestamps')
    hits=rows("EXECUTE s6_search(1,'PHỞ',NULL,50,NULL,NULL);")
    expect(any(r['kind']=='DISH' and r['id']=='1' for r in hits), 'Accent-insensitive catalog search')
    expect(not any(r['kind']=='POST' and r['id'] in ('102','103') for r in hits), 'Search privacy')
    expect(not rows("EXECUTE s6_search(1,'zzzznotfound','POST',10,NULL,NULL);"), 'Search empty state')
    expect(not rows("EXECUTE s6_search(1,'%%','POST',10,NULL,NULL);"), 'LIKE wildcard escaping')
    search_seen=[]
    after='NULL,NULL'
    while True:
        page=rows("EXECUTE s6_search(1,'mon',NULL,20,"+after+');')
        displayed=page[:20]
        search_seen.extend((int(r['type_rank']),int(r['id'])) for r in displayed)
        if len(page)<=20:
            break
        after=displayed[-1]['type_rank']+','+displayed[-1]['id']
    expect(len(search_seen)==338 and len(set(search_seen))==338 and search_seen==sorted(search_seen),
           'Legacy search sample only: 338 results, no duplicate or missing rows; relevance pending BE')
    expect(2 in [i for _,i in nearby(0,0.01)] and 3 not in [i for _,i in nearby(0,0.01)], 'Exact 5km filter')
    isolated=rows('EXECUTE s6_nearby_candidates('+','.join(map(str,bounds(10,10)))+');')
    expect(any(r['id']=='8' for r in isolated) and 8 not in [i for _,i in nearby(10,10)],
           'Bounding box corner removed by Haversine')
    expect(len(nearby(0,0))==50 and nearby(0,0)==sorted(nearby(0,0)), 'Nearest 50 sorted before LIMIT')
    expect(6 in [i for _,i in nearby(0,179.99)], 'Antimeridian bounding box')
    expect(7 in [i for _,i in nearby(90,0)], 'Polar bounding box')
    expect(1 <= int(rows('EXECUTE s6_random_dish;')[0]['id']) <=100,
           'Legacy random sample only: real catalog entity; BE pool pending')
    scores=rows('EXECUTE s6_score_posts('+literal(END)+');')
    byid={int(r['post_id']):r for r in scores}
    expect(Decimal(byid[101]['score'])==4 and byid[101]['savers_7d']=='2'
           and Decimal(byid[101]['dish_score'])==5,
           'BE post score L+S=4; dish contribution N+L+S=5; unique savers')
    expect(byid[108]['savers_7d']=='0', 'Old active save is not renewed by another collection')
    expect(103 not in byid and 106 not in byid and 107 not in byid and 105 in byid,
           'Window start included/end excluded/hidden/inactive excluded')
    expect(Decimal(byid[105]['score'])==0 and Decimal(byid[105]['dish_score'])==1,
           'New post without interactions has zero post score but contributes one to dish')
    expect(Decimal(byid[104]['score'])==1 and Decimal(byid[104]['dish_score'])==1,
           'Old post can trend on recent active interaction without new-post bonus')
    # Test collection removal in a transaction and roll it back before staging.
    # A direct assertion query inside DO uses the same surviving user/post grouping as Q09.
    playlist_result=sql("BEGIN; DELETE FROM collection_items WHERE collection_id=11 AND post_id=101; "
        +"CREATE TEMP TABLE score_after_one AS EXECUTE s6_score_posts("+literal(END)+"); "
        +"DO $test$ BEGIN IF (SELECT savers_7d FROM score_after_one WHERE post_id=101) IS DISTINCT FROM 2::numeric "
        +"THEN RAISE EXCEPTION 'Removing one collection removed a surviving saver'; END IF; END $test$; "
        +"DELETE FROM collection_items WHERE collection_id=10 AND post_id=101; "
        +"CREATE TEMP TABLE score_after_all AS EXECUTE s6_score_posts("+literal(END)+"); "
        +"DO $test$ BEGIN IF (SELECT savers_7d FROM score_after_all WHERE post_id=101) IS DISTINCT FROM 1::numeric "
        +"THEN RAISE EXCEPTION 'Removing final collection did not remove saver'; END IF; END $test$; ROLLBACK;")
    expect(playlist_result.returncode==0,
           'Playlist semantics: removing one save preserves user count; removing final save drops it')
    staged=[{'post_id':int(r['post_id']),'dish_id':int(r['dish_id']),
             'score':int(Decimal(r['score'])), 'dish_score':int(Decimal(r['dish_score']))} for r in scores]
    payload=literal(json.dumps(staged))
    parent_posts='ARRAY['+','.join(str(s['post_id']) for s in staged)+']::bigint[]'
    parent_dishes='ARRAY['+','.join(str(i) for i in sorted({s['dish_id'] for s in staged}))+']::bigint[]'
    sql('BEGIN; EXECUTE s6_publish_lock; EXECUTE s6_lock_posts('+parent_posts+');'
        +'EXECUTE s6_lock_dishes('+parent_dishes+');'
        +'EXECUTE s6_publish_bundle('
        +literal(END)+",'be-v1.3-unique-savers-draft',"+payload+'::jsonb); COMMIT;')
    run=int(rows('EXECUTE s6_latest_run;')[0]['id'])
    ds=rows(f'EXECUTE s6_trending_dishes(NULL,{run},50,NULL,NULL);')
    ts=rows(f'EXECUTE s6_trending_tags(NULL,{run},50,NULL,NULL);')
    expect(Decimal(next(r['score'] for r in ds if r['id']=='1'))==9,
           'BE dish score includes three new posts plus three likes plus three unique saves')
    # Dish 3 has two new posts and ranks beyond the first 50; read its cursor page.
    new_only=rows(f'EXECUTE s6_trending_dishes(NULL,{run},50,2,4);')
    expect(any(r['id']=='3' and Decimal(r['score'])==2 for r in new_only),
           'Dish with new posts but no interactions remains visible through zero-score post sources')
    expect(not ts and rows(f'SELECT count(*) AS n FROM trending_tag_snapshots WHERE run_id={run};')[0]['n']=='0',
           'BE v1 publication does not write pending Tag snapshots')
    expect(102 not in visible_ids(f'EXECUTE s6_trending_posts(1,{run},50,NULL,NULL);'), 'Snapshot read rechecks block')
    ranked=rows(f'EXECUTE s6_trending_posts(1,{run},10,NULL,NULL);')
    next_ranked=rows(f'EXECUTE s6_trending_posts(1,{run},10,'+ranked[9]['score']+','+ranked[9]['id']+');')
    expect(not ({r['id'] for r in ranked[:10]} & {r['id'] for r in next_ranked[:10]}),
           'Trending score/ID cursor handles tied scores')
    before=rows('SELECT count(*) AS n FROM trending_runs;')[0]['n']
    bad=literal(json.dumps([{'post_id':999999,'dish_id':1,'score':1,'dish_score':1}]))
    result=sql('BEGIN; EXECUTE s6_publish_bundle('+literal(END)+",'invalid',"+bad+'::jsonb); COMMIT;',check=False)
    expect(result.returncode!=0 and '23503' in result.stderr, 'Invalid publication fails FK')
    expect(rows('SELECT count(*) AS n FROM trending_runs;')[0]['n']==before,
           'Failed publication leaves no partial run; previous snapshot remains')
    holder=subprocess.Popen(['docker','exec',NAME,'psql','-X','-q','-U','postgres','-d',DB,'-c',
                             'SELECT pg_advisory_lock(7101,1); SELECT pg_sleep(5); SELECT pg_advisory_unlock(7101,1);'],
                            stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8')
    try:
        for _ in range(20):
            held=rows("SELECT EXISTS(SELECT 1 FROM pg_locks WHERE locktype='advisory' AND classid=7101 AND objid=1 AND objsubid=2 AND granted) AS held;")[0]['held']
            if held=='t':
                break
            time.sleep(0.05)
        else:
            raise AssertionError('Second connection did not acquire test lock')
        expect(rows('EXECUTE s6_publish_lock;')[0]['acquired']=='f', 'Concurrent publisher cannot acquire same advisory lock')
    finally:
        holder.communicate(timeout=15)
    expect(holder.returncode==0 and rows('EXECUTE s6_publish_lock;')[0]['acquired']=='t',
           'Publication lock is available after holder releases it')
    expect(102 not in [int(r['post_id']) for r in rows("EXECUTE s6_ai_context(1,'pho',10);")], 'AI context respects block')
    expect(visible_ids('EXECUTE s6_ai_validate_posts(1,ARRAY[101,102,103,999999]::bigint[]);')==[101],
           'AI reference validation rejects hidden/blocked/nonexistent')
    expect(not rows('EXECUTE s6_chat_history(1,2,10,NULL,NULL);'), 'Chat history owner isolation')
    sql("UPDATE chat_sessions SET created_at='2026-11-01T00:00Z' WHERE id IN (1,2); "
        +"INSERT INTO chat_sessions(id,user_id,created_at) VALUES "
        +"(3,1,'2026-11-01T00:00Z'),(4,1,'2026-11-01T00:00Z'); "
        +"INSERT INTO chat_messages(id,session_id,role,content,status,created_at) "
        +"SELECT i,1,'user','history fixture','OK','2026-11-03T00:00Z' FROM generate_series(10,14) i;")
    history_seen=[]
    before='NULL,NULL'
    while True:
        page=rows('EXECUTE s6_chat_history(1,1,2,'+before+');')
        displayed=page[:2]
        history_seen.extend(int(r['id']) for r in displayed)
        if len(page)<=2:
            break
        before=literal(displayed[-1]['created_at'])+','+displayed[-1]['id']
    expect(history_seen==[14,13,12,11,10,1], 'Chat history DESC keyset preserves tied timestamps across pages')
    sessions=rows('EXECUTE s6_chat_sessions(1,2,NULL,NULL);')
    expect([int(r['id']) for r in sessions]==[4,3,1]
           and next(r for r in sessions if r['id']=='1')['last_message_at'].startswith('2026-11-03')
           and next(r for r in sessions if r['id']=='3')['last_message_at']=='',
           'Session page owner filter, tie-break, batched lastMessageAt and empty-session NULL')
    expect(visible_ids("EXECUTE s6_chat_sessions(1,2,'2026-11-01T00:00Z',3);")==[1]
           and visible_ids('EXECUTE s6_chat_sessions(2,2,NULL,NULL);')==[2],
           'Session cursor next page and separate owner isolation')
    sql("INSERT INTO notifications(id,user_id,actor_id,type,created_at,read_at) VALUES "
        +"(201,1,3,'FOLLOW','2026-11-03T00:00Z',NULL),"
        +"(202,1,3,'FOLLOW','2026-11-03T00:00Z',NULL),"
        +"(203,1,3,'FOLLOW','2026-11-03T00:00Z',NULL),"
        +"(204,1,3,'FOLLOW','2026-11-03T00:00Z','2026-11-04T00:00Z'),"
        +"(205,2,3,'FOLLOW','2026-11-03T00:00Z',NULL);")
    inbox=rows('EXECUTE s6_notifications(1,2,NULL,NULL);')[0]
    items=json.loads(inbox['items'])
    expect([r['id'] for r in items]==[204,203,202] and inbox['unread_count']=='3',
           'Inbox first+1 owner rows with GLOBAL unreadCount beyond displayed page')
    after=literal(items[1]['created_at'])+','+str(items[1]['id'])
    next_inbox=rows('EXECUTE s6_notifications(1,2,'+after+');')[0]
    empty=rows("EXECUTE s6_notifications(1,2,'2026-11-03T00:00Z',201);")[0]
    expect([r['id'] for r in json.loads(next_inbox['items'])]==[202,201]
           and json.loads(empty['items'])==[] and empty['unread_count']=='3',
           'Inbox keyset next/empty page preserves global unreadCount')
    other=rows('EXECUTE s6_notifications(2,2,NULL,NULL);')[0]
    expect([r['id'] for r in json.loads(other['items'])]==[205] and other['unread_count']=='1',
           'Inbox and unreadCount are isolated to the authenticated owner')
    sql(f'DELETE FROM posts WHERE id=101;')
    expect(101 not in visible_ids(f'EXECUTE s6_trending_posts(NULL,{run},50,NULL,NULL);'), 'Post deletion removes snapshot entry')
    metrics={}
    for name,command in [('feed','EXECUTE s6_feed_latest(1,10,NULL,NULL)'),
                         ('search',"EXECUTE s6_search(1,'pho',NULL,10,NULL,NULL)"),
                         ('nearby_candidates','EXECUTE s6_nearby_candidates(-0.05,0.05,-0.05,0.05)')]:
        times=[]
        for _ in range(20):
            plan=json.loads(rows('EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) '+command+';')[0]['QUERY PLAN'])
            times.append(plan[0]['Execution Time'])
        metrics[name]={'samples':20,'sql_median_ms':round(statistics.median(times),3),
                       'sql_p95_ms':round(sorted(times)[18],3)}
    return {'postgresql':version,'checks_passed':len(passed),'checks':passed,
            'fixture_posts_initial':249,'fixture_posts_during_measurement':248,
            'fixture_dishes':100,'deep_pages':pages,
            'sql_only_metrics':metrics,'api_p95_measured':False}


if __name__=='__main__':
    started=False
    try:
        docker('run','--name',NAME,'--network','none','-e','POSTGRES_HOST_AUTH_METHOD=trust',
               '-e','POSTGRES_DB='+DB,'-d','postgres:16')
        started=True
        for _ in range(80):
            ready=docker('exec',NAME,'pg_isready','-U','postgres','-d',DB,check=False)
            if ready.returncode==0:
                break
            time.sleep(0.5)
        else:
            raise RuntimeError('PostgreSQL not ready')
        sql(DDL,prepare=False)
        sql(FIXTURE,prepare=False)
        result=verify()
        result['image_digest']=docker('image','inspect','postgres:16','--format','{{index .RepoDigests 0}}').stdout.strip()
        print(json.dumps(result,ensure_ascii=False,indent=2))
    finally:
        if started:
            docker('rm','-f','-v',NAME,check=False)
