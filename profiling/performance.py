import pstats
import os
import pandas as pd
from io import StringIO


def analyse(stats_file):
    stats = pstats.Stats(stats_file)

    # Convert stats to a readable string
    s = StringIO()
    stats.stream = s
    stats.sort_stats("cumulative")  # Sort by cumulative time
    stats.print_stats()

    # Get a list of all python files in the current directory
    files = [f for f in os.listdir() if f.endswith(".py")]

    # Split the stats into lines
    lines = s.getvalue().split("\n")

    # Filter out lines that don't contain a file name
    # lines = [line for line in lines if any(file in line for file in files)]

    # Read the stats output into a DataFrame
    data = []
    for line in lines[5:]:  # Skip header lines
        parts = line.split()
        if len(parts) >= 6:  # Ensure it's a valid data row
            try:
                ncalls = parts[0]  # Number of calls
                tottime = float(parts[1])  # Total time in function
                percall1 = float(parts[2])  # Time per call (total)
                cumtime = float(parts[3])  # Cumulative time
                percall2 = float(parts[4])  # Time per call (cumulative)
                func = " ".join(parts[5:])  # Function name
                data.append((ncalls, tottime, percall1, cumtime, percall2, func))
            except ValueError:
                continue  # Skip malformed lines

    # Create DataFrame
    df = pd.DataFrame(data, columns=["ncalls", "tottime", "percall_total", "cumtime", "percall_cum", "function"])
    df["ncalls"] = df["ncalls"].astype(str).str.replace(r"\D", "", regex=True).astype(float)  # Clean up ncalls

    return df
