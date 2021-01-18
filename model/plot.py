#!/usr/bin/env python3

"""
plot.py: plot log of ESD system behavior
"""

import matplotlib.pyplot as plt

def main():
    """
    Main function: plot the simulation.
    """
    
    # This will hold the headings for columns
    headings = []
    # This will hold each column, as a list
    columns = []

    log = open("log.tsv")
    for line in log:
        line = line.strip()
        if line == '':
            continue
        parts = line.split('\t')
        if parts[0].startswith('#'):
            # This is a header
            headings = parts
            headings[0] = headings[0][1:].strip()
        else:
            # This is data. Assume all columns are the same length
            for i, item in enumerate(parts):
                if len(columns) <= i:
                    columns.append([])
                columns[i].append(float(item))
                
    # Now plot
    
    # Find what to plot against
    x_heading = "block"
    x_column_number = headings.index(x_heading)
    if x_column_number == -1:
        raise RuntimeError("No column: " + x_heading)
        
    fig, axes = plt.subplots(len(columns) - 1, 1, sharex=True)
    fig.suptitle('ESD Simulation Results')

    axis_cursor = 0
        
    for column_number in range(len(columns)):
        if column_number == x_column_number:
            # Don't plot against self
            continue
            
        # Plot this column against the designated x
        ax = axes[axis_cursor]
        ax.plot(columns[x_column_number], columns[column_number], '-')
        ax.set_xlabel(headings[x_column_number])
        ax.set_ylabel(headings[column_number])
        
        if headings[column_number] == "price":
            # Special axes here so we can see 1.0
            ax.set_ylim(0, 2)
            ax.set_yticks([0, 0.7, 1, 1.3, 2])
            ax.hlines(1.0, min(columns[x_column_number]), max(columns[x_column_number]))
        
        # Make the next plot on the next axes
        axis_cursor += 1
            
    # Show all the plots
    plt.show()
    
if __name__ == "__main__":
    main()
