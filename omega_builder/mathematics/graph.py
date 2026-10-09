"""Graph-theoretic primitives for bounded agent orchestration."""
from heapq import heappop,heappush
from math import inf, isfinite

class GraphError(ValueError):
    pass

def _graph(adj):
    if not isinstance(adj,dict) or len(adj)>1000:
        raise GraphError("Graph must be an adjacency mapping with <=1000 nodes")
    nodes=set(adj)
    if not nodes or any(not isinstance(k,str) or not k for k in nodes):
        raise GraphError("Nodes must be nonempty strings")
    out={}
    for source,edges in adj.items():
        if not isinstance(edges,dict) or any(target not in nodes for target in edges):
            raise GraphError("All targets must be declared")
        row={}
        for target,cost in edges.items():
            if type(cost) not in (float,int) or not isfinite(float(cost)) or cost<0:
                raise GraphError("Dijkstra requires finite nonnegative weights")
            row[target]=float(cost)
        out[source]=row
    return out

def dijkstra(adj,start,target=None):
    adj=_graph(adj)
    if start not in adj or target is not None and target not in adj:
        raise GraphError("Unknown start or target")
    dist={v:inf for v in adj}
    prev={}
    dist[start]=0.
    queue=[(0.,start)]
    while queue:
        cost,here=heappop(queue)
        if cost>dist[here]:
            continue
        if here==target:
            break
        for there,w in adj[here].items():
            new=cost+w
            if new<dist[there]:
                dist[there]=new
                prev[there]=here
                heappush(queue,(new,there))
    if target is None:
        return dist
    if dist[target]==inf:
        return {"distance":None,"path":[]}
    path=[target]
    while path[-1]!=start:
        path.append(prev[path[-1]])
    return {"distance":dist[target],"path":list(reversed(path))}

def topological_sort(adj):
    adj=_graph(adj)
    indegree={v:0 for v in adj}
    for edges in adj.values():
        for to in edges:
            indegree[to]+=1
    queue=sorted(v for v,d in indegree.items() if d==0)
    out=[]
    while queue:
        node=queue.pop(0)
        out.append(node)
        for target in sorted(adj[node]):
            indegree[target]-=1
            if indegree[target]==0:
                queue.append(target)
                queue.sort()
    if len(out)!=len(adj):
        raise GraphError("Cycle detected; graph is not a DAG")
    return out

def adjacency_matrix(adj):
    adj=_graph(adj)
    keys=sorted(adj)
    return {"nodes":keys,"weights":[[adj[src].get(dst,0.) for dst in keys] for src in keys]}

def laplacian(adj):
    """Undirected, nonnegative weighted graph combinatorial Laplacian L=D-A."""
    adj=_graph(adj)
    for u,edges in adj.items():
        for v,w in edges.items():
            if u!=v and adj[v].get(u)!=w:
                raise GraphError("Laplacian requires symmetric weights")
    matrix=adjacency_matrix(adj)
    keys=matrix["nodes"]
    a=matrix["weights"]
    n=len(keys)
    return {"nodes":keys,"matrix":[[(sum(a[i])-a[i][i] if i==j else 0.)-a[i][j]
                                    for j in range(n)] for i in range(n)]}
