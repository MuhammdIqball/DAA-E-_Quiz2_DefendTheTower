from collections import deque
import heapq


def find_shortest_path(grid, start, end, rows, cols):
    if grid[start[1]][start[0]] == 1 or grid[end[1]][end[0]] == 1:
        return None

    queue = deque()
    queue.append(start)
    visited = {start: None}
    directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]

    while queue:
        current = queue.popleft()

        if current == end:
            path = []
            node = end
            while node is not None:
                path.append(node)
                node = visited[node]
            path.reverse()
            return path

        cx, cy = current
        for dx, dy in directions:
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < cols and 0 <= ny < rows:
                if (nx, ny) not in visited and grid[ny][nx] != 1:
                    visited[(nx, ny)] = current
                    queue.append((nx, ny))

    return None


def is_path_exists(grid, start, end, rows, cols):
    return find_shortest_path(grid, start, end, rows, cols) is not None


def dijkstra(grid, start, end, rows, cols):
    if grid[start[1]][start[0]] == 1 or grid[end[1]][end[0]] == 1:
        return None

    dist = {start: 0}
    parent = {start: None}
    heap = [(0, start[0], start[1])]
    directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]

    while heap:
        cost, cx, cy = heapq.heappop(heap)
        current = (cx, cy)

        if current == end:
            path = []
            node = end
            while node is not None:
                path.append(node)
                node = parent[node]
            path.reverse()
            return path

        if cost > dist.get(current, float('inf')):
            continue

        for dx, dy in directions:
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < cols and 0 <= ny < rows:
                if grid[ny][nx] != 1:
                    new_cost = cost + 1
                    neighbor = (nx, ny)
                    if new_cost < dist.get(neighbor, float('inf')):
                        dist[neighbor] = new_cost
                        parent[neighbor] = current
                        heapq.heappush(heap, (new_cost, nx, ny))

    return None

