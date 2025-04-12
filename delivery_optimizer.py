import openrouteservice
from openrouteservice import convert
from ortools.constraint_solver import pywrapcp, routing_enums_pb2
import os
from dotenv import load_dotenv

load_dotenv()

def geocode_addresses(client, addresses):
    coords = []
    for address in addresses:
        res = client.pelias_search(text=address)
        if not res or "features" not in res or len(res["features"]) == 0:
            raise ValueError(f"Geocoding failed for: {address}")
        coord = res["features"][0]["geometry"]["coordinates"]
        coords.append(coord)
    return coords

def create_distance_matrix(client, coords):
    matrix = client.distance_matrix(locations=coords, profile='driving-car', metrics=['distance'], resolve_locations=True)
    return matrix['distances']

def optimize_route(addresses):
    client = openrouteservice.Client(key=os.getenv("ORS_API_KEY"))
    coords = geocode_addresses(client, addresses)
    distance_matrix = create_distance_matrix(client, coords)

    manager = pywrapcp.RoutingIndexManager(len(distance_matrix), 1, 0)
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        return int(distance_matrix[manager.IndexToNode(from_index)][manager.IndexToNode(to_index)])

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC

    solution = routing.SolveWithParameters(search_parameters)

    if solution:
        index = routing.Start(0)
        optimized_order = []
        while not routing.IsEnd(index):
            optimized_order.append(manager.IndexToNode(index))
            index = solution.Value(routing.NextVar(index))
        optimized_order.append(manager.IndexToNode(index))  # return to depot

        route = [addresses[i] for i in optimized_order]
        ordered_coords = [coords[i][::-1] for i in optimized_order]  # [lat, lon]
        
        total_distance = sum(
            distance_matrix[optimized_order[i]][optimized_order[i + 1]]
            for i in range(len(optimized_order) - 1)
        )

        return route, total_distance, ordered_coords
    else:
        return None, None, None
