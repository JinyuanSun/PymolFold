import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

def plot_ca_plddt(pdb_file, size=(5,3), dpi=120):
    plddts = []
    with open(pdb_file, "r") as f:
        lines = f.readlines()
        for line in lines:
            if " CA " in line:
                plddt = float(line[60:66])
                plddts.append(plddt)
    if max(plddts) <= 1.0:
        y = np.array([plddt * 100 for plddt in plddts])
        print("Guessing the scale is [0,1], we scale it to [0, 100]")
    else:
        y = np.array(plddts)
    x = np.arange(len(y)) + 1

    # Create color array based on conditions
    colors = np.where(y > 90, 'blue', 
              np.where((y > 70) & (y <= 90), 'lightblue', 
              np.where((y > 50) & (y <= 70), 'yellow', 'orange')))

    plt.figure(figsize=size, dpi=dpi)

    # Create scatter plot with colored markers
    plt.plot(x, y, color='black')
    plt.scatter(x, y, color=colors, zorder=10, edgecolors='black')

    plt.ylim(0, 100) # Make sure y axis is in range 0-100
    plt.xlabel('Residue')
    plt.ylabel('pLDDT')
    plt.title('Predicted LDDT per residue')

    # Create legend
    legend_elements = [mpatches.Patch(color='blue', label='Very high'),
                       mpatches.Patch(color='lightblue', label='Confident'),
                       mpatches.Patch(color='yellow', label='Low'),
                       mpatches.Patch(color='orange', label='Very low')]
    plt.legend(handles=legend_elements, title='Confidence', loc='upper left', bbox_to_anchor=(1, 1))

    plt.tight_layout() # Make sure nothing gets cropped off
    plt.show()
