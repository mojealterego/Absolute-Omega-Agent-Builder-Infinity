"""Offline SQLite primitives: key/value, time-series, relations, vectors and temporal facts.

Not a distributed NoSQL/GraphDB/VectorDB/lakehouse system. SQLite commits are
transactional on one node. Embeddings must be supplied, never inferred.
"""
from __future__ import annotations
import json
import sqlite3
from datetime import datetime,timezone
from math import sqrt,fsum,isfinite


class StoreError(ValueError):
    pass


def _key(s):
    if not isinstance(s,str) or not 1<=len(s)<=512:
        raise StoreError("Key must be a nonempty string <=512 characters")
    return s


def _number(x):
    if type(x) not in (int,float):
        raise StoreError("Expected numeric real")
    y=float(x)
    if not isfinite(y):
        raise StoreError("Number must be finite")
    return y


def _vector(v):
    if not isinstance(v,(list,tuple)) or not 1<=len(v)<=2048:
        raise StoreError("Vector dimension must be 1..2048")
    out=[_number(x) for x in v]
    if fsum(x*x for x in out)==0:
        raise StoreError("Zero vector not supported for cosine retrieval")
    return out


def _serialize(value):
    try:
        data=json.dumps(value,ensure_ascii=False,allow_nan=False,sort_keys=True)
    except (ValueError,TypeError) as exc:
        raise StoreError("Value must be JSON serializable and finite") from exc
    if len(data)>500000:
        raise StoreError("JSON value too large")
    return data


