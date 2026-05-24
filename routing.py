import math
from models import Warehouse

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two points
    on the Earth in kilometers.
    """
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return float('inf')
    
    R = 6371.0  # Earth radius in kilometers
    
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) *
         math.sin(delta_lambda / 2.0) ** 2)
         
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

def build_warehouse_graph():
    """
    Constructs an undirected graph of warehouses.
    Each warehouse is connected to its K-nearest neighbors (K=3)
    to ensure connectivity without generating a fully connected graph.
    """
    warehouses = Warehouse.query.all()
    # Initialize adjacency list
    graph = {w.warehouse_code: {} for w in warehouses}
    
    K = 3
    for w in warehouses:
        if w.lat is None or w.lng is None:
            continue
            
        distances = []
        for other in warehouses:
            if other.id == w.id or other.lat is None or other.lng is None:
                continue
                
            dist = haversine_distance(w.lat, w.lng, other.lat, other.lng)
            distances.append((dist, other))
            
        # Sort by distance and pick the K nearest neighbors
        distances.sort(key=lambda x: x[0])
        for dist, other in distances[:K]:
            # Add undirected edge (symmetric weights)
            graph[w.warehouse_code][other.warehouse_code] = dist
            graph[other.warehouse_code][w.warehouse_code] = dist
            
    return graph

def dijkstra(graph, start, end):
    """
    Find the shortest path between start and end nodes
    in the graph using Dijkstra's algorithm.
    """
    import heapq
    
    # Priority queue stores: (accumulated_distance, current_node, path_taken)
    queue = [(0, start, [start])]
    visited = set()
    
    while queue:
        cost, current, path = heapq.heappop(queue)
        
        if current in visited:
            continue
            
        visited.add(current)
        
        if current == end:
            return cost, path
            
        for neighbor, weight in graph.get(current, {}).items():
            if neighbor not in visited:
                heapq.heappush(queue, (cost + weight, neighbor, path + [neighbor]))
                
    return float('inf'), []
