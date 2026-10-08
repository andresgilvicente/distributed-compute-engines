"""Monte Carlo estimation of pi on a Ray cluster."""

import os
import time

import numpy as np
import ray
from dotenv import load_dotenv

# Load the cluster configuration from the .env file
load_dotenv()

ray.init(
    address=f"ray://{os.getenv('HOST')}:{os.getenv('HEADNODEPORT')}",
    dashboard_port=int(os.getenv("DASHBOARDPORT")),
)

# Number of tasks the workload is split into
NUM_TASKS = 200

# Total number of points per experiment: 5, 10 and 50 million
POINT_COUNTS = [n * 1_000_000 for n in (5, 10, 50)]


@ray.remote
def count_points_in_circle(total_points: int) -> int:
    """Count random points that fall inside the unit circle.

    Each task handles its share of the experiment (total_points // NUM_TASKS).

    Args:
        total_points: Total number of points of the whole experiment.

    Returns:
        Number of points with x^2 + y^2 <= 1.
    """
    points_per_task = total_points // NUM_TASKS
    x = np.random.random(points_per_task)
    y = np.random.random(points_per_task)
    return int(((x**2 + y**2) <= 1).sum())


for total_points in POINT_COUNTS:
    start = time.time()

    # .remote() is non-blocking: it returns an ObjectRef (a future) per task
    futures = [count_points_in_circle.remote(total_points) for _ in range(NUM_TASKS)]

    # ray.get() blocks until every task finishes
    # pi = 4 * (points inside the circle / total points)
    pi = 4 * sum(ray.get(futures)) / total_points

    elapsed = time.time() - start
    print(
        f"Points: {total_points}, Pi: {pi}, "
        f"Time: {elapsed:.3f} s, Throughput: {total_points / elapsed:.0f} points/s"
    )
