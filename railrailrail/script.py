import csv
import json
from railrailrail.railgraph import RailGraph

# Setup
rail_graph = RailGraph.from_file(
    "config/network_tel_4.toml",
    "config/station_coordinates.csv"
)

# Get all valid station codes (exclude pseudo station codes)
stations = [
    code for code, station in rail_graph.station_code_to_station.items()
    if not station.has_pseudo_station_code
]

rows = []
count = 0
for start in stations:
    for end in stations:
        if start == end:
            continue
        try:
            pathinfo = rail_graph.find_shortest_path(start, end)
        except Exception:
            continue  # skip invalid pairs
        if not pathinfo or not pathinfo.nodes:
            continue
        nodes = pathinfo.nodes
        edges = pathinfo.edges
        costs = pathinfo.costs
        total_cost = pathinfo.total_cost
        row = {
            "origin": start,
            "destination": end,
            "total_cost": total_cost,
            "nodes": json.dumps(nodes).replace('"', "'"),
            "edges": json.dumps(edges),
            "costs": json.dumps(costs)
        }
        rows.append(row)
        count += 1
        if count % 100 == 0:
            print(f"Processed {count} routes...")

# Write all results to a single CSV
if rows:
    with open("all_routes.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"Done: all_routes.csv generated with {len(rows)} routes.")
else:
    print("No routes found.")