class SQLiteKnowledgeStore:
    def __init__(self,path=":memory:"):
        if not isinstance(path,str) or not path:
            raise StoreError("SQLite file path must be a nonempty string")
        self.db=sqlite3.connect(path)
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS kv (
              key TEXT PRIMARY KEY, value_json TEXT NOT NULL,
              provenance TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS relations (
              subject TEXT NOT NULL, predicate TEXT NOT NULL, object TEXT NOT NULL,
              provenance TEXT NOT NULL,
              PRIMARY KEY(subject,predicate,object));
            CREATE TABLE IF NOT EXISTS ts (
              series TEXT NOT NULL, timestamp_ms INTEGER NOT NULL,
              value REAL NOT NULL, provenance TEXT NOT NULL,
              PRIMARY KEY(series,timestamp_ms));
            CREATE TABLE IF NOT EXISTS vectors (
              key TEXT PRIMARY KEY, vector_json TEXT NOT NULL,
              provenance TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS lineage (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              source TEXT NOT NULL, target TEXT NOT NULL,
              operation TEXT NOT NULL, provenance TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS temporal_facts (
              id INTEGER PRIMARY KEY AUTOINCREMENT, fact_key TEXT NOT NULL,
              value_json TEXT NOT NULL,
              valid_from_ms INTEGER NOT NULL, valid_to_ms INTEGER NOT NULL,
              recorded_ms INTEGER NOT NULL, provenance TEXT NOT NULL,
              CHECK(valid_to_ms > valid_from_ms));
            CREATE INDEX IF NOT EXISTS ix_temp
              ON temporal_facts(fact_key,recorded_ms,valid_from_ms,valid_to_ms);
        """)

    def close(self):
        self.db.close()

    def __enter__(self):
        return self

    def __exit__(self,*args):
        self.close()

    def put_kv(self,key,value,provenance="user"):
        key,provenance=_key(key),_key(provenance)
        body=_serialize(value)
        with self.db:
            self.db.execute("INSERT INTO kv VALUES (?,?,?) ON CONFLICT(key) DO UPDATE SET value_json=excluded.value_json,provenance=excluded.provenance",(key,body,provenance))

    def get_kv(self,key):
        row=self.db.execute("SELECT value_json,provenance FROM kv WHERE key=?",(_key(key),)).fetchone()
        return None if row is None else {"value":json.loads(row[0]),"provenance":row[1]}

    def add_relation(self,subject,predicate,object,provenance="user"):
        vals=tuple(_key(x) for x in (subject,predicate,object,provenance))
        with self.db:
            self.db.execute("INSERT OR IGNORE INTO relations VALUES (?,?,?,?)",vals)

    def neighbors(self,subject,predicate=None):
        _key(subject)
        if predicate is not None:
            _key(predicate)
            rows=self.db.execute("SELECT predicate,object,provenance FROM relations WHERE subject=? AND predicate=? ORDER BY object LIMIT 1000",(subject,predicate))
        else:
            rows=self.db.execute("SELECT predicate,object,provenance FROM relations WHERE subject=? ORDER BY predicate,object LIMIT 1000",(subject,))
        return [{"predicate":p,"object":o,"provenance":source} for p,o,source in rows]

    def add_timeseries(self,series,timestamp_ms,value,provenance="user"):
        _key(series);_key(provenance)
        if type(timestamp_ms) is not int:
            raise StoreError("Timestamp must be integer epoch milliseconds")
        with self.db:
            self.db.execute("INSERT INTO ts VALUES (?,?,?,?)",(series,timestamp_ms,_number(value),provenance))

    def query_timeseries(self,series,start_ms,end_ms):
        _key(series)
        if type(start_ms) is not int or type(end_ms) is not int or start_ms>end_ms:
            raise StoreError("Invalid time window")
        rows=self.db.execute("SELECT timestamp_ms,value,provenance FROM ts WHERE series=? AND timestamp_ms BETWEEN ? AND ? ORDER BY timestamp_ms LIMIT 10000",(series,start_ms,end_ms))
        return [{"timestamp_ms":t,"value":v,"provenance":p} for t,v,p in rows]

    def put_vector(self,key,vector,provenance="user"):
        key,provenance=_key(key),_key(provenance)
        data=_serialize(_vector(vector))
        with self.db:
            self.db.execute("INSERT INTO vectors VALUES (?,?,?) ON CONFLICT(key) DO UPDATE SET vector_json=excluded.vector_json,provenance=excluded.provenance",(key,data,provenance))

    def search_vector(self,vector,top_k=5):
        v=_vector(vector)
        if type(top_k) is not int or not 1<=top_k<=100:
            raise StoreError("top_k must be 1..100")
        candidates=[]
        length=sqrt(fsum(x*x for x in v))
        for key,raw,provenance in self.db.execute("SELECT key,vector_json,provenance FROM vectors LIMIT 10001"):
            if len(candidates)>=10000:
                raise StoreError("Exact vector search limited to 10000 records")
            w=json.loads(raw)
            if len(w)!=len(v):
                continue
            den=length*sqrt(fsum(x*x for x in w))
            score=fsum(x*y for x,y in zip(v,w))/den
            candidates.append({"key":key,"score":score,"provenance":provenance})
        return sorted(candidates,key=lambda r:(-r["score"],r["key"]))[:top_k]

    def record_lineage(self,source,target,operation,provenance="user"):
        vals=tuple(_key(x) for x in (source,target,operation,provenance))
        with self.db:
            cursor=self.db.execute("INSERT INTO lineage(source,target,operation,provenance) VALUES (?,?,?,?)",vals)
        return cursor.lastrowid

    def get_lineage(self,target):
        rows=self.db.execute("SELECT id,source,operation,provenance FROM lineage WHERE target=? ORDER BY id LIMIT 1000",(_key(target),))
        return [{"id":i,"source":s,"operation":o,"provenance":p} for i,s,o,p in rows]

    def add_temporal_fact(self,key,value,valid_from_ms,valid_to_ms,recorded_ms,provenance="user"):
        """Append-only bitemporal event; caller supplies recorded/valid times.

        A later recorded event supersedes an earlier event for the same key
        AND only on the overlapping valid-time interval. JSON null is tombstone.
        """
        _key(key);_key(provenance)
        times=(valid_from_ms,valid_to_ms,recorded_ms)
        if any(type(x) is not int for x in times) or valid_from_ms>=valid_to_ms:
            raise StoreError("Invalid bitemporal timestamps")
        with self.db:
            self.db.execute("""INSERT INTO temporal_facts
              (fact_key,value_json,valid_from_ms,valid_to_ms,recorded_ms,provenance)
              VALUES (?,?,?,?,?,?)""",
              (key,_serialize(value),*times,provenance))

    def fact_at(self,key,valid_ms,known_ms):
        """Valid-time and transaction-time snapshot. No external clock assumptions."""
        _key(key)
        if type(valid_ms) is not int or type(known_ms) is not int:
            raise StoreError("Timestamps must be integers")
        row=self.db.execute("""SELECT value_json,recorded_ms,provenance
             FROM temporal_facts
             WHERE fact_key=? AND valid_from_ms<=? AND valid_to_ms>?
               AND recorded_ms<=?
             ORDER BY recorded_ms DESC, id DESC LIMIT 1""",
             (key,valid_ms,valid_ms,known_ms)).fetchone()
        if row is None:
            return None
        data=json.loads(row[0])
        if data is None:
            return None
        return {"value":data,"recorded_ms":row[1],"provenance":row[2]}